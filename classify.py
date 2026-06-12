"""
Clasificador de contenido comercial + extraccion de marca.

Flujo:
  1. Heuristica barata sobre titulo/seccion (lexico de gacetilla, tag Empresariales,
     patron de El Observador) → arma el pool de candidatas.
  2. Si hay GEMINI_API_KEY: un solo prompt batch con Gemini Flash clasifica los
     titulos de la semana de los medios sin marca explicita (El País, la diaria,
     Montevideo Portal no-tag) y extrae la marca de cada nota comercial.
  3. Para candidatas heuristicas sin LLM, fetch del HTML buscando MARCADORES_COMERCIALES.

La key de Gemini se resuelve: env GEMINI_API_KEY → .env → Secret Manager observadordw.
Sin key, el pipeline funciona igual con heuristicas (menor recall en El País/la diaria).
"""

import json
import logging
import os
import re
import subprocess

import requests

import config
from collectors import common

logger = logging.getLogger("classify")


def _norm(s: str) -> str:
    import unicodedata
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower().strip()

GEMINI_URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
              f"{config.GEMINI_MODEL}:generateContent")

PROMPT_BATCH = """Sos analista del equipo comercial de El Observador (diario uruguayo).
Te paso una lista de titulares publicados esta semana en medios uruguayos.

Identifica cuales son CONTENIDO COMERCIAL: notas que existen por un acuerdo de pauta
(branded content, gacetilla empresarial, publirreportaje): lanzamientos de producto,
campañas publicitarias, aniversarios de empresa, aperturas de locales, alianzas de marca,
promociones, "empresariales".

NO es comercial la cobertura editorial donde una empresa es noticia: resultados financieros,
conflictos, fusiones/adquisiciones reportadas por periodistas, politica, deporte, policiales.
Tampoco: noticias internacionales de empresas (ej. "Goldman Sachs reorganiza sus negocios",
"Prada diseña trajes para la NASA"), llamados laborales o licitaciones de entes publicos,
resultados de loterias/quinielas, ni autopromocion del propio medio (newsletters, canales
de WhatsApp, crucigramas del diario).

Para cada nota COMERCIAL devolve la marca/empresa protagonista (nombre corto y limpio,
ej. "Claro", "DEEPAL", "Banco Itaú").

Titulares (formato id | medio | seccion | titulo):
{listado}

Devolve SOLO un JSON (sin markdown) con esta forma:
{{"comerciales": [{{"id": 12, "marca": "Claro", "confianza": 0.9}}]}}
Si ninguna es comercial: {{"comerciales": []}}"""

PROMPT_MARCA = """Del siguiente titular y bajada de una nota comercial publicada en un
diario uruguayo, extrae la marca/empresa protagonista (nombre corto, ej. "Claro").
Titular: {titulo}
Bajada: {bajada}
Devolve SOLO un JSON: {{"marca": "..."}} (o {{"marca": null}} si no se identifica)."""


# ============================================================
# Gemini
# ============================================================

def resolver_api_key() -> str | None:
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    if os.path.exists(".env"):
        for line in open(".env", encoding="utf-8"):
            if line.strip().startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"')
    try:
        out = subprocess.run(
            ["gcloud", "secrets", "versions", "access", "latest",
             "--secret", config.GCP_SECRET_NAME, "--project", config.GCP_PROJECT_SECRETS],
            capture_output=True, text=True, timeout=30,
        )
        if out.returncode == 0 and out.stdout.strip():
            logger.info("GEMINI_API_KEY obtenida de Secret Manager (%s)", config.GCP_PROJECT_SECRETS)
            return out.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    logger.warning("Sin GEMINI_API_KEY: se usa solo heuristica (menor recall en El País/la diaria)")
    return None


def _gemini(prompt: str, api_key: str) -> dict | None:
    try:
        resp = requests.post(
            GEMINI_URL,
            params={"key": api_key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
            },
            timeout=90,
        )
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except Exception as e:
        logger.error("Error llamando a Gemini: %s", e)
        return None


# ============================================================
# Heuristica
# ============================================================

def señales_heuristicas(item: dict) -> list[str]:
    señales = list(item.get("señales", []))
    titulo = (item.get("titulo") or "").lower()
    for w in config.LEXICO_GACETILLA:
        if w in titulo:
            señales.append(f"lexico:{w}")
    return señales


