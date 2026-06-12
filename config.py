"""
Configuracion del identificador de contenido comercial en diarios uruguayos.

Los medios objetivo estan documentados en MEDIOS.md — NO quitar ninguno.
"""

# === Medios a monitorear (ver MEDIOS.md) ===
MEDIOS = {
    "elobservador": {
        "nombre": "El Observador",
        "url": "https://www.elobservador.com.uy/",
        "es_propio": True,  # nuestro medio
    },
    "elpais": {
        "nombre": "El País",
        "url": "https://www.elpais.com.uy/",
        "es_propio": False,
    },
    "montevideo": {
        "nombre": "Montevideo Portal",
        "url": "https://www.montevideo.com.uy/",
        "es_propio": False,
    },
    "ladiaria": {
        "nombre": "la diaria",
        "url": "https://ladiaria.com.uy/",
        "es_propio": False,
    },
}

# === HTTP ===
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
TIMEOUT = 20
SLEEP_ENTRE_REQUESTS = 0.7  # ser buenos vecinos

# === Ventana de analisis ===
DIAS_VENTANA = 7

# === Marcadores de contenido comercial en HTML (minusculas) ===
MARCADORES_COMERCIALES = [
    "contenido patrocinado",
    "espacio patrocinado",
    "nota patrocinada",
    "espacio de marca",
    "contenido comercial",
    "branded content",
    "brand studio",
    "presentado por",
    "powered by",
    "espacio contratado",
    "contenido generado por la marca",
    "publirreportaje",
    "empresariales",
]

# === Palabras tipicas de gacetilla/branded en titulo o bajada (señal debil) ===
LEXICO_GACETILLA = [
    "lanza", "lanzamiento", "presenta", "presentó", "relanza",
    "celebra", "festeja", "aniversario", "inaugura", "apertura",
    "nueva sucursal", "alianza", "se suma", "llega a uruguay",
    "campaña", "edición limitada", "renueva", "desembarca",
    "consolida", "reafirma", "apuesta", "innovación", "beneficios exclusivos",
]

# === Gemini (clasificador LLM, opcional pero recomendado) ===
GEMINI_MODEL = "gemini-2.5-flash"
# La key se busca en: env GEMINI_API_KEY -> .env local -> Secret Manager observadordw
GCP_PROJECT_SECRETS = "observadordw"
GCP_SECRET_NAME = "gemini-api-key"

# === Salidas ===
DATA_DIR = "data"
DASHBOARD_FILE = "dashboard.html"
