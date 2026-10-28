#!/usr/bin/env python3
"""Build the Population Trials replay console: one self-contained HTML file
with a recorded run's replay bundle embedded. Regenerate per run:
  python3 build_ui.py runs/<run-name> ui/population-trials-console.html
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
run_dir = HERE / sys.argv[1]
out = pathlib.Path(sys.argv[2])
replay = (run_dir / "replay.json").read_text()

HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Population Trials — Replay Console · A2ZAI Lab</title>
<style>
  :root{--navy:#101B33;--navy2:#16264A;--cream:#FBF6EA;--orange:#E8762D;--red:#D64533;--teal:#2E9E7B;--ink:#EDEAE2;--dim:#9AA5BC;--line:#2A3B63}
  *{box-sizing:border-box;font-family:ui-sans-serif,system-ui,'Segoe UI',Roboto,sans-serif}
  body{margin:0;background:var(--navy);color:var(--ink)}
  header{display:flex;align-items:baseline;gap:14px;padding:14px 20px;border-bottom:1px solid var(--line)}
  header h1{font-size:19px;margin:0;letter-spacing:.4px} header h1 b{color:var(--orange)}
  header .sub{color:var(--dim);font-size:12.5px}
  header .run{margin-left:auto;font-size:12.5px;color:var(--cream);background:var(--navy2);border:1px solid var(--line);padding:5px 10px;border-radius:20px}
  main{display:grid;grid-template-columns:250px 1fr 330px;gap:0;min-height:calc(100vh - 57px)}
  .panel{padding:16px;border-right:1px solid var(--line)}
  .panel h3{font-size:11px;letter-spacing:1.6px;color:var(--dim);margin:18px 0 8px;text-transform:uppercase}
  .panel h3:first-child{margin-top:0}
  .opt{display:block;width:100%;text-align:left;background:var(--navy2);border:1px solid var(--line);color:var(--ink);border-radius:8px;padding:8px 10px;margin:6px 0;font-size:13px;cursor:pointer}
  .opt.sel{border-color:var(--orange);box-shadow:inset 0 0 0 1px var(--orange)}
  .opt.dis{opacity:.45;cursor:not-allowed}
  .opt small{display:block;color:var(--dim);font-size:11px;margin-top:2px}
  input[type=range]{width:100%;accent-color:var(--orange)}
  .row{display:flex;gap:8px;align-items:center}
  .btn{background:var(--orange);border:none;color:#fff;font-weight:700;border-radius:8px;padding:9px 14px;cursor:pointer;font-size:13px}
  .btn.ghost{background:var(--navy2);color:var(--ink);border:1px solid var(--line)}
  .stage{padding:16px 18px;border-right:1px solid var(--line)}
  .weekline{display:flex;align-items:baseline;gap:12px}
  .weekline .wk{font-size:26px;font-weight:800}
  .weekline .epi{color:var(--dim);font-size:13px}
  .counts{margin-left:auto;display:flex;gap:14px;font-size:13px}
  .counts b{font-size:16px}
  .dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:0}
  canvas#grid{width:100%;background:#0C1528;border:1px solid var(--line);border-radius:10px}
  .zones{display:flex;gap:14px;color:var(--dim);font-size:11.5px;margin-top:6px;flex-wrap:wrap}
  .right{padding:16px}
  canvas#curve{width:100%;background:var(--cream);border-radius:10px}
  .score{margin-top:14px;background:var(--navy2);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
  .score .big{font-size:30px;font-weight:800}
  .bar{height:8px;background:#0C1528;border-radius:4px;margin:5px 0 9px;overflow:hidden}
  .bar i{display:block;height:100%;background:var(--orange);width:0;transition:width .5s}
  .bar.g i{background:var(--teal)} .bar.r i{background:var(--red)}
  .score label{font-size:11.5px;color:var(--dim);display:flex;justify-content:space-between}
  .gate{margin-top:8px;font-size:12.5px;color:var(--orange);font-weight:700}
  .trace{margin-top:14px;font-size:12.5px}
  .trace .card{background:var(--navy2);border:1px solid var(--line);border-radius:8px;padding:8px 10px;margin:6px 0}
  .trace .card b{color:var(--cream)}
  .trace .why{color:var(--dim);font-size:12px}
  footer{padding:10px 20px;border-top:1px solid var(--line);color:var(--dim);font-size:12.5px}
  footer b{color:var(--cream)}
  #agentCard{font-size:12.5px;color:var(--ink)}
  @media(max-width:1100px){main{grid-template-columns:1fr}.panel,.stage,.right{border-right:none;border-bottom:1px solid var(--line)}}
</style></head><body>
<header>
  <h1>POPULATION <b>TRIALS</b></h1><span class="sub">A2ZAI Lab — a scored simulation, not a demo</span>
  <span class="run" id="runChip"></span>
</header>
<main>
  <aside class="panel">
    <h3>Dataset</h3>
    <button class="opt sel">Texas flu — fall 2025 season<small>CDC ILINet via Delphi API · verified pull · 49 weeks</small></button>
    <button class="opt dis">Dallas County — school absences (DCHHS)<small>flagship calibration key · wiring next</small></button>
    <button class="opt dis">Chicago crime — 7.7M+ records<small>city data portal · second case</small></button>
    <h3>Model seat</h3>
    <div id="seats"></div>
    <h3>Pool size (view)</h3>
    <input type="range" id="poolRange" min="100" max="1000" step="100" value="1000">
    <div class="row"><span id="poolLabel" style="font-size:13px"></span></div>
    <small style="color:var(--dim)">Recorded run: 1,000 agents. The slider thins the view; it never rewrites the run.</small>
    <h3>Question</h3>
    <button class="opt sel">Reproduce the season<small>calibration — the pool must earn its score first</small></button>
    <button class="opt dis">What if: close schools at the peak?<small>🔒 locked — unlocks at calibration ≥ 70 (Lab gate)</small></button>
    <h3>Playback</h3>
    <div class="row"><button class="btn" id="playBtn">▶ Replay</button>
    <button class="btn ghost" id="resetBtn">↺</button>
    <label style="font-size:12px;color:var(--dim)">speed <select id="speed"><option>1</option><option>2</option><option>4</option></select>×</label></div>
    <input type="range" id="scrub" min="0" max="14" value="0" style="margin-top:10px">
    <h3>Agent</h3><div id="agentCard">Click any dot to read its season.</div>
  </aside>
  <section class="stage">
    <div class="weekline"><span class="wk" id="wkLabel">Week 1</span><span class="epi" id="epiLabel"></span>
      <span class="counts">
        <span><span class="dot" style="background:#C9CFDB"></span>Well <b id="cS">–</b></span>
        <span><span class="dot" style="background:var(--red)"></span>Sick <b id="cI">–</b></span>
        <span><span class="dot" style="background:var(--teal)"></span>Recovered <b id="cR">–</b></span>
      </span></div>
    <canvas id="grid" width="1000" height="560"></canvas>
    <div class="zones"><span>▦ school catchments</span><span>▦ workplaces</span><span>▦ senior communities</span><span>▦ essential services</span><span style="margin-left:auto">one dot = one agent · states recorded every week of the run</span></div>
  </section>
  <aside class="right">
    <h3 style="font-size:11px;letter-spacing:1.6px;color:var(--dim);margin:0 0 8px">THE SCORE ASSEMBLES LIVE</h3>
    <canvas id="curve" width="620" height="300"></canvas>
    <div class="score">
      <div class="row"><span class="big" id="scoreBig">–</span><span style="color:var(--dim)">/ 100 calibration</span></div>
      <label>curve shape <span id="vShape"></span></label><div class="bar" id="bShape"><i></i></div>
      <label>peak timing <span id="vPeak"></span></label><div class="bar" id="bPeak"><i></i></div>
      <label>magnitude <span id="vMag"></span></label><div class="bar" id="bMag"><i></i></div>
      <div class="gate" id="gateLine"></div>
    </div>
    <div class="trace"><h3 style="font-size:11px;letter-spacing:1.6px;color:var(--dim)">TRACE — THIS WEEK</h3><div id="traceBox"></div></div>
  </aside>
</main>
<footer><b>The value, on the artifact:</b> a cheap agent pool must reproduce a real season it never saw — scored in public — before any of its advice may be believed. Run cost: $0.00 (stand-in agents, v0) · receipts live with the run.</footer>
<script>
const R = __REPLAY__;
const N = R.n_agents, W = R.weekly_states.length;
const grid = document.getElementById('grid'), g = grid.getContext('2d');
const curve = document.getElementById('curve'), c = curve.getContext('2d');
const COLS = 40, ROWS = 25, CW = grid.width / COLS, CH = grid.height / ROWS;
const ZONE = {school_household:'rgba(232,118,45,.06)',working_adult:'rgba(70,120,220,.07)',elder:'rgba(46,158,123,.07)',essential_worker:'rgba(200,170,60,.07)'};
const agents = [];
(function(){ // lay agents into cohort zones, in creation order
  const bounds=[]; let acc=0;
  const order=['school_household','working_adult','elder','essential_worker'];
  for(const co of order){ const n=R.agent_cohorts.filter(x=>x===co).length; bounds.push([acc,acc+n,co]); acc+=n; }
  for(let i=0;i<N;i++){
    const zone=bounds.find(b=>i>=b[0]&&i<b[1]);
    const li=i-zone[0], perRow=COLS, row=Math.floor(li/perRow), col=li%perRow;
    const zr=Math.floor((zone[0]/N)*ROWS), 
    agents.push({i,cohort:R.agent_cohorts[i],x:(col+0.5)*CW,y:0,zr,zone});
  }
  // simple global grid placement (zones drawn as tints by index bands)
  agents.forEach((a,idx)=>{ a.x=((idx%COLS)+0.5)*CW; a.y=(Math.floor(idx/COLS)+0.5)*CH; });
  agents._bounds=bounds;
})();
let week=0, playing=false, timer=null, viewN=1000, picked=null;
const seats=[['mock v0 — rule stand-ins','recorded run · $0.00',true],['Muse Spark 1.3','v1 · takes the seat next',false],['Muse Wonder 1.0','examiner tier · Trial #1: 97.2',false],['Muse Glimmer 30B','open weights · via Modal',false]];
document.getElementById('seats').innerHTML=seats.map(s=>`<button class="opt ${s[2]?'sel':'dis'}">${s[2]?'●':'○'} ${s[0]}<small>${s[1]}</small></button>`).join('');
document.getElementById('runChip').textContent='RECORDED RUN · '+R.run;
document.getElementById('poolLabel').textContent='1,000 agents shown';
function stateAt(a,w){ return R.weekly_states[w][a.i]; }
function drawGrid(){
  g.clearRect(0,0,grid.width,grid.height);
  for(const [s,e,co] of agents._bounds){ const y0=(s/N)*grid.height; g.fillStyle=ZONE[co]; g.fillRect(0,y0,grid.width,((e-s)/N)*grid.height); }
  const step=Math.max(1,Math.round(N/viewN));
  for(let k=0;k<N;k+=step){ const a=agents[k]; const st=stateAt(a,week);
    g.beginPath(); g.arc(a.x,a.y,picked===a.i?7:5.4,0,7);
    g.fillStyle= st==='I' ? '#D64533' : st==='R' ? '#2E9E7B' : '#C9CFDB'; g.fill();
    if(picked===a.i){ g.strokeStyle='#E8762D'; g.lineWidth=2; g.stroke(); } }
  const s=R.weekly_states[week];
  document.getElementById('cS').textContent=[...s].filter(x=>x==='S').length;
  document.getElementById('cI').textContent=[...s].filter(x=>x==='I').length;
  document.getElementById('cR').textContent=[...s].filter(x=>x==='R').length;
  document.getElementById('wkLabel').textContent='Week '+(week+1)+' of '+W;
  document.getElementById('epiLabel').textContent='epiweek '+R.epiweeks[week]+' · the holdout — the pool never saw these weeks';
}
function drawCurve(){
  const w=curve.width,h=curve.height,pad=34; c.clearRect(0,0,w,h);
  const mx=Math.max(...R.real_wili,...R.sim_ili_pct)*1.15;
  const X=i=>pad+(w-pad-8)*i/(W-1), Y=v=>h-26-(h-48)*v/mx;
  c.strokeStyle='#D8CFBB'; c.beginPath(); c.moveTo(pad,8); c.lineTo(pad,h-26); c.lineTo(w-8,h-26); c.stroke();
  c.font='11px sans-serif'; c.fillStyle='#6B6250';
  c.fillText('ILI %',6,16); c.fillText('weeks →',w-52,h-8);
  c.lineWidth=2.6; c.strokeStyle='#1B2A4A'; c.beginPath();
  R.real_wili.forEach((v,i)=>{ const x=X(i),y=Y(v); i?c.lineTo(x,y):c.moveTo(x,y); }); c.stroke();
  c.strokeStyle='#E8762D'; c.setLineDash([6,4]); c.beginPath();
  for(let i=0;i<=week;i++){ const x=X(i),y=Y(R.sim_ili_pct[i]); i?c.lineTo(x,y):c.moveTo(x,y); } c.stroke(); c.setLineDash([]);
  c.fillStyle='#1B2A4A'; c.fillText('— reality',pad+8,16);
  c.fillStyle='#E8762D'; c.fillText('–– the pool',pad+70,16);
}
function drawTrace(){
  const box=document.getElementById('traceBox'); const samples=R.sample_decisions[week]||[];
  let html='';
  if(R.planner_trace && R.planner_trace.length){
    for(const p of R.planner_trace.filter(p=>p.week===week))
      html+=`<div class="card"><b>${p.cohort}</b> — contacts ×${p.params.contact_factor_mean}, care-seek ${p.params.care_seek}<div class="why">“${p.params.rationale||''}”</div></div>`;
  }
  for(const s of samples.slice(0,4))
    html+=`<div class="card"><b>agent #${s.agent}</b> · ${s.cohort}<div class="why">saw ILI ${Number(s.card.local_ili_pct).toFixed(1)}% → contacts ×${s.decision.contact_factor}, attend: ${s.decision.attend_school?'yes':'no'}, care-seek ${s.decision.care_seek}</div></div>`;
  box.innerHTML=html||'<div class="why">No trace recorded for this week.</div>';
}
function drawScore(final){
  const sc=R.score, upto = final?1:(week+1)/W;
  const set=(bar,val,max,label,el)=>{ document.querySelector('#'+bar+' i').style.width=(100*val/max*upto)+'%'; document.getElementById(el).textContent=final?val.toFixed(1)+' / '+max:'…'; };
  set('bShape',sc.components.curve_shape_40,40,'','vShape'); set('bPeak',sc.components.peak_timing_30,30,'','vPeak'); set('bMag',sc.components.magnitude_30,30,'','vMag');
  document.getElementById('scoreBig').textContent= final? sc.calibration_score.toFixed(1) : '···';
  document.getElementById('gateLine').textContent = final
    ? (sc.may_publish_whatifs? '✓ gate passed — what-if questions unlocked' : '⛔ gate: peak missed by '+sc.peak_week_error+' wks → what-if conclusions NOT published')
    : 'score lands when the holdout completes…';
  document.querySelector('#bPeak').className='bar '+(sc.peak_week_error>=3?'r':'');
}
function render(){ drawGrid(); drawCurve(); drawTrace(); drawScore(week>=W-1); document.getElementById('scrub').value=week; }
function step(){ if(week<W-1){ week++; render(); } else { pause(); } }
function play(){ playing=true; document.getElementById('playBtn').textContent='⏸ Pause';
  timer=setInterval(step, 750/Number(document.getElementById('speed').value)); }
function pause(){ playing=false; document.getElementById('playBtn').textContent='▶ Replay'; clearInterval(timer); }
document.getElementById('playBtn').onclick=()=> playing?pause():(week>=W-1?(week=0,render(),play()):play());
document.getElementById('resetBtn').onclick=()=>{ pause(); week=0; render(); };
document.getElementById('speed').onchange=()=>{ if(playing){ pause(); play(); } };
document.getElementById('scrub').oninput=e=>{ pause(); week=Number(e.target.value); render(); };
document.getElementById('poolRange').oninput=e=>{ viewN=Number(e.target.value); document.getElementById('poolLabel').textContent=viewN.toLocaleString()+' agents shown'; drawGrid(); };
grid.onclick=e=>{ const r=grid.getBoundingClientRect(); const x=(e.clientX-r.left)*grid.width/r.width, y=(e.clientY-r.top)*grid.height/r.height;
  let best=null,bd=1e9; for(const a of agents){ const d=(a.x-x)**2+(a.y-y)**2; if(d<bd){bd=d;best=a;} }
  if(best){ picked=best.i; const hist=[...Array(W)].map((_,w)=>stateAt(best,w)).join('');
    const name={S:'well',I:'SICK',R:'recovered'};
    document.getElementById('agentCard').innerHTML=`<b>agent #${best.i}</b> · ${best.cohort}<br>season: ${hist.split('').map(ch=>name[ch]).join(' → ')}<br><span style="color:var(--dim)">final state: ${name[stateAt(best,W-1)]}</span>`;
    drawGrid(); } };
render();
</script></body></html>
"""

out.write_text(HTML.replace("__REPLAY__", replay))
print(f"wrote {out} ({out.stat().st_size/1024:.0f} KB) with run {run_dir.name}")
