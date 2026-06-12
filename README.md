# Dashboard Comercial — Pauta de marcas en diarios uruguayos

Identifica **cada semana** qué marcas pautaron contenido comercial (branded content,
gacetillas, empresariales) en los principales medios uruguayos, cruza esa información
con El Observador y lo presenta en un dashboard.

**Los medios a monitorear están documentados en [MEDIOS.md](MEDIOS.md) — leer antes de tocar nada.**

## Corrida semanal

```bash
pip install -r requirements.txt   # solo la primera vez (requests)
python run_weekly.py              # colecta + clasifica + cruza + dashboard
open dashboard.html               # ver el resultado
```

Opciones:
```bash
python run_weekly.py --solo elobservador montevideo   # correr solo algunos medios
```

## Qué hace

1. **Colecta** (`collectors/`): baja las notas de los últimos 7 días de los 4 medios
   (sitemaps, tag Empresariales, Google News como complemento).
2. **Clasifica** (`classify.py`): separa contenido comercial de editorial.
   - El Observador y Montevideo Portal tienen patrón estructural (alta precisión, sin LLM).
   - El País y la diaria: clasificación de titulares en lote con **Gemini 2.5 Flash**.
   - La API key se resuelve sola: env `GEMINI_API_KEY` → `.env` → Secret Manager de
     `observadordw` (mismo secret `gemini-api-key` de la suite de agentes).
   - Sin key funciona igual con heurísticas (menor recall en El País / la diaria).
3. **Cruza marcas** (`run_weekly.py`): por cada marca, en qué medios pautó, si pauta
   con nosotros y si El Observador le dedicó alguna nota (editorial o comercial).
4. **Dashboard** (`build_dashboard.py` → `dashboard.html`): standalone, doble click.
   KPI clave para el equipo comercial: **marcas que pautan en la competencia y no con nosotros**.

## Salidas

- `dashboard.html` — dashboard de la semana (data embebida, se puede mandar por mail)
- `data/latest.json` — datos de la última corrida
- `data/<YYYY>-W<WW>.json` — histórico por semana ISO

## Costo

Una corrida usa ~4-8 llamadas a Gemini Flash (batch de titulares) → centavos de dólar.
Los sitios se consultan con pausas de 0,7 s entre requests.
