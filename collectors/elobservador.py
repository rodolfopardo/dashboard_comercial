"""
Collector de El Observador (nuestro medio).

Patron de nota comercial (ver MEDIOS.md, verificado 2026-06-12 con Claro y DEEPAL):
  - URL sin seccion: elobservador.com.uy/<slug>-n<ID>
  - HTML sin <meta property="mrf:authors">
  - <meta property="mrf:tags" content="sub-section:"> vacio
"""

import logging
import re
from urllib.parse import urlparse

from . import common

logger = logging.getLogger("collectors.elobservador")

SITEMAPS = [
    "https://www.elobservador.com.uy/sitemap.xml",
    "https://www.elobservador.com.uy/sitemap-news.xml",
]

# Secciones raiz que no son notas (servicios)
IGNORAR_SLUGS = ("funebres",)


def collect() -> list[dict]:
    vistos, items = set(), []
    for sm in SITEMAPS:
        resp = common.get(sm)
        if not resp:
            continue
        for it in common.parse_sitemap(resp.text):
            url = it["url"]
            if url in vistos or not common.dentro_de_ventana(it["lastmod"]):
                continue
            vistos.add(url)
            path = urlparse(url).path.strip("/")
            partes = path.split("/")
            seccion = partes[0] if len(partes) > 1 else None
            if seccion in IGNORAR_SLUGS or path.startswith("lorem-ipsum"):
                continue
            items.append({
                "medio": "elobservador",
                "url": url,
                "titulo": it["title"],
                "seccion": seccion,
                "fecha": it["lastmod"],
                # candidata fuerte si va a raiz (sin seccion); se confirma con el HTML
                "candidata": seccion is None,
            })

    # Confirmar candidatas mirando el HTML (sin autor + sub-section vacio)
    candidatas = [i for i in items if i["candidata"]]
    print(f"→ El Observador: {len(items)} notas en la semana, "
          f"verificando {len(candidatas)} candidatas (sin seccion en URL)...", flush=True)
    for it in items:
        if not it["candidata"]:
            continue
        print(f"  · revisando: {(it['titulo'] or it['url'])[:75]}", flush=True)
        resp = common.get(it["url"])
        if not resp:
            it["candidata"] = False
            continue
        html_str = resp.text
        sin_autor = '<meta property="mrf:authors"' not in html_str
        sub_vacia = re.search(
            r'<meta property="mrf:tags" content="sub-section:"\s*/?>', html_str
        ) is not None
        it["es_comercial_confirmado"] = sin_autor and sub_vacia
        if it["es_comercial_confirmado"]:
            print(f"    ✔ COMERCIAL confirmada (sin autor + sin seccion): "
                  f"{(it['titulo'] or '')[:70]}", flush=True)
        it["señales"] = (["sin seccion en URL"]
                         + (["sin autor (mrf:authors)"] if sin_autor else [])
                         + (["sub-section vacia"] if sub_vacia else [])
                         + common.buscar_marcadores(html_str))
        if not it["titulo"]:
            it["titulo"] = common.meta_title(html_str)
        it["bajada"] = common.meta_description(html_str)

    logger.info("El Observador: %d notas, %d candidatas",
                len(items), sum(1 for i in items if i.get("candidata")))
    return items
