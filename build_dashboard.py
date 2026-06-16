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
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root{
    --bg:#eef2f0; --card:#ffffff; --ink:#0f1a14; --muted:#647a70;
    --green:#16b364; --green-d:#0f8a4c; --green-soft:#e4f8ed;
    --amber:#e8870b; --amber-soft:#fdf1de;
    --blue:#2563eb; --border:#e3e9e6; --shadow:0 1px 3px rgba(15,26,20,.06),0 8px 24px rgba(15,26,20,.05);
  }
  *{box-sizing:border-box;margin:0}
  html{-webkit-text-size-adjust:100%}
  body{font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink);line-height:1.5}
  a{color:var(--green-d);text-decoration:none}
  a:hover{text-decoration:underline}

  header{background:#0f1a14;color:#fff;padding:20px 28px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
  header img.logo{width:46px;height:46px;border-radius:11px;flex:0 0 auto}
  header .titulo h1{font-size:20px;font-weight:700;letter-spacing:-.2px}
  header .titulo .sub{opacity:.7;font-size:13px;margin-top:2px}
  header .meta{margin-left:auto;text-align:right;font-size:12px;opacity:.75;line-height:1.6}
  header .meta b{color:var(--green);font-weight:700;font-size:14px}

  main{max-width:1240px;margin:24px auto;padding:0 22px}

  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:20px}
  .kpi{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:18px 20px;box-shadow:var(--shadow);position:relative;overflow:hidden}
  .kpi::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--green)}
  .kpi.op::before{background:var(--amber)}
  .kpi.blue::before{background:var(--blue)}
  .kpi .n{font-size:32px;font-weight:800;letter-spacing:-1px}
  .kpi.op .n{color:var(--amber)} .kpi .n{color:var(--green-d)} .kpi.blue .n{color:var(--blue)} .kpi.ink .n{color:var(--ink)}
  .kpi .l{font-size:11.5px;color:var(--muted);margin-top:4px;text-transform:uppercase;letter-spacing:.5px;font-weight:600}

  .grid2{display:grid;grid-template-columns:1.3fr 1fr;gap:16px;margin-bottom:20px}
  @media(max-width:860px){.grid2{grid-template-columns:1fr}}
  .panel{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:18px 20px;box-shadow:var(--shadow)}
  .panel h3{font-size:13px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);margin-bottom:14px;font-weight:700}
  .chart-wrap{position:relative;height:230px}

  .filtros{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:16px 18px;box-shadow:var(--shadow);margin-bottom:18px;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
  .filtros .search{flex:1;min-width:220px;position:relative}
  .filtros .search input{width:100%;padding:10px 12px 10px 36px;border:1px solid var(--border);border-radius:10px;font-size:14px;background:#fff;color:var(--ink)}
  .filtros .search input:focus{outline:none;border-color:var(--green)}
  .filtros .search svg{position:absolute;left:11px;top:50%;transform:translateY(-50%);opacity:.4}
  .chips{display:flex;gap:7px;flex-wrap:wrap}
  .chip-f{padding:7px 13px;border-radius:99px;border:1px solid var(--border);background:#fff;font-size:12.5px;font-weight:600;color:var(--muted);cursor:pointer;user-select:none;transition:.12s;display:inline-flex;align-items:center;gap:6px}
  .chip-f .c{width:8px;height:8px;border-radius:99px;background:#cbd5cf}
  .chip-f.on{background:var(--green-soft);border-color:var(--green);color:var(--green-d)}
  .chip-f.on .c{background:var(--green)}
  .chip-f.op.on{background:var(--amber-soft);border-color:var(--amber);color:var(--amber)}
  .chip-f.op.on .c{background:var(--amber)}
  select.sel{padding:8px 11px;border:1px solid var(--border);border-radius:10px;font-size:13px;background:#fff;color:var(--ink);cursor:pointer}
  .btn-clr{padding:8px 13px;border:1px solid var(--border);border-radius:10px;font-size:12.5px;font-weight:600;color:var(--muted);background:#fff;cursor:pointer}
  .btn-clr:hover{border-color:var(--green);color:var(--green-d)}
  .resultados{font-size:12.5px;color:var(--muted);margin-left:auto;font-weight:600}

  h2{font-size:16px;margin:24px 0 12px;display:flex;align-items:center;gap:8px}
  h2 .badge{background:var(--green-soft);color:var(--green-d);font-size:12px;padding:2px 9px;border-radius:99px;font-weight:700}

  .tabla{background:var(--card);border:1px solid var(--border);border-radius:14px;overflow:hidden;box-shadow:var(--shadow)}
  table{width:100%;border-collapse:collapse;font-size:13.5px}
  th{background:#f3f7f5;text-align:left;padding:11px 14px;font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);font-weight:700;cursor:pointer;white-space:nowrap}
  th.center,td.center{text-align:center}
  th .arr{opacity:.4;font-size:9px}
  td{padding:11px 14px;border-top:1px solid var(--border);vertical-align:top}
  tbody tr:hover{background:#f8faf9}
  .dot{display:inline-block;min-width:24px;padding:2px 8px;border-radius:99px;background:var(--green);color:#fff;font-weight:700;font-size:12px}
  .dot.cero{background:#eef2f0;color:#9aa8a1;font-weight:500}
  .pill{display:inline-block;border-radius:99px;padding:3px 11px;font-size:11.5px;font-weight:700}
  .pill.op{background:var(--amber-soft);color:var(--amber)}
  .pill.si{background:var(--green-soft);color:var(--green-d)}
  .chip{display:inline-block;background:#f3f7f5;border-radius:6px;padding:2px 8px;font-size:11px;color:var(--muted);margin:1px 2px;border:1px solid var(--border)}
  .chip.llm{background:#eef4ff;color:#2952cc;border-color:#d4e0ff}
  .medio-tag{display:inline-block;font-size:11px;font-weight:700;padding:2px 8px;border-radius:6px;background:#f3f7f5;color:var(--muted)}
  .titulo-nota{font-weight:600;color:var(--ink)} .titulo-nota:hover{color:var(--green-d)}
  .fecha{font-size:11px;color:var(--muted);margin-top:2px}
  .vacio{padding:34px;text-align:center;color:var(--muted);font-size:14px}
  footer{text-align:center;color:#9aa8a1;font-size:12px;margin:32px 0 24px}
</style>
</head>
<body>
<header>
  <img class="logo" src="data:image/png;base64,__LOGO__" alt="El Observador">
  <div class="titulo">
    <h1>Pauta comercial en medios uruguayos</h1>
    <div class="sub" id="sub"></div>
  </div>
  <div class="meta" id="meta"></div>
</header>

<main>
  <div class="kpis" id="kpis"></div>

  <div class="grid2">
    <div class="panel">
      <h3>Notas comerciales por medio</h3>
      <div class="chart-wrap"><canvas id="chMedio"></canvas></div>
    </div>
    <div class="panel">
      <h3>Marcas: ¿pautan con nosotros?</h3>
      <div class="chart-wrap"><canvas id="chOp"></canvas></div>
    </div>
  </div>

  <div class="filtros">
    <div class="search">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
      <input id="q" placeholder="Buscar marca o título…" autocomplete="off">
    </div>
    <div class="chips" id="chipsMedio"></div>
    <div class="chip-f op" id="chipOp"><span class="c"></span>Solo oportunidades</div>
    <select class="sel" id="selSeccion"></select>
    <button class="btn-clr" id="btnClr">Limpiar</button>
    <span class="resultados" id="resultados"></span>
  </div>

  <h2>Marcas que pautaron <span class="badge" id="badgeMarcas"></span></h2>
  <div class="tabla" id="tabla-marcas"></div>

  <h2>Notas comerciales detectadas <span class="badge" id="badgeNotas"></span></h2>
  <div class="tabla" id="lista-notas"></div>
</main>

<footer>El Observador · Identificador de contenido comercial · generado __GENERADO__</footer>

<script>
const DATA = __DATA__;
const MEDIOS = DATA.medios;
const ORDEN = ["elobservador","elpais","montevideo","ladiaria"];
const COLOR = {elobservador:"#16b364", elpais:"#2563eb", montevideo:"#e8870b", ladiaria:"#9333ea"};

// pauta_en_eo por marca (para derivar oportunidades sobre el set filtrado)
const PAUTA = {};
DATA.marcas.forEach(m => PAUTA[m.marca] = m.pauta_en_eo);

document.getElementById("sub").textContent =
  `Semana ${DATA.semana} · últimos ${DATA.ventana_dias} días`;
document.getElementById("meta").innerHTML =
  `<b>${DATA.semana}</b><br>${DATA.resumen.notas_analizadas.toLocaleString("es")} notas analizadas<br>generado ${DATA.generado.slice(0,16).replace("T"," ")}`;

// ---- estado de filtros ----
const state = { q:"", medios:new Set(ORDEN), soloOp:false, seccion:"all", sortMarca:["marca","asc"], sortNota:["fecha","desc"] };

// secciones disponibles
const secciones = [...new Set(DATA.notas_comerciales.map(n=>n.seccion).filter(Boolean))].sort();
document.getElementById("selSeccion").innerHTML =
  `<option value="all">Todas las secciones</option>` + secciones.map(s=>`<option value="${s}">${s}</option>`).join("");

// chips de medio
document.getElementById("chipsMedio").innerHTML = ORDEN.map(k =>
  `<div class="chip-f on" data-medio="${k}"><span class="c" style="background:${COLOR[k]}"></span>${MEDIOS[k]}</div>`).join("");

function notasFiltradas(){
  const q = state.q.toLowerCase();
  return DATA.notas_comerciales.filter(n=>{
    if(!state.medios.has(n.medio)) return false;
    if(state.seccion!=="all" && n.seccion!==state.seccion) return false;
    if(state.soloOp && PAUTA[n.marca]) return false;
    if(q){ const hay = (n.titulo||"")+" "+(n.marca||""); if(!hay.toLowerCase().includes(q)) return false; }
    return true;
  });
}

function marcasFiltradas(notas){
  const map = {};
  notas.forEach(n=>{
    const k = n.marca || "(sin identificar)";
    if(!map[k]) map[k] = {marca:k, medios:{}, total:0, pauta_en_eo:!!PAUTA[k], notas:[]};
    map[k].medios[n.medio] = (map[k].medios[n.medio]||0)+1;
    map[k].total++; map[k].notas.push(n);
  });
  return Object.values(map);
}

// ---- charts ----
let chMedio, chOp;
function initCharts(){
  chMedio = new Chart(document.getElementById("chMedio"), {
    type:"bar",
    data:{labels:ORDEN.map(k=>MEDIOS[k]), datasets:[{data:ORDEN.map(()=>0),
      backgroundColor:ORDEN.map(k=>COLOR[k]), borderRadius:7, barThickness:34}]},
    options:{indexAxis:"y", plugins:{legend:{display:false}}, responsive:true, maintainAspectRatio:false,
      scales:{x:{beginAtZero:true,ticks:{precision:0,color:"#647a70"},grid:{color:"#eef2f0"}},
              y:{ticks:{color:"#0f1a14",font:{weight:600}},grid:{display:false}}}}
  });
  chOp = new Chart(document.getElementById("chOp"), {
    type:"doughnut",
    data:{labels:["Oportunidad (pauta afuera)","Ya pauta con nosotros"],
      datasets:[{data:[0,0], backgroundColor:["#e8870b","#16b364"], borderWidth:0, hoverOffset:6}]},
    options:{cutout:"62%", responsive:true, maintainAspectRatio:false,
      plugins:{legend:{position:"bottom",labels:{boxWidth:12,padding:14,color:"#647a70",font:{size:12}}}}}
  });
}
function updateCharts(notas, marcas){
  chMedio.data.datasets[0].data = ORDEN.map(k=>notas.filter(n=>n.medio===k).length);
  chMedio.update();
  const op = marcas.filter(m=>!m.pauta_en_eo && m.marca!=="(sin identificar)").length;
  const si = marcas.filter(m=>m.pauta_en_eo).length;
  chOp.data.datasets[0].data = [op, si];
  chOp.update();
}

// ---- render ----
function sortBy(arr, key, dir, accessor){
  const s=[...arr].sort((a,b)=>{ let x=accessor(a),y=accessor(b);
    if(typeof x==="string"){x=x.toLowerCase();y=(y||"").toLowerCase();}
    return x<y?-1:x>y?1:0; });
  return dir==="desc"? s.reverse():s;
}

function celdas(m){ return ORDEN.map(k=>{const n=m.medios[k]||0;
  return `<td class="center"><span class="dot ${n?"":"cero"}">${n}</span></td>`;}).join(""); }

function renderMarcas(marcas){
  const [key,dir]=state.sortMarca;
  const acc = key==="marca"?(m=>m.marca): key==="total"?(m=>m.total):(m=>m.pauta_en_eo?1:0);
  const ms = sortBy(marcas,key,dir,acc);
  document.getElementById("badgeMarcas").textContent = `${marcas.length}`;
  const arr=(k)=> state.sortMarca[0]===k? (state.sortMarca[1]==="asc"?"▲":"▼"):"";
  document.getElementById("tabla-marcas").innerHTML = ms.length ? `
    <table><thead><tr>
      <th data-sm="marca">Marca <span class="arr">${arr("marca")}</span></th>
      ${ORDEN.map(k=>`<th class="center">${MEDIOS[k]}</th>`).join("")}
      <th class="center" data-sm="total"># notas <span class="arr">${arr("total")}</span></th>
      <th data-sm="eo">Lectura comercial <span class="arr">${arr("eo")}</span></th>
    </tr></thead><tbody>
    ${ms.map(m=>{
      const lectura = m.marca==="(sin identificar)" ? `<span class="chip">sin marca</span>`
        : m.pauta_en_eo ? `<span class="pill si">✓ ya pauta con nosotros</span>`
        : `<span class="pill op">⚡ pauta en competencia</span>`;
      return `<tr><td><strong>${m.marca}</strong></td>${celdas(m)}
        <td class="center"><span class="dot">${m.total}</span></td><td>${lectura}</td></tr>`;
    }).join("")}
    </tbody></table>` : `<div class="vacio">No hay marcas con los filtros actuales.</div>`;
  document.querySelectorAll("[data-sm]").forEach(th=>th.onclick=()=>{
    const k=th.dataset.sm; state.sortMarca = state.sortMarca[0]===k?[k,state.sortMarca[1]==="asc"?"desc":"asc"]:[k,"asc"]; render();});
}

function renderNotas(notas){
  const [key,dir]=state.sortNota;
  const acc = key==="fecha"?(n=>n.fecha||""): key==="medio"?(n=>MEDIOS[n.medio]): (n=>n.marca||"");
  const ns = sortBy(notas,key,dir,acc);
  document.getElementById("badgeNotas").textContent = `${notas.length}`;
  const arr=(k)=> state.sortNota[0]===k? (state.sortNota[1]==="asc"?"▲":"▼"):"";
  document.getElementById("lista-notas").innerHTML = ns.length ? `
    <table><thead><tr>
      <th data-sn="medio">Medio <span class="arr">${arr("medio")}</span></th>
      <th data-sn="marca">Marca <span class="arr">${arr("marca")}</span></th>
      <th>Nota</th>
      <th data-sn="fecha">Fecha <span class="arr">${arr("fecha")}</span></th>
      <th>Señales</th>
    </tr></thead><tbody>
    ${ns.map(n=>{
      const op = n.marca && !PAUTA[n.marca];
      return `<tr>
        <td><span class="medio-tag" style="color:${COLOR[n.medio]}">${MEDIOS[n.medio]}</span></td>
        <td><strong>${n.marca||"—"}</strong> ${op?'<span class="pill op" style="font-size:10px">⚡</span>':""}</td>
        <td><a class="titulo-nota" href="${n.url}" target="_blank">${n.titulo||n.url}</a>
            ${n.seccion?`<div class="fecha">sección: ${n.seccion}</div>`:""}</td>
        <td>${n.fecha?n.fecha.slice(0,10):"—"}</td>
        <td>${(n["señales"]||[]).map(s=>`<span class="chip ${s.startsWith("llm")?"llm":""}">${s}</span>`).join("")}</td>
      </tr>`;
    }).join("")}
    </tbody></table>` : `<div class="vacio">No hay notas con los filtros actuales.</div>`;
  document.querySelectorAll("[data-sn]").forEach(th=>th.onclick=()=>{
    const k=th.dataset.sn; state.sortNota = state.sortNota[0]===k?[k,state.sortNota[1]==="asc"?"desc":"asc"]:[k,"asc"]; render();});
}

function renderKpis(notas, marcas){
  const op = marcas.filter(m=>!m.pauta_en_eo && m.marca!=="(sin identificar)").length;
  const mediosActivos = new Set(notas.map(n=>n.medio)).size;
  document.getElementById("kpis").innerHTML = [
    [notas.length,"Notas comerciales","ink"],
    [marcas.filter(m=>m.marca!=="(sin identificar)").length,"Marcas únicas",""],
    [op,"Pautan afuera y no con nosotros","op"],
    [mediosActivos+" / "+ORDEN.length,"Medios con pauta","blue"],
  ].map(([n,l,c])=>`<div class="kpi ${c}"><div class="n">${n}</div><div class="l">${l}</div></div>`).join("");
}

function render(){
  const notas = notasFiltradas();
  const marcas = marcasFiltradas(notas);
  document.getElementById("resultados").textContent = `${notas.length} notas · ${marcas.length} marcas`;
  renderKpis(notas, marcas);
  updateCharts(notas, marcas);
  renderMarcas(marcas);
  renderNotas(notas);
}

// ---- eventos ----
document.getElementById("q").addEventListener("input", e=>{state.q=e.target.value; render();});
document.getElementById("selSeccion").addEventListener("change", e=>{state.seccion=e.target.value; render();});
document.querySelectorAll("[data-medio]").forEach(ch=>ch.addEventListener("click",()=>{
  const k=ch.dataset.medio;
  if(state.medios.has(k)){state.medios.delete(k); ch.classList.remove("on");}
  else{state.medios.add(k); ch.classList.add("on");}
  render();
}));
document.getElementById("chipOp").addEventListener("click",function(){
  state.soloOp=!state.soloOp; this.classList.toggle("on"); render();
});
document.getElementById("btnClr").addEventListener("click",()=>{
  state.q=""; state.medios=new Set(ORDEN); state.soloOp=false; state.seccion="all";
  document.getElementById("q").value=""; document.getElementById("selSeccion").value="all";
  document.querySelectorAll("[data-medio]").forEach(c=>c.classList.add("on"));
  document.getElementById("chipOp").classList.remove("on");
  render();
});

initCharts();
render();
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
