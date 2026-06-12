"""
Collector de El País (elpais.com.uy).

No expone seccion "patrocinado" en sitemaps → este collector junta TODAS las notas
de la semana; la deteccion fina la hace classify.py (heuristica + Gemini) y para
las candidatas se baja el HTML buscando marcadores.
"""

import logging
from urllib.parse import urlparse

from . import common

logger = logging.getLogger("collectors.elpais")

SITEMAPS = [
    "https://www.elpais.com.uy/news-sitemap.xml",
    "https://www.elpais.com.uy/news-sitemap-content.xml",
    "https://www.elpais.com.uy/news-sitemap-latest.xml",
]

IGNORAR_SECCIONES = ("horoscopo",)


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
            partes = urlparse(url).path.strip("/").split("/")
            seccion = partes[0] if partes else None
            if seccion in IGNORAR_SECCIONES:
                continue
            items.append({
                "medio": "elpais",
                "url": url,
                "titulo": it["title"],
                "seccion": seccion,
                "fecha": it["lastmod"],
                "candidata": False,  # la define el clasificador de titulos
            })
    logger.info("El País: %d notas de la semana", len(items))
    return items
