"""
Corrida semanal del identificador de contenido comercial.

  python run_weekly.py            # colecta + clasifica + cruza + genera dashboard
  python run_weekly.py --solo elobservador montevideo

Salidas:
  data/latest.json      -> datos de la corrida (para el dashboard)
  data/<YYYY>-W<WW>.json -> snapshot historico de la semana ISO
  dashboard.html        -> dashboard standalone (doble click)
"""

import argparse
import datetime
import json
import logging
import os
import unicodedata

import config
import classify
from collectors import COLLECTORS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_weekly")


def normalizar(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return s.lower().strip()


def cruzar_marcas(items: list[dict]) -> dict:
    """Agrupa por marca: en que medios pauto y si El Observador le dedico nota."""
    comerciales = [i for i in items if i.get("es_comercial")]
    todas_eo = [i for i in items if i["medio"] == "elobservador"]

    marcas = {}
    for it in comerciales:
        marca = it.get("marca") or "(sin identificar)"
        key = normalizar(marca)
        m = marcas.setdefault(key, {"marca": marca, "medios": {}, "notas": [],
                                    "pauta_en_eo": False, "mencion_editorial_eo": []})
        m["medios"].setdefault(it["medio"], 0)
        m["medios"][it["medio"]] += 1
        m["notas"].append({k: it.get(k) for k in ("medio", "url", "titulo", "fecha", "señales")})
        if it["medio"] == "elobservador":
            m["pauta_en_eo"] = True

    # ¿Hubo nota (editorial o comercial) en EO que mencione la marca en el titulo?
    for m in marcas.values():
        key = normalizar(m["marca"])
        if not key or key == "(sin identificar)" or len(key) < 3:
            continue
        for nota in todas_eo:
            if key in normalizar(nota.get("titulo") or ""):
                m["mencion_editorial_eo"].append({"url": nota["url"], "titulo": nota["titulo"],
                                                  "es_comercial": nota.get("es_comercial", False)})
    return marcas


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo", nargs="*", choices=list(COLLECTORS), default=None,
                        help="correr solo estos medios")
    args = parser.parse_args()

    medios = args.solo or list(COLLECTORS)
    items = []
    print(f"### PASO 1/4 · Colectar notas de la ultima semana ({len(medios)} medios)", flush=True)
    for medio in medios:
        print(f"\n→ {config.MEDIOS[medio]['nombre']} ({config.MEDIOS[medio]['url']})", flush=True)
        try:
            nuevos = COLLECTORS[medio]()
            items.extend(nuevos)
            print(f"  {len(nuevos)} notas colectadas", flush=True)
        except Exception:
            logger.exception("Collector %s fallo; sigo con el resto", medio)

    print(f"\n### PASO 2/4 · Clasificar {len(items)} notas (comercial vs editorial)", flush=True)
    items = classify.clasificar(items)
    print("\n### PASO 3/4 · Cruzar marcas entre medios y con El Observador", flush=True)
    marcas = cruzar_marcas(items)

    hoy = datetime.date.today()
    semana_iso = f"{hoy.isocalendar()[0]}-W{hoy.isocalendar()[1]:02d}"
    payload = {
        "generado": datetime.datetime.now().isoformat(timespec="seconds"),
        "semana": semana_iso,
        "ventana_dias": config.DIAS_VENTANA,
        "medios": {k: v["nombre"] for k, v in config.MEDIOS.items()},
        "resumen": {
            "notas_analizadas": len(items),
            "notas_comerciales": sum(1 for i in items if i.get("es_comercial")),
            "marcas_unicas": len(marcas),
            "por_medio": {
                m: sum(1 for i in items if i["medio"] == m and i.get("es_comercial"))
                for m in config.MEDIOS
            },
        },
        "marcas": sorted(marcas.values(), key=lambda m: -len(m["notas"])),
        "notas_comerciales": [
            {k: i.get(k) for k in ("medio", "url", "titulo", "seccion", "fecha", "marca", "señales")}
            for i in items if i.get("es_comercial")
        ],
    }

    os.makedirs(config.DATA_DIR, exist_ok=True)
    for nombre in ("latest.json", f"{semana_iso}.json"):
        with open(os.path.join(config.DATA_DIR, nombre), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)
    logger.info("Datos escritos en %s/latest.json y %s/%s.json",
                config.DATA_DIR, config.DATA_DIR, semana_iso)

    print("\n### PASO 4/4 · Generar dashboard", flush=True)
    import build_dashboard
    build_dashboard.build()
    print(f"  Dashboard regenerado: {config.DASHBOARD_FILE} (abrir con doble click)", flush=True)

    r = payload["resumen"]
    print(f"\n=== Semana {semana_iso} ===")
    print(f"Notas analizadas: {r['notas_analizadas']}")
    print(f"Notas comerciales: {r['notas_comerciales']}")
    for m, n in r["por_medio"].items():
        print(f"  - {config.MEDIOS[m]['nombre']}: {n}")
    print(f"Marcas unicas: {r['marcas_unicas']}")


if __name__ == "__main__":
    main()
