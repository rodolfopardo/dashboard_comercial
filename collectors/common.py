"""Helpers compartidos por los collectors."""

import datetime
import logging
import re
import time

import requests

import config

logger = logging.getLogger("collectors")

_session = requests.Session()
_session.headers.update({"User-Agent": config.USER_AGENT, "Accept-Language": "es-UY,es;q=0.9"})


class _CurlResponse:
    """Respuesta minima compatible con requests.Response (solo .text/.status_code)."""

    def __init__(self, text: str):
        self.text = text
        self.status_code = 200


def _curl_fallback(url: str) -> "_CurlResponse | None":
    """Cloudflare a veces bloquea la sesion de requests pero deja pasar curl."""
    import subprocess
    try:
        out = subprocess.run(
            ["curl", "-sL", "--max-time", str(config.TIMEOUT),
             "-A", config.USER_AGENT, url],
            capture_output=True, text=True, timeout=config.TIMEOUT + 10,
        )
        if out.returncode == 0 and out.stdout and "Attention Required! | Cloudflare" not in out.stdout:
            logger.info("Recuperado via curl: %s", url)
            return _CurlResponse(out.stdout)
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def get(url: str, **kw):
    """GET con UA de navegador, 2 reintentos y fallback a curl. None si falla."""
    for intento in range(2):
        try:
            resp = _session.get(url, timeout=config.TIMEOUT, **kw)
            time.sleep(config.SLEEP_ENTRE_REQUESTS)
            if resp.status_code == 200:
                return resp
            logger.warning("HTTP %s en %s (intento %d)", resp.status_code, url, intento + 1)
        except requests.RequestException as e:
            logger.warning("Error de red en %s: %s (intento %d)", url, e, intento + 1)
        time.sleep(2 * (intento + 1))
    return _curl_fallback(url)


def parse_sitemap(xml: str) -> list[dict]:
    """Extrae {url, lastmod, title} de un sitemap (urlset). Regex, sin deps."""
    items = []
    for block in re.findall(r"<url>(.*?)</url>", xml, re.S):
        loc = re.search(r"<loc>\s*([^<]+?)\s*</loc>", block)
        if not loc:
            continue
        lastmod = re.search(r"<lastmod>\s*([^<]+?)\s*</lastmod>", block)
        pubdate = re.search(r"<news:publication_date>\s*([^<]+?)\s*</news:publication_date>", block)
        title = re.search(r"<news:title>\s*([^<]+?)\s*</news:title>", block)
        items.append({
            "url": loc.group(1),
            "lastmod": (pubdate or lastmod).group(1) if (pubdate or lastmod) else None,
            "title": _unescape(title.group(1)) if title else None,
        })
    return items


def _unescape(s: str) -> str:
    import html
    return html.unescape(s).strip()


def dentro_de_ventana(fecha_iso: str | None, dias: int = None) -> bool:
    """True si la fecha ISO esta dentro de la ventana de analisis (o no hay fecha)."""
    if not fecha_iso:
        return True  # sin fecha no descartamos; se filtra despues
    dias = dias or config.DIAS_VENTANA
    try:
        f = datetime.datetime.fromisoformat(fecha_iso.replace("Z", "+00:00"))
    except ValueError:
        return True
    limite = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=dias)
    return f >= limite


def texto_visible(html_str: str) -> str:
    """Texto plano aproximado del HTML (sin scripts/estilos)."""
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html_str, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s)


def buscar_marcadores(html_str: str) -> list[str]:
    """Marcadores comerciales presentes en el HTML (case-insensitive)."""
    low = html_str.lower()
    return [m for m in config.MARCADORES_COMERCIALES if m in low]


def meta_title(html_str: str) -> str | None:
    m = re.search(r'<meta property="og:title" content="([^"]+)"', html_str)
    if m:
        return _unescape(m.group(1))
    m = re.search(r"<title>([^<]+)</title>", html_str)
    return _unescape(m.group(1)) if m else None


def meta_description(html_str: str) -> str | None:
    m = re.search(r'<meta (?:name|property)="(?:og:)?description" content="([^"]*)"', html_str)
    return _unescape(m.group(1)) if m else None
