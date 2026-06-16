"""Genera dashboard.html standalone con data/latest.json embebido (doble click y listo)."""

import base64
import json
import os

import config

TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pauta comercial en medios uruguayos · El Observador</title>
<style>
  :root { --azul:#00386c; --acento:#f5a623; --gris:#f4f6f8; --borde:#e2e8f0; }
  * { box-sizing:border-box; margin:0; }
  body { font-family:-apple-system,'Segoe UI',Roboto,sans-serif; background:var(--gris); color:#1a202c; }
  header { background:var(--azul); color:#fff; padding:22px 32px; display:flex; align-items:center; gap:16px; flex-wrap:wrap; }
  header img.logo { width:44px; height:44px; border-radius:9px; flex:0 0 auto; }
  header .titulo { display:flex; flex-direction:column; gap:3px; }
  header h1 { font-size:21px; font-weight:700; }
  header .sub { opacity:.75; font-size:13px; }
  main { max-width:1180px; margin:26px auto; padding:0 20px; }
  .kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:14px; margin-bottom:26px; }
  .kpi { background:#fff; border:1px solid var(--borde); border-radius:10px; padding:16px 18px; }
  .kpi .n { font-size:30px; font-weight:800; color:var(--azul); }
  .kpi .l { font-size:12px; color:#64748b; margin-top:4px; text-transform:uppercase; letter-spacing:.4px; }
  h2 { font-size:16px; margin:26px 0 12px; color:var(--azul); }
  table { width:100%; border-collapse:collapse; background:#fff; border:1px solid var(--borde); border-radius:10px; overflow:hidden; font-size:14px; }
  th { background:#eef2f7; text-align:left; padding:10px 12px; font-size:12px; text-transform:uppercase; letter-spacing:.4px; color:#475569; }
  td { padding:10px 12px; border-top:1px solid var(--borde); vertical-align:top; }
  td.center, th.center { text-align:center; }
  .dot { display:inline-block; min-width:26px; padding:2px 7px; border-radius:99px; background:var(--azul); color:#fff; font-weight:700; font-size:12px; }
  .dot.cero { background:#cbd5e1; color:#475569; font-weight:400; }
  .chip { display:inline-block; background:#eef2f7; border-radius:6px; padding:2px 8px; font-size:11px; color:#475569; margin:1px 2px; }
  .chip.op { background:#fff7e6; color:#92600a; border:1px solid #f5d9a8; font-weight:600; }
  .chip.si { background:#e6f6ec; color:#176b3a; }
  a { color:var(--azul); }
  .nota { margin:3px 0; line-height:1.45; }
  .nota .medio { font-size:11px; color:#64748b; }
  .vacio { background:#fff; border:1px dashed var(--borde); border-radius:10px; padding:28px; text-align:center; color:#64748b; }
  footer { text-align:center; color:#94a3b8; font-size:12px; margin:34px 0 22px; }
</style>
</head>
<body>
<header>
  <img class="logo" src="data:image/png;base64,__LOGO__" alt="El Observador">
  <div class="titulo">
    <h1>Pauta comercial en medios uruguayos</h1>
    <span class="sub" id="sub"></span>
  </div>
</header>
<main>
  <div class="kpis" id="kpis"></div>
  <h2>Marcas que pautaron esta semana</h2>
  <div id="tabla-marcas"></div>
  <h2>Todas las notas comerciales detectadas</h2>
  <div id="lista-notas"></div>
</main>
<footer>El Observador · Identificador de contenido comercial · generado __GENERADO__</footer>
<script>
const DATA = __DATA__;
const MEDIOS = DATA.medios;
const ORDEN = ["elobservador","elpais","montevideo","ladiaria"];

document.getElementById("sub").textContent =
  `Semana ${DATA.semana} · últimos ${DATA.ventana_dias} días · generado ${DATA.generado.replace("T"," ")}`;

const r = DATA.resumen;
const oportunidades = DATA.marcas.filter(m => !m.pauta_en_eo && m.marca !== "(sin identificar)").length;
document.getElementById("kpis").innerHTML = [
  [r.notas_comerciales, "Notas comerciales"],
  [r.marcas_unicas, "Marcas únicas"],
  [r.por_medio.elobservador ?? 0, "En El Observador"],
  [oportunidades, "Pautan afuera y no con nosotros"],
  [r.notas_analizadas, "Notas analizadas"],
].map(([n,l]) => `<div class="kpi"><div class="n">${n}</div><div class="l">${l}</div></div>`).join("");

function celdas(m) {
  return ORDEN.map(k => {
    const n = m.medios[k] || 0;
    return `<td class="center"><span class="dot ${n? "":"cero"}">${n}</span></td>`;
  }).join("");
}

const marcas = DATA.marcas;
document.getElementById("tabla-marcas").innerHTML = marcas.length ? `
  <table>
    <tr><th>Marca</th>${ORDEN.map(k=>`<th class="center">${MEDIOS[k]}</th>`).join("")}
        <th>Nota en El Observador</th><th>Lectura comercial</th></tr>
    ${marcas.map(m => {
      const menciones = (m.mencion_editorial_eo||[]).map(n =>
        `<div class="nota"><a href="${n.url}" target="_blank">${n.titulo||n.url}</a></div>`).join("") || "—";
      const lectura = m.pauta_en_eo
        ? `<span class="chip si">ya pauta con nosotros</span>`
        : `<span class="chip op">OPORTUNIDAD: pauta en competencia</span>`;
      return `<tr><td><strong>${m.marca}</strong></td>${celdas(m)}<td>${menciones}</td><td>${lectura}</td></tr>`;
    }).join("")}
  </table>` : `<div class="vacio">No se detectaron notas comerciales esta semana.</div>`;

const notas = DATA.notas_comerciales;
document.getElementById("lista-notas").innerHTML = notas.length ? `
  <table>
    <tr><th>Medio</th><th>Marca</th><th>Nota</th><th>Señales de detección</th></tr>
    ${notas.map(n => `<tr>
      <td>${MEDIOS[n.medio]}</td>
      <td><strong>${n.marca||"—"}</strong></td>
      <td class="nota"><a href="${n.url}" target="_blank">${n.titulo||n.url}</a>
          ${n.fecha? `<div class="medio">${n.fecha}</div>`:""}</td>
      <td>${(n["señales"]||[]).map(s=>`<span class="chip">${s}</span>`).join("")}</td>
    </tr>`).join("")}
  </table>` : `<div class="vacio">Sin notas comerciales detectadas.</div>`;
</script>
</body>
</html>
"""


def build():
    with open(os.path.join(config.DATA_DIR, "latest.json"), encoding="utf-8") as f:
        data = json.load(f)
    logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
    with open(logo_path, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode("ascii")
    html = (TEMPLATE
            .replace("__DATA__", json.dumps(data, ensure_ascii=False))
            .replace("__GENERADO__", data["generado"])
            .replace("__LOGO__", logo_b64))
    with open(config.DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    build()
