"""
Collector de la diaria (ladiaria.com.uy).

Fuente: sitemap-news_48hs.xml (ultimas 48 h) + primeras paginas del sitemap de
articulos para cubrir la semana. Sin seccion comercial explicita → la deteccion
fina la hace classify.py.
"""

import logging
from urllib.parse import urlparse

from . import common

logger = logging.getLogger("collectors.ladiaria")

SITEMAPS = [
    "https://ladiaria.com.uy/sitemap-news_48hs.xml",
    # las primeras paginas del sitemap general traen lo mas reciente
    "https://ladiaria.com.uy/sitemap-news_sitemap.xml",
    "https://ladiaria.com.uy/sitemap-news_sitemap.xml?p=2",
]


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
            items.append({
                "medio": "ladiaria",
                "url": url,
                "titulo": it["title"],
                "seccion": seccion,
                "fecha": it["lastmod"],
                "candidata": False,
            })
    logger.info("la diaria: %d notas de la semana", len(items))
    return items