def confirmar_con_html(item: dict) -> bool:
    """Baja la nota y busca marcadores comerciales explicitos."""
    if not item.get("url") or "news.google.com" in (item.get("url") or ""):
        return False
    resp = common.get(item["url"])
    if not resp:
        return False
    marcadores = common.buscar_marcadores(resp.text)
    if marcadores:
        item.setdefault("señales", []).extend(f"marcador:{m}" for m in marcadores)
    if not item.get("bajada"):
        item["bajada"] = common.meta_description(resp.text)
    return bool(marcadores)


# ============================================================
# Pipeline de clasificacion
# ============================================================

def clasificar(items: list[dict]) -> list[dict]:
    """Marca cada item con es_comercial, marca y señales. Devuelve la misma lista."""
    api_key = resolver_api_key()

    for it in items:
        it["señales"] = señales_heuristicas(it)
        it["es_comercial"] = False
        it["marca"] = None

    # 1. Alta precision sin LLM
    for it in items:
        if it["medio"] == "elobservador" and it.get("es_comercial_confirmado"):
            it["es_comercial"] = True
        if it["medio"] == "montevideo" and "tag Empresariales" in it["señales"]:
            it["es_comercial"] = True

    # 2. Batch LLM sobre titulos del resto
    pendientes = [it for it in items
                  if not it["es_comercial"] and it.get("titulo")
                  and not (it["medio"] == "elobservador" and it.get("candidata") is False
                           and it.get("seccion"))]
    # El Observador con seccion = editorial seguro; igual el LLM ve el resto
    if api_key and pendientes:
        total_lotes = (len(pendientes) + 79) // 80
        print(f"\n→ Clasificando {len(pendientes)} titulares con Gemini en {total_lotes} lotes...")
        for lote_ini in range(0, len(pendientes), 80):
            lote = pendientes[lote_ini:lote_ini + 80]
            print(f"  · lote {lote_ini // 80 + 1}/{total_lotes} ({len(lote)} titulares)", flush=True)
            listado = "\n".join(
                f"{i} | {config.MEDIOS[it['medio']]['nombre']} | {it.get('seccion') or '-'} | {it['titulo']}"
                for i, it in enumerate(lote)
            )
            out = _gemini(PROMPT_BATCH.format(listado=listado), api_key)
            if not out:
                continue
            for hit in out.get("comerciales", []):
                try:
                    it = lote[int(hit["id"])]
                except (KeyError, ValueError, IndexError):
                    continue
                it["es_comercial"] = True
                it["marca"] = (hit.get("marca") or "").strip() or None
                it["señales"].append(f"llm:{hit.get('confianza', '')}")
                print(f"    ✔ COMERCIAL [{config.MEDIOS[it['medio']]['nombre']}] "
                      f"{it['marca'] or '?'} :: {(it['titulo'] or '')[:75]}", flush=True)
    else:
        # Sin LLM: candidatas heuristicas se confirman con marcadores en HTML
        for it in pendientes:
            if any(s.startswith("lexico:") for s in it["señales"]):
                if confirmar_con_html(it):
                    it["es_comercial"] = True

    # 3. Extraer marca donde falte
    for it in items:
        if it["es_comercial"] and not it["marca"]:
            it["marca"] = extraer_marca(it, api_key)
            if it["marca"]:
                print(f"    · marca extraida: {it['marca']} ({it['medio']})", flush=True)

    # 4. Descartar autopromocion del propio medio
    for it in items:
        if it["es_comercial"] and it.get("marca"):
            if _norm(it["marca"]) == _norm(config.MEDIOS[it["medio"]]["nombre"]):
                it["es_comercial"] = False
                it["señales"].append("descartada:autopromocion")

    n = sum(1 for i in items if i["es_comercial"])
    logger.info("Clasificacion: %d notas comerciales sobre %d", n, len(items))
    return items


def extraer_marca(item: dict, api_key: str | None) -> str | None:
    if api_key:
        out = _gemini(PROMPT_MARCA.format(
            titulo=item.get("titulo") or "",
            bajada=item.get("bajada") or "",
        ), api_key)
        if out and out.get("marca"):
            return str(out["marca"]).strip()
    # Fallback: primera palabra capitalizada "rara" del titulo
    titulo = item.get("titulo") or ""
    m = re.match(r"^([A-ZÁÉÍÓÚÜÑ][\w&áéíóúüñ]+(?:\s+[A-ZÁÉÍÓÚÜÑ][\w&áéíóúüñ]+)?)", titulo)
    return m.group(1) if m else None
