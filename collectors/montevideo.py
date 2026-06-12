"""
Collector de Montevideo Portal (montevideo.com.uy).

Cloudflare bloquea los sitemaps y el RSS legacy esta de baja (ver MEDIOS.md).
Las notas comerciales llevan tag/categoria "Empresariales".

Fuentes:
  1. Pagina de tag https://www.montevideo.com.uy/tag/Empresariales  (alta precision)
  2. Home server-side: URLs <Categoria>/<slug>-uc<ID>                (resto de notas)
  3. Google News RSS site:montevideo.com.uy                          (complemento)
"""

import logging
import re
from urllib.parse import urlparse

from . import common

logger = logging.getLogger("collectors.montevideo")

TAG_EMPRESARIALES = "https://www.montevideo.com.uy/tag/Empresariales"
HOME = "https://www.montevideo.com.uy/"
GNEWS = ("https://news.google.com/rss/search?"
         "q=site:montevideo.com.uy%20when:7d&hl=es-419&gl=UY&ceid=UY:es")

RE_NOTA = re.compile(r"https://www\.montevideo\.com\.uy/([A-Za-z][\w-]*)/([^\"'<>\s]+-uc\d+)")
IGNORAR_CATEGORIAS = ("SIN-CATEGORIZAR", "categoria", "tag")  # tienda/productos y listados


def _extraer_notas(html_str: str, candidata: bool) -> list[dict]:
    items = []
    for m in RE_NOTA.finditer(html_str):
        cat, slug = m.group(1), m.group(2)
        if cat in IGNORAR_CATEGORIAS:
            continue
        url = f"https://www.montevideo.com.uy/{cat}/{slug}"
        titulo = slug.rsplit("-uc", 1)[0].replace("-", " ").strip()
        items.append({
            "medio": "montevideo",
            "url": url,
            "titulo": titulo or None,
            "seccion": cat,
            "fecha": None,  # el portal no expone fecha en el listado
            "candidata": candidata or cat.lower() == "empresariales",
        })
    return items


def collect() -> list[dict]:
    items, vistos = [], set()

    # 1. Tag Empresariales: todo lo que liste es comercial, pero es un archivo
    # historico → hay que confirmar la fecha de cada nota (datePublished del JSON-LD)
    resp = common.get(TAG_EMPRESARIALES)
    if resp:
        for it in _extraer_notas(resp.text, candidata=True):
            if it["url"] in vistos:
                continue
            vistos.add(it["url"])
            nota = common.get(it["url"])
            if not nota:
                continue
            fecha = re.search(r'"datePublished"\s*:\s*"([^"]+)"', nota.text)
            it["fecha"] = fecha.group(1) if fecha else None
            if not common.dentro_de_ventana(it["fecha"]):
                print(f"  · tag Empresariales: descartada por vieja ({it['fecha']}) "
                      f"{(it['titulo'] or '')[:60]}", flush=True)
                continue
            titulo_real = common.meta_title(nota.text)
            if titulo_real:
                it["titulo"] = titulo_real
            it["bajada"] = common.meta_description(nota.text)
            it["señales"] = ["tag Empresariales"]
            print(f"    ✔ COMERCIAL (tag Empresariales, {it['fecha'] or 's/f'}): "
                  f"{(it['titulo'] or '')[:65]}", flush=True)
            items.append(it)

    # 2. Home (notas del dia, server-side)
    resp = common.get(HOME)
    if resp:
        for it in _extraer_notas(resp.text, candidata=False):
            if it["url"] not in vistos:
                vistos.add(it["url"])
                items.append(it)

    # 3. Google News (titulos reales + cobertura de la semana)
    import unicodedata

    def _norm_titulo(t):
        s = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode()
        return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()

    titulos_vistos = {_norm_titulo(i["titulo"]) for i in items if i.get("titulo")}
    resp = common.get(GNEWS)
    if resp:
        for m in re.finditer(r"<item>(.*?)</item>", resp.text, re.S):
            block = m.group(1)
            t = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", block, re.S)
            titulo = re.sub(r"\s*-\s*Montevideo Portal\s*$", "", t.group(1)).strip() if t else None
            if not titulo:
                continue
            # Google News redirige; usamos la URL del redirector como referencia
            link = re.search(r"<link>([^<]+)</link>", block)
            fecha = re.search(r"<pubDate>([^<]+)</pubDate>", block)
            key = _norm_titulo(titulo)
            if key in titulos_vistos:
                continue
            titulos_vistos.add(key)
            items.append({
                "medio": "montevideo",
                "url": link.group(1) if link else None,
                "titulo": titulo,
                "seccion": None,
                "fecha": fecha.group(1) if fecha else None,
                "candidata": False,
            })

    logger.info("Montevideo Portal: %d notas (%d via tag Empresariales)",
                len(items), sum(1 for i in items if "tag Empresariales" in i.get("señales", [])))
    return items
