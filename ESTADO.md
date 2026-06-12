# ESTADO DEL PROYECTO — Identificador de contenido comercial en diarios uruguayos

**Cliente:** El Observador (equipo comercial) · **Carpeta:** `observador/dashboard_comercial/`
**Última actualización:** 12 de junio de 2026 (sesión inicial, proyecto creado desde cero)

## 1. Qué es

Pipeline semanal que detecta qué **marcas pautaron contenido comercial** (branded content,
gacetillas, empresariales) en 4 medios uruguayos, cruza con El Observador
(¿pauta con nosotros? ¿le dedicamos nota?) y genera `dashboard.html`.
Los 4 medios obligatorios y cómo detecta cada uno están en **MEDIOS.md** (pedido explícito
de Rodolfo: documentar a qué medios hay que salir a buscar).

## 2. Estado: FUNCIONANDO ✅

Primera corrida real (12-jun-2026, semana 2026-W24, ventana 7 días):
- ~2.700 notas analizadas → **~30 notas comerciales, ~29 marcas** (varía un poco por corrida,
  Gemini tiene casos borde).
- Detecciones destacadas: **Claro** pautó en El Observador Y en El País la misma semana;
  El País es por lejos el que más branded content publica (~16-18 notas/semana);
  DEEPAL pautó en EO el 4-jun (quedó fuera de ventana por 1 día).

## 3. Cómo correr

```bash
cd ~/Documents/Documentos/observador/dashboard_comercial
python3 run_weekly.py     # imprime en vivo lo que va encontrando (4 pasos)
open dashboard.html
```

GEMINI_API_KEY se toma sola del Secret Manager de `observadordw` vía gcloud
(secret `gemini-api-key`, el de la suite de agentes). Tarda ~3-5 min.

## 4. Decisiones técnicas clave

- **El Observador**: comercial = URL sin sección + sin `mrf:authors` + `sub-section:` vacío.
  Verificación estructural, sin LLM. Casos validados: Claro, DEEPAL.
- **Montevideo Portal**: tag "Empresariales" = comercial, PERO la página del tag es archivo
  histórico → se confirma `datePublished` de cada nota (filtro de ventana).
  Sitemaps bloqueados por Cloudflare; se usa home + tag + Google News RSS.
- **El País / la diaria**: sin marca explícita → batch de titulares a Gemini 2.5 Flash
  (80 por llamada, ~4-8 llamadas/corrida, centavos).
- **Cloudflare a veces bloquea la sesión de requests pero no curl** → `common.get()` tiene
  2 reintentos + fallback a subprocess curl.
- la diaria trae ~2.000 URLs porque su sitemap paginado no siempre tiene fecha; el
  clasificador igual solo manda a Gemini los pendientes con título (~265).

## 5. Pendientes (para la próxima)

1. **Validar con Rodolfo** los resultados de la primera semana (¿falsos positivos? ¿faltó alguna marca conocida?).
2. **Histórico/tendencia**: el dashboard hoy muestra solo la última semana; `data/<YYYY-WW>.json`
   ya guarda histórico para agregar evolución semanal.
3. **Automatizar la corrida** (cron local o Cloud Function tipo suite de agentes) para
   que corra sola cada lunes.
4. **Repo git**: inicializado local; falta crear remoto privado en GitHub si se quiere.
5. Posible mejora de recall en El País: además de titulares, mirar la sección
   (las comerciales suelen ir en `negocios`/`el-empresario`) y los marcadores en HTML.

## 6. Archivos

| Archivo | Qué es |
|---|---|
| `MEDIOS.md` | **Los 4 medios obligatorios** + patrón de detección de cada uno |
| `config.py` | Medios, ventana (7 días), marcadores, modelo Gemini |
| `collectors/<medio>.py` | Un collector por medio |
| `collectors/common.py` | HTTP con reintentos + fallback curl, parser de sitemaps |
| `classify.py` | Heurísticas + Gemini batch + extracción de marca |
| `run_weekly.py` | Orquestador (4 pasos, salida en vivo) |
| `build_dashboard.py` | Genera `dashboard.html` standalone |
| `data/` | `latest.json` + snapshots semanales |
