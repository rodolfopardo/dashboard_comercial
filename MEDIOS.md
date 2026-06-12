# Medios a monitorear (OBLIGATORIO)

> **Estos son los 4 medios uruguayos a los que hay que salir a buscar contenido
> comercial TODAS las semanas.** Definidos por Rodolfo el 2026-06-12.
> Si se agrega o quita un medio, actualizar este archivo y `config.py`.

| # | Medio | URL | Rol |
|---|-------|-----|-----|
| 1 | El Observador | https://www.elobservador.com.uy/ | **Nuestro medio** (casa) |
| 2 | El País | https://www.elpais.com.uy/ | Competencia |
| 3 | Montevideo Portal | https://www.montevideo.com.uy/ | Competencia |
| 4 | la diaria | https://ladiaria.com.uy/ | Competencia |

## Cómo identifica el contenido comercial cada medio (verificado 2026-06-12)

### 1. El Observador (`elobservador.com.uy`)
- **Fuente de notas:** `https://www.elobservador.com.uy/sitemap.xml` (rolling, ~100 últimas notas
  con `lastmod`) y `sitemap-news.xml`. Sin Cloudflare, responde a curl con UA de navegador.
- **Patrón de nota comercial** (verificado con notas reales de Claro y DEEPAL):
  - La URL **no tiene sección**: `elobservador.com.uy/<slug>-n<ID>` (las editoriales van
    `/<seccion>/<slug>-n<ID>`).
  - En el HTML **no existe** `<meta property="mrf:authors">` (las editoriales tienen periodista).
  - `<meta property="mrf:tags" content="sub-section:">` viene **vacío**.
  - Autor en JSON-LD = `Organization "El Observador"` (no discrimina por sí solo: las
    editoriales también, usar los 2 criterios de arriba).
- **Ojo:** hay notas editoriales que también van a raíz (ej. políticas), pero esas SÍ tienen
  `mrf:authors`. El par (sin sección + sin autor) es el discriminador.

### 2. El País (`elpais.com.uy`)
- **Fuente de notas:** `news-sitemap.xml`, `news-sitemap-content.xml`, `news-sitemap-latest.xml`
  (con `news:publication_date` y `news:keywords`). Secciones en URL: ovacion, informacion,
  paula, negocios, el-empresario, bienestar, etc.
- **No expone una sección "patrocinado" en el sitemap** → detección en dos pasos:
  1. Clasificador de títulos (heurística + Gemini) sobre todo el sitemap de la semana.
  2. Para candidatos, fetch del HTML y buscar marcadores: "contenido patrocinado",
     "espacio de marca", "presentado por", "powered by", autor organización.

### 3. Montevideo Portal (`montevideo.com.uy`)
- **Cloudflare bloquea** `/sitemap.xml`; el RSS legacy (`anxml.aspx`) está dado de baja.
- **Las notas comerciales llevan tag/categoría "Empresariales"**:
  - Página de tag: `https://www.montevideo.com.uy/tag/Empresariales`
  - En la nota, JSON-LD `articleSection` y links `/tag/...`.
- **Fuentes que sí funcionan:** la home (`/`) renderiza server-side con URLs
  `https://www.montevideo.com.uy/<Categoria>/<slug>-uc<ID>`, y Google News RSS
  (`news.google.com/rss/search?q=site:montevideo.com.uy...`) como complemento.
- Ignorar `/SIN-CATEGORIZAR/` (son productos de la tienda, no notas).

### 4. la diaria (`ladiaria.com.uy`)
- **Fuente de notas:** `https://ladiaria.com.uy/sitemap-news_48hs.xml` (últimas 48 h; correr
  el collector al menos 3-4 veces por semana o usar `sitemap-news_sitemap.xml` paginado).
- Secciones en URL: politica, deporte, economia, `/articulo/`, etc.
- Sin sección comercial explícita → mismo flujo de dos pasos que El País.
  la diaria publica poco contenido comercial; su formato típico es "contenido generado
  por la marca" / acuerdos institucionales.

## Qué se considera "contenido comercial"
Nota publicada en el sitio del medio cuyo protagonista es una **marca/empresa** y que
existe por un acuerdo comercial (pauta, branded content, gacetilla empresarial):
lanzamientos de producto, campañas, aniversarios de empresa, aperturas, alianzas de marca,
"empresariales". **No cuenta**: cobertura editorial donde la marca es noticia
(resultados financieros, escándalos, M&A reportado por periodistas).
