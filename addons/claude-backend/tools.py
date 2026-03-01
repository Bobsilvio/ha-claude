"""Tool definitions and execution for Home Assistant AI assistant."""

import os
import json
import logging
import requests
from datetime import datetime, timedelta

import api

try:
    import mcp
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

logger = logging.getLogger(__name__)

AI_SIGNATURE = getattr(api, "AGENT_NAME", "Amira") or "Amira"

# Buffer for chunked HTML dashboard creation (draft mode)
# Key: dashboard name (slug), Value: {"html": str, "title": str, "entities": list, ...}
_html_drafts: dict = {}


def _build_dashboard_html(title: str, entities: list, theme: str,
                          accent_color: str, sections: list,
                          *, lang: str | None = None,
                          footer_text: str | None = None) -> str:
    """Build HTML dashboard from structured design spec V2.

    The agent designs the dashboard architecture (sections, layout, grouping, colors).
    This function renders beautiful HTML with auth, WebSocket, Chart.js.

    Section types: hero, pills, flow, gauge, gauges, kpi, chart, trend, entities, controls, stats, value
    Layout: each section has 'span' (1=third, 2=two-thirds, 3=full-width, default 3).
    """
    import html as html_module

    safe_title = html_module.escape(title)
    entities_json = json.dumps(entities, ensure_ascii=False)
    sections_json = json.dumps(sections, ensure_ascii=False)

    h = accent_color.lstrip('#')
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    try:
        accent_rgb = f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"
    except (ValueError, IndexError):
        accent_rgb = "102,126,234"

    theme_css = ""
    if theme == "dark":
        theme_css = ":root{--bg:#0f172a;--bg2:#1e293b;--text:#e2e8f0;--text2:#94a3b8;--card:rgba(30,41,59,.85);--border:#334155}"
    elif theme == "light":
        theme_css = ":root{--bg:#f0f2f5;--bg2:#fff;--text:#1a1a2e;--text2:#6b7280;--card:rgba(255,255,255,.85);--border:#e2e8f0}"

    if not lang:
        lang = getattr(api, "LANGUAGE", "en") or "en"
    lang = (str(lang).lower() or "en")
    if lang not in ("en", "it", "es", "fr"):
        lang = "en"

    agent_name = getattr(api, "AGENT_NAME", "Amira") or "Amira"
    default_footer = getattr(api, "HTML_DASHBOARD_FOOTER", "") or ""
    if not footer_text:
        footer_text = default_footer.strip() or f"Dashboard by {agent_name} · Real-time"

    html = r"""<!DOCTYPE html>
<html lang="__LANG__">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<script src="https://unpkg.com/vue@3/dist/vue.global.prod.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
<style>
:root{--accent:__ACCENT__;--accent-rgb:__ACCENT_RGB__;--bg:#f0f2f5;--bg2:#fff;--text:#1a1a2e;--text2:#6b7280;
--card:rgba(255,255,255,.85);--border:#e2e8f0;--green:#10b981;--yellow:#f59e0b;--red:#ef4444;--blue:#3b82f6;--r:16px}
@media(prefers-color-scheme:dark){:root{--bg:#0f172a;--bg2:#1e293b;--text:#e2e8f0;--text2:#94a3b8;--card:rgba(30,41,59,.85);--border:#334155}}
__THEME_CSS__
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;min-height:100vh}
.dash{max-width:1400px;margin:0 auto;padding:1.25rem;display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}
.span-1{grid-column:span 1}.span-2{grid-column:span 2}.span-3{grid-column:span 3}
@media(max-width:980px){.dash{grid-template-columns:1fr}.span-1,.span-2,.span-3{grid-column:span 1}}
.conn{position:fixed;top:.75rem;right:.75rem;display:flex;align-items:center;gap:6px;font-size:.7rem;
padding:5px 12px;background:var(--card);border:1px solid var(--border);border-radius:20px;backdrop-filter:blur(8px);z-index:100}
.cdot{width:7px;height:7px;border-radius:50%;background:var(--red)}.cdot.on{background:var(--green);box-shadow:0 0 6px var(--green)}
.hero{display:flex;align-items:center;gap:1.25rem;background:linear-gradient(135deg,var(--accent),color-mix(in srgb,var(--accent),#000 30%));color:#fff;
padding:1.5rem;border-radius:var(--r);box-shadow:0 8px 24px rgba(var(--accent-rgb),.25);flex-wrap:wrap}
.hero-ico{font-size:2.5rem}.hero h2{font-size:1.4rem;font-weight:800}.hero p{opacity:.85;font-size:.85rem;margin-top:2px}
.hero-stats{display:flex;gap:1rem;flex-wrap:wrap;margin-top:.5rem;font-size:.85rem;opacity:.9}
.pills{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:.65rem}
.pill{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:10px 12px;backdrop-filter:blur(8px)}
.pill-l{font-size:.72rem;color:var(--text2)}.pill-v{font-size:1.1rem;font-weight:800;margin-top:2px}.pill-v small{font-weight:600;color:var(--text2);font-size:.72rem}
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:1rem;backdrop-filter:blur(12px);height:100%}
.card-h{display:flex;justify-content:space-between;align-items:center;margin-bottom:.75rem}
.card-t{font-weight:750;font-size:.92rem}.card-ico{margin-right:6px}
.s-gradient{background:linear-gradient(135deg,rgba(var(--accent-rgb),.12),rgba(var(--accent-rgb),.03))}
.s-outlined{background:transparent;border:2px solid var(--accent)}.s-flat{backdrop-filter:none;background:var(--bg2)}
.flow{display:grid;gap:.65rem}.flow-n{border:1px solid var(--border);border-radius:14px;padding:.7rem;background:rgba(0,0,0,.04);text-align:center}
.flow-n.mid{background:rgba(var(--accent-rgb),.12);border-color:rgba(var(--accent-rgb),.3)}
.flow-l{font-size:.72rem;color:var(--text2);margin-bottom:2px}.flow-v{font-size:1.3rem;font-weight:900;line-height:1.1}.flow-u{font-size:.68rem;color:var(--text2)}
.gauge-w{display:grid;grid-template-columns:130px 1fr;gap:.75rem;align-items:center}
@media(max-width:640px){.gauge-w{grid-template-columns:1fr;justify-items:center}}
.gauge-svg{width:130px;height:130px}.gauge-bg{fill:none;stroke:var(--border);stroke-width:10}.gauge-fg{fill:none;stroke:var(--accent);stroke-width:10;stroke-linecap:round;
transform:rotate(-90deg);transform-origin:60px 60px;transition:stroke-dasharray .6s ease}
.gauge-txt{font-size:18px;font-weight:900;fill:var(--text);text-anchor:middle}
.gauge-stats{display:grid;gap:.4rem}.gs{background:var(--bg2);border-radius:10px;padding:.5rem .65rem}.gs-l{font-size:.72rem;color:var(--text2)}.gs-v{font-weight:800;margin-top:1px}
.gauges{display:grid;grid-template-columns:repeat(auto-fill,minmax(90px,1fr));gap:.6rem}
.gi{text-align:center}.gi svg{width:85px;height:85px}.gi .gn{font-size:.7rem;color:var(--text2);margin-top:.1rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kpi{display:grid;grid-template-columns:repeat(auto-fill,minmax(115px,1fr));gap:.55rem}
.ki{background:var(--bg2);border-radius:12px;padding:.65rem;text-align:center}
.ki-l{font-size:.7rem;color:var(--text2)}.ki-v{font-size:1.2rem;font-weight:900;margin-top:2px;line-height:1.1}.ki-u{font-size:.65rem;color:var(--text2)}
.chart-box{position:relative;width:100%;height:250px}.chart-box canvas{display:block;width:100%!important;height:100%!important}
.elist .er{display:flex;align-items:center;gap:.4rem;padding:.45rem .6rem;border-radius:10px;margin-bottom:.25rem;background:var(--bg2)}
.er:hover{background:var(--border)}.er-ico{font-size:1rem;width:22px;text-align:center;flex-shrink:0}
.er-nm{flex:1;font-size:.83rem;font-weight:500;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.er-v{font-weight:700;font-size:.95rem;white-space:nowrap}.er-u{font-size:.68rem;color:var(--text2);margin-left:2px}
.tog{position:relative;width:40px;height:22px;cursor:pointer;background:var(--border);border-radius:11px;transition:background .2s;border:none;flex-shrink:0}
.tog.on{background:var(--green)}.tog::after{content:'';position:absolute;top:2px;left:2px;width:18px;height:18px;border-radius:50%;background:#fff;transition:transform .2s;box-shadow:0 1px 3px rgba(0,0,0,.2)}
.tog.on::after{transform:translateX(18px)}
.sl-w{display:flex;align-items:center;gap:6px;flex-shrink:0;width:110px}
.sl{-webkit-appearance:none;appearance:none;width:100%;height:5px;border-radius:3px;background:var(--border);outline:none;cursor:pointer}
.sl::-webkit-slider-thumb{-webkit-appearance:none;width:14px;height:14px;border-radius:50%;background:var(--accent);cursor:pointer}.sl-v{font-size:.78rem;font-weight:600}
.ctrls{display:grid;grid-template-columns:repeat(auto-fill,minmax(95px,1fr));gap:.6rem}
.cb{text-align:center;padding:.85rem .4rem;border-radius:14px;background:var(--bg2);cursor:pointer;transition:all .2s;border:2px solid transparent}
.cb:hover{border-color:var(--accent)}.cb.on{background:rgba(var(--accent-rgb),.15);border-color:var(--accent)}
.cb-ico{font-size:1.5rem;margin-bottom:.1rem}.cb-nm{font-size:.75rem;font-weight:500}.cb-st{font-size:.6rem;color:var(--text2);margin-top:.1rem}
.stats{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:.6rem}
.si{text-align:center;padding:.65rem;background:var(--bg2);border-radius:12px}
.si-ico{font-size:1.2rem;margin-bottom:.05rem}.si-v{font-size:1.4rem;font-weight:900;line-height:1}.si-u{font-size:.62rem;color:var(--text2)}.si-n{font-size:.7rem;color:var(--text2);margin-top:.1rem}
.bigv{text-align:center;padding:.75rem}.bigv-v{font-size:2.3rem;font-weight:900;line-height:1}.bigv-u{font-size:.9rem;color:var(--text2);margin-left:3px}.bigv-l{color:var(--text2);margin-top:.2rem;font-size:.82rem}
.trend-kpis{display:flex;gap:.75rem;margin-bottom:.85rem;flex-wrap:wrap}
.trend-kpi{display:flex;align-items:center;gap:.6rem;background:var(--bg2);border-radius:14px;padding:.55rem .85rem;flex:1;min-width:120px}
.trend-kpi-ico{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.1rem;flex-shrink:0;color:#fff}
.trend-kpi-v{font-size:1.25rem;font-weight:900;line-height:1.1}.trend-kpi-l{font-size:.7rem;color:var(--text2)}
.trend-chart{position:relative;width:100%;height:220px}.trend-chart canvas{display:block;width:100%!important;height:100%!important}
.err{background:#fee2e2;color:#991b1b;padding:1rem;border-radius:12px;margin-top:1rem;font-size:.85rem}
.ft{text-align:center;padding:1rem 0 .5rem;font-size:.68rem;color:var(--text2);grid-column:1/-1}
</style>
</head>
<body>
<div id="app">
<div class="conn"><div :class="['cdot',connected&&'on']"></div>{{ connected ? 'Live' : '...' }}</div>
<div class="dash">
<template v-for="(s,i) in sections" :key="i">

<div v-if="s.type==='hero'" class="hero span-3">
<div class="hero-ico">{{ s.icon || '\u26a1' }}</div>
<div><h2>{{ s.title }}</h2><p v-if="s.description">{{ s.description }}</p>
<div class="hero-stats"><span v-for="it in items(s)" :key="it.e">{{ it.label || nm(it.e) }}: <b>{{ fv(it.e) }} {{ fu(it.e) }}</b></span></div>
</div></div>

<div v-else-if="s.type==='pills'" class="pills span-3">
<div v-for="it in items(s)" :key="it.e" class="pill"><div class="pill-l">{{ it.label || nm(it.e) }}</div>
<div class="pill-v">{{ fv(it.e) }} <small>{{ fu(it.e) }}</small></div></div></div>

<div v-else :class="['span-'+(s.span||3)]"><div :class="['card',s.style?'s-'+s.style:'']">
<div v-if="s.title" class="card-h"><div><span v-if="s.icon" class="card-ico">{{ s.icon }}</span><span class="card-t">{{ s.title }}</span></div></div>

<div v-if="s.type==='flow'" class="flow" :style="{gridTemplateColumns:'repeat('+(s.nodes||[]).length+',1fr)'}">
<div v-for="nd in s.nodes||[]" :key="nd.entity" :class="['flow-n',nd.highlight&&'mid']">
<div class="flow-l">{{ nd.label || nm(nd.entity) }}</div><div class="flow-v">{{ fv(nd.entity) }}</div><div class="flow-u">{{ fu(nd.entity) }}</div></div></div>

<div v-else-if="s.type==='gauge'" class="gauge-w">
<svg viewBox="0 0 120 120" class="gauge-svg"><circle cx="60" cy="60" r="48" class="gauge-bg"/>
<circle cx="60" cy="60" r="48" class="gauge-fg" :style="{strokeDasharray:gPct(s.entity)*3.014+' 301.4'}"/>
<text x="60" y="64" class="gauge-txt">{{ sv(s.entity) }}%</text></svg>
<div class="gauge-stats"><div v-for="st in s.stats||[]" :key="st.entity" class="gs">
<div class="gs-l">{{ st.label || nm(st.entity) }}</div><div class="gs-v">{{ fv(st.entity) }} {{ fu(st.entity) }}</div></div></div></div>

<div v-else-if="s.type==='gauges'" class="gauges">
<div v-for="it in items(s)" :key="it.e" class="gi">
<svg viewBox="0 0 36 36"><circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--border)" stroke-width="2.5"/>
<circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--accent)" stroke-width="2.5" :stroke-dasharray="gPct(it.e)+' 100'"
stroke-linecap="round" transform="rotate(-90 18 18)" style="transition:stroke-dasharray .6s ease"/>
<text x="18" y="17" text-anchor="middle" fill="var(--text)" style="font-size:.55rem;font-weight:700">{{ sv(it.e) }}</text>
<text x="18" y="22" text-anchor="middle" fill="var(--text2)" style="font-size:.28rem">{{ fu(it.e) || it.label }}</text>
</svg><div class="gn">{{ it.label || nm(it.e) }}</div></div></div>

<div v-else-if="s.type==='kpi'" class="kpi">
<div v-for="it in items(s)" :key="it.e" class="ki"><div class="ki-l">{{ it.label || nm(it.e) }}</div>
<div class="ki-v">{{ fv(it.e) }}</div><div class="ki-u">{{ fu(it.e) }}</div></div></div>

<div v-else-if="s.type==='chart'" class="chart-box"><canvas :id="'ch-'+i"></canvas></div>

<div v-else-if="s.type==='entities'" class="elist">
<div v-for="it in items(s)" :key="it.e" class="er">
<span class="er-ico">{{ dIco(it.e) }}</span><span class="er-nm">{{ it.label || nm(it.e) }}</span>
<template v-if="togDom(it.e)"><button :class="['tog',isOn(it.e)&&'on']" @click="toggle(it.e)"></button></template>
<template v-else-if="slDom(it.e)"><div class="sl-w"><input type="range" class="sl" :min="slMin(it.e)" :max="slMax(it.e)" :step="slStep(it.e)"
:value="numVal(it.e)" @change="setVal(it.e,$event.target.value)"/><span class="sl-v">{{ sv(it.e) }}</span></div></template>
<template v-else><span class="er-v">{{ fv(it.e) }}</span><span class="er-u">{{ fu(it.e) }}</span></template>
</div></div>

<div v-else-if="s.type==='controls'" class="ctrls">
<div v-for="it in items(s)" :key="it.e" :class="['cb',isOn(it.e)&&'on']" @click="toggle(it.e)">
<div class="cb-ico">{{ dIco(it.e) }}</div><div class="cb-nm">{{ it.label || nm(it.e) }}</div>
<div class="cb-st">{{ isOn(it.e) ? 'ON' : 'OFF' }}</div></div></div>

<div v-else-if="s.type==='stats'" class="stats">
<div v-for="it in items(s)" :key="it.e" class="si"><div class="si-ico">{{ dIco(it.e) }}</div>
<div class="si-v">{{ fv(it.e) }}</div><div class="si-u">{{ fu(it.e) }}</div>
<div class="si-n">{{ it.label || nm(it.e) }}</div></div></div>

<div v-else-if="s.type==='value'" class="bigv">
<div class="bigv-v">{{ fv(s.entity) }}<span class="bigv-u">{{ fu(s.entity) }}</span></div>
<div v-if="s.subtitle" class="bigv-l">{{ s.subtitle }}</div>
<div v-else class="bigv-l">{{ nm(s.entity) }}</div></div>

<div v-else-if="s.type==='trend'">
<div class="trend-kpis">
<div v-for="(it,j) in items(s)" :key="it.e" class="trend-kpi">
<div class="trend-kpi-ico" :style="{background:it.color||PAL[j%PAL.length]}">{{ it.icon || dIco(it.e) }}</div>
<div><div class="trend-kpi-v">{{ fv(it.e) }} <small style="font-size:.65rem;color:var(--text2)">{{ fu(it.e) }}</small></div>
<div class="trend-kpi-l">{{ it.label || nm(it.e) }}</div></div>
</div></div>
<div class="trend-chart"><canvas :id="'trend-'+i"></canvas></div>
</div>

</div></div>
</template>
<div v-if="error" class="err">{{ error }}</div>
<div class="ft">__FOOTER__</div>
</div></div>

<script>
(function(){
const{createApp,ref,reactive,onMounted,onUnmounted,nextTick}=Vue;
const ENTITIES=__ENTITIES_JSON__;
const SECTIONS=__SECTIONS_JSON__;
const PAL=['#667eea','#10b981','#f59e0b','#ef4444','#8b5cf6','#ec4899','#06b6d4','#84cc16','#f97316','#14b8a6'];
const DICO={sensor:'\ud83d\udcca',binary_sensor:'\ud83d\udd14',switch:'\ud83d\udd0c',light:'\ud83d\udca1',climate:'\ud83c\udf21\ufe0f',cover:'\ud83e\ude9f',fan:'\ud83c\udf00',
input_boolean:'\ud83d\udd18',input_number:'\ud83d\udd22',number:'\ud83d\udd22',automation:'\u2699\ufe0f',script:'\ud83d\udcdc',person:'\ud83d\udc64',weather:'\ud83c\udf24\ufe0f',
media_player:'\ud83c\udfb5',camera:'\ud83d\udcf7',lock:'\ud83d\udd12',vacuum:'\ud83e\uddf9'};
// Token cache — populated once, reused for all requests
let _cachedToken='';
function getToken(){try{return JSON.parse(localStorage.getItem('hassTokens')||'{}').access_token||''}catch(e){return''}}
// Resolve auth token across all HA contexts:
// 1. postMessage to parent iframe (HA Lovelace panel — works in Companion App)
// 2. window.externalApp (Android Companion App standalone)
// 3. window.webkit.messageHandlers (iOS Companion App standalone)
// 4. localStorage.hassTokens (desktop browser)
function getTokenAsync(){
  if(_cachedToken)return Promise.resolve(_cachedToken);
  return new Promise(resolve=>{
    const done=t=>{_cachedToken=t||'';resolve(_cachedToken)};
    // Strategy 1: ask parent window (works when page is inside HA Lovelace iframe)
    if(window.parent&&window.parent!==window){
      const onMsg=ev=>{
        if(ev.data&&ev.data.type==='auth/token'&&ev.data.token){
          window.removeEventListener('message',onMsg);
          clearTimeout(t1);
          done(ev.data.token);
        }
      };
      window.addEventListener('message',onMsg);
      const t1=setTimeout(()=>{
        window.removeEventListener('message',onMsg);
        tryNative();
      },1500);
      try{window.parent.postMessage({type:'auth/get_token'},'*')}catch(e){clearTimeout(t1);tryNative();}
      return;
    }
    tryNative();
    function tryNative(){
      try{
        if(window.externalApp&&window.externalApp.getExternalAuth){
          window.externalApp.getExternalAuth({callback:'_haTokenCb',type:'bearer'});
          window._haTokenCb=r=>{delete window._haTokenCb;done(r&&r.access_token?r.access_token:getToken())};
          setTimeout(()=>{if(window._haTokenCb){delete window._haTokenCb;done(getToken())}},2000);
          return;
        }
        if(window.webkit&&window.webkit.messageHandlers&&window.webkit.messageHandlers.getExternalAuth){
          window.webkit.messageHandlers.getExternalAuth.postMessage({callback:'_haTokenCb',type:'bearer'});
          window._haTokenCb=r=>{delete window._haTokenCb;done(r&&r.access_token?r.access_token:getToken())};
          setTimeout(()=>{if(window._haTokenCb){delete window._haTokenCb;done(getToken())}},2000);
          return;
        }
      }catch(e){}
      done(getToken());
    }
  });
}
function haHeaders(){return _cachedToken?{'Authorization':'Bearer '+_cachedToken,'Content-Type':'application/json'}:{'Content-Type':'application/json'}}

createApp({setup(){
const connected=ref(false),error=ref(''),sections=ref(SECTIONS),states=reactive({});
let ws,msgId=1,charts={},reconTimer,pollTimer;

function nm(e){return states[e]?.friendly_name||e.split('.').pop().replace(/_/g,' ')}
function sv(e){return states[e]?.state??'...'}
function fv(e){const s=states[e];if(!s)return'...';const n=parseFloat(s.state),u=(s.unit||'').toLowerCase();
if(isNaN(n))return s.state;if((u==='w'||u==='wh')&&Math.abs(n)>=1000)return(n/1000).toFixed(2);
return Math.abs(n)>=10000?n.toFixed(0):Math.abs(n)>=100?n.toFixed(1):Math.abs(n)>=1?n.toFixed(2):n.toFixed(3)}
function fu(e){const s=states[e];if(!s)return'';const n=parseFloat(s.state),u=s.unit||'';
if(u.toLowerCase()==='w'&&Math.abs(n)>=1000)return'kW';if(u.toLowerCase()==='wh'&&Math.abs(n)>=1000)return'kWh';return u}
function isOn(e){const s=sv(e);return s==='on'}
function numVal(e){return parseFloat(sv(e))||0}
function gPct(e){return Math.min(100,Math.max(0,numVal(e)))}
function dIco(e){return DICO[e.split('.')[0]]||'\ud83d\udce6'}
function togDom(e){const d=e.split('.')[0];return['switch','light','input_boolean'].includes(d)}
function slDom(e){const d=e.split('.')[0];return['number','input_number'].includes(d)}
function slMin(e){return states[e]?.attributes?.min??0}
function slMax(e){return states[e]?.attributes?.max??100}
function slStep(e){return states[e]?.attributes?.step??1}
function items(sec){if(sec.items)return sec.items.map(it=>typeof it==='string'?{e:it,label:'',color:'',icon:''}:{e:it.entity,label:it.label||'',color:it.color||'',icon:it.icon||''});
if(sec.entities)return sec.entities.map(e=>({e,label:'',color:'',icon:''}));return ENTITIES.map(e=>({e,label:'',color:'',icon:''}))}

function callSvc(d,svc,eid,data){
fetch('/api/services/'+d+'/'+svc,{method:'POST',headers:haHeaders(),
body:JSON.stringify({entity_id:eid,...(data||{})})}).catch(x=>console.warn(x))}
function toggle(eid){const d=eid.split('.')[0];callSvc(d==='light'?'light':d==='input_boolean'?'input_boolean':'switch','toggle',eid,{})}
function setVal(eid,v){const d=eid.split('.')[0];callSvc(d==='input_number'?'input_number':'number','set_value',eid,{value:parseFloat(v)})}

function applyStates(list){list.forEach(s=>{if(ENTITIES.includes(s.entity_id))states[s.entity_id]={state:s.state,friendly_name:s.attributes?.friendly_name||'',
unit:s.attributes?.unit_of_measurement||'',attributes:s.attributes||{}}});nextTick(()=>{initCharts();initTrends()})}

function fetchStates(){
fetch('/api/states',{headers:haHeaders()}).then(r=>{if(!r.ok)throw new Error(r.status);return r.json()}).then(applyStates)
.catch(e=>{if(!connected.value)error.value='REST: '+e.message})}

function startPolling(){if(pollTimer)return;fetchStates();pollTimer=setInterval(fetchStates,5000)}

function connect(){getTokenAsync().then(token=>{
if(!token){error.value='';startPolling();return}
try{const p=location.protocol==='https:'?'wss:':'ws:';
ws=new WebSocket(p+'//'+location.host+'/api/websocket');
ws.onmessage=ev=>{const m=JSON.parse(ev.data);
if(m.type==='auth_required')ws.send(JSON.stringify({type:'auth',access_token:token}));
else if(m.type==='auth_ok'){connected.value=true;error.value='';fetchStates();ws.send(JSON.stringify({id:msgId++,type:'subscribe_events',event_type:'state_changed'}))}
else if(m.type==='auth_invalid'){error.value='';connected.value=false;startPolling()}
else if(m.type==='event'&&m.event?.event_type==='state_changed'){const d=m.event.data;
if(d&&ENTITIES.includes(d.entity_id)&&d.new_state){states[d.entity_id]={state:d.new_state.state,friendly_name:d.new_state.attributes?.friendly_name||'',
unit:d.new_state.attributes?.unit_of_measurement||'',attributes:d.new_state.attributes||{}};initCharts()}}};
ws.onerror=()=>{connected.value=false;startPolling()};
ws.onclose=()=>{connected.value=false;reconTimer=setTimeout(connect,10000)};
}catch(e){startPolling()}})}

function initCharts(){const dk=window.matchMedia('(prefers-color-scheme:dark)').matches;
SECTIONS.forEach((sec,i)=>{if(sec.type!=='chart')return;
const cv=document.getElementById('ch-'+i);if(!cv)return;
if(charts[i])charts[i].destroy();
const eids=sec.entities||ENTITIES;
const nums=eids.filter(e=>!isNaN(parseFloat(states[e]?.state)));if(!nums.length)return;
const labels=nums.map(e=>(states[e]?.friendly_name||e.split('.').pop()).replace(/_/g,' '));
const data=nums.map(e=>parseFloat(states[e]?.state)||0);const ct=sec.chart_type||'bar';
charts[i]=new Chart(cv,{type:ct,data:{labels,datasets:[{data,backgroundColor:PAL.slice(0,data.length),borderWidth:0,
borderRadius:ct==='bar'?6:0,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,
plugins:{legend:{display:ct!=='bar',position:'bottom',labels:{boxWidth:12,padding:8,font:{size:11},color:dk?'#94a3b8':'#6b7280'}}},
scales:ct==='bar'||ct==='line'?{x:{grid:{color:dk?'#334155':'#e2e8f0'},ticks:{color:dk?'#94a3b8':'#6b7280',font:{size:10}}},
y:{grid:{color:dk?'#334155':'#e2e8f0'},ticks:{color:dk?'#94a3b8':'#6b7280',font:{size:10}}}}:{}}
})})}

let trendsLoaded=false;
function initTrends(){if(trendsLoaded)return;trendsLoaded=true;
const dk=window.matchMedia('(prefers-color-scheme:dark)').matches;
SECTIONS.forEach((sec,i)=>{if(sec.type!=='trend')return;
const cv=document.getElementById('trend-'+i);if(!cv)return;
const eids=(sec.items||[]).map(it=>typeof it==='string'?it:it.entity);
if(!eids.length)return;const hours=sec.hours||24;
const end=new Date().toISOString(),start=new Date(Date.now()-hours*3600000).toISOString();
fetch('/api/history/period/'+start+'?filter_entity_id='+eids.join(',')+'&end_time='+end+'&minimal_response&no_attributes',{headers:haHeaders()})
.then(r=>r.json()).then(histData=>{
if(!Array.isArray(histData)||!histData.length)return;
const datasets=[];
histData.forEach((entityHist,j)=>{if(!entityHist.length)return;
const eid=entityHist[0].entity_id;
const item=(sec.items||[]).find(it=>(typeof it==='string'?it:it.entity)===eid)||{};
const color=item.color||PAL[j%PAL.length];
const pts=entityHist.filter(p=>!isNaN(parseFloat(p.state))).map(p=>({x:new Date(p.last_changed),y:parseFloat(p.state)}));
datasets.push({label:item.label||eid.split('.').pop().replace(/_/g,' '),data:pts,borderColor:color,
backgroundColor:function(ctx){const c=ctx.chart.ctx,area=ctx.chart.chartArea;if(!area)return color+'33';
const g=c.createLinearGradient(0,area.top,0,area.bottom);g.addColorStop(0,color+'66');g.addColorStop(1,color+'05');return g},
fill:true,tension:.4,borderWidth:2,pointRadius:0,pointHitRadius:8})});
if(charts['t'+i])charts['t'+i].destroy();
charts['t'+i]=new Chart(cv,{type:'line',data:{datasets},
options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
plugins:{legend:{display:datasets.length>1,position:'bottom',labels:{boxWidth:10,padding:8,font:{size:11},color:dk?'#94a3b8':'#6b7280',usePointStyle:true}},
tooltip:{callbacks:{label:function(ctx){return ctx.dataset.label+': '+ctx.parsed.y.toFixed(1)}}}},
scales:{x:{type:'time',time:{tooltipFormat:'HH:mm',displayFormats:{hour:'HH:mm',day:'MMM d'}},
grid:{color:dk?'#33415522':'#e2e8f022'},ticks:{color:dk?'#94a3b8':'#6b7280',font:{size:10},maxTicksLimit:8}},
y:{grid:{color:dk?'#33415522':'#e2e8f022'},ticks:{color:dk?'#94a3b8':'#6b7280',font:{size:10}}}}}
})}).catch(e=>console.warn('Trend fetch error:',e))})}

onMounted(connect);
onUnmounted(()=>{ws?.close();clearTimeout(reconTimer);clearInterval(pollTimer);Object.values(charts).forEach(c=>c.destroy())});
return{sections,connected,error,nm,sv,fv,fu,isOn,numVal,gPct,dIco,togDom,slDom,slMin,slMax,slStep,items,toggle,setVal,PAL}
}}).mount('#app');
})();
</script>
</body>
</html>"""

    html = html.replace("__TITLE__", safe_title)
    html = html.replace("__ENTITIES_JSON__", entities_json)
    html = html.replace("__SECTIONS_JSON__", sections_json)
    html = html.replace("__ACCENT__", accent_color)
    html = html.replace("__ACCENT_RGB__", accent_rgb)
    html = html.replace("__THEME_CSS__", theme_css)
    html = html.replace("__LANG__", lang)
    html = html.replace("__FOOTER__", html_module.escape(str(footer_text)))

    return html


# Standard Vue + WebSocket boilerplate for auto-completing truncated HTML dashboards
_VUE_BOILERPLATE = """
<script>
const ENTITIES = __ENTITIES_JSON__;
const {createApp, ref, reactive, computed, onMounted, onUnmounted} = Vue;
createApp({
  setup() {
    const states = reactive({});
    const conn = reactive({ok: false, mode: 'connecting'});
    const title = __TITLE_JSON__;
    const nowText = ref('');

    const sv = (eid) => (states[eid]||{}).state || '';
    const nv = (eid) => parseFloat(sv(eid)) || 0;
    const fmt = (v, d) => v != null && !isNaN(v) ? Number(v).toFixed(d != null ? d : 1) : '--';
    const entityName = (eid) => (states[eid]||{}).friendly_name || eid.split('.').pop().replace(/_/g, ' ');
    const powerText = (w) => {
      const a = Math.abs(w||0);
      return a >= 1000 ? {val: fmt(a/1000,1), unit:'kW'} : {val: fmt(a,0), unit:'W'};
    };

    // Generic entity value getters - model templates may use specific vars
    // We expose all entity values as computed properties via Proxy
    const entityProxy = new Proxy({}, {
      get(_, prop) {
        // Try to find an entity matching the prop name
        for (const eid of ENTITIES) {
          const short = eid.split('.').pop();
          if (short === prop || short.replace(/_/g,'') === prop.replace(/_/g,'')) {
            return nv(eid);
          }
        }
        return undefined;
      }
    });

    // Common computed shortcuts the model might use
    const solarW = computed(() => {
      for (const e of ENTITIES) { if (/solar.*power|solar.*watt|solarpower/i.test(e)) return nv(e); }
      return 0;
    });
    const gridW = computed(() => {
      for (const e of ENTITIES) { if (/grid.*power|gridpower/i.test(e)) return nv(e); }
      return 0;
    });
    const battW = computed(() => {
      for (const e of ENTITIES) { if (/batter.*power|battery_power/i.test(e)) return nv(e); }
      return 0;
    });
    const battSoc = computed(() => {
      for (const e of ENTITIES) { if (/batterysoc|battery.*soc|battery.*level/i.test(e)) return nv(e); }
      return null;
    });
    const price = computed(() => {
      for (const e of ENTITIES) { if (/prezzo|price|costo.*kwh/i.test(e)) return nv(e); }
      return null;
    });
    const solarShare = computed(() => {
      for (const e of ENTITIES) { if (/contributo.*solar|solar.*share|solar.*percent/i.test(e)) return nv(e); }
      return null;
    });
    const solarTodayKwh = computed(() => {
      for (const e of ENTITIES) { if (/solar.*oggi|solar.*today|solare_oggi/i.test(e)) return nv(e); }
      return null;
    });

    let timeInterval, ws;
    const updateTime = () => { nowText.value = new Date().toLocaleTimeString(); };

    let _tok = '';
    const getTokenAsync = () => {
      if (_tok) return Promise.resolve(_tok);
      return new Promise(resolve => {
        const done = t => { _tok = t||''; resolve(_tok); };
        // 1. parent postMessage (HA Lovelace iframe — Companion App)
        if (window.parent && window.parent !== window) {
          const onMsg = ev => {
            if (ev.data && ev.data.type === 'auth/token' && ev.data.token) {
              window.removeEventListener('message', onMsg);
              clearTimeout(t1);
              done(ev.data.token);
            }
          };
          window.addEventListener('message', onMsg);
          const t1 = setTimeout(() => { window.removeEventListener('message', onMsg); tryNative(); }, 1500);
          try { window.parent.postMessage({type:'auth/get_token'}, '*'); } catch(e) { clearTimeout(t1); tryNative(); }
          return;
        }
        tryNative();
        function tryNative() {
          try {
            if (window.externalApp && window.externalApp.getExternalAuth) {
              window.externalApp.getExternalAuth({callback:'_haTokenCb2',type:'bearer'});
              window._haTokenCb2 = r => { delete window._haTokenCb2; done(r&&r.access_token?r.access_token:''); };
              setTimeout(() => { if (window._haTokenCb2) { delete window._haTokenCb2; done(''); } }, 2000);
              return;
            }
            if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.getExternalAuth) {
              window.webkit.messageHandlers.getExternalAuth.postMessage({callback:'_haTokenCb2',type:'bearer'});
              window._haTokenCb2 = r => { delete window._haTokenCb2; done(r&&r.access_token?r.access_token:''); };
              setTimeout(() => { if (window._haTokenCb2) { delete window._haTokenCb2; done(''); } }, 2000);
              return;
            }
          } catch(e) {}
          try { done(JSON.parse(localStorage.getItem('hassTokens')||'{}').access_token||''); } catch(e) { done(''); }
        }
      });
    };
    const connectWS = () => {
      getTokenAsync().then(token => {
        const authHdr = token ? {'Authorization':'Bearer '+token} : {};
        fetch('/api/states', {headers:{...authHdr,'Content-Type':'application/json'}})
          .then(r=>r.json()).then(list => {
            if (Array.isArray(list)) list.forEach(s => {
              if (ENTITIES.includes(s.entity_id))
                states[s.entity_id] = {state: s.state, friendly_name: (s.attributes||{}).friendly_name || s.entity_id, unit: (s.attributes||{}).unit_of_measurement || ''};
            });
          });
        if (!token) { conn.mode = 'polling'; return; }
        const proto = location.protocol==='https:'?'wss:':'ws:';
        ws = new WebSocket(proto+'//'+location.host+'/api/websocket');
        ws.onmessage = (e) => {
          const msg = JSON.parse(e.data);
          if (msg.type==='auth_required') ws.send(JSON.stringify({type:'auth',access_token:token}));
          if (msg.type==='auth_ok') {
            conn.ok=true; conn.mode='WebSocket';
            ws.send(JSON.stringify({id:1,type:'subscribe_events',event_type:'state_changed'}));
          }
          if (msg.type==='event' && msg.event?.data?.new_state) {
            const ns = msg.event.data.new_state;
            if (ENTITIES.includes(ns.entity_id))
              states[ns.entity_id] = {state: ns.state, friendly_name: (ns.attributes||{}).friendly_name || ns.entity_id, unit: (ns.attributes||{}).unit_of_measurement || ''};
          }
        };
        ws.onclose = () => { conn.ok=false; conn.mode='reconnecting'; setTimeout(connectWS, 5000); };
      });
    };

    onMounted(() => { connectWS(); updateTime(); timeInterval = setInterval(updateTime, 1000); });
    onUnmounted(() => { ws?.close(); clearInterval(timeInterval); });

    return {
      states, conn, title, nowText, sv, nv, fmt, entityName, powerText,
      solarW, gridW, battW, battSoc, price, solarShare, solarTodayKwh,
      ENTITIES
    };
  }
}).mount('#app');
</script>
"""


def _autocomplete_truncated_html(html: str, entities: list) -> str:
    """Auto-complete truncated HTML that's missing the Vue.createApp script.
    GPT-5.2 often hits output token limits before writing the JS section."""
    import re

    # Strip any trailing incomplete tags/attributes
    # Find the last complete closing tag
    last_close = max(html.rfind('>'), html.rfind('\n'))
    if last_close > 0 and last_close < len(html) - 1:
        html = html[:last_close + 1]

    # Close unclosed divs/sections
    open_divs = html.lower().count('<div') - html.lower().count('</div')
    open_sections = html.lower().count('<section') - html.lower().count('</section')
    closers = '</div>' * max(0, open_divs)
    closers += '</section>' * max(0, open_sections)

    # Check if we need to close body/html
    has_body_close = '</body>' in html.lower()
    has_html_close = '</html>' in html.lower()

    # Build the completion
    completion = closers
    if not has_body_close:
        completion += '\n<footer style="margin-top:16px;color:rgba(255,255,255,.4);font-size:12px;text-align:center">__FOOTER__</footer>\n'
        completion += _VUE_BOILERPLATE
        completion += '</body>'
    if not has_html_close:
        completion += '</html>'

    return html + completion


def _fill_html_placeholders(
    html: str,
    *,
    title: str,
    entities: list,
    theme: str,
    accent_color: str,
    lang: str | None = None,
    footer_text: str | None = None,
) -> str:
    import html as html_module

    safe_title = html_module.escape(title)
    title_json = json.dumps(title, ensure_ascii=False)
    entities_json = json.dumps(entities, ensure_ascii=False)

    h = (accent_color or "").lstrip('#')
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    try:
        accent_rgb = f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"
    except (ValueError, IndexError):
        accent_rgb = "102,126,234"

    # For raw HTML: __THEME_CSS__ outputs just CSS properties (no :root{} wrapper)
    # so the agent can embed them in any selector: :root { __THEME_CSS__ }
    theme_css = ""
    if theme == "dark":
        theme_css = "--bg:#0f172a;--bg2:#1e293b;--text:#e2e8f0;--text2:#94a3b8;--card:rgba(30,41,59,.85);--border:#334155"
    elif theme == "light":
        theme_css = "--bg:#f0f2f5;--bg2:#fff;--text:#1a1a2e;--text2:#6b7280;--card:rgba(255,255,255,.85);--border:#e2e8f0"

    if not lang:
        lang = getattr(api, "LANGUAGE", "en") or "en"
    lang = (str(lang).lower() or "en")
    if lang not in ("en", "it", "es", "fr"):
        lang = "en"

    agent_name = getattr(api, "AGENT_NAME", "Amira") or "Amira"
    default_footer = getattr(api, "HTML_DASHBOARD_FOOTER", "") or ""
    if not footer_text:
        footer_text = default_footer.strip() or f"Dashboard by {agent_name} · Real-time"

    # Build initial states snapshot — injected directly into HTML so the page
    # renders immediately without needing client-side auth (works in Companion App)
    initial_states_json = "{}"
    try:
        all_s = api.get_all_states()
        if isinstance(all_s, list) and entities:
            snap = {
                s["entity_id"]: {
                    "state": s.get("state", ""),
                    "friendly_name": (s.get("attributes") or {}).get("friendly_name", ""),
                    "unit": (s.get("attributes") or {}).get("unit_of_measurement", ""),
                    "attributes": s.get("attributes") or {},
                }
                for s in all_s if s.get("entity_id") in entities
            }
            initial_states_json = json.dumps(snap, ensure_ascii=False)
    except Exception:
        pass

    out = str(html)
    out = out.replace("__TITLE__", safe_title)
    out = out.replace("__TITLE_JSON__", title_json)
    out = out.replace("__ENTITIES_JSON__", entities_json)
    out = out.replace("__INITIAL_STATES_JSON__", initial_states_json)
    out = out.replace("__ACCENT__", accent_color)
    out = out.replace("__ACCENT_RGB__", accent_rgb)
    out = out.replace("__THEME_CSS__", theme_css)
    out = out.replace("__LANG__", lang)
    out = out.replace("__FOOTER__", html_module.escape(str(footer_text)))
    return out


def _fix_css_var_in_js(html: str) -> str:
    """Fix CSS var('--prop') mistakenly used inside <script> blocks.

    AI models sometimes write Chart.js options like:
        ticks: { color: var('--text-color') }
    which is invalid JS (var is a keyword). This replaces such occurrences
    inside <script> tags with getComputedStyle lookups.
    """
    import re

    # Extract all <script>...</script> blocks
    def _fix_script_block(match):
        script = match.group(0)
        # Replace var('--xxx') or var("--xxx") with getComputedStyle lookup
        fixed = re.sub(
            r"""\bvar\(\s*['"](--([\w-]+))['"]\s*\)""",
            r"getComputedStyle(document.documentElement).getPropertyValue('\1').trim()",
            script
        )
        if fixed != script:
            logger.info("Sanitized CSS var() inside <script> block")
        return fixed

    return re.sub(r'<script\b[^>]*>[\s\S]*?</script>', _fix_script_block, html, flags=re.IGNORECASE)


def _fix_auth_redirect(html: str) -> str:
    """Fix AI-generated auth patterns that break HA Companion App.

    Problems we fix:
    1. Sync token read: `const tok = JSON.parse(localStorage.getItem('hassTokens')...).access_token`
       → tok is '' when injected, so ALL fetch calls using tok fail silently
    2. Redirect on missing token: `if(!tok){ location.href='/?redirect=...' }`
       → causes infinite loading loop in Companion App
    3. Stale headers object: `const headers = { Authorization: 'Bearer ' + tok }`
       → built when tok='', never updated even after token is resolved

    Strategy: inject getTokenAsync() at the top of every <script> block that
    references hassTokens or tok/token auth patterns, then patch fetch calls
    to use the resolved token.
    """
    import re

    _GETTOKEN_HELPER = (
        "/* ── Amira auth patch ── */\n"
        "let tok='';\n"
        "function _getTokenAsync(){if(tok)return Promise.resolve(tok);\n"
        "return new Promise(function(resolve){\n"
        "var done=function(t){tok=t||'';resolve(tok)};\n"
        "if(window.parent&&window.parent!==window){\n"
        "var onMsg=function(ev){if(ev.data&&ev.data.type==='auth/token'&&ev.data.token){"
        "window.removeEventListener('message',onMsg);clearTimeout(t1);done(ev.data.token)}};\n"
        "window.addEventListener('message',onMsg);\n"
        "var t1=setTimeout(function(){window.removeEventListener('message',onMsg);_tryNative()},1500);\n"
        "try{window.parent.postMessage({type:'auth/get_token'},'*')}catch(e){clearTimeout(t1);_tryNative();}\n"
        "return;}\n"
        "_tryNative();\n"
        "function _tryNative(){\n"
        "try{var s=localStorage.getItem('hassTokens');if(s){var a=JSON.parse(s||'{}').access_token;if(a)return done(a);}}"
        "catch(e){}\n"
        "done('');\n"
        "}})};\n"
        "function _authHeader(){return tok?{'Authorization':'Bearer '+tok,'Content-Type':'application/json'}:{'Content-Type':'application/json'}}\n"
        "/* ── end auth patch ── */\n"
    )

    def _patch_script(m):
        script_tag = m.group(1)  # opening <script...>
        body = m.group(2)
        closing = m.group(3)

        # Skip scripts that don't do HA auth (e.g. CDN libs inline)
        needs_patch = bool(re.search(
            r"hassTokens|localStorage.*access_token|Authorization.*Bearer|/api/states|/api/websocket",
            body, re.IGNORECASE
        ))
        if not needs_patch:
            return m.group(0)

        # Already patched
        if "_getTokenAsync" in body or "Amira auth patch" in body:
            return m.group(0)

        # Remove stale sync token declarations
        body = re.sub(
            r"(?:const|let|var)\s+tok\s*=\s*JSON\.parse\([^;]+hassTokens[^;]+\)[^;]*;\s*\n?",
            "",
            body, flags=re.IGNORECASE
        )
        # Remove token redirects
        body = re.sub(
            r"if\s*\(\s*!tok\s*\)\s*\{[^}]*location\.href[^}]*\}\s*;?\s*\n?",
            "", body, flags=re.IGNORECASE
        )
        body = re.sub(
            r"if\s*\(\s*!tok\s*\)\s*location\.href\s*=[^;\n]+[;\n]",
            "", body, flags=re.IGNORECASE
        )
        # Remove stale const headers = {Authorization: 'Bearer '+tok} — tok is '' at that point
        body = re.sub(
            r"(?:const|let|var)\s+headers\s*=\s*\{[^}]*Authorization[^}]*\+\s*tok[^}]*\}\s*;\s*\n?",
            "", body, flags=re.IGNORECASE
        )

        # Wrap entry-point calls in _getTokenAsync().then(...)
        # Match: load();  (optionally followed by setInterval(load, N))
        for _fn in ("load", "init", "start", "main", "render", "fetchAll", "fetchStates"):
            # Pattern: bare call at statement level (not inside a function definition)
            body = re.sub(
                rf"^(\s*)({_fn}\(\s*\)\s*;)\s*$",
                rf"\1_getTokenAsync().then(function(){{ {_fn}(); }});",
                body, flags=re.MULTILINE
            )

        return script_tag + "\n" + _GETTOKEN_HELPER + body + closing

    patched = re.sub(
        r"(<script(?:[^>]*)>)([\s\S]*?)(</script>)",
        _patch_script,
        html,
        flags=re.IGNORECASE
    )

    if patched != html:
        logger.info("🔒 Fixed sync auth redirect pattern in AI-generated HTML")

    return patched


def _stamp_description(description: str, action: str = "create") -> str:
    """Add Amira watermark to a description field.

    action: 'create' or 'modify' — selects the verb prefix by language.
    If the signature is already present, returns description unchanged.
    """
    if AI_SIGNATURE in (description or ""):
        return description

    verbs = {
        "create": {"en": "Created with", "it": "Creato con", "es": "Creado con", "fr": "Créé avec"},
        "modify": {"en": "Modified with", "it": "Modificato con", "es": "Modificado con", "fr": "Modifié avec"},
    }
    lang = getattr(api, "LANGUAGE", "en") or "en"
    verb = verbs.get(action, verbs["create"]).get(lang, verbs[action]["en"])
    stamp = f"{verb} {AI_SIGNATURE}"

    if description and description.strip():
        return f"{description.strip()} | {stamp}"
    return stamp


# User-friendly tool descriptions (Italian)
TOOL_DESCRIPTIONS = {
    "get_entities": "Carico dispositivi",
    "get_entity_state": "Leggo stato dispositivo",
    "call_service": "Eseguo comando",
    "search_entities": "Cerco dispositivi",
    "get_integration_entities": "Cerco entità integrazione",
    "get_automations": "Carico automazioni",
    "update_automation": "Modifico automazione",
    "create_automation": "Creo automazione",
    "trigger_automation": "Avvio automazione",
    "delete_automation": "Elimino automazione",
    "get_scripts": "Carico script",
    "run_script": "Eseguo script",
    "update_script": "Modifico script",
    "create_script": "Creo script",
    "delete_script": "Elimino script",
    "get_dashboards": "Carico dashboard",
    "get_dashboard_config": "Leggo config dashboard",
    "update_dashboard": "Modifico dashboard",
    "create_dashboard": "Creo dashboard",
    "read_html_dashboard": "Leggo HTML dashboard",
    "create_html_dashboard": "Creo dashboard HTML (sezioni strutturate)",
    "delete_dashboard": "Elimino dashboard",
    "get_frontend_resources": "Verifico card installate",
    "get_scenes": "Carico scene",
    "activate_scene": "Attivo scena",
    "get_areas": "Carico stanze",
    "manage_areas": "Gestisco stanze",
    "get_history": "Carico storico",
    "get_statistics": "Carico statistiche",
    "send_notification": "Invio notifica",
    "read_config_file": "Leggo file config",
    "write_config_file": "Salvo file config",
    "list_config_files": "Elenco file config",
    "check_config": "Valido configurazione",
    "create_backup": "Creo backup",
    "get_available_services": "Carico servizi",
    "get_events": "Carico eventi",
    "manage_entity": "Gestisco entità",
    "get_devices": "Carico dispositivi",
    "shopping_list": "Lista spesa",
    "browse_media": "Sfoglio media",
    "list_snapshots": "Elenco snapshot",
    "restore_snapshot": "Ripristino snapshot",
    "manage_helpers": "Gestisco helper",
    "get_repairs": "Carico riparazioni",
    "dismiss_repair": "Ignoro riparazione",
}


def get_tool_description(tool_name: str) -> str:
    """Get user-friendly Italian description for a tool."""
    return TOOL_DESCRIPTIONS.get(tool_name, tool_name.replace('_', ' ').title())


# ---- Tool definitions (shared across providers) ----

HA_TOOLS_DESCRIPTION = [
    {
        "name": "get_entities",
        "description": "Get the current state of all Home Assistant entities, or filter by domain (e.g. 'light', 'switch', 'sensor', 'automation', 'climate').",
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Optional domain filter (e.g. 'light', 'switch', 'sensor')."
                }
            },
            "required": []
        }
    },
    {
        "name": "get_entity_state",
        "description": "Get the current state and attributes of a specific entity.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The entity ID (e.g. 'light.living_room')."
                }
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "call_service",
        "description": "Call a Home Assistant service to control devices: turn on/off lights, switches, set climate temperature, lock/unlock, open/close covers, send notifications, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Service domain (e.g. 'light', 'switch', 'climate', 'cover')."
                },
                "service": {
                    "type": "string",
                    "description": "Service name (e.g. 'turn_on', 'turn_off', 'toggle')."
                },
                "entity_id": {
                    "type": "string",
                    "description": "Optional shortcut for targeting a single entity (e.g. 'light.living_room'). If provided, it will be mapped into data.entity_id."
                },
                "data": {
                    "type": "object",
                    "description": "Service data including target entity_id and parameters."
                }
            },
            "required": ["domain", "service"]
        }
    },
    {
        "name": "create_automation",
        "description": "Create a new Home Assistant automation with triggers, conditions, and actions.",
        "parameters": {
            "type": "object",
            "properties": {
                "alias": {"type": "string", "description": "Name for the automation."},
                "description": {"type": "string", "description": "Description of the automation."},
                "trigger": {"type": "array", "description": "List of triggers.", "items": {"type": "object"}},
                "condition": {"type": "array", "description": "Optional conditions.", "items": {"type": "object"}},
                "action": {"type": "array", "description": "List of actions.", "items": {"type": "object"}},
                "mode": {"type": "string", "enum": ["single", "restart", "queued", "parallel"]}
            },
            "required": ["alias", "trigger", "action"]
        }
    },
    {
        "name": "get_automations",
        "description": "Find existing automations. Optionally pass a query to search by alias/entity. Returns a compact list of matches to keep responses small. To modify an automation, use update_automation.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Optional search text (room name, device name, entity_id fragment, alias keywords)."},
                "limit": {"type": "integer", "description": "Max results to return (default 10).", "minimum": 1, "maximum": 50}
            },
            "required": []
        }
    },
    {
        "name": "update_automation",
        "description": "Update or modify an existing automation by its ID. Prefer passing a 'changes' object with only the fields you want to change (alias, description, trigger(s), condition(s), action(s), mode). For compatibility, you may also pass those fields at the top-level and the tool will normalize them into 'changes'. The tool reads automations.yaml, finds the automation, applies the changes, creates a snapshot, and saves.",
        "parameters": {
            "type": "object",
            "properties": {
                "automation_id": {"type": "string", "description": "The automation's 'id' field from automations.yaml (e.g. '1728373064590')."},
                "changes": {"type": "object", "description": "Fields to update. Can include: alias, description, trigger, condition, action, mode. Only pass the fields you want to change."},
                "add_condition": {"type": "object", "description": "A single condition to ADD to the existing conditions (appended, does not replace). Use this for simple additions like excluding a team."}
            },
            "required": ["automation_id"]
        }
    },
    {
        "name": "trigger_automation",
        "description": "Manually trigger an existing automation.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Automation entity_id."}
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "get_available_services",
        "description": "Get all available Home Assistant service domains and services.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "search_entities",
        "description": "Search entities by keyword in entity_id or friendly_name. Use this to find specific devices, sensors, or integrations.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keyword (e.g. 'calcio', 'temperature', 'motion', 'light')."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_integration_entities",
        "description": (
            "Find all entities belonging to a specific integration/custom component by its platform name. "
            "Use this when the user mentions an integration or brand (e.g. 'Tigo', 'Shelly', 'SolarEdge', 'EPCube') "
            "and search_entities returns nothing — the entities may not have the brand name in their entity_id or friendly_name. "
            "This searches the HA entity registry by platform name."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "integration": {
                    "type": "string",
                    "description": "Integration/platform name to search for (e.g. 'tigo', 'shelly', 'solaredge', 'epcube'). Case-insensitive partial match."
                }
            },
            "required": ["integration"]
        }
    },
    {
        "name": "get_events",
        "description": "Get all available Home Assistant event types. Use this to discover events fired by integrations and addons.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_history",
        "description": "Get the state history of an entity over a time period. Useful for checking past values, trends, and when things changed.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "The entity ID to get history for."},
                "hours": {"type": "number", "description": "Hours of history to retrieve (default 24, max 168)."}
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "get_scenes",
        "description": "Get all available scenes in Home Assistant.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "activate_scene",
        "description": "Activate a Home Assistant scene.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Scene entity_id (e.g. 'scene.movie_night')."}
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "get_scripts",
        "description": "Get all available scripts in Home Assistant.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "run_script",
        "description": "Run a Home Assistant script with optional variables.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Script entity_id (e.g. 'script.goodnight')."},
                "variables": {"type": "object", "description": "Optional variables to pass to the script."}
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "update_script",
        "description": "Update/modify an existing script directly in scripts.yaml. Reads the file, finds the script, applies changes, creates a snapshot, saves. Use this instead of write_config_file for scripts.",
        "parameters": {
            "type": "object",
            "properties": {
                "script_id": {"type": "string", "description": "The script ID (e.g. 'goodnight_routine' without 'script.' prefix)."},
                "changes": {"type": "object", "description": "Object with the fields to change (e.g. {\"alias\": \"New Name\", \"sequence\": [...]}). Only specified fields are modified."}
            },
            "required": ["script_id", "changes"]
        }
    },
    {
        "name": "get_areas",
        "description": "Get all areas/rooms configured in Home Assistant and their entities. Useful for room-based control like 'turn off everything in the bedroom'.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "send_notification",
        "description": "Send a notification to Home Assistant (persistent notification visible in HA UI, or to a mobile device).",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "The notification message."},
                "title": {"type": "string", "description": "Optional notification title."},
                "target": {"type": "string", "description": "Notify service target (e.g. 'mobile_app_phone'). If empty, creates a persistent notification in HA."}
            },
            "required": ["message"]
        }
    },
    {
        "name": "get_dashboards",
        "description": "Get all Lovelace dashboards in Home Assistant.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "create_dashboard",
        "description": "Create a NEW Lovelace YAML dashboard. YOU design the complete views and cards structure creatively based on the user's request. Use the best card types for each entity: gauge for percentages, history-graph for trends, thermostat for climate, light for lights, button for scripts/scenes, weather-forecast for weather, glance for quick overview, picture-elements for floorplans. Group entities logically. Use grid/horizontal-stack/vertical-stack for layout. Add markdown cards for section headers. Use themed titles and icons. Available card types: entities, gauge, history-graph, weather-forecast, light, thermostat, button, markdown, grid, horizontal-stack, vertical-stack, glance, picture-entity, sensor, alarm-panel, media-control, map, logbook, energy-distribution, statistics-graph, tile, mushroom (if HACS installed).",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Dashboard title (e.g. 'Luci e Temperature')."},
                "url_path": {"type": "string", "description": "URL slug (lowercase, no spaces, e.g. 'luci-temp'). Must be unique."},
                "icon": {"type": "string", "description": "MDI icon (e.g. 'mdi:thermometer', 'mdi:lightbulb'). Optional."},
                "views": {
                    "type": "array",
                    "description": "List of views (tabs) with cards. Each view has: title, path, icon, cards[].",
                    "items": {"type": "object"}
                }
            },
            "required": ["title", "url_path", "views"]
        }
    },
    {
        "name": "create_script",
        "description": "Create a new Home Assistant script with a sequence of actions.",
        "parameters": {
            "type": "object",
            "properties": {
                "script_id": {"type": "string", "description": "Unique script ID (lowercase, underscores, e.g. 'goodnight_routine')."},
                "alias": {"type": "string", "description": "Friendly name for the script."},
                "description": {"type": "string", "description": "Description of what the script does."},
                "sequence": {"type": "array", "description": "List of actions to execute in order.", "items": {"type": "object"}},
                "mode": {"type": "string", "enum": ["single", "restart", "queued", "parallel"], "description": "Execution mode (default: single)."}
            },
            "required": ["script_id", "alias", "sequence"]
        }
    },
    {
        "name": "delete_dashboard",
        "description": "Delete a Lovelace dashboard by its ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "dashboard_id": {"type": "string", "description": "The dashboard ID (get it from get_dashboards)."}
            },
            "required": ["dashboard_id"]
        }
    },
    {
        "name": "delete_automation",
        "description": "Delete an existing automation. Works for both UI-created automations (via API) and YAML-based automations (removes from file). If removing from YAML, creates a snapshot first and requires Home Assistant restart.",
        "parameters": {
            "type": "object",
            "properties": {
                "automation_id": {"type": "string", "description": "The automation entity_id (e.g. 'automation.my_automation')."}
            },
            "required": ["automation_id"]
        }
    },
    {
        "name": "delete_script",
        "description": "Delete an existing script. Works for both UI-created scripts (via API) and YAML-based scripts (removes from file). If removing from YAML, creates a snapshot first and requires Home Assistant restart.",
        "parameters": {
            "type": "object",
            "properties": {
                "script_id": {"type": "string", "description": "The script ID without prefix (e.g. 'goodnight_routine')."}
            },
            "required": ["script_id"]
        }
    },
    {
        "name": "manage_areas",
        "description": "Manage Home Assistant areas/rooms: list, create, rename, or delete areas.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "create", "update", "delete"], "description": "Action to perform."},
                "name": {"type": "string", "description": "Area name (for create/update)."},
                "area_id": {"type": "string", "description": "Area ID (for update/delete)."},
                "icon": {"type": "string", "description": "MDI icon for the area (optional)."}
            },
            "required": ["action"]
        }
    },
    {
        "name": "manage_entity",
        "description": "Update entity registry: rename, assign to area, enable/disable an entity.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "The entity ID to manage."},
                "name": {"type": "string", "description": "New friendly name (optional)."},
                "area_id": {"type": "string", "description": "Assign to area ID (optional). Use manage_areas list to get IDs."},
                "disabled_by": {"type": "string", "enum": ["user", ""], "description": "Set to 'user' to disable, '' to enable."},
                "icon": {"type": "string", "description": "Custom icon (optional)."}
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "get_devices",
        "description": "Get all devices registered in Home Assistant with manufacturer, model, and area.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_statistics",
        "description": "Get advanced statistics (min, max, mean, sum) for a sensor over a time period. Useful for energy, temperature trends, averages.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Sensor entity_id (e.g. 'sensor.temperature')."},
                "period": {"type": "string", "enum": ["5minute", "hour", "day", "week", "month"], "description": "Statistics period (default: hour)."},
                "hours": {"type": "number", "description": "How many hours back to query (default 24, max 720)."}
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "shopping_list",
        "description": "Manage the Home Assistant shopping list: view items, add new items, or mark items as complete.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "add", "complete"], "description": "Action to perform."},
                "name": {"type": "string", "description": "Item name (for add)."},
                "item_id": {"type": "string", "description": "Item ID (for complete, get from list)."}
            },
            "required": ["action"]
        }
    },
    {
        "name": "create_backup",
        "description": "Create a full Home Assistant backup. This may take a few minutes.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "browse_media",
        "description": "Browse available media content (music, photos, etc.) from media players.",
        "parameters": {
            "type": "object",
            "properties": {
                "media_content_id": {"type": "string", "description": "Content path to browse (empty for root)."},
                "media_content_type": {"type": "string", "description": "Media type (e.g. 'music', 'image'). Default: 'music'."}
            },
            "required": []
        }
    },
    {
        "name": "get_dashboard_config",
        "description": "Get the full configuration of a Lovelace dashboard. Use this to read an existing dashboard before modifying it.",
        "parameters": {
            "type": "object",
            "properties": {
                "url_path": {"type": "string", "description": "Dashboard URL path (e.g. 'lovelace', 'energy-dashboard'). Use 'lovelace' or null for the default dashboard. Use get_dashboards to list all."}
            },
            "required": []
        }
    },
    {
        "name": "update_dashboard",
        "description": "Update/modify an existing Lovelace dashboard. ALWAYS call get_dashboard_config first to read current config, then creatively redesign or modify based on user request. You can add/remove/rearrange views and cards. Supports all native card types and custom cards (card-mod, bubble-card, mushroom, etc. if installed - check with get_frontend_resources). When modifying, preserve existing content the user wants to keep while improving the layout and design.",
        "parameters": {
            "type": "object",
            "properties": {
                "url_path": {"type": "string", "description": "Dashboard URL path. Use 'lovelace' or null for the default dashboard."},
                "views": {"type": "array", "description": "Complete array of views with their cards. This REPLACES all views.", "items": {"type": "object"}}
            },
            "required": ["views"]
        }
    },
    {
        "name": "get_frontend_resources",
        "description": "List all registered Lovelace frontend resources (custom cards, modules). Use this to check if custom cards like card-mod, bubble-card, mushroom-cards, etc. are installed via HACS.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "read_config_file",
        "description": "Read a Home Assistant configuration file (e.g. configuration.yaml, automations.yaml, scripts.yaml, secrets.yaml, ui-lovelace.yaml, or any YAML/JSON file in the config directory). Returns file content as text.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "File path relative to HA config dir (e.g. 'configuration.yaml', 'ui-lovelace.yaml', 'dashboards/energy.yaml')."}
            },
            "required": ["filename"]
        }
    },
    {
        "name": "write_config_file",
        "description": "Write/update a Home Assistant configuration file. ALWAYS creates a snapshot backup first (automatically). Use for editing configuration.yaml, YAML dashboards, includes, packages, etc. After writing, call check_config to validate.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "File path relative to HA config dir (e.g. 'configuration.yaml', 'ui-lovelace.yaml')."},
                "content": {"type": "string", "description": "The full file content to write."}
            },
            "required": ["filename", "content"]
        }
    },
    {
        "name": "check_config",
        "description": "Validate Home Assistant configuration. Call this after modifying configuration.yaml or any YAML file. Returns 'valid' or error details.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "list_config_files",
        "description": "List files in the Home Assistant config directory (or a subdirectory). Useful to discover YAML dashboards, packages, includes, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Subdirectory to list (empty for root config dir). E.g. 'dashboards', 'packages', 'custom_components'."}
            },
            "required": []
        }
    },
    {
        "name": "list_snapshots",
        "description": "List all available configuration snapshots. Snapshots are auto-created before any file modification.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "restore_snapshot",
        "description": "Restore a file from a previously created snapshot. Use list_snapshots to see available snapshots.",
        "parameters": {
            "type": "object",
            "properties": {
                "snapshot_id": {"type": "string", "description": "The snapshot ID (from list_snapshots)."}
            },
            "required": ["snapshot_id"]
        }
    },
    {
        "name": "manage_helpers",
        "description": "Create, update, delete, or list Home Assistant helpers (input_boolean, input_number, input_select, input_text, input_datetime).",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list", "create", "update", "delete"],
                    "description": "Action to perform."
                },
                "helper_type": {
                    "type": "string",
                    "enum": ["input_boolean", "input_number", "input_select", "input_text", "input_datetime"],
                    "description": "Type of helper."
                },
                "helper_id": {
                    "type": "string",
                    "description": "Helper ID without domain prefix (e.g. 'guest_mode' for input_boolean.guest_mode). Required for create/update/delete."
                },
                "name": {
                    "type": "string",
                    "description": "Friendly name for the helper."
                },
                "icon": {
                    "type": "string",
                    "description": "MDI icon (e.g. 'mdi:toggle-switch')."
                },
                "min": {"type": "number", "description": "Minimum value (input_number only)."},
                "max": {"type": "number", "description": "Maximum value (input_number only)."},
                "step": {"type": "number", "description": "Step value (input_number only)."},
                "unit_of_measurement": {"type": "string", "description": "Unit (input_number only)."},
                "mode": {"type": "string", "enum": ["box", "slider"], "description": "Display mode (input_number only)."},
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of options (input_select only)."
                },
                "initial": {"type": "string", "description": "Initial/default value."},
                "has_date": {"type": "boolean", "description": "Include date (input_datetime only)."},
                "has_time": {"type": "boolean", "description": "Include time (input_datetime only)."},
                "min_length": {"type": "integer", "description": "Min length (input_text only)."},
                "max_length": {"type": "integer", "description": "Max length (input_text only)."},
                "pattern": {"type": "string", "description": "Regex pattern (input_text only)."}
            },
            "required": ["action", "helper_type"]
        }
    },
    {
        "name": "read_html_dashboard",
        "description": "Read the HTML source code of an existing custom dashboard. Use this to understand the current design, style, colors, and layout before modifying it with create_html_dashboard (same name to overwrite).",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Dashboard name/slug (e.g., 'clima-fotovoltaico')"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "create_html_dashboard",
        "description": "Create a custom HTML dashboard with real-time entity monitoring.\n\nMULTI-PAGE STRATEGIES:\n- Option A (HTML tabs): Create a SINGLE HTML file with a JS tab router — use show/hide div sections with a top nav bar. Call this tool ONCE. Best for self-contained dashboards.\n- Option B (HA sidebar pages): Call this tool MULTIPLE TIMES, once per section, each with a unique name/title. Each call creates a separate entry in the HA sidebar. Best when the user wants independent navigation.\nAlways ask the user which option they prefer before generating HTML for multi-page requests.\n\nPREFERRED: Raw HTML mode — provide a complete 'html' string with your own HTML/CSS/JS for unique, creative designs.\nFALLBACK: Structured mode — provide 'sections' array for quick standard layouts.\n\nCHUNKED MODE (for large HTML): If your HTML is longer than 6000 characters, split it into parts:\n- Call 1: create_html_dashboard(title, name, entities, html='<part1: head+CSS+start of body>', draft=true)\n- Call 2: create_html_dashboard(name='same-slug', html='<part2: rest of template>', draft=true)\n- Call 3: create_html_dashboard(name='same-slug', html='<part3: script+closing tags>') ← no draft = finalize and save\nEach chunk should be under 6000 chars. The tool concatenates all parts.\n\nRaw HTML placeholders (the tool replaces them):\n- __ENTITIES_JSON__ (JSON array of entity_ids — MANDATORY)\n- __TITLE__ (HTML-escaped), __TITLE_JSON__ (JSON string for JS)\n- __ACCENT__ (hex color e.g. #22c55e), __ACCENT_RGB__ (r,g,b for rgba())\n- __THEME_CSS__ (CSS properties WITHOUT :root wrapper, e.g. --bg:#0f172a;--text:#e2e8f0. Use as: :root{__THEME_CSS__})\n- __LANG__ (en/it/es/fr), __FOOTER__ (HTML-escaped footer)\n\nCRITICAL — ENTITIES: The pre-loaded context (## ENTITÀ TROVATE) already contains the correct entity_ids. You MUST:\n1. Copy ALL entity_ids from ## ENTITÀ TROVATE into the entities[] parameter of this tool call\n2. Use __ENTITIES_JSON__ placeholder in the HTML — the server replaces it with the validated list\n3. In JS, iterate over ENTITIES array (from __ENTITIES_JSON__) — NEVER filter /api/states by device_class or any attribute. The ENTITIES array IS the correct filtered list.\n4. NEVER hardcode entity_ids — use __ENTITIES_JSON__ so the server controls the list\n\nIMPORTANT: Do NOT use var(--primary-background-color) or HA frontend CSS vars — they don't exist in /local/ pages. Define your own colors.\nRaw HTML must include: Vue 3 CDN, WebSocket to /api/websocket, Bearer token via getTokenAsync() (supports both localStorage.hassTokens for browser and window.externalApp/webkit for HA Companion App). Never block on token — always fall back to polling if token unavailable.\n\nStructured section types: hero, pills, flow, gauge, gauges, kpi, chart, trend, entities, controls, stats, value.\nLayout: 'span' (1=third, 2=two-thirds, 3=full). Card styles: gradient, outlined, flat.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Dashboard title shown in HA sidebar."},
                "name": {"type": "string", "description": "URL-safe slug (lowercase, hyphens, e.g. 'energy-flow')."},
                "icon": {"type": "string", "description": "MDI icon for sidebar (e.g. 'mdi:solar-power'). Default: mdi:web."},
                "entities": {"type": "array", "items": {"type": "string"}, "description": "ALL entity_ids to monitor via WebSocket."},
                "theme": {"type": "string", "enum": ["auto", "light", "dark"], "description": "Color theme. 'auto' follows OS."},
                "accent_color": {"type": "string", "description": "Accent color hex (e.g. '#667eea')."},
                "lang": {"type": "string", "enum": ["en", "it", "es", "fr"], "description": "HTML lang attribute. Default: add-on language."},
                "footer_text": {"type": "string", "description": "Footer text. Default: configured html_dashboard_footer or 'Dashboard by <agent_name> · Real-time'."},
                "html": {"type": "string", "description": "Raw HTML mode: full HTML/CSS/JS code. If provided, 'sections' is optional. For large HTML (>6000 chars), use draft=true and send in multiple calls."},
                "draft": {"type": "boolean", "description": "If true, buffer this HTML chunk without creating the dashboard. Call again with same 'name' to append more chunks. Omit draft (or false) on the last call to finalize."},
                "return_html": {"type": "boolean", "description": "Leave false (default). The dashboard is always saved to a file. NEVER set true — do NOT echo HTML in chat."},
                "sections": {
                    "type": "array",
                    "description": "Array of dashboard sections. Each has a 'type' + type-specific props.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["hero", "pills", "flow", "gauge", "gauges", "kpi", "chart", "trend", "entities", "controls", "stats", "value"]},
                            "title": {"type": "string", "description": "Section title."},
                            "icon": {"type": "string", "description": "Emoji character (e.g. ⚡🏠💡🌡️🔋🔌🛡️). Do NOT use mdi: icons, only emoji."},
                            "span": {"type": "integer", "description": "Layout: 1=third, 2=two-thirds, 3=full (default)."},
                            "style": {"type": "string", "enum": ["gradient", "outlined", "flat"]},
                            "description": {"type": "string", "description": "Hero description."},
                            "entity": {"type": "string", "description": "Single entity for gauge/value."},
                            "subtitle": {"type": "string", "description": "Value subtitle."},
                            "chart_type": {"type": "string", "enum": ["bar", "line", "doughnut", "radar", "pie"]},
                            "hours": {"type": "integer", "description": "Hours of history for trend charts (1-168, default 24)."},
                            "entities": {"type": "array", "items": {"type": "string"}, "description": "Entity IDs."},
                            "items": {"type": "array", "items": {"type": "object", "properties": {"entity": {"type": "string"}, "label": {"type": "string"}, "color": {"type": "string", "description": "CSS color hex (e.g. '#ef4444') for trend badge and chart line."}, "icon": {"type": "string", "description": "Emoji icon for trend KPI badge."}}, "required": ["entity"]}, "description": "Entities with custom labels."},
                            "nodes": {"type": "array", "items": {"type": "object", "properties": {"entity": {"type": "string"}, "label": {"type": "string"}, "highlight": {"type": "boolean"}}, "required": ["entity"]}, "description": "Flow nodes."},
                            "stats": {"type": "array", "items": {"type": "object", "properties": {"entity": {"type": "string"}, "label": {"type": "string"}}, "required": ["entity"]}, "description": "Gauge side stats."}
                        },
                        "required": ["type"]
                    }
                }
            },
            "required": ["title", "name", "entities"]
        }
    },
    {
        "name": "get_repairs",
        "description": "Get active issues/repairs from Home Assistant and system health info. Returns open repair issues (deprecated integrations, config problems, broken devices) and resolution suggestions.",
        "parameters": {
            "type": "object",
            "properties": {
                "include_ignored": {
                    "type": "boolean",
                    "description": "Include issues already dismissed/ignored by user. Default: false."
                }
            },
            "required": []
        }
    },
    {
        "name": "dismiss_repair",
        "description": "Dismiss/ignore a specific repair issue in Home Assistant. Use after the user has reviewed and acknowledged an issue.",
        "parameters": {
            "type": "object",
            "properties": {
                "issue_id": {
                    "type": "string",
                    "description": "The issue_id to dismiss (from get_repairs results)"
                },
                "domain": {
                    "type": "string",
                    "description": "The domain/integration of the issue (from get_repairs results)"
                }
            },
            "required": ["issue_id", "domain"]
        }
    }
]


# ============================================================================
# MCP TOOLS INTEGRATION (Model Context Protocol)
# ============================================================================

def _get_mcp_tools_anthropic():
    """Convert MCP tools to Anthropic format."""
    if not MCP_AVAILABLE:
        return []
    
    try:
        manager = mcp.get_mcp_manager()
        all_mcp_tools = manager.get_all_tools()
        
        mcp_tools = []
        for tool_name, tool_info in all_mcp_tools.items():
            mcp_tools.append({
                "name": tool_name,
                "description": f"{tool_info['description']} (MCP: {tool_info['server']})",
                "input_schema": tool_info.get("inputSchema", {"type": "object", "properties": {}})
            })
        
        if mcp_tools:
            logger.debug(f"Added {len(mcp_tools)} MCP tools to Anthropic toolkit")
        
        return mcp_tools
    except Exception as e:
        logger.warning(f"Error loading MCP tools: {e}")
        return []


def _get_mcp_tools_openai():
    """Convert MCP tools to OpenAI format."""
    if not MCP_AVAILABLE:
        return []
    
    try:
        manager = mcp.get_mcp_manager()
        all_mcp_tools = manager.get_all_tools()
        
        mcp_tools = []
        for tool_name, tool_info in all_mcp_tools.items():
            mcp_tools.append({
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": f"{tool_info['description']} (MCP: {tool_info['server']})",
                    "parameters": tool_info.get("inputSchema", {"type": "object", "properties": {}})
                }
            })
        
        if mcp_tools:
            logger.debug(f"Added {len(mcp_tools)} MCP tools to OpenAI toolkit")
        
        return mcp_tools
    except Exception as e:
        logger.warning(f"Error loading MCP tools: {e}")
        return []


def get_anthropic_tools():
    """Convert tools to Anthropic format."""
    from intent import INTENT_TOOL_SETS
    tools = HA_TOOLS_DESCRIPTION
    if not api.ENABLE_FILE_ACCESS:
        config_edit_tools = set(INTENT_TOOL_SETS.get("config_edit", []))
        filtered_count = len([t for t in tools if t["name"] in config_edit_tools])
        logger.info(f"ENABLE_FILE_ACCESS=False: filtering {filtered_count} config_edit tools: {config_edit_tools}")
        tools = [t for t in tools if t["name"] not in config_edit_tools]
    
    anthropic_tools = [
        {"name": t["name"], "description": t["description"], "input_schema": t["parameters"]}
        for t in tools
    ]
    
    # Add MCP tools if available
    anthropic_tools.extend(_get_mcp_tools_anthropic())
    
    return anthropic_tools


def get_openai_tools():
    """Convert tools to OpenAI function-calling format."""
    from intent import INTENT_TOOL_SETS
    tools = HA_TOOLS_DESCRIPTION
    if not api.ENABLE_FILE_ACCESS:
        config_edit_tools = set(INTENT_TOOL_SETS.get("config_edit", []))
        filtered_count = len([t for t in tools if t["name"] in config_edit_tools])
        logger.debug(f"OpenAI: filtering {filtered_count} config_edit tools")
        tools = [t for t in tools if t["name"] not in config_edit_tools]
    
    openai_tools = [
        {"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}}
        for t in tools
    ]
    
    # Add MCP tools if available
    openai_tools.extend(_get_mcp_tools_openai())
    
    return openai_tools


def get_gemini_tools(intent_info: dict | None = None):
    """Convert tools to Google Gemini format. If intent_info provided, filter to focused tools."""
    from intent import INTENT_TOOL_SETS
    from google.genai import types

    def _sanitize_gemini_schema(obj):
        """Remove JSON-schema fields that have caused schema errors in Gemini SDKs.

        We keep only structural fields needed for function calling.
        """
        blocked_keys = {
            "minimum",
            "maximum",
            "exclusiveMinimum",
            "exclusiveMaximum",
            "multipleOf",
            "minItems",
            "maxItems",
            "minLength",
            "maxLength",
            "pattern",
            "format",
            "examples",
            "default",
        }

        if isinstance(obj, dict):
            cleaned = {}
            for k, v in obj.items():
                if k in blocked_keys:
                    continue
                cleaned[k] = _sanitize_gemini_schema(v)
            return cleaned
        if isinstance(obj, list):
            return [_sanitize_gemini_schema(v) for v in obj]
        return obj

    # Start with all tools or filtered by intent
    tool_names = intent_info.get("tools") if intent_info else None
    if tool_names:
        all_tools = [t for t in HA_TOOLS_DESCRIPTION if t["name"] in tool_names]
    else:
        all_tools = HA_TOOLS_DESCRIPTION
    if not api.ENABLE_FILE_ACCESS:
        config_edit_tools = set(INTENT_TOOL_SETS.get("config_edit", []))
        all_tools = [t for t in all_tools if t["name"] not in config_edit_tools]
    declarations = []
    for t in all_tools:
        declarations.append(
            types.FunctionDeclaration(
                name=t["name"],
                description=t["description"],
                parameters_json_schema=_sanitize_gemini_schema(t["parameters"]),
            )
        )
    return types.Tool(function_declarations=declarations)


# ---- Tool execution ----


# Tools that perform write operations (blocked in read-only mode)
WRITE_TOOLS = {
    "create_automation", "update_automation", "delete_automation",
    "create_script", "update_script", "delete_script",
    "create_dashboard", "update_dashboard", "delete_dashboard",
    "call_service", "write_config_file", "send_notification",
    "manage_entity", "create_backup", "manage_helpers",
    "dismiss_repair",
}
# Tools that are write-only when action is NOT "list"
WRITE_WHEN_NOT_LIST = {"manage_areas", "shopping_list"}


def _read_only_response(tool_name: str, tool_input: dict) -> str:
    """Return YAML preview instead of executing a write tool in read-only mode."""
    import yaml
    yaml_output = yaml.dump(tool_input, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return json.dumps({
        "status": "read_only",
        "message": f"Read-only mode: '{tool_name}' was NOT executed.",
        "yaml_preview": yaml_output,
        "tool_name": tool_name,
        "IMPORTANT": api.tr("read_only_instruction") + api.tr("read_only_note")
    }, ensure_ascii=False, default=str)


def _extract_entity_ids(obj, _in_service_key=False):
    """Recursively extract all entity_id references from a config dict/list.

    Skips values that are HA service names (e.g. 'switch.turn_on') — those
    live in the 'service' / 'action' keys and look like domain.verb but are
    NOT entity_ids.  Only strings found under an 'entity_id' key (or inside
    a bare string that is clearly an entity) are collected.
    """
    # Known HA service verbs — strings ending with these are service calls,
    # not entity_ids, and must be excluded from validation.
    _SERVICE_VERBS = {
        "turn_on", "turn_off", "toggle", "open_cover", "close_cover",
        "stop_cover", "lock", "unlock", "trigger", "press", "set_temperature",
        "set_humidity", "set_hvac_mode", "set_fan_mode", "set_swing_mode",
        "set_preset_mode", "set_value", "set_speed", "play_media",
        "media_play", "media_pause", "media_stop", "media_next_track",
        "media_previous_track", "volume_up", "volume_down", "volume_mute",
        "volume_set", "send_message", "notify", "reload", "restart",
        "start", "stop", "pause", "resume", "activate", "deactivate",
        "enable", "disable", "update_entity", "install", "skip",
        "set_datetime", "select_option", "select_first", "select_last",
        "select_next", "select_previous", "increment", "decrement",
        "open", "close", "set_position", "set_tilt_position",
    }

    ids = set()
    if isinstance(obj, str):
        # If we're inside a "service" key, never extract entity_ids from the value
        if _in_service_key:
            return ids
        import re as _re
        for m in _re.finditer(
            r'(?:sensor|switch|light|climate|binary_sensor|input_boolean|'
            r'automation|number|select|button|cover|fan|lock|media_player|'
            r'vacuum|weather|water_heater|scene|script|input_number|'
            r'input_select|input_text|person|device_tracker|calendar|'
            r'camera|update|group|sun)\.[a-z0-9_]+', obj
        ):
            candidate = m.group(0)
            # Exclude service calls: domain.verb where verb is a known service
            suffix = candidate.split(".", 1)[1] if "." in candidate else ""
            if suffix not in _SERVICE_VERBS:
                ids.add(candidate)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k == "entity_id":
                if isinstance(v, str):
                    ids.add(v)
                elif isinstance(v, list):
                    ids.update(e for e in v if isinstance(e, str))
            else:
                # Pass flag so string values under "service"/"action" are skipped
                in_svc = k in ("service", "action")
                ids.update(_extract_entity_ids(v, _in_service_key=in_svc))
    elif isinstance(obj, list):
        for item in obj:
            ids.update(_extract_entity_ids(item))
    return ids


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool call and return the result as string."""
    try:
        # Handle MCP tools first
        if tool_name.startswith("mcp_"):
            if MCP_AVAILABLE:
                logger.info(f"Executing MCP tool: {tool_name}")
                manager = mcp.get_mcp_manager()
                result = manager.call_tool(tool_name, tool_input)
                logger.debug(f"MCP tool result ({len(result)} chars): {result[:300]}")
                return result
            else:
                return json.dumps({"error": f"MCP tool '{tool_name}' requested but MCP module not available"})
        
        # Read-only mode: block write tools and return YAML preview
        session_id = getattr(api, 'current_session_id', 'default')
        if api.read_only_sessions.get(session_id, False):
            if tool_name in WRITE_TOOLS:
                logger.info(f"Read-only mode: blocked write tool '{tool_name}'")
                return _read_only_response(tool_name, tool_input)
            if tool_name in WRITE_WHEN_NOT_LIST:
                action = tool_input.get("action", "list")
                if action != "list":
                    logger.info(f"Read-only mode: blocked write action '{action}' on '{tool_name}'")
                    return _read_only_response(tool_name, tool_input)

        if tool_name == "get_entities":
            domain = tool_input.get("domain", "")
            states = api.get_all_states()
            if domain:
                states = [s for s in states if s.get("entity_id", "").startswith(f"{domain}.")]
            # Limit results for providers with small context windows
            max_entities = 30 if api.AI_PROVIDER == "github" else 100
            result = []
            for s in states[:max_entities]:
                result.append({
                    "entity_id": s.get("entity_id"),
                    "state": s.get("state"),
                    "friendly_name": s.get("attributes", {}).get("friendly_name", ""),
                    "attributes": {k: v for k, v in s.get("attributes", {}).items()
                                   if k in ("friendly_name", "unit_of_measurement", "device_class",
                                            "brightness", "color_temp", "temperature",
                                            "current_temperature", "hvac_modes")}
                })
            return json.dumps(result, ensure_ascii=False, default=str)

        elif tool_name == "get_entity_state":
            entity_id = tool_input.get("entity_id", "")
            result = api.call_ha_api("GET", f"states/{entity_id}")
            # Return only essential fields to save tokens
            if isinstance(result, dict):
                slim = {
                    "entity_id": result.get("entity_id"),
                    "state": result.get("state"),
                    "friendly_name": result.get("attributes", {}).get("friendly_name", ""),
                    "last_changed": result.get("last_changed", "")
                }
                # Include only useful attributes
                attrs = result.get("attributes", {})
                useful_keys = ("friendly_name", "unit_of_measurement", "device_class",
                              "brightness", "color_temp", "temperature", "current_temperature",
                              "hvac_modes", "hvac_action", "preset_mode", "source", "media_title",
                              "id")  # 'id' is critical for automations
                slim["attributes"] = {k: v for k, v in attrs.items() if k in useful_keys}
                return json.dumps(slim, ensure_ascii=False, default=str)
            return json.dumps(result, ensure_ascii=False, default=str)

        elif tool_name == "call_service":
            domain = str(tool_input.get("domain", "") or "").strip()
            service = str(tool_input.get("service", "") or "").strip()
            data = tool_input.get("data", {})
            if not isinstance(data, dict):
                data = {}

            # Compatibility: some models send entity_id at the top level.
            # Normalize into the service payload so HA doesn't return 400.
            top_entity_id = tool_input.get("entity_id")
            if top_entity_id and "entity_id" not in data and "target" not in data:
                data["entity_id"] = top_entity_id

            # Also accept alternate shapes
            # - service_data: {...}
            # - target: {entity_id: ...}
            service_data = tool_input.get("service_data")
            if isinstance(service_data, dict):
                # Only fill missing keys to avoid overriding explicit data
                for k, v in service_data.items():
                    if k not in data:
                        data[k] = v

            target = tool_input.get("target")
            if isinstance(target, dict) and "target" not in data:
                data["target"] = target

            if not domain or not service:
                return json.dumps(
                    {
                        "status": "error",
                        "error": "Missing required arguments: 'domain' and 'service'.",
                        "example": {
                            "domain": "light",
                            "service": "turn_on",
                            "data": {"entity_id": "light.living_room"},
                        },
                    },
                    ensure_ascii=False,
                    default=str,
                )

            # If we still have no target, return a clearer error (prevents HA 400).
            if not data or (not data.get("entity_id") and not data.get("target")):
                return json.dumps(
                    {
                        "status": "error",
                        "error": "Missing target for service call. Provide 'entity_id' or 'data' with entity_id/target.",
                        "example": {
                            "domain": domain,
                            "service": service,
                            "data": {"entity_id": "light.living_room"},
                        },
                    },
                    ensure_ascii=False,
                    default=str,
                )

            result = api.call_ha_api("POST", f"services/{domain}/{service}", data)
            if isinstance(result, dict) and result.get("error"):
                return json.dumps({"status": "error", "result": result}, ensure_ascii=False, default=str)
            return json.dumps({"status": "success", "result": result}, ensure_ascii=False, default=str)

        elif tool_name == "create_automation":
            import yaml
            import time as _time
            # Accept both singular and plural keys from the model
            alias = tool_input.get("alias", "New Automation")
            config = {
                "id": str(int(_time.time() * 1000)),  # unique ID like HA UI generates
                "alias": alias,
                "description": _stamp_description(tool_input.get("description", ""), "create"),
                "triggers": tool_input.get("triggers") or tool_input.get("trigger", []),
                "conditions": tool_input.get("conditions") or tool_input.get("condition", []),
                "actions": tool_input.get("actions") or tool_input.get("action", []),
                "mode": tool_input.get("mode", "single"),
            }

            # ---- Entity validation: reject if entity_ids don't exist ----
            referenced_entities = _extract_entity_ids(config.get("actions", [])) | _extract_entity_ids(config.get("triggers", [])) | _extract_entity_ids(config.get("conditions", []))
            if referenced_entities:
                all_states = api.get_all_states()
                known_ids = {s.get("entity_id") for s in all_states if s.get("entity_id")}
                invalid = [eid for eid in referenced_entities if eid not in known_ids]
                if invalid:
                    # Try to suggest corrections
                    suggestions = {}
                    for bad_id in invalid:
                        domain = bad_id.split(".")[0] if "." in bad_id else ""
                        name_part = bad_id.split(".", 1)[1] if "." in bad_id else bad_id
                        # Find similar entity_ids in the same domain
                        candidates = [kid for kid in known_ids if kid.startswith(domain + ".") and (name_part in kid or kid.split(".", 1)[1] in name_part)]
                        if candidates:
                            suggestions[bad_id] = candidates[:3]
                    msg = {
                        "status": "error",
                        "message": f"Entity IDs not found: {', '.join(invalid)}. Use search_entities to find the correct IDs.",
                        "invalid_entities": invalid,
                    }
                    if suggestions:
                        msg["suggestions"] = suggestions
                    return json.dumps(msg, ensure_ascii=False, default=str)

            # Strategy: write directly to automations.yaml (same as update_automation)
            yaml_path = api.get_config_file_path("automation", "automations.yaml")
            created_via = None
            snapshot = None

            if yaml_path and os.path.isfile(yaml_path):
                try:
                    # Snapshot before modifying
                    try:
                        rel_path = os.path.relpath(yaml_path, api.HA_CONFIG_DIR) if yaml_path.startswith(api.HA_CONFIG_DIR + "/") else os.path.basename(yaml_path)
                        snapshot = api.create_snapshot(rel_path)
                    except Exception:
                        snapshot = api.create_snapshot("automations.yaml")

                    with open(yaml_path, "r", encoding="utf-8") as f:
                        automations = yaml.safe_load(f) or []
                    if not isinstance(automations, list):
                        automations = []

                    automations.append(config)
                    with open(yaml_path, "w", encoding="utf-8") as f:
                        yaml.dump(automations, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

                    # Reload automations so HA picks up the change
                    try:
                        api.call_ha_api("POST", "services/automation/reload", {})
                    except Exception:
                        pass
                    created_via = "yaml"
                except Exception as e:
                    logger.warning(f"YAML create_automation failed: {e}")

            # Fallback: REST API
            if created_via is None:
                result = api.call_ha_api("POST", f"config/automation/config/{config['id']}", config)
                if isinstance(result, dict) and "error" not in result:
                    created_via = "rest_api"
                else:
                    return json.dumps({"status": "error", "result": result}, ensure_ascii=False, default=str)

            created_yaml = yaml.dump(config, default_flow_style=False, allow_unicode=True)
            resp = {
                "status": "success",
                "message": f"Automation '{alias}' created!",
                "yaml": created_yaml,
                "IMPORTANT": "Show the user the YAML code you created."
            }
            if isinstance(snapshot, dict) and snapshot.get("snapshot_id"):
                resp["snapshot"] = snapshot
            return json.dumps(resp, ensure_ascii=False, default=str)

        elif tool_name == "get_automations":
            query = tool_input.get("query") if isinstance(tool_input, dict) else None
            # Accept automation_id as an alias for query (model may pass it directly)
            if not query and isinstance(tool_input, dict):
                query = tool_input.get("automation_id") or tool_input.get("id") or ""
            query = (query or "").strip()
            limit = tool_input.get("limit") if isinstance(tool_input, dict) else None
            try:
                limit = int(limit) if limit is not None else 10
            except Exception:
                limit = 10
            limit = max(1, min(limit, 50))

            # If a query is provided, search automations.yaml for compact matches
            if query:
                q = query.lower()
                matches = []
                total_yaml = None
                try:
                    import yaml

                    yaml_path = api.get_config_file_path("automation", "automations.yaml")
                    if yaml_path and os.path.isfile(yaml_path):
                        with open(yaml_path, "r", encoding="utf-8") as f:
                            automations_yaml = yaml.safe_load(f) or []
                        if isinstance(automations_yaml, list):
                            total_yaml = len(automations_yaml)
                            for a in automations_yaml:
                                if not isinstance(a, dict):
                                    continue
                                alias = str(a.get("alias", "") or "")
                                aid = str(a.get("id", "") or "")
                                hay = (yaml.safe_dump(a, allow_unicode=True, sort_keys=False) or "").lower()
                                if q in alias.lower() or (aid and q in aid.lower()) or q in hay:
                                    y = yaml.safe_dump(a, allow_unicode=True, sort_keys=False) or ""
                                    if len(y) > 2500:
                                        y = y[:2500] + "\n... [TRUNCATED]"
                                    matches.append({
                                        "id": aid,
                                        "alias": alias,
                                        "yaml": y,
                                    })
                                    if len(matches) >= limit:
                                        break
                except Exception:
                    pass

                # Fallback: search states list by friendly_name/entity_id
                if not matches:
                    states = api.get_all_states()
                    autos = [s for s in states if s.get("entity_id", "").startswith("automation.")]
                    for s in autos:
                        eid = str(s.get("entity_id", "") or "")
                        fn = str(s.get("attributes", {}).get("friendly_name", "") or "")
                        aid = str(s.get("attributes", {}).get("id", "") or "")
                        if q in eid.lower() or q in fn.lower() or (aid and q in aid.lower()):
                            matches.append({
                                "entity_id": eid,
                                "state": s.get("state"),
                                "friendly_name": fn,
                                "id": aid,
                                "last_triggered": s.get("attributes", {}).get("last_triggered", ""),
                            })
                            if len(matches) >= limit:
                                break

                return json.dumps(
                    {
                        "query": query,
                        "matched": len(matches),
                        "total": total_yaml,
                        "automations": matches,
                        "edit_hint": "If you want to modify one, use update_automation with its id.",
                    },
                    ensure_ascii=False,
                    default=str,
                )

            # No query: return the full list (compact fields)
            states = api.get_all_states()
            autos = [s for s in states if s.get("entity_id", "").startswith("automation.")]
            result = [
                {
                    "entity_id": a.get("entity_id"),
                    "state": a.get("state"),
                    "friendly_name": a.get("attributes", {}).get("friendly_name", ""),
                    "id": a.get("attributes", {}).get("id", ""),
                    "last_triggered": a.get("attributes", {}).get("last_triggered", ""),
                }
                for a in autos
            ]

            total = len(result)
            result = result[:limit]
            return json.dumps(
                {
                    "total": total,
                    "returned": len(result),
                    "automations": result,
                    "edit_hint": "To edit an automation, use update_automation with the automation's id and the changes you want to make.",
                },
                ensure_ascii=False,
                default=str,
            )

        elif tool_name == "update_automation":
            import yaml
            import difflib
            automation_id = tool_input.get("automation_id", "")
            changes = tool_input.get("changes", {})
            add_condition = tool_input.get("add_condition", None)

            # Compatibility: some models incorrectly pass fields at top-level
            # instead of nesting under {changes:{...}}.
            # Normalize top-level fields into changes.
            if not isinstance(changes, dict):
                changes = {}

            if not changes:
                allowed_top_level = (
                    "alias",
                    "description",
                    "trigger",
                    "triggers",
                    "condition",
                    "conditions",
                    "action",
                    "actions",
                    "mode",
                )
                for k in allowed_top_level:
                    if k in tool_input:
                        changes[k] = tool_input.get(k)

            if not automation_id:
                return json.dumps({"error": "automation_id is required."})

            # ---- Entity validation on changes ----
            referenced_entities = _extract_entity_ids(changes)
            if referenced_entities:
                all_states = api.get_all_states()
                known_ids = {s.get("entity_id") for s in all_states if s.get("entity_id")}
                invalid = [eid for eid in referenced_entities if eid not in known_ids]
                if invalid:
                    suggestions = {}
                    for bad_id in invalid:
                        domain = bad_id.split(".")[0] if "." in bad_id else ""
                        name_part = bad_id.split(".", 1)[1] if "." in bad_id else bad_id
                        candidates = [kid for kid in known_ids if kid.startswith(domain + ".") and (name_part in kid or kid.split(".", 1)[1] in name_part)]
                        if candidates:
                            suggestions[bad_id] = candidates[:3]
                    msg = {
                        "status": "error",
                        "message": f"Entity IDs not found: {', '.join(invalid)}. Use search_entities to find the correct IDs.",
                        "invalid_entities": invalid,
                    }
                    if suggestions:
                        msg["suggestions"] = suggestions
                    return json.dumps(msg, ensure_ascii=False, default=str)

            # Strategy: try YAML first, then REST API fallback (for UI-created automations)
            updated_via = None
            old_yaml = ""
            new_yaml = ""
            snapshot = None
            reload_result = None
            diff_unified = ""

            # --- ATTEMPT 1: YAML file ---
            yaml_path = api.get_config_file_path("automation", "automations.yaml")
            if os.path.isfile(yaml_path):
                try:
                    with open(yaml_path, "r", encoding="utf-8") as f:
                        automations = yaml.safe_load(f)

                    if isinstance(automations, list):
                        found = None
                        found_idx = None
                        for idx, auto in enumerate(automations):
                            if str(auto.get("id", "")) == str(automation_id):
                                found = auto
                                found_idx = idx
                                break

                        if found is not None:
                            old_yaml = yaml.dump(found, default_flow_style=False, allow_unicode=True)
                            # Determine which key variants the existing automation uses
                            trig_key = "triggers" if "triggers" in found else "trigger"
                            cond_key = "conditions" if "conditions" in found else "condition"
                            act_key = "actions" if "actions" in found else "action"

                            # Remap trigger/condition/action keys in changes to match existing key style
                            if "trigger" in changes and trig_key == "triggers":
                                changes["triggers"] = changes.pop("trigger")
                            elif "triggers" in changes and trig_key == "trigger":
                                changes["trigger"] = changes.pop("triggers")

                            if "condition" in changes and cond_key == "conditions":
                                changes["conditions"] = changes.pop("condition")
                            elif "conditions" in changes and cond_key == "condition":
                                changes["condition"] = changes.pop("conditions")

                            if "action" in changes and act_key == "actions":
                                changes["actions"] = changes.pop("action")
                            elif "actions" in changes and act_key == "action":
                                changes["action"] = changes.pop("actions")

                            # FIX: If trigger(s) are being modified but description is NOT in changes,
                            # remove the old description so AI can regenerate it with new content
                            triggers_modified = ("trigger" in changes or "triggers" in changes)
                            description_provided = ("description" in changes)
                            if triggers_modified and not description_provided:
                                found["description"] = ""  # Reset description when triggers change without new description

                            for key, value in changes.items():
                                found[key] = value
                            if add_condition:
                                if cond_key not in found or not found[cond_key]:
                                    found[cond_key] = []
                                if not isinstance(found[cond_key], list):
                                    found[cond_key] = [found[cond_key]]
                                found[cond_key].append(add_condition)
                            # Stamp description with AI signature
                            found["description"] = _stamp_description(found.get("description", ""), "modify")
                            new_yaml = yaml.dump(found, default_flow_style=False, allow_unicode=True)

                            # Snapshot the actual file path (supports configuration.yaml include mapping)
                            try:
                                rel_snapshot_path = None
                                if isinstance(yaml_path, str) and yaml_path.startswith(api.HA_CONFIG_DIR + "/"):
                                    rel_snapshot_path = os.path.relpath(yaml_path, api.HA_CONFIG_DIR)
                                else:
                                    rel_snapshot_path = os.path.basename(yaml_path)
                                snapshot = api.create_snapshot(rel_snapshot_path)
                            except Exception:
                                snapshot = api.create_snapshot("automations.yaml")

                            automations[found_idx] = found
                            with open(yaml_path, "w", encoding="utf-8") as f:
                                yaml.dump(automations, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
                            updated_via = "yaml"

                            # Apply changes immediately: reload automations after file update
                            try:
                                reload_result = api.call_ha_api("POST", "services/automation/reload", {})
                            except Exception as e:
                                reload_result = {"error": str(e)}
                except Exception as e:
                    logger.warning(f"YAML update attempt failed: {e}")

            # --- ATTEMPT 2: REST API (for UI-created automations) ---
            if updated_via is None:
                try:
                    # Get current config via REST API
                    current = api.call_ha_api("GET", f"config/automation/config/{automation_id}")
                    if isinstance(current, dict) and "error" not in current:
                        old_yaml = yaml.dump(current, default_flow_style=False, allow_unicode=True)

                        # Normalize: HA may use 'condition' or 'conditions' - unify to what HA returned
                        cond_key = "conditions" if "conditions" in current else "condition"

                        # Remap condition↔conditions in changes to match existing key
                        if "condition" in changes and cond_key == "conditions":
                            changes["conditions"] = changes.pop("condition")
                        elif "conditions" in changes and cond_key == "condition":
                            changes["condition"] = changes.pop("conditions")

                        # FIX: If trigger(s) are being modified but description is NOT in changes,
                        # remove the old description so AI can regenerate it with new content
                        triggers_modified = ("trigger" in changes or "triggers" in changes)
                        description_provided = ("description" in changes)
                        if triggers_modified and not description_provided:
                            current["description"] = ""  # Reset description when triggers change without new description

                        # Apply changes
                        for key, value in changes.items():
                            current[key] = value
                        if add_condition:
                            if cond_key not in current or not current[cond_key]:
                                current[cond_key] = []
                            if not isinstance(current[cond_key], list):
                                current[cond_key] = [current[cond_key]]
                            current[cond_key].append(add_condition)

                        # Ensure no duplicate condition/conditions keys
                        if "condition" in current and "conditions" in current:
                            # Keep whichever has data, prefer 'conditions' (new format)
                            if current.get("conditions"):
                                current.pop("condition", None)
                            else:
                                current.pop("conditions", None)

                        # Stamp description with AI signature
                        current["description"] = _stamp_description(current.get("description", ""), "modify")
                        new_yaml = yaml.dump(current, default_flow_style=False, allow_unicode=True)
                        # Save via REST API (HA uses POST for both create and update)
                        save_result = api.call_ha_api("POST", f"config/automation/config/{automation_id}", current)
                        if isinstance(save_result, dict) and "error" not in save_result:
                            updated_via = "rest_api"
                        else:
                            return json.dumps({"error": f"REST API update failed: {save_result}",
                                               "IMPORTANT": "STOP. Inform the user about the error. Do NOT try other tools."}, default=str)
                    else:
                        return json.dumps({"error": f"Automation '{automation_id}' not found in YAML or via REST API.",
                                           "IMPORTANT": "STOP. Tell the user the automation was not found. Do NOT call more tools."}, default=str)
                except Exception as e:
                    return json.dumps({"error": f"Failed to update automation: {str(e)}",
                                       "IMPORTANT": "STOP. Inform the user about the error. Do NOT try other tools."})

            msg_parts = [f"Automation updated via {'YAML file' if updated_via == 'yaml' else 'HA REST API (UI-created automation)'}.",]

            try:
                if isinstance(old_yaml, str) and isinstance(new_yaml, str) and old_yaml and new_yaml:
                    diff_lines = difflib.unified_diff(
                        old_yaml.splitlines(),
                        new_yaml.splitlines(),
                        fromfile="before.yaml",
                        tofile="after.yaml",
                        lineterm="",
                    )
                    diff_unified = "\n".join(diff_lines)
            except Exception:
                diff_unified = ""

            return json.dumps({
                "status": "success",
                "message": " ".join(msg_parts),
                "updated_via": updated_via,
                "old_yaml": old_yaml,
                "new_yaml": new_yaml,
                "diff_unified": diff_unified,
                "snapshot": snapshot.get("snapshot_id", "") if (updated_via == "yaml" and isinstance(snapshot, dict)) else "N/A (REST API)",
                "reload_result": reload_result if updated_via == "yaml" else "N/A (REST API)",
                "tip": "Changes applied immediately via REST API. No reload needed." if updated_via == "rest_api" else "Automations reloaded automatically after YAML update.",
                "IMPORTANT": "DONE. Show the user old_yaml and new_yaml AND the diff_unified (lines -/+). Stop. Do NOT call any more tools."
            }, ensure_ascii=False, default=str)

        elif tool_name == "trigger_automation":
            entity_id = tool_input.get("entity_id", "")
            result = api.call_ha_api("POST", "services/automation/trigger", {"entity_id": entity_id})
            return json.dumps({"status": "success", "result": result}, ensure_ascii=False, default=str)

        elif tool_name == "get_available_services":
            svc_raw = api.call_ha_api("GET", "services")
            if isinstance(svc_raw, list):
                compact = {s.get("domain", ""): list(s.get("services", {}).keys()) for s in svc_raw}
                return json.dumps(compact, ensure_ascii=False)
            return json.dumps(svc_raw, ensure_ascii=False, default=str)

        elif tool_name == "search_entities":
            query = tool_input.get("query", "").lower().strip()
            states = api.get_all_states()
            matches = []

            import re

            STOPWORDS = {
                # IT
                "il", "lo", "la", "i", "gli", "le", "un", "uno", "una",
                "di", "del", "dello", "della", "dei", "degli", "delle",
                "a", "ad", "al", "allo", "alla", "ai", "agli", "alle",
                "da", "dal", "dallo", "dalla", "dai", "dagli", "dalle",
                "in", "su", "per", "con", "senza", "e", "o",
                # EN/ES/FR common
                "the", "a", "an", "of", "to", "in", "on", "for", "and", "or",
                "el", "la", "los", "las", "un", "una", "de", "del", "al", "y", "o",
                "le", "la", "les", "un", "une", "de", "du", "des", "et", "ou",
            }

            def _tokenize(text):
                if not text:
                    return []
                parts = re.split(r"[\s_\-\.]+", text.lower())
                tokens = [p.strip() for p in parts if p and p.strip()]
                # keep short tokens only if they are meaningful (avoid noise)
                out = []
                for t in tokens:
                    if t in STOPWORDS:
                        continue
                    if len(t) <= 1:
                        continue
                    out.append(t)
                return out

            query_tokens = _tokenize(query)

            # Build search index with scoring
            search_results = []

            for s in states:
                eid = s.get("entity_id", "").lower()
                fname = s.get("attributes", {}).get("friendly_name", "").lower()

                score = 0

                # Strong signals: exact substring match
                if query and query in eid:
                    score += 120
                if query and query in fname:
                    score += 110

                eid_tokens = _tokenize(eid.replace(".", " "))
                fname_tokens = _tokenize(fname)
                all_tokens = set(eid_tokens) | set(fname_tokens)

                matched = set()
                # Token coverage: multi-word queries must match multiple tokens
                for qt in query_tokens:
                    if qt in all_tokens:
                        matched.add(qt)
                        score += 55 if qt in fname_tokens else 50
                        continue

                    # Fuzzy token matching only for reasonably long tokens
                    if len(qt) >= 4:
                        for tt in all_tokens:
                            if tt.startswith(qt):
                                matched.add(qt)
                                score += 28 if tt in fname_tokens else 24
                                break
                        if qt not in matched:
                            for tt in all_tokens:
                                if qt in tt or tt in qt:
                                    matched.add(qt)
                                    score += 18 if tt in fname_tokens else 14
                                    break

                total_q = len(query_tokens)
                missing = [t for t in query_tokens if t not in matched]
                coverage = (len(matched) / total_q) if total_q else 0.0

                # Extra boost: full token coverage for multiword queries
                if total_q >= 2 and coverage >= 1.0:
                    score += 80

                # Penalize missing tokens heavily for multiword queries
                if total_q >= 2 and missing:
                    score -= 45 * len(missing)

                # If we only matched 1 token out of >=2, keep it but demote heavily.
                if total_q >= 2 and coverage < 0.5:
                    score -= 80

                # Phrase bonus: query tokens appear in order in friendly_name
                if total_q >= 2:
                    phrase = " ".join(query_tokens)
                    if phrase and phrase in fname:
                        score += 90

                # Fallback: if query is empty or tokenization is empty, do nothing
                if not query or not (query_tokens or query.strip()):
                    continue

                if score > 0:
                    if coverage >= 1.0 and score >= 140:
                        quality = "high"
                    elif coverage >= 0.75 and score >= 90:
                        quality = "medium"
                    else:
                        quality = "low"

                    search_results.append({
                        "entity_id": s.get("entity_id"),
                        "state": s.get("state"),
                        "friendly_name": s.get("attributes", {}).get("friendly_name", ""),
                        "match_quality": quality,
                        "token_coverage": round(coverage, 3),
                        "matched_tokens": sorted(list(matched))[:20],
                        "missing_tokens": missing[:20],
                        "score": score,
                    })

            # Sort by score (descending) and take top results
            search_results.sort(key=lambda x: (-x["score"], x["entity_id"]))
            max_results = 20 if api.AI_PROVIDER == "github" else 50
            matches = [{k: v for k, v in item.items() if k != "score"} for item in search_results[:max_results]]

            return json.dumps(matches, ensure_ascii=False, default=str)

        elif tool_name == "get_integration_entities":
            keyword = tool_input.get("integration", "").lower().strip()
            if not keyword:
                return json.dumps({"error": "integration keyword is required"})

            # Get entity registry via WebSocket (contains platform/integration info)
            reg_result = api.call_ha_websocket("config/entity_registry/list")
            registry = reg_result.get("result", []) if isinstance(reg_result, dict) else []
            if not registry:
                return json.dumps({"error": "Could not retrieve entity registry", "detail": str(reg_result)[:200]})

            # Try to also match by config_entry title (e.g. "Tigo Energy" for keyword "tigo")
            matched_entry_ids: set = set()
            try:
                cfg_result = api.call_ha_websocket("config_entries/get_entries")
                entries = cfg_result.get("result", []) if isinstance(cfg_result, dict) else []
                for e in entries:
                    domain = (e.get("domain") or "").lower()
                    title = (e.get("title") or "").lower()
                    if keyword in domain or keyword in title:
                        matched_entry_ids.add(e.get("entry_id", ""))
            except Exception:
                pass  # optional, platform match is enough

            # Filter entities by platform name OR config_entry_id match
            matched_registry = [
                r for r in registry
                if keyword in (r.get("platform") or "").lower()
                or (matched_entry_ids and r.get("config_entry_id") in matched_entry_ids)
            ]

            if not matched_registry:
                return json.dumps({
                    "found": 0, "entities": [],
                    "note": f"No entities found for integration '{keyword}'. Try search_entities for name-based search."
                })

            # Enrich with current states
            all_states = api.get_all_states()
            state_map = {s.get("entity_id"): s for s in all_states}
            entities = []
            for r in matched_registry:
                eid = r.get("entity_id", "")
                state = state_map.get(eid, {})
                entities.append({
                    "entity_id": eid,
                    "state": state.get("state", "unavailable"),
                    "friendly_name": (
                        state.get("attributes", {}).get("friendly_name")
                        or r.get("name")
                        or r.get("original_name")
                        or ""
                    ),
                    "unit": state.get("attributes", {}).get("unit_of_measurement", ""),
                    "platform": r.get("platform", ""),
                })
            entities.sort(key=lambda x: x["entity_id"])
            return json.dumps({"found": len(entities), "integration": keyword, "entities": entities},
                              ensure_ascii=False, default=str)

        elif tool_name == "get_events":
            events = api.call_ha_api("GET", "events")
            if isinstance(events, list):
                result = [{"event": e.get("event", ""), "listener_count": e.get("listener_count", 0)} for e in events]
                return json.dumps(result, ensure_ascii=False, default=str)
            return json.dumps(events, ensure_ascii=False, default=str)

        elif tool_name == "get_history":
            entity_id = tool_input.get("entity_id", "")
            hours = min(int(tool_input.get("hours", 24)), 168)
            start = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S")
            endpoint = f"history/period/{start}?filter_entity_id={entity_id}&significant_changes_only=1"
            result = api.call_ha_api("GET", endpoint)
            if isinstance(result, list) and result:
                entries = result[0] if isinstance(result[0], list) else result
                max_e = 20 if api.AI_PROVIDER == "github" else 50
                summary = [{"state": e.get("state"), "last_changed": e.get("last_changed")} for e in entries[-max_e:]]
                return json.dumps({"entity_id": entity_id, "hours": hours, "total_changes": len(entries), "history": summary}, ensure_ascii=False, default=str)
            return json.dumps({"entity_id": entity_id, "hours": hours, "history": []}, ensure_ascii=False, default=str)

        elif tool_name == "get_scenes":
            states = api.get_all_states()
            scenes = [{"entity_id": s.get("entity_id"), "state": s.get("state"),
                       "friendly_name": s.get("attributes", {}).get("friendly_name", "")}
                      for s in states if s.get("entity_id", "").startswith("scene.")]
            return json.dumps(scenes, ensure_ascii=False, default=str)

        elif tool_name == "activate_scene":
            entity_id = tool_input.get("entity_id", "")
            result = api.call_ha_api("POST", "services/scene/turn_on", {"entity_id": entity_id})
            return json.dumps({"status": "success", "scene": entity_id, "result": result}, ensure_ascii=False, default=str)

        elif tool_name == "get_scripts":
            states = api.get_all_states()
            scripts = [{"entity_id": s.get("entity_id"), "state": s.get("state"),
                        "friendly_name": s.get("attributes", {}).get("friendly_name", ""),
                        "last_triggered": s.get("attributes", {}).get("last_triggered", "")}
                       for s in states if s.get("entity_id", "").startswith("script.")]
            return json.dumps(scripts, ensure_ascii=False, default=str)

        elif tool_name == "run_script":
            entity_id = tool_input.get("entity_id", "")
            variables = tool_input.get("variables", {})
            script_id = entity_id.replace("script.", "") if entity_id.startswith("script.") else entity_id
            result = api.call_ha_api("POST", f"services/script/{script_id}", variables)
            return json.dumps({"status": "success", "script": entity_id, "result": result}, ensure_ascii=False, default=str)

        elif tool_name == "update_script":
            import yaml
            script_id = tool_input.get("script_id", "")
            changes = tool_input.get("changes", {})

            if not script_id:
                return json.dumps({"error": "script_id is required."})

            # Remove 'script.' prefix if present
            script_id = script_id.replace("script.", "") if script_id.startswith("script.") else script_id

            yaml_path = api.get_config_file_path("script", "scripts.yaml")
            if not os.path.isfile(yaml_path):
                return json.dumps({"error": "scripts.yaml not found."})

            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    scripts = yaml.safe_load(f)

                if not isinstance(scripts, dict):
                    return json.dumps({"error": "scripts.yaml is not a valid dict."})

                if script_id not in scripts:
                    return json.dumps({"error": f"Script '{script_id}' not found.",
                                       "available_scripts": list(scripts.keys())[:20]})

                found = scripts[script_id]
                if not isinstance(found, dict):
                    found = {}

                # Capture old state for diff
                old_yaml = yaml.dump({script_id: found}, default_flow_style=False, allow_unicode=True)

                # Apply changes
                for key, value in changes.items():
                    found[key] = value

                # Stamp description with AI signature
                found["description"] = _stamp_description(found.get("description", ""), "modify")

                # Capture new state for diff
                new_yaml = yaml.dump({script_id: found}, default_flow_style=False, allow_unicode=True)

                # Create snapshot before saving
                snapshot = api.create_snapshot("scripts.yaml")

                # Write back
                scripts[script_id] = found
                with open(yaml_path, "w", encoding="utf-8") as f:
                    yaml.dump(scripts, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

                return json.dumps({
                    "status": "success",
                    "message": f"Script '{found.get('alias', script_id)}' updated.",
                    "old_yaml": old_yaml,
                    "new_yaml": new_yaml,
                    "snapshot": snapshot.get("snapshot_id", ""),
                    "tip": "Call services/script/reload to apply changes.",
                    "IMPORTANT": "DONE. Show the user the before/after diff and stop. Do NOT call any more tools."
                }, ensure_ascii=False, default=str)
            except Exception as e:
                return json.dumps({"error": f"Failed to update script: {str(e)}"})

        elif tool_name == "get_areas":
            try:
                template = '[{% for area in areas() %}{"id":{{ area | tojson }}, "name":{{ area_name(area) | tojson }}, "entities":{{ area_entities(area) | list | tojson }}}{% if not loop.last %},{% endif %}{% endfor %}]'
                url = f"{api.HA_URL}/api/template"
                resp = requests.post(url, headers=api.get_ha_headers(), json={"template": template}, timeout=30)
                if resp.status_code == 200:
                    areas_data = json.loads(resp.text)
                    if api.AI_PROVIDER == "github":
                        for area in areas_data:
                            area["entities"] = area["entities"][:10]
                    return json.dumps(areas_data, ensure_ascii=False, default=str)
                return json.dumps({"error": f"Template API error: {resp.status_code}"}, default=str)
            except Exception as e:
                return json.dumps({"error": f"Could not get areas: {str(e)}"}, default=str)

        elif tool_name == "send_notification":
            message = tool_input.get("message", "")
            title = tool_input.get("title", "Amira")
            target = tool_input.get("target", "")
            if target:
                result = api.call_ha_api("POST", f"services/notify/{target}", {"message": message, "title": title})
            else:
                result = api.call_ha_api("POST", "services/persistent_notification/create", {"message": message, "title": title})
            return json.dumps({"status": "success", "result": result}, ensure_ascii=False, default=str)

        elif tool_name == "get_dashboards":
            ws_result = api.call_ha_websocket("lovelace/dashboards/list")
            if ws_result.get("success") and ws_result.get("result"):
                dashboards = ws_result["result"]
                result = [{"id": d.get("id"), "title": d.get("title"), "url_path": d.get("url_path"),
                           "icon": d.get("icon", ""), "mode": d.get("mode", "")} for d in dashboards]
                return json.dumps(result, ensure_ascii=False, default=str)
            return json.dumps({"error": f"Could not get dashboards: {ws_result}"}, default=str)

        elif tool_name == "create_dashboard":
            title = tool_input.get("title", "AI Dashboard")
            url_path = tool_input.get("url_path", "ai-dashboard")
            icon = tool_input.get("icon", "mdi:robot")
            views = tool_input.get("views", [])

            # Reject empty dashboards - force the model to include views with cards
            if not views or len(views) == 0:
                logger.warning(f"⚠️ create_dashboard called WITHOUT views - rejecting. Args: {tool_input}")
                return json.dumps({
                    "error": "REJECTED: views array is REQUIRED and must contain at least one view with cards. "
                             "Do NOT call create_dashboard without views. "
                             "STEP 1: Call search_entities to find the correct entity_ids. "
                             "STEP 2: Build a complete views array with cards (gauge, entities, history-graph, etc.). "
                             "STEP 3: Call create_dashboard again with title, url_path, icon, AND the complete views array."
                }, ensure_ascii=False, default=str)

            # Also reject views that have no cards
            empty_views = [i for i, v in enumerate(views) if not v.get("cards")]
            if empty_views and len(empty_views) == len(views):
                logger.warning(f"⚠️ create_dashboard called with views but ALL views have no cards - rejecting")
                return json.dumps({
                    "error": "REJECTED: All views are empty (no cards). Each view MUST contain a 'cards' array with at least one card. "
                             "Build proper cards (gauge, entities, history-graph, button, etc.) for each view before calling create_dashboard."
                }, ensure_ascii=False, default=str)

            logger.info(f"📊 Creating dashboard: title='{title}', url_path='{url_path}', views={len(views)}")

            # Step 1: Register dashboard via WebSocket (REST API doesn't support this)
            try:
                ws_result = api.call_ha_websocket(
                    "lovelace/dashboards/create",
                    url_path=url_path,
                    title=title,
                    icon=icon,
                    show_in_sidebar=True,
                    require_admin=False
                )
                logger.info(f"📊 Dashboard create WS response: {ws_result}")
                
                if ws_result.get("success") is False:
                    error_msg = ws_result.get("error", {}).get("message", str(ws_result))
                    logger.error(f"❌ Failed to create dashboard: {error_msg}")
                    return json.dumps({"error": f"Failed to create dashboard: {error_msg}"}, default=str)
            except Exception as e:
                logger.error(f"❌ Exception creating dashboard: {e}")
                return json.dumps({"error": f"Exception creating dashboard: {str(e)}"}, default=str)

            # Step 2: Set the dashboard config with views and cards via WebSocket
            try:
                ws_config = api.call_ha_websocket(
                    "lovelace/config/save",
                    url_path=url_path,
                    config={"views": views}
                )
                logger.info(f"📊 Dashboard config save WS response: {ws_config}")
                
                if ws_config.get("success") is False:
                    error_msg = ws_config.get("error", {}).get("message", str(ws_config))
                    logger.warning(f"⚠️ Dashboard registered but config failed: {error_msg}")
                    return json.dumps({"status": "partial", "message": f"Dashboard registered but config failed: {error_msg}"}, default=str)
            except Exception as e:
                logger.error(f"❌ Exception saving dashboard config: {e}")
                # Don't fail completely - the dashboard was created
                pass

            # Return the YAML so AI can show it to the user
            import yaml
            dashboard_yaml = yaml.dump({"views": views}, default_flow_style=False, allow_unicode=True)
            logger.info(f"✅ Dashboard '{title}' created successfully at /{url_path}")
            return json.dumps({
                "status": "success",
                "message": f"Dashboard '{title}' created! It appears in the sidebar at /{url_path}",
                "url_path": url_path,
                "views_count": len(views),
                "yaml": dashboard_yaml,
                "IMPORTANT": "Show the user the dashboard YAML you created."
            }, ensure_ascii=False, default=str)

        elif tool_name == "read_html_dashboard":
            name = tool_input.get("name", "")
            safe_name = name.lower().replace(" ", "-").replace("_", "-").replace(".", "-")
            # Load from www/dashboards/ (legacy .html_dashboards/ support removed)
            fpath = os.path.join(api.HA_CONFIG_DIR, "www", "dashboards", safe_name + ".html")
            if os.path.isfile(fpath):
                with open(fpath, "r", encoding="utf-8") as f:
                    html = f.read()
                return json.dumps({"status": "success", "name": name, "html": html, "size": len(html)}, ensure_ascii=False)
            return json.dumps({"status": "error", "message": f"Dashboard '{name}' not found. Use list: /custom_dashboards"})

        elif tool_name == "create_html_dashboard":
            _raw_title = tool_input.get("title", "Custom Dashboard")
            # Always prefix with "Amira — " so all HTML dashboards are clearly identified
            # in the HA sidebar, regardless of what name the AI chose.
            _PREFIX = "Amira \u2014 "  # em-dash
            title = _raw_title if _raw_title.startswith(_PREFIX) else _PREFIX + _raw_title
            name = tool_input.get("name", "dashboard")
            icon = tool_input.get("icon", "mdi:web")
            entities = tool_input.get("entities", [])
            theme = tool_input.get("theme", "auto")
            accent_color = tool_input.get("accent_color", "#667eea")
            sections = tool_input.get("sections", [])
            lang = tool_input.get("lang")
            footer_text = tool_input.get("footer_text")
            raw_html = tool_input.get("html")
            return_html = bool(tool_input.get("return_html", False))
            is_draft = bool(tool_input.get("draft", False))

            # --- Draft (chunked) mode ---
            if is_draft and raw_html:
                if name in _html_drafts:
                    _html_drafts[name]["html"] += raw_html
                    chunk_num = _html_drafts[name].get("chunks", 1) + 1
                    _html_drafts[name]["chunks"] = chunk_num
                    total = len(_html_drafts[name]["html"])
                    logger.info(f"📝 Draft chunk #{chunk_num} appended for '{name}': +{len(raw_html)} chars (total: {total})")
                    return json.dumps({
                        "status": "draft_appended",
                        "message": f"Chunk #{chunk_num} appended ({len(raw_html)} chars). Total so far: {total} chars. "
                                   f"Send more chunks with draft=true, or omit draft to finalize and save.",
                        "name": name, "total_chars": total
                    }, default=str)
                else:
                    _html_drafts[name] = {
                        "html": raw_html, "title": title, "icon": icon,
                        "entities": entities, "theme": theme, "accent_color": accent_color,
                        "lang": lang, "footer_text": footer_text, "chunks": 1
                    }
                    logger.info(f"📝 Draft started for '{name}': {len(raw_html)} chars, {len(entities)} entities")
                    return json.dumps({
                        "status": "draft_started",
                        "message": f"Draft started ({len(raw_html)} chars). Send more chunks with draft=true and same name='{name}', "
                                   f"or omit draft to finalize and save.",
                        "name": name, "total_chars": len(raw_html)
                    }, default=str)

            # --- Finalize: merge draft if exists ---
            if name in _html_drafts:
                draft = _html_drafts.pop(name)
                draft_html = draft["html"]
                if raw_html:
                    draft_html += raw_html
                raw_html = draft_html
                # Use draft metadata if current call doesn't provide them
                if not entities and draft.get("entities"):
                    entities = draft["entities"]
                if title == "Custom Dashboard" and draft.get("title"):
                    title = draft["title"]
                if icon == "mdi:web" and draft.get("icon"):
                    icon = draft["icon"]
                if theme == "auto" and draft.get("theme"):
                    theme = draft["theme"]
                if accent_color == "#667eea" and draft.get("accent_color"):
                    accent_color = draft["accent_color"]
                if not lang and draft.get("lang"):
                    lang = draft["lang"]
                if not footer_text and draft.get("footer_text"):
                    footer_text = draft["footer_text"]
                chunks = draft.get("chunks", 1) + (1 if tool_input.get("html") else 0)
                logger.info(f"📝 Draft finalized for '{name}': {chunks} chunks, {len(raw_html)} chars total")

            if raw_html is not None:
                if not isinstance(raw_html, str) or not raw_html.strip():
                    return json.dumps({"error": "html must be a non-empty string when provided."}, default=str)
                if len(raw_html) > 900_000:
                    return json.dumps({"error": f"html is too large ({len(raw_html)} chars). Please reduce size."}, default=str)
                # Auto-complete truncated HTML: GPT-5.2 often hits output token limit
                # before writing the Vue.createApp script section
                html_lower = raw_html.lower()
                if "createapp" not in html_lower:
                    raw_html = _autocomplete_truncated_html(raw_html, entities)
                    logger.info(f"Auto-completed truncated HTML (no createApp): added Vue boilerplate ({len(raw_html)} chars total)")
                elif ".mount(" not in raw_html:
                    # createApp exists but script is truncated (no .mount call)
                    # The HTML is too large for a single call — force chunked mode
                    logger.warning(f"Truncated Vue app detected: createApp present but .mount() missing ({len(raw_html)} chars)")
                    return json.dumps({"error": (
                        "TRUNCATED HTML: Your script is incomplete (createApp exists but .mount() is missing — you hit the output token limit). "
                        "You MUST use CHUNKED/DRAFT mode to send the HTML in 2-3 smaller parts:\n"
                        "  Call 1: create_html_dashboard(title=..., name=..., entities=[...], html='<!DOCTYPE html>...<style>CSS</style></head><body>...template HTML...', draft=true)\n"
                        "  Call 2: create_html_dashboard(name=..., html='<script>...complete Vue.createApp({...}).mount(\"#app\")</script></body></html>')\n"
                        "Each chunk MUST be under 6000 chars. The tool concatenates all parts automatically. "
                        "Do NOT omit draft=true on intermediate calls. The LAST call must NOT have draft."
                    )}, default=str)
            else:
                if not sections:
                    return json.dumps({"error": (
                        "MISSING CONTENT: You must pass your HTML code as the 'html' parameter in the tool call arguments. "
                        "Do NOT write HTML as text — put it in the tool arguments JSON: "
                        "{\"title\":\"...\",\"name\":\"...\",\"entities\":[...],\"html\":\"<!DOCTYPE html><html>...</html>\"} "
                        "Include title, name, entities array, and the complete html string."
                    )}, default=str)
            # In raw HTML mode, entities are optional metadata (the HTML is already complete).
            # In structured (sections) mode, entities are required to build the template.
            if not entities and raw_html is None:
                return json.dumps({"error": "entities is required. Provide an array of entity_ids to monitor."}, default=str)
            if not entities:
                logger.info("create_html_dashboard: no entities provided for raw HTML — saving as-is")

            # Pre-filter: discard strings that are clearly not HA entity_ids.
            # The AI (especially codex) often passes JS variable expressions like
            # stat.low, x.state, b.entity_id, arr.map, ids.tot instead of real entity_ids.
            # Strategy: whitelist known HA domains — real entity_ids always start with one.
            import re as _re_eid
            _HA_DOMAINS = {
                "sensor", "binary_sensor", "switch", "light", "climate", "cover",
                "fan", "input_boolean", "input_number", "input_select", "input_text",
                "input_datetime", "number", "select", "text", "automation", "script",
                "scene", "media_player", "camera", "lock", "vacuum", "alarm_control_panel",
                "weather", "person", "device_tracker", "zone", "sun", "timer", "counter",
                "group", "remote", "siren", "update", "button", "event", "image",
                "lawn_mower", "todo", "notify", "persistent_notification",
            }
            _prefiltered = []
            _prefilter_skipped = []
            for eid in entities:
                if not isinstance(eid, str):
                    _prefilter_skipped.append(str(eid))
                    continue
                _parts = eid.split(".", 1)
                # Must be domain.slug, domain in HA whitelist, slug non-empty and only safe chars
                if (len(_parts) == 2
                        and _parts[0] in _HA_DOMAINS
                        and len(_parts[1]) >= 2
                        and _re_eid.match(r'^[a-z0-9_]+$', _parts[1])):
                    _prefiltered.append(eid)
                else:
                    _prefilter_skipped.append(eid)
            if _prefilter_skipped:
                logger.info(f"🔍 Pre-filtered {len(_prefilter_skipped)} non-entity strings from entities list: {_prefilter_skipped[:10]}")
            entities = _prefiltered

            # Fallback: if AI passed no valid entity_ids at all but we have raw HTML,
            # scan the HTML for real HA entity_id literals (quoted strings matching domain.slug).
            if not entities and raw_html:
                try:
                    _domains_re = '|'.join(sorted(_HA_DOMAINS, key=len, reverse=True))
                    _html_eids = list(dict.fromkeys(
                        m.strip("'\"") for m in _re_eid.findall(
                            r'["\'](?:' + _domains_re + r')\.[a-z0-9_]{2,}["\']',
                            raw_html
                        )
                    ))
                    if _html_eids:
                        logger.info(f"🔍 Extracted {len(_html_eids)} entity_ids from HTML content: {_html_eids[:10]}")
                        entities = _html_eids
                except Exception as _ex:
                    logger.warning(f"Entity extraction from HTML failed: {_ex}")

            # Last-resort fallback: use the entity_ids pre-loaded by smart context
            # (intent.py saves them on api._last_smart_context_entity_ids).
            # This kicks in when the AI passed only JS garbage and the HTML scan found nothing.
            if not entities:
                _ctx_eids = getattr(api, "_last_smart_context_entity_ids", None)
                if _ctx_eids:
                    entities = list(_ctx_eids)
                    logger.info(f"🔄 Using {len(entities)} entity_ids from smart context pre-load as fallback")

            # Validate entities: only keep those that exist and are not unknown/unavailable
            original_count = len(entities)
            valid_entities = []
            invalid_entities = []
            try:
                all_states = api.call_ha_api("GET", "states")
                states_map = {s["entity_id"]: s["state"] for s in all_states} if isinstance(all_states, list) else {}
                for eid in entities:
                    if eid not in states_map:
                        invalid_entities.append(f"{eid} (not found)")
                    elif states_map[eid] in ("unknown", "unavailable"):
                        invalid_entities.append(f"{eid} ({states_map[eid]})")
                    else:
                        valid_entities.append(eid)
            except Exception as e:
                logger.warning(f"⚠️ Could not validate entities, using all: {e}")
                valid_entities = entities

            if invalid_entities:
                logger.info(f"🧹 Filtered {len(invalid_entities)}/{original_count} entities: {invalid_entities}")

            if not valid_entities:
                if raw_html is not None:
                    # Raw HTML mode: entities are optional metadata, the HTML is already complete.
                    # Save anyway even if extracted entity references are wrong/unknown.
                    if original_count > 0:
                        logger.warning(
                            f"⚠️ All {original_count} entities invalid for raw HTML dashboard — "
                            f"saving without entity metadata: {invalid_entities}"
                        )
                    entities = []
                else:
                    return json.dumps({"error": f"No valid entities found. All {original_count} entities are either missing or unknown/unavailable: {invalid_entities}"}, default=str)
            else:
                entities = valid_entities

            mode = "raw" if raw_html is not None else "structured"
            logger.info(
                f"🎨 Creating HTML dashboard ({mode}): title='{title}', name='{name}', "
                f"entities={len(entities)}/{original_count} valid, sections={len(sections) if isinstance(sections, list) else 0}"
            )

            if raw_html is not None:
                html_content = _fill_html_placeholders(
                    raw_html,
                    title=title,
                    entities=entities,
                    theme=theme,
                    accent_color=accent_color,
                    lang=lang,
                    footer_text=footer_text,
                )
            else:
                # Build HTML from structured sections spec
                html_content = _build_dashboard_html(
                    title,
                    entities,
                    theme,
                    accent_color,
                    sections,
                    lang=lang,
                    footer_text=footer_text,
                )

            # Sanitize: fix CSS var() and auth redirect patterns (common AI mistakes)
            html_content = _fix_css_var_in_js(html_content)
            html_content = _fix_auth_redirect(html_content)

            logger.info(f"🎨 HTML generated: {len(html_content)} chars")

            try:
                # Save HTML to /config/www/dashboards/ - served by HA at /local/dashboards/
                # This avoids Ingress token dependency entirely (stable URL, same-origin)
                html_dashboards_dir = os.path.join(api.HA_CONFIG_DIR, "www", "dashboards")
                os.makedirs(html_dashboards_dir, exist_ok=True)

                # Save the agent-generated HTML file
                safe_filename = name.lower().replace(" ", "-").replace("_", "-").replace(".", "-")
                if not safe_filename.endswith(".html"):
                    safe_filename += ".html"

                file_path = os.path.join(html_dashboards_dir, safe_filename)

                # Read old content for diff (if file already exists)
                _old_html = ""
                if os.path.exists(file_path):
                    try:
                        with open(file_path, "r", encoding="utf-8") as _f:
                            _old_html = _f.read()
                    except Exception:
                        pass

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_content)

                logger.info(f"✅ HTML dashboard file saved: {file_path}")

                # URL for iframe - /local/ is HA's static file server (no Ingress token needed)
                dashboard_url = f"/local/dashboards/{safe_filename}"
                logger.info(f"🔗 Dashboard iframe URL: {dashboard_url}")

                # Create a Lovelace dashboard wrapper with iframe in sidebar
                safe_url_path = name.lower().replace(" ", "-").replace("_", "-").replace(".", "-")
                # HA requires url_path to contain at least one hyphen
                if "-" not in safe_url_path:
                    safe_url_path = safe_url_path + "-dash"
                dashboard_created = False
                
                try:
                    ws_result = api.call_ha_websocket(
                        "lovelace/dashboards/create",
                        url_path=safe_url_path,
                        title=title,
                        icon=icon,
                        show_in_sidebar=True,
                        require_admin=False
                    )
                    logger.info(f"📊 Dashboard create WS response: {ws_result}")
                    if ws_result.get("success") is not False:
                        dashboard_created = True
                    else:
                        # If it already exists, treat as success (upsert)
                        err_code = (ws_result.get("error") or {}).get("code", "")
                        if err_code in ("already_exists", "home_assistant_error"):
                            logger.info(f"📊 Dashboard '{safe_url_path}' already exists — updating config")
                            dashboard_created = True
                except Exception as e:
                    logger.error(f"❌ Exception creating Lovelace dashboard: {e}")

                # Add iframe card pointing to our HTML file
                sidebar_message = "HTML file is ready (sidebar integration skipped)"
                if dashboard_created:
                    try:
                        ws_config = api.call_ha_websocket(
                            "lovelace/config/save",
                            url_path=safe_url_path,
                            config={"views": [{
                                "title": title, "path": safe_url_path, "type": "panel",
                                "cards": [{"type": "iframe", "url": dashboard_url}]
                            }]}
                        )
                        if ws_config.get("success") is True:
                            sidebar_message = api.tr("dashboard_sidebar_ready", path=safe_url_path)
                        else:
                            sidebar_message = api.tr("dashboard_sidebar_failed")
                    except Exception as e:
                        logger.error(f"❌ Exception saving dashboard config: {e}")
                        sidebar_message = api.tr("dashboard_sidebar_failed")

                result = {
                    "status": "success",
                    "message": f"✨ {api.tr('dashboard_created_successfully')}'{title}'. {sidebar_message}",
                    "title": title,
                    "name": name,
                    "filename": safe_filename,
                    "html_url": dashboard_url,
                    "url_path": safe_url_path,
                    "sidebar_ready": dashboard_created,
                    "entities_count": len(entities),
                    "mode": mode,
                    "sections_count": len(sections) if isinstance(sections, list) else 0,
                    "IMPORTANT": f"✨ Dashboard '{title}' is ready! Reply with ONE short sentence confirming it was created. Do NOT include any HTML code in your reply.",
                }
                # Compute diff if we overwrote an existing file
                if _old_html and _old_html != html_content:
                    import difflib as _difflib
                    _old_lines = _old_html.splitlines(keepends=True)
                    _new_lines = html_content.splitlines(keepends=True)
                    _diff_lines = list(_difflib.unified_diff(
                        _old_lines, _new_lines, fromfile="old", tofile="new", lineterm=""
                    ))
                    if _diff_lines:
                        _MAX_DIFF_LINES = 120
                        _diff_str = "".join(_diff_lines[:_MAX_DIFF_LINES])
                        if len(_diff_lines) > _MAX_DIFF_LINES:
                            _diff_str += f"\n... ({len(_diff_lines) - _MAX_DIFF_LINES} righe aggiuntive)"
                        result["diff"] = _diff_str
                        result["IMPORTANT"] = f"✨ Dashboard '{title}' modificata! Reply with ONE short sentence confirming the edit. Do NOT include any HTML code in your reply."

                if return_html:
                    result["html"] = html_content
                if invalid_entities:
                    result["filtered_entities"] = invalid_entities
                    result["warning"] = f"{len(invalid_entities)} entities were removed (not found or unknown/unavailable). The dashboard only monitors {len(entities)} valid entities."
                return json.dumps(result, ensure_ascii=False, default=str)

            except Exception as e:
                logger.error(f"❌ Exception creating HTML dashboard: {e}", exc_info=True)
                return json.dumps({"error": f"Failed to create HTML dashboard: {str(e)}"}, default=str)
            import yaml
            script_id = tool_input.get("script_id", "")
            config = {
                "alias": tool_input.get("alias", "New Script"),
                "description": _stamp_description(tool_input.get("description", ""), "create"),
                "sequence": tool_input.get("sequence", []),
                "mode": tool_input.get("mode", "single"),
            }
            result = api.call_ha_api("POST", f"config/script/config/{script_id}", config)
            if isinstance(result, dict) and "error" not in result:
                # Return the YAML so AI can show it to the user
                created_yaml = yaml.dump(config, default_flow_style=False, allow_unicode=True)
                return json.dumps({
                    "status": "success",
                    "message": f"Script '{config['alias']}' created (script.{script_id})",
                    "entity_id": f"script.{script_id}",
                    "yaml": created_yaml,
                    "result": result,
                    "IMPORTANT": "Show the user the YAML code you created."
                }, ensure_ascii=False, default=str)
            return json.dumps({"status": "error", "result": result}, ensure_ascii=False, default=str)

        # ===== DELETE OPERATIONS (WebSocket) =====
        elif tool_name == "delete_dashboard":
            dashboard_id = tool_input.get("dashboard_id", "")
            result = api.call_ha_websocket("lovelace/dashboards/delete", dashboard_id=dashboard_id)
            if result.get("success"):
                return json.dumps({"status": "success", "message": f"Dashboard '{dashboard_id}' deleted."}, ensure_ascii=False)
            error_msg = result.get("error", {}).get("message", str(result))
            return json.dumps({"error": f"Failed to delete dashboard: {error_msg}"}, default=str)

        elif tool_name == "delete_automation":
            import yaml
            automation_id = tool_input.get("automation_id", "")
            logger.info(f"delete_automation called: automation_id='{automation_id}'")

            # Need the object_id (without automation. prefix)
            object_id = automation_id.replace("automation.", "") if automation_id.startswith("automation.") else automation_id

            # Try API first (for UI-created automations)
            result = api.call_ha_api("DELETE", f"config/automation/config/{object_id}")
            if result and not isinstance(result, dict):
                logger.info(f"Automation deleted via API: {automation_id}")
                return json.dumps({"status": "success", "message": f"Automation '{automation_id}' deleted via API."}, ensure_ascii=False, default=str)

            # If API failed, try removing from YAML file (for file-based automations)
            logger.info(f"API delete failed, trying YAML file removal for: {automation_id}")
            yaml_path = api.get_config_file_path("automation", "automations.yaml")

            if not os.path.isfile(yaml_path):
                return json.dumps({"error": f"Cannot delete automation: API failed and {yaml_path} not found."}, ensure_ascii=False)

            try:
                # Create snapshot before modifying
                snapshot = api.create_snapshot("automations.yaml")

                with open(yaml_path, "r", encoding="utf-8") as f:
                    automations = yaml.safe_load(f) or []

                if not isinstance(automations, list):
                    return json.dumps({"error": "automations.yaml is not a list format"}, ensure_ascii=False)

                # Find and remove the automation by ID or alias
                found = False
                original_count = len(automations)

                # Try matching by ID first
                automations = [a for a in automations if str(a.get("id", "")) != object_id]

                # If no match by ID, try by alias (the display name)
                if len(automations) == original_count:
                    # Extract the name from the full automation_id if it looks like a title
                    name_to_match = automation_id.replace("automation.", "").replace("_", " ")
                    automations = [a for a in automations if a.get("alias", "").lower() != name_to_match.lower()]

                if len(automations) < original_count:
                    found = True
                    # Write back to file
                    with open(yaml_path, "w", encoding="utf-8") as f:
                        yaml.dump(automations, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

                    logger.info(f"Automation deleted from YAML: {automation_id}")
                    return json.dumps({
                        "status": "success",
                        "message": f"Automation '{automation_id}' removed from {yaml_path}. Restart Home Assistant to apply changes.",
                        "snapshot": snapshot,
                        "restart_required": True
                    }, ensure_ascii=False, default=str)
                else:
                    return json.dumps({"error": f"Automation '{automation_id}' not found in {yaml_path}"}, ensure_ascii=False)

            except Exception as e:
                logger.error(f"Error deleting automation from YAML: {e}")
                return json.dumps({"error": f"Failed to delete from YAML: {str(e)}"}, ensure_ascii=False)

        elif tool_name == "delete_script":
            import yaml
            script_id = tool_input.get("script_id", "")
            logger.info(f"delete_script called: script_id='{script_id}'")

            object_id = script_id.replace("script.", "") if script_id.startswith("script.") else script_id

            # Try API first (for UI-created scripts)
            result = api.call_ha_api("DELETE", f"config/script/config/{object_id}")
            if result and not isinstance(result, dict):
                logger.info(f"Script deleted via API: {script_id}")
                return json.dumps({"status": "success", "message": f"Script '{script_id}' deleted via API."}, ensure_ascii=False, default=str)

            # If API failed, try removing from YAML file
            logger.info(f"API delete failed, trying YAML file removal for: {script_id}")
            yaml_path = api.get_config_file_path("script", "scripts.yaml")

            if not os.path.isfile(yaml_path):
                return json.dumps({"error": f"Cannot delete script: API failed and {yaml_path} not found."}, ensure_ascii=False)

            try:
                # Create snapshot before modifying
                snapshot = api.create_snapshot("scripts.yaml")

                with open(yaml_path, "r", encoding="utf-8") as f:
                    scripts = yaml.safe_load(f) or {}

                if not isinstance(scripts, dict):
                    return json.dumps({"error": "scripts.yaml is not a dict format"}, ensure_ascii=False)

                # Remove the script by key
                if object_id in scripts:
                    del scripts[object_id]

                    # Write back to file
                    with open(yaml_path, "w", encoding="utf-8") as f:
                        yaml.dump(scripts, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

                    logger.info(f"Script deleted from YAML: {script_id}")
                    return json.dumps({
                        "status": "success",
                        "message": f"Script '{script_id}' removed from {yaml_path}. Restart Home Assistant to apply changes.",
                        "snapshot": snapshot,
                        "restart_required": True
                    }, ensure_ascii=False, default=str)
                else:
                    return json.dumps({"error": f"Script '{script_id}' not found in {yaml_path}"}, ensure_ascii=False)

            except Exception as e:
                logger.error(f"Error deleting script from YAML: {e}")
                return json.dumps({"error": f"Failed to delete from YAML: {str(e)}"}, ensure_ascii=False)

        # ===== AREA MANAGEMENT (WebSocket) =====
        elif tool_name == "manage_areas":
            action = tool_input.get("action", "list")
            if action == "list":
                result = api.call_ha_websocket("config/area_registry/list")
                areas = result.get("result", [])
                summary = [{"area_id": a.get("area_id"), "name": a.get("name"), "icon": a.get("icon", "")} for a in areas]
                return json.dumps({"areas": summary, "count": len(summary)}, ensure_ascii=False, default=str)
            elif action == "create":
                name = tool_input.get("name", "")
                params = {"name": name}
                if tool_input.get("icon"):
                    params["icon"] = tool_input["icon"]
                result = api.call_ha_websocket("config/area_registry/create", **params)
                if result.get("success"):
                    area = result.get("result", {})
                    return json.dumps({"status": "success", "message": f"Area '{name}' created.", "area_id": area.get("area_id")}, ensure_ascii=False, default=str)
                error_msg = result.get("error", {}).get("message", str(result))
                return json.dumps({"error": f"Failed to create area: {error_msg}"}, default=str)
            elif action == "update":
                area_id = tool_input.get("area_id", "")
                params = {"area_id": area_id}
                if tool_input.get("name"):
                    params["name"] = tool_input["name"]
                if tool_input.get("icon"):
                    params["icon"] = tool_input["icon"]
                result = api.call_ha_websocket("config/area_registry/update", **params)
                if result.get("success"):
                    return json.dumps({"status": "success", "message": f"Area '{area_id}' updated."}, ensure_ascii=False, default=str)
                error_msg = result.get("error", {}).get("message", str(result))
                return json.dumps({"error": f"Failed to update area: {error_msg}"}, default=str)
            elif action == "delete":
                area_id = tool_input.get("area_id", "")
                result = api.call_ha_websocket("config/area_registry/delete", area_id=area_id)
                if result.get("success"):
                    return json.dumps({"status": "success", "message": f"Area '{area_id}' deleted."}, ensure_ascii=False, default=str)
                error_msg = result.get("error", {}).get("message", str(result))
                return json.dumps({"error": f"Failed to delete area: {error_msg}"}, default=str)

        # ===== ENTITY REGISTRY (WebSocket) =====
        elif tool_name == "manage_entity":
            entity_id = tool_input.get("entity_id", "")
            params = {"entity_id": entity_id}
            if tool_input.get("name") is not None:
                params["name"] = tool_input["name"]
            if tool_input.get("area_id") is not None:
                params["area_id"] = tool_input["area_id"]
            if tool_input.get("disabled_by") is not None:
                params["disabled_by"] = tool_input["disabled_by"] if tool_input["disabled_by"] else None
            if tool_input.get("icon") is not None:
                params["icon"] = tool_input["icon"]
            result = api.call_ha_websocket("config/entity_registry/update", **params)
            if result.get("success"):
                entry = result.get("result", {})
                return json.dumps({"status": "success", "message": f"Entity '{entity_id}' updated.",
                                   "name": entry.get("name"), "area_id": entry.get("area_id"),
                                   "disabled_by": entry.get("disabled_by")}, ensure_ascii=False, default=str)
            error_msg = result.get("error", {}).get("message", str(result))
            return json.dumps({"error": f"Failed to update entity: {error_msg}"}, default=str)

        # ===== DEVICE REGISTRY (WebSocket) =====
        elif tool_name == "get_devices":
            result = api.call_ha_websocket("config/device_registry/list")
            devices = result.get("result", [])
            summary = []
            for d in devices[:100]:  # Limit to 100 devices
                summary.append({
                    "id": d.get("id"),
                    "name": d.get("name_by_user") or d.get("name", ""),
                    "manufacturer": d.get("manufacturer", ""),
                    "model": d.get("model", ""),
                    "area_id": d.get("area_id", ""),
                    "via_device_id": d.get("via_device_id", "")
                })
            return json.dumps({"devices": summary, "count": len(devices), "showing": len(summary)}, ensure_ascii=False, default=str)

        # ===== ADVANCED STATISTICS (WebSocket) =====
        elif tool_name == "get_statistics":
            entity_id = tool_input.get("entity_id", "")
            period = tool_input.get("period", "hour")
            hours = min(tool_input.get("hours", 24), 720)
            start_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + "Z"
            result = api.call_ha_websocket(
                "recorder/statistics_during_period",
                start_time=start_time,
                statistic_ids=[entity_id],
                period=period
            )
            stats = result.get("result", {}).get(entity_id, [])
            # Summarize: take last 50 entries max
            summary_stats = []
            for s in stats[-50:]:
                summary_stats.append({
                    "start": s.get("start"),
                    "mean": s.get("mean"),
                    "min": s.get("min"),
                    "max": s.get("max"),
                    "sum": s.get("sum"),
                    "state": s.get("state")
                })
            return json.dumps({"entity_id": entity_id, "period": period,
                               "hours": hours, "statistics": summary_stats,
                               "total_entries": len(stats)}, ensure_ascii=False, default=str)

        # ===== SHOPPING LIST (WebSocket) =====
        elif tool_name == "shopping_list":
            action = tool_input.get("action", "list")
            if action == "list":
                result = api.call_ha_websocket("shopping_list/items")
                items = result.get("result", [])
                return json.dumps({"items": items, "count": len(items)}, ensure_ascii=False, default=str)
            elif action == "add":
                name = tool_input.get("name", "")
                result = api.call_ha_websocket("shopping_list/items/add", name=name)
                if result.get("success"):
                    return json.dumps({"status": "success", "message": f"'{name}' added to shopping list.",
                                       "item": result.get("result", {})}, ensure_ascii=False, default=str)
                error_msg = result.get("error", {}).get("message", str(result))
                return json.dumps({"error": f"Failed to add item: {error_msg}"}, default=str)
            elif action == "complete":
                item_id = tool_input.get("item_id", "")
                result = api.call_ha_websocket("shopping_list/items/update", item_id=item_id, complete=True)
                if result.get("success"):
                    return json.dumps({"status": "success", "message": f"Item marked as complete."}, ensure_ascii=False, default=str)
                error_msg = result.get("error", {}).get("message", str(result))
                return json.dumps({"error": f"Failed to complete item: {error_msg}"}, default=str)

        # ===== BACKUP (Supervisor REST API) =====
        elif tool_name == "create_backup":
            try:
                ha_token = api.get_ha_token()
                resp = requests.post(
                    "http://supervisor/backups/new/full",
                    headers={"Authorization": f"Bearer {ha_token}", "Content-Type": "application/json"},
                    json={"name": f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"},
                    timeout=300
                )
                result = resp.json()
                if result.get("result") == "ok":
                    slug = result.get("data", {}).get("slug", "")
                    return json.dumps({"status": "success", "message": f"Backup created successfully!", "slug": slug}, ensure_ascii=False, default=str)
                return json.dumps({"error": f"Backup failed: {result}"}, default=str)
            except Exception as e:
                return json.dumps({"error": f"Backup error: {str(e)}"}, default=str)

        # ===== BROWSE MEDIA (WebSocket) =====
        elif tool_name == "browse_media":
            content_id = tool_input.get("media_content_id", "")
            content_type = tool_input.get("media_content_type", "music")
            params = {"media_content_type": content_type}
            if content_id:
                params["media_content_id"] = content_id
            result = api.call_ha_websocket("media_player/browse_media", **params)
            if result.get("success"):
                media = result.get("result", {})
                children = media.get("children", [])
                summary = []
                for c in children[:50]:
                    summary.append({
                        "title": c.get("title", ""),
                        "media_content_id": c.get("media_content_id", ""),
                        "media_content_type": c.get("media_content_type", ""),
                        "media_class": c.get("media_class", ""),
                        "can_expand": c.get("can_expand", False),
                        "can_play": c.get("can_play", False)
                    })
                return json.dumps({"title": media.get("title", "Media"), "children": summary,
                                   "count": len(children)}, ensure_ascii=False, default=str)
            error_msg = result.get("error", {}).get("message", str(result))
            return json.dumps({"error": f"Browse media failed: {error_msg}"}, default=str)

        # ===== DASHBOARD READ/EDIT =====
        elif tool_name == "get_dashboard_config":
            try:
                url_path = tool_input.get("url_path", None)
                params = {}
                if url_path and url_path != "lovelace":
                    params["url_path"] = url_path
                result = api.call_ha_websocket("lovelace/config", **params)
                if result.get("success"):
                    config = result.get("result", {})
                    views = config.get("views", [])
                    # Summarize to avoid huge response
                    summary_views = []
                    for v in views:
                        try:
                            cards = v.get("cards", [])
                            card_summary = []
                            for c in cards:
                                try:
                                    card_info = {"type": c.get("type", "unknown")}
                                    if c.get("title"):
                                        card_info["title"] = c["title"]
                                    if c.get("entity"):
                                        card_info["entity"] = c["entity"]
                                    if c.get("entities"):
                                        entities = c.get("entities")
                                        if isinstance(entities, list):
                                            card_info["entities"] = entities[:10]
                                        else:
                                            card_info["entities"] = entities
                                    # Include full card for custom types
                                    if c.get("type", "").startswith("custom:"):
                                        card_info = c
                                    card_summary.append(card_info)
                                except Exception as e:
                                    logger.warning(f"⚠️ Error processing card: {e}")
                                    card_summary.append({"type": "error", "error": str(e)})
                            summary_views.append({
                                "title": v.get("title", ""),
                                "path": v.get("path", ""),
                                "icon": v.get("icon", ""),
                                "cards_count": len(cards),
                                "cards": card_summary
                            })
                        except Exception as e:
                            logger.warning(f"⚠️ Error processing view: {e}")
                            summary_views.append({"title": f"Error: {e}", "cards": []})
                    
                    logger.info(f"📊 Dashboard config loaded: {len(views)} views, {sum(len(v.get('cards', [])) for v in views)} cards")
                    return json.dumps({"url_path": url_path or "lovelace",
                                       "views": summary_views, "views_count": len(views),
                                       "full_config": config}, ensure_ascii=False, default=str)
                error_msg = result.get("error", {}).get("message", str(result))
                logger.error(f"❌ Lovelace API error: {error_msg}")
                return json.dumps({"error": f"Failed to get dashboard config: {error_msg}"}, default=str)
            except Exception as e:
                logger.error(f"❌ Exception in get_dashboard_config: {e}")
                return json.dumps({"error": f"Exception reading dashboard: {str(e)}"}, default=str)

        elif tool_name == "update_dashboard":
            import yaml
            url_path = tool_input.get("url_path", None)
            views = tool_input.get("views", [])
            old_yaml = ""
            new_yaml = ""
            snapshot_id = ""

            logger.info(f"📊 Updating dashboard: url_path='{url_path}', new_views={len(views)}")

            # Auto-snapshot: save current dashboard config before modifying
            try:
                snap_params = {}
                if url_path and url_path != "lovelace":
                    snap_params["url_path"] = url_path
                old_config = api.call_ha_websocket("lovelace/config", **snap_params)
                if old_config.get("success"):
                    old_result = old_config.get("result", {})
                    old_yaml = yaml.dump({"views": old_result.get("views", [])}, default_flow_style=False, allow_unicode=True)

                    # Create a restoreable snapshot (stored in SNAPSHOTS_DIR with .meta)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_url = (url_path or "lovelace").replace("/", "__").replace("\\", "__")
                    snapshot_id = f"{timestamp}_dashboard__{safe_url}"
                    snapshot_path = os.path.join(api.SNAPSHOTS_DIR, snapshot_id)
                    os.makedirs(api.SNAPSHOTS_DIR, exist_ok=True)
                    with open(snapshot_path, "w", encoding="utf-8") as sf:
                        json.dump({"url_path": url_path or "lovelace", "config": old_result}, sf, ensure_ascii=False)
                    with open(snapshot_path + ".meta", "w", encoding="utf-8") as mf:
                        json.dump({
                            "snapshot_id": snapshot_id,
                            "timestamp": timestamp,
                            "kind": "lovelace_dashboard",
                            "url_path": url_path or "lovelace",
                            # Keep original_file for list_snapshots compatibility
                            "original_file": f"lovelace:{url_path or 'lovelace'}",
                        }, mf, ensure_ascii=False)
                    logger.info(f"📊 Dashboard snapshot saved: {snapshot_id}")
            except Exception as e:
                logger.warning(f"⚠️ Could not snapshot dashboard before update: {e}")

            new_yaml = yaml.dump({"views": views}, default_flow_style=False, allow_unicode=True)

            params = {"config": {"views": views}}
            if url_path and url_path != "lovelace":
                params["url_path"] = url_path
            
            logger.info(f"📊 Saving dashboard config WS request: {list(params.keys())}")
            result = api.call_ha_websocket("lovelace/config/save", **params)
            logger.info(f"📊 Dashboard config save WS response: {result}")
            
            if result.get("success"):
                logger.info(f"✅ Dashboard '{url_path or 'lovelace'}' updated successfully")
                return json.dumps({
                    "status": "success",
                    "message": f"Dashboard '{url_path or 'lovelace'}' updated with {len(views)} view(s). A backup snapshot was saved.",
                    "views_count": len(views),
                    "old_yaml": old_yaml,
                    "new_yaml": new_yaml,
                    "snapshot": snapshot_id or "",
                    "IMPORTANT": "Show the user the before/after diff of the dashboard YAML."
                }, ensure_ascii=False, default=str)
            error_msg = result.get("error", {}).get("message", str(result))
            logger.error(f"❌ Failed to update dashboard: {error_msg}")
            return json.dumps({"error": f"Failed to update dashboard: {error_msg}"}, default=str)

        elif tool_name == "get_frontend_resources":
            result = api.call_ha_websocket("lovelace/resources")
            if result.get("success"):
                resources = result.get("result", [])
                summary = []
                for r in resources:
                    url = r.get("url", "")
                    # Extract card name from URL
                    name = url.split("/")[-1].split(".")[0].split("?")[0] if url else ""
                    summary.append({
                        "id": r.get("id"),
                        "url": url,
                        "type": r.get("type", "module"),
                        "name": name
                    })
                # Check for common custom cards
                all_urls = " ".join([r.get("url", "") for r in resources]).lower()
                detected = []
                for card_name in ["card-mod", "bubble-card", "mushroom", "mini-graph", "mini-media-player",
                                  "button-card", "layout-card", "stack-in-card", "slider-entity-row",
                                  "auto-entities", "decluttering-card", "apexcharts-card", "swipe-card",
                                  "tabbed-card", "vertical-stack-in-card", "atomic-calendar"]:
                    if card_name in all_urls:
                        detected.append(card_name)
                return json.dumps({"resources": summary, "count": len(summary),
                                   "detected_custom_cards": detected}, ensure_ascii=False, default=str)
            error_msg = result.get("error", {}).get("message", str(result))
            return json.dumps({"error": f"Failed to get resources: {error_msg}"}, default=str)

        # ===== CONFIG FILE OPERATIONS =====
        elif tool_name == "read_config_file":
            filename = tool_input.get("filename", "")
            # Security: prevent path traversal
            if ".." in filename or filename.startswith("/"):
                return json.dumps({"error": "Invalid filename. Use relative paths only (e.g. 'configuration.yaml')."})
            filepath = os.path.join(api.HA_CONFIG_DIR, filename)
            if not os.path.isfile(filepath):
                return json.dumps({"error": f"File '{filename}' not found in HA config directory."})
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                # Truncate very large files
                if len(content) > 15000:
                    content = content[:15000] + f"\n\n... [TRUNCATED - file is {len(content)} chars total]"
                return json.dumps({"filename": filename, "content": content,
                                   "size": os.path.getsize(filepath)}, ensure_ascii=False, default=str)
            except Exception as e:
                return json.dumps({"error": f"Failed to read '{filename}': {str(e)}"})

        elif tool_name == "write_config_file":
            filename = tool_input.get("filename", "")
            content = tool_input.get("content", "")
            if ".." in filename or filename.startswith("/"):
                return json.dumps({"error": "Invalid filename. Use relative paths only."})
            if not filename:
                return json.dumps({"error": "filename is required."})
            filepath = os.path.join(api.HA_CONFIG_DIR, filename)
            # Read existing content before overwriting (used for diff display)
            old_content = ""
            if os.path.isfile(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        old_content = f.read()
                except Exception:
                    pass
            # Auto-create snapshot before writing
            snapshot = api.create_snapshot(filename)
            try:
                # Create parent directories if needed
                os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else filepath, exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                msg = f"File '{filename}' saved successfully."
                if snapshot.get("snapshot_id"):
                    msg += f" Backup snapshot created: {snapshot['snapshot_id']}"
                return json.dumps({"status": "success", "message": msg, "snapshot": snapshot,
                                   "old_yaml": old_content, "new_yaml": content,
                                   "tip": "Call check_config to validate the configuration."}, ensure_ascii=False, default=str)
            except Exception as e:
                return json.dumps({"error": f"Failed to write '{filename}': {str(e)}", "snapshot": snapshot})

        elif tool_name == "check_config":
            try:
                ha_token = api.get_ha_token()
                resp = requests.post(
                    f"{api.HA_URL}/api/config/core/check_config",
                    headers={"Authorization": f"Bearer {ha_token}", "Content-Type": "application/json"},
                    timeout=30
                )
                result = resp.json()
                errors = result.get("errors", None)
                valid = result.get("result", "") == "valid"
                if valid:
                    return json.dumps({"status": "valid", "message": "Configuration is valid! You can reload or restart HA."}, ensure_ascii=False)
                return json.dumps({"status": "invalid", "errors": errors,
                                   "message": "Configuration has errors! Fix them or restore from snapshot."}, ensure_ascii=False, default=str)
            except Exception as e:
                return json.dumps({"error": f"Config check failed: {str(e)}"})

        elif tool_name == "list_config_files":
            subpath = tool_input.get("path", "")
            logger.info(f"list_config_files called: subpath='{subpath}', ENABLE_FILE_ACCESS={api.ENABLE_FILE_ACCESS}")
            if ".." in subpath:
                return json.dumps({"error": "Invalid path."})
            dirpath = os.path.join(api.HA_CONFIG_DIR, subpath) if subpath else api.HA_CONFIG_DIR
            logger.info(f"list_config_files: checking directory '{dirpath}'")
            if not os.path.isdir(dirpath):
                logger.error(f"list_config_files: directory not found: '{dirpath}'")
                return json.dumps({"error": f"Directory '{subpath}' not found."})
            entries = []
            try:
                for entry in sorted(os.listdir(dirpath)):
                    full = os.path.join(dirpath, entry)
                    rel = os.path.join(subpath, entry) if subpath else entry
                    if os.path.isdir(full):
                        entries.append({"name": entry, "type": "directory", "path": rel})
                    else:
                        entries.append({"name": entry, "type": "file", "path": rel,
                                       "size": os.path.getsize(full)})
                # Filter out hidden/system and very large dirs
                entries = [e for e in entries if not e["name"].startswith(".")][:100]
                return json.dumps({"path": subpath or "/", "entries": entries,
                                   "count": len(entries)}, ensure_ascii=False, default=str)
            except Exception as e:
                return json.dumps({"error": f"Failed to list '{subpath}': {str(e)}"})

        # ===== SNAPSHOT MANAGEMENT =====
        elif tool_name == "list_snapshots":
            if not os.path.isdir(api.SNAPSHOTS_DIR):
                return json.dumps({"snapshots": [], "count": 0})
            snapshots = []
            for f in sorted(os.listdir(api.SNAPSHOTS_DIR)):
                if f.endswith(".meta"):
                    continue
                meta_path = os.path.join(api.SNAPSHOTS_DIR, f + ".meta")
                if os.path.isfile(meta_path):
                    with open(meta_path, "r") as mf:
                        meta = json.load(mf)
                    snapshots.append(meta)
                else:
                    snapshots.append({"snapshot_id": f, "original_file": f.split("_", 2)[-1].replace("__", "/")})
            return json.dumps({"snapshots": snapshots, "count": len(snapshots)}, ensure_ascii=False, default=str)

        elif tool_name == "restore_snapshot":
            snapshot_id = tool_input.get("snapshot_id", "")
            reload_after = tool_input.get("reload", True)
            snapshot_id = (snapshot_id or "").strip()
            if not snapshot_id:
                return json.dumps({"error": "snapshot_id is required."}, ensure_ascii=False)
            if snapshot_id != os.path.basename(snapshot_id) or ".." in snapshot_id or "/" in snapshot_id or "\\" in snapshot_id:
                return json.dumps({"error": "Invalid snapshot_id."}, ensure_ascii=False)
            snapshot_path = os.path.join(api.SNAPSHOTS_DIR, snapshot_id)
            meta_path = snapshot_path + ".meta"
            if not os.path.isfile(snapshot_path):
                return json.dumps({"error": f"Snapshot '{snapshot_id}' not found. Use list_snapshots."})

            meta = {}
            if os.path.isfile(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as mf:
                        meta = json.load(mf) or {}
                except Exception:
                    meta = {}

            kind = meta.get("kind") or "file"

            # --- Dashboard snapshots (lovelace) ---
            if kind == "lovelace_dashboard":
                try:
                    with open(snapshot_path, "r", encoding="utf-8") as sf:
                        snap = json.load(sf) or {}
                except Exception as e:
                    return json.dumps({"error": f"Invalid dashboard snapshot content: {e}"}, ensure_ascii=False)

                url_path = snap.get("url_path") or meta.get("url_path") or "lovelace"
                config_to_restore = snap.get("config")
                if not isinstance(config_to_restore, dict):
                    return json.dumps({"error": "Dashboard snapshot has no valid config."}, ensure_ascii=False)

                # Snapshot current state before overwriting
                try:
                    snap_params = {}
                    if url_path and url_path != "lovelace":
                        snap_params["url_path"] = url_path
                    current = api.call_ha_websocket("lovelace/config", **snap_params)
                    if current.get("success"):
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        safe_url = (url_path or "lovelace").replace("/", "__").replace("\\", "__")
                        pre_snapshot_id = f"{timestamp}_dashboard__{safe_url}"
                        pre_snapshot_path = os.path.join(api.SNAPSHOTS_DIR, pre_snapshot_id)
                        os.makedirs(api.SNAPSHOTS_DIR, exist_ok=True)
                        with open(pre_snapshot_path, "w", encoding="utf-8") as psf:
                            json.dump({"url_path": url_path or "lovelace", "config": current.get("result", {})}, psf, ensure_ascii=False)
                        with open(pre_snapshot_path + ".meta", "w", encoding="utf-8") as pmf:
                            json.dump({
                                "snapshot_id": pre_snapshot_id,
                                "timestamp": timestamp,
                                "kind": "lovelace_dashboard",
                                "url_path": url_path or "lovelace",
                                "original_file": f"lovelace:{url_path or 'lovelace'}",
                            }, pmf, ensure_ascii=False)
                except Exception:
                    pass

                params = {"config": config_to_restore}
                if url_path and url_path != "lovelace":
                    params["url_path"] = url_path
                result = api.call_ha_websocket("lovelace/config/save", **params)
                if result.get("success"):
                    return json.dumps({
                        "status": "success",
                        "message": f"Dashboard '{url_path or 'lovelace'}' restored from snapshot '{snapshot_id}'.",
                        "restored_file": f"lovelace:{url_path or 'lovelace'}",
                        "reload_result": result,
                    }, ensure_ascii=False, default=str)
                error_msg = result.get("error", {}).get("message", str(result))
                return json.dumps({"error": f"Failed to restore dashboard snapshot: {error_msg}"}, ensure_ascii=False, default=str)

            # --- File snapshots (default) ---
            original_file = meta.get("original_file", "") if isinstance(meta, dict) else ""
            if not original_file:
                # Try to reconstruct from snapshot name
                parts = snapshot_id.split("_", 2)
                if len(parts) >= 3:
                    original_file = parts[2].replace("__", "/")
            if not original_file:
                return json.dumps({"error": "Cannot determine original file from snapshot."}, ensure_ascii=False)

            # Security: prevent path traversal
            if ".." in original_file or original_file.startswith("/") or original_file.startswith("\\"):
                return json.dumps({"error": "Invalid original file in snapshot metadata."}, ensure_ascii=False)

            # Create a snapshot of current state before restoring
            api.create_snapshot(original_file)

            # Restore file
            import shutil
            dest = os.path.join(api.HA_CONFIG_DIR, original_file)
            os.makedirs(os.path.dirname(dest) if os.path.dirname(dest) else api.HA_CONFIG_DIR, exist_ok=True)
            shutil.copy2(snapshot_path, dest)

            reload_result = None
            if reload_after:
                try:
                    lower = original_file.lower()
                    if "automation" in lower or lower.endswith("automations.yaml"):
                        reload_result = api.call_ha_api("POST", "services/automation/reload", {})
                    elif "script" in lower or lower.endswith("scripts.yaml"):
                        reload_result = api.call_ha_api("POST", "services/script/reload", {})
                    elif "lovelace" in lower or "dashboard" in lower or lower.endswith("ui-lovelace.yaml"):
                        reload_result = api.call_ha_api("POST", "services/lovelace/reload", {})
                    elif "sensor" in lower or "template" in lower or "binary_sensor" in lower:
                        reload_result = api.call_ha_api("POST", "services/homeassistant/reload_all", {})
                    else:
                        # Generic reload for any other YAML config file
                        reload_result = api.call_ha_api("POST", "services/homeassistant/reload_all", {})
                except Exception as e:
                    reload_result = {"error": str(e)}

            return json.dumps({
                "status": "success",
                "message": f"Restored '{original_file}' from snapshot '{snapshot_id}'. A new snapshot of the overwritten file was created.",
                "restored_file": original_file,
                "reload_result": reload_result,
            }, ensure_ascii=False, default=str)

        elif tool_name == "manage_helpers":
            import yaml
            helper_type = tool_input.get("helper_type", "")
            action = tool_input.get("action", "list")
            helper_id = tool_input.get("helper_id", "")

            valid_types = ("input_boolean", "input_number", "input_select", "input_text", "input_datetime")
            if helper_type not in valid_types:
                return json.dumps({
                    "error": f"Invalid helper_type: {helper_type}. Must be one of: {', '.join(valid_types)}."
                }, ensure_ascii=False)

            if action == "list":
                states = api.get_all_states()
                helpers = [
                    {
                        "entity_id": s.get("entity_id"),
                        "state": s.get("state"),
                        "friendly_name": s.get("attributes", {}).get("friendly_name", ""),
                    }
                    for s in states
                    if s.get("entity_id", "").startswith(f"{helper_type}.")
                ]
                return json.dumps(
                    {"helpers": helpers, "count": len(helpers), "type": helper_type},
                    ensure_ascii=False, default=str,
                )

            if not helper_id:
                return json.dumps({"error": "helper_id is required for create/update/delete."}, ensure_ascii=False)

            # Clean the helper_id (remove domain prefix if provided)
            if helper_id.startswith(f"{helper_type}."):
                helper_id = helper_id[len(helper_type) + 1:]

            if action in ("create", "update"):
                config = {}
                if tool_input.get("name"):
                    config["name"] = tool_input["name"]
                if tool_input.get("icon"):
                    config["icon"] = tool_input["icon"]
                if tool_input.get("initial") is not None:
                    config["initial"] = tool_input["initial"]

                # Type-specific fields
                if helper_type == "input_number":
                    if tool_input.get("min") is not None:
                        config["min"] = tool_input["min"]
                    if tool_input.get("max") is not None:
                        config["max"] = tool_input["max"]
                    if tool_input.get("step") is not None:
                        config["step"] = tool_input["step"]
                    if tool_input.get("unit_of_measurement"):
                        config["unit_of_measurement"] = tool_input["unit_of_measurement"]
                    if tool_input.get("mode"):
                        config["mode"] = tool_input["mode"]
                    # Defaults for required fields
                    if "min" not in config:
                        config["min"] = 0
                    if "max" not in config:
                        config["max"] = 100
                elif helper_type == "input_select":
                    if tool_input.get("options"):
                        config["options"] = tool_input["options"]
                elif helper_type == "input_datetime":
                    if tool_input.get("has_date") is not None:
                        config["has_date"] = tool_input["has_date"]
                    if tool_input.get("has_time") is not None:
                        config["has_time"] = tool_input["has_time"]
                elif helper_type == "input_text":
                    if tool_input.get("min_length") is not None:
                        config["min"] = tool_input["min_length"]
                    if tool_input.get("max_length") is not None:
                        config["max"] = tool_input["max_length"]
                    if tool_input.get("pattern"):
                        config["pattern"] = tool_input["pattern"]

                result = api.call_ha_api("POST", f"config/{helper_type}/config/{helper_id}", config)
                if isinstance(result, dict) and "error" not in result:
                    created_yaml = yaml.dump(config, default_flow_style=False, allow_unicode=True, sort_keys=False)
                    verb = "created" if action == "create" else "updated"
                    return json.dumps({
                        "status": "success",
                        "message": f"Helper {helper_type}.{helper_id} {verb}.",
                        "entity_id": f"{helper_type}.{helper_id}",
                        "yaml": created_yaml,
                        "IMPORTANT": f"Show the user the YAML code for the helper you {verb}."
                    }, ensure_ascii=False, default=str)
                return json.dumps({"status": "error", "result": result}, ensure_ascii=False, default=str)

            elif action == "delete":
                result = api.call_ha_api("DELETE", f"config/{helper_type}/config/{helper_id}")
                if result is None or (isinstance(result, dict) and "error" not in result):
                    return json.dumps({
                        "status": "success",
                        "message": f"Helper {helper_type}.{helper_id} deleted."
                    }, ensure_ascii=False, default=str)
                return json.dumps({"status": "error", "result": result}, ensure_ascii=False, default=str)

            return json.dumps({"error": f"Unknown action: {action}"}, ensure_ascii=False)

        elif tool_name == "get_repairs":
            include_ignored = tool_input.get("include_ignored", False)
            repairs_result = api.call_ha_websocket("repairs/list_issues")
            resolution_result = api.call_ha_websocket("resolution/info")

            # Parse repair issues
            issues = []
            if repairs_result.get("success"):
                raw_issues = repairs_result.get("result", {}).get("issues", [])
                for issue in raw_issues:
                    if not include_ignored and issue.get("ignored", False):
                        continue
                    issues.append({
                        "issue_id": issue.get("issue_id"),
                        "domain": issue.get("domain"),
                        "severity": issue.get("severity"),
                        "is_fixable": issue.get("is_fixable", False),
                        "ignored": issue.get("ignored", False),
                        "created": issue.get("created"),
                        "translation_key": issue.get("translation_key"),
                        "translation_placeholders": issue.get("translation_placeholders"),
                        "learn_more_url": issue.get("learn_more_url"),
                    })

            # Parse resolution/health info
            health = {}
            suggestions = []
            if resolution_result.get("success"):
                res_data = resolution_result.get("result", {})
                health = {
                    "unsupported": res_data.get("unsupported", []),
                    "unhealthy": res_data.get("unhealthy", []),
                }
                for sug in res_data.get("suggestions", []):
                    suggestions.append({
                        "uuid": sug.get("uuid"),
                        "type": sug.get("type"),
                        "context": sug.get("context"),
                        "reference": sug.get("reference"),
                    })

            return json.dumps({
                "issues_count": len(issues),
                "issues": issues,
                "suggestions": suggestions,
                "health": health,
            }, ensure_ascii=False, default=str)

        elif tool_name == "dismiss_repair":
            issue_id = tool_input.get("issue_id", "")
            domain = tool_input.get("domain", "")
            if not issue_id or not domain:
                return json.dumps({"error": "Both issue_id and domain are required"})
            result = api.call_ha_websocket("repairs/ignore_issue",
                                           issue_id=issue_id, domain=domain)
            if result.get("success"):
                return json.dumps({
                    "status": "success",
                    "message": f"Issue '{issue_id}' from '{domain}' dismissed."
                }, ensure_ascii=False, default=str)
            error_msg = result.get("error", {})
            if isinstance(error_msg, dict):
                error_msg = error_msg.get("message", str(error_msg))
            return json.dumps({"error": f"Failed to dismiss: {error_msg}"}, default=str)

        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    except Exception as e:
        logger.error(f"Tool error ({tool_name}): {e}")
        return json.dumps({"error": str(e)})


# ---- System prompt ----

SYSTEM_PROMPT = """You are an AI assistant integrated into Home Assistant. You help users manage their smart home.

You can:
1. **Query entities** - See device states (lights, sensors, switches, climate, covers, etc.)
2. **Control devices** - Turn on/off lights, switches, set temperatures, etc.
3. **Search entities** - Find specific devices or integrations by keyword
4. **Entity history** - Check past values and trends ("what was the temperature yesterday?")
5. **Advanced statistics** - Get min/max/mean/sum statistics for sensors over time periods
6. **Scenes & scripts** - List, activate scenes, run scripts, create new scripts
7. **Areas/rooms** - List, create, rename, delete areas. Assign entities to areas
8. **Devices & entity registry** - List devices, rename entities, enable/disable entities, assign to areas
9. **Create automations** - Build new automations with triggers, conditions, and actions
10. **List & trigger automations** - See and run existing automations
11. **Delete automations/scripts/dashboards** - Remove unwanted configurations
12. **Notifications** - Send persistent notifications or push to mobile devices
13. **Discover services & events** - See all available HA services and event types
14. **Create & modify dashboards** - Create NEW dashboards or modify EXISTING ones with any card type
15. **Check custom cards** - Verify which HACS custom cards are installed (card-mod, bubble-card, mushroom, etc.)
16. **Shopping list** - View, add, and complete shopping list items
17. **Backup** - Create full Home Assistant backups
18. **Browse media** - Browse media content from players (music, photos, etc.)
19. **Read/write config files** - Read and edit configuration.yaml, automations.yaml, YAML dashboards, packages, etc.
20. **Validate config** - Check HA configuration for errors after editing
21. **Snapshots** - Automatic backups before every file change, with restore capability

## Configuration File Management
- Use **list_config_files** to explore the HA config directory
- Use **read_config_file** to read any YAML/config file (including YAML-mode dashboards like ui-lovelace.yaml)
- Use **write_config_file** to modify files (auto-creates a snapshot before writing)
- Use **check_config** to validate after editing configuration.yaml
- Use **list_snapshots** and **restore_snapshot** to manage/restore backups

IMPORTANT for config editing:
1. ALWAYS read the file first with read_config_file
2. Make targeted changes (don't rewrite everything unless necessary)
3. After writing configuration.yaml, ALWAYS call check_config to validate
4. If validation fails, use restore_snapshot to undo changes
5. Snapshots are created automatically before every write - inform the user about this safety net

## Dashboard Management
- Use **get_dashboards** to list all dashboards
- Use **get_dashboard_config** to read an existing dashboard's full configuration
- Use **update_dashboard** to modify an existing dashboard (replaces all views)
- Use **create_dashboard** to create a brand new dashboard
- Use **get_frontend_resources** to check which custom cards (HACS) are installed
- Use **delete_dashboard** to remove a dashboard

## Custom HTML Dashboards
- Use **create_html_dashboard** to create a custom HTML dashboard.
- For FULL customization, provide the full HTML in the tool input field **html** and use placeholder **__ENTITIES_JSON__** to bind exactly the validated entities.
- NEVER show HTML code in the chat. The dashboard is saved to a file — just confirm the URL.

IMPORTANT: When modifying a dashboard, ALWAYS:
1. First call get_dashboard_config to read the current config
2. Modify the views/cards as needed
3. Save with update_dashboard passing the complete views array

### ENTITY RULE (CRITICAL)
- NEVER invent or guess entity IDs. ALWAYS use search_entities first to find REAL entity IDs.
- Only use entity IDs that appear in the search results.
- If a search returns no results for a category, DO NOT include cards for that category.
- Example: if search_entities("light") returns only light.soggiorno and light.camera, use ONLY those two.

### Dashboard Layout (CRITICAL - never put cards in a flat vertical list!)
Always create visually appealing layouts using grids and stacks:

**Use grid cards to arrange items in columns:**
{"type": "grid", "columns": 2, "square": false, "cards": [card1, card2, card3, card4]}

**Use horizontal-stack for side-by-side cards:**
{"type": "horizontal-stack", "cards": [card1, card2]}

**Use vertical-stack to group related cards:**
{"type": "vertical-stack", "cards": [headerCard, contentCard]}

CRITICAL - Dashboard Creation Handling:
- ALWAYS attempt create_dashboard tool first - IT MUST WORK
- If tool succeeds: Dashboard is created, user sees it in sidebar
- If tool fails: DO NOT tell user "manually edit files"
- On failure: Generate dashboard YAML and provide it in a clean code block
- Message: "I've prepared your dashboard. You can add this to your Lovelace config."

**Best layout practices:**
- Use a grid with 2-3 columns for button/entity cards
- Group related sensors in horizontal-stack
- Use vertical-stack with a markdown header + grid of cards for sections
- Example section structure:
  {"type": "vertical-stack", "cards": [
    {"type": "markdown", "content": "## \U0001f4a1 Luci"},
    {"type": "grid", "columns": 3, "square": false, "cards": [
      {"type": "button", "entity": "light.soggiorno", "name": "Soggiorno", "icon": "mdi:sofa", "show_state": true},
      {"type": "button", "entity": "light.camera", "name": "Camera", "icon": "mdi:bed", "show_state": true}
    ]}
  ]}

### Standard Lovelace card types:
- entities: {"type": "entities", "title": "Lights", "entities": ["light.living_room"]}
- gauge: {"type": "gauge", "entity": "sensor.temperature"}
- history-graph: {"type": "history-graph", "entities": [{"entity": "sensor.temp"}], "hours_to_show": 24}
- thermostat: {"type": "thermostat", "entity": "climate.living_room"}
- button: {"type": "button", "entity": "switch.outlet", "name": "Toggle"}
- markdown: {"type": "markdown", "content": "# Title"}

### Custom cards (check availability with get_frontend_resources first!):

**card-mod** - Style any card with CSS:
{"type": "entities", "entities": ["light.room"], "card_mod": {"style": "ha-card { background: rgba(0,0,0,0.3); border-radius: 16px; }"}}

**bubble-card** - Modern UI cards:
{"type": "custom:bubble-card", "card_type": "button", "entity": "light.room", "name": "Light", "icon": "mdi:lightbulb", "button_type": "switch"}
{"type": "custom:bubble-card", "card_type": "pop-up", "hash": "#room", "name": "Living Room", "icon": "mdi:sofa"}
{"type": "custom:bubble-card", "card_type": "separator", "name": "Section", "icon": "mdi:home"}

**mushroom cards**:
{"type": "custom:mushroom-entity-card", "entity": "light.room", "fill_container": true}
{"type": "custom:mushroom-climate-card", "entity": "climate.room"}

**button-card** - Highly customizable buttons:
{"type": "custom:button-card", "entity": "light.room", "name": "Light", "icon": "mdi:lightbulb", "show_state": true,
 "styles": {"card": [{"background-color": "rgba(0,0,0,0.3)"}]}}

**mini-graph-card** - Beautiful sensor graphs:
{"type": "custom:mini-graph-card", "entities": ["sensor.temperature"], "hours_to_show": 24, "line_color": "#e74c3c"}

Before using any custom: card type, ALWAYS call get_frontend_resources to verify it's installed.
If the user wants a custom card that is not installed, inform them and suggest installing it via HACS.

## Automations
When creating automations, use proper Home Assistant formats:
- State trigger: {"platform": "state", "entity_id": "binary_sensor.motion", "to": "on"}
- Time trigger: {"platform": "time", "at": "07:00:00"}
- Sun trigger: {"platform": "sun", "event": "sunset", "offset": "-00:30:00"}
- Service action: {"service": "light.turn_on", "target": {"entity_id": "light.living_room"}, "data": {"brightness": 255}}

**CRITICAL - Entity Selection:**
BEFORE creating an automation, script, or dashboard:
1. ALWAYS use search_entities to find the correct entity_id (search for "light", "switch", "sensor", etc.)
2. If the user says "luce" (light) or mentions a device, search BOTH "light" AND "switch" domains
3. Present found entities to the user and ASK which one to use if there are multiple matches
4. NEVER guess or invent entity IDs - only use entities that actually exist

**CRITICAL - Show YAML After Creation:**
After CREATING or MODIFYING an automation, script, or dashboard, you MUST immediately show the YAML code to the user in your response. This is MANDATORY - never skip this step.

When managing areas/rooms, use manage_areas. To assign an entity to a room, use manage_entity with the area_id.
For advanced sensor analytics (averages, peaks, trends), use get_statistics instead of get_history.
When a user asks about specific devices or addons, use search_entities to find them by keyword.
Use get_history for recent state changes, get_statistics for aggregated data over longer periods.
Use get_areas when the user refers to rooms.

**CRITICAL - Delete/Modify Confirmation (ALWAYS REQUIRED):**
BEFORE deleting or modifying ANY automation, script, or dashboard:
1. **List all options**: Use get_automations, get_scripts, or get_dashboards to see all available items
2. **Identify with certainty**: Match by exact alias/name - if the user says "remove this one", look at the conversation context to identify which one was just created/discussed
3. **Show what you'll delete/modify**: Display the name/alias of the item you identified
4. **ASK for confirmation**: Ask the user to confirm the deletion (e.g. "Do you want to delete automation 'Name'? Confirm?")
5. **Wait for user response**: NEVER proceed without explicit confirmation from the user
6. **NEVER delete the wrong item**: If there's ANY doubt, ask the user to clarify which item they mean

This is a DESTRUCTIVE operation - mistakes can delete important automations. ALWAYS confirm first.
To delete resources (after confirmation), use delete_automation, delete_script, or delete_dashboard.

## CRITICAL BEHAVIOR RULES
- When the user asks you to CREATE or MODIFY something (dashboard, automation, script, config), DO IT IMMEDIATELY.
- NEVER just describe what you plan to do. Execute ALL necessary tool calls in sequence and complete the task fully.
- Only respond with the final result AFTER the task is complete.
- If a task requires multiple tool calls, keep calling tools until the task is done. Do not stop halfway to explain your plan.

## SHOW YOUR CHANGES (CRITICAL)
When you modify an automation, script, configuration, or any YAML file, ALWAYS show the user exactly what you changed.
In your final response, include:
1. A brief summary of what you did
2. The relevant YAML section BEFORE (old) and AFTER (new) using code blocks, for example:

**Prima (old):**
```yaml
condition: []
```

**Dopo (new):**
```yaml
condition:
  - condition: not
    conditions:
      - condition: template
        value_template: "{{ 'Inter' in trigger.to_state.state }}"
```

This helps the user understand and verify the changes. Keep the diff focused on what changed, not the entire file.

## EFFICIENCY RULES (ABSOLUTELY CRITICAL - MAXIMUM 1-2 tool calls per task)
- EVERY extra tool call wastes 5-20 seconds. Users WILL experience errors and timeouts with too many calls.
- When context is pre-loaded in the user message, ALL that data is already available. NEVER re-fetch it.
- PRE-LOADED DATA = do NOT call: get_automations, get_scripts, get_dashboards, read_config_file, list_config_files, search_entities, get_entity_state for data already present.
- For modifying automations: call update_automation ONCE with automation_id + changes. That's IT. ONE call total.
- For modifying scripts: call update_script ONCE with script_id + changes. That's IT. ONE call total.
- After update_automation or update_script succeeds: STOP. Show the diff to the user. Do NOT call any verification tools.
- NEVER verify changes by calling get_automations or read_config_file after an update - the tool already returns old/new YAML.
- The MAXIMUM number of tool calls for ANY modification task is 2. If you've made 2 calls, you MUST respond.
- For other config editing: read_config_file \u2192 write_config_file \u2192 check_config (3 calls max).

Always respond in the same language the user uses.
Be concise but informative."""


# Compact prompt for providers with small context (GitHub Models free tier: 8k tokens)
def get_compact_prompt():
    """Generate compact prompt with language-specific instructions."""
    lang_instruction = api.get_lang_text("respond_instruction")
    show_yaml_rule = api.get_lang_text("show_yaml_rule")
    confirm_entity_rule = api.get_lang_text("confirm_entity_rule")
    confirm_delete_rule = api.get_lang_text("confirm_delete_rule")
    example_vs_create_rule = api.get_lang_text("example_vs_create_rule")

    agent_instr = getattr(api, "AGENT_INSTRUCTIONS", "") or ""
    agent_block = f"\nAssistant persona (user-configured):\n{agent_instr.strip()}\n" if agent_instr.strip() else ""

    return f"""You are a Home Assistant AI assistant. Control devices, query states, search entities, check history, create automations, create dashboards.{agent_block}
{example_vs_create_rule}
{confirm_entity_rule}
{show_yaml_rule}
{confirm_delete_rule}
When users ask about specific devices, use search_entities. Use get_history for past data.
To create a dashboard, ALWAYS first search entities to find real entity IDs, then use create_dashboard with proper Lovelace cards.
To create a CUSTOM HTML dashboard: use __ENTITIES_JSON__ placeholder in HTML. Copy ALL entity_ids from ## ENTITÀ TROVATE into entities[]. In JS iterate ENTITIES array — NEVER filter /api/states by device_class.
{lang_instruction} Be concise."""


def get_compact_prompt_with_files():
    """Generate compact prompt with files support and language-specific instructions."""
    before_text = api.get_lang_text("before")
    after_text = api.get_lang_text("after")
    lang_instruction = api.get_lang_text("respond_instruction")
    show_yaml_rule = api.get_lang_text("show_yaml_rule")
    confirm_entity_rule = api.get_lang_text("confirm_entity_rule")
    confirm_delete_rule = api.get_lang_text("confirm_delete_rule")
    example_vs_create_rule = api.get_lang_text("example_vs_create_rule")

    agent_instr = getattr(api, "AGENT_INSTRUCTIONS", "") or ""
    agent_block = f"\nAssistant persona (user-configured):\n{agent_instr.strip()}\n" if agent_instr.strip() else ""

    return f"""You are a Home Assistant AI assistant. Control devices, query states, create automations/dashboards, and READ CONFIG FILES.{agent_block}
Use list_config_files to explore folders (e.g., 'lovelace', 'yaml'). Use read_config_file to read YAML/JSON files.
Use get_automations, get_scripts, get_dashboards to list existing configs.
When users ask about files/folders, use list_config_files first to show what's available.

{example_vs_create_rule}
{show_yaml_rule}
{confirm_entity_rule}
{confirm_delete_rule}

CRITICAL - Show changes clearly:
When you MODIFY configs, show ONLY the changed sections in diff format:
**{before_text}:**
```yaml
- condition: []
```
**{after_text}:**
```yaml
+ condition:
+   - condition: state
+     entity_id: light.room
+     state: "on"
```

For NEW creations, show the complete YAML.

For CUSTOM HTML dashboards: use __ENTITIES_JSON__ placeholder, copy ALL entity_ids from ## ENTITÀ TROVATE into entities[], iterate ENTITIES array in JS — NEVER filter /api/states by device_class.

{lang_instruction} Be concise."""


# Compact tool definitions for low-token providers
HA_TOOLS_COMPACT = [
    {
        "name": "get_entities",
        "description": "Get HA entity states, optionally filtered by domain.",
        "parameters": {"type": "object", "properties": {"domain": {"type": "string"}}, "required": []}
    },
    {
        "name": "call_service",
        "description": "Call HA service (e.g. light.turn_on, switch.toggle, climate.set_temperature, scene.turn_on, script.turn_on).",
        "parameters": {"type": "object", "properties": {
            "domain": {"type": "string"}, "service": {"type": "string"},
            "entity_id": {"type": "string"},
            "data": {"type": "object"}
        }, "required": ["domain", "service"]}
    },
    {
        "name": "search_entities",
        "description": "Search entities by keyword in entity_id or friendly_name.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
    },
    {
        "name": "get_history",
        "description": "Get state history of an entity. Params: entity_id (required), hours (default 24).",
        "parameters": {"type": "object", "properties": {
            "entity_id": {"type": "string"}, "hours": {"type": "number"}
        }, "required": ["entity_id"]}
    },
    {
        "name": "create_automation",
        "description": "Create HA automation with alias, trigger, action.",
        "parameters": {"type": "object", "properties": {
            "alias": {"type": "string"}, "trigger": {"type": "array", "items": {"type": "object"}},
            "action": {"type": "array", "items": {"type": "object"}}
        }, "required": ["alias", "trigger", "action"]}
    },
    {
        "name": "create_dashboard",
        "description": "Create a NEW Lovelace dashboard. Params: title, url_path (slug), views (array of {title, cards[]}). Card types: entities, gauge, history-graph, thermostat, button.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"}, "url_path": {"type": "string"},
            "icon": {"type": "string"},
            "views": {"type": "array", "items": {"type": "object"}}
        }, "required": ["title", "url_path", "views"]}
    }
]

# Extended tool set for GitHub with file access enabled
# Balance between COMPACT (6 tools) and FULL (40 tools) to stay under 8k token limit
HA_TOOLS_EXTENDED = HA_TOOLS_COMPACT + [
    {
        "name": "list_config_files",
        "description": "List files and directories in Home Assistant config folder. Use empty path for root, or 'lovelace', 'yaml', etc.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []}
    },
    {
        "name": "read_config_file",
        "description": "Read content of a config file (YAML, JSON, etc). Returns file content as text.",
        "parameters": {"type": "object", "properties": {"filename": {"type": "string"}}, "required": ["filename"]}
    },
    {
        "name": "get_automations",
        "description": "Find existing automations. Optionally pass a query to search by alias/entity. Returns a compact list of matches.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50}
            },
            "required": []
        }
    },
    {
        "name": "get_scripts",
        "description": "Get list of all scripts with id, name, and full config.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_dashboards",
        "description": "Get list of all Lovelace dashboards.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_areas",
        "description": "Get list of areas/rooms in Home Assistant.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
]


def get_system_prompt() -> str:
    """Get system prompt appropriate for current provider."""
    # If custom system prompt is set, use it directly
    if api.CUSTOM_SYSTEM_PROMPT is not None:
        return api.CUSTOM_SYSTEM_PROMPT

    agent_instr = getattr(api, "AGENT_INSTRUCTIONS", "") or ""
    agent_block = ""
    if agent_instr.strip():
        agent_block = (
            "## Assistant Persona (user-configured)\n"
            + agent_instr.strip()
            + "\n\n"
        )

    base_prompt = agent_block + """You are an AI assistant integrated into Home Assistant. You help users manage their smart home.

You can:
1. **Query entities** - See device states (lights, sensors, switches, climate, covers, etc.)
2. **Control devices** - Turn on/off lights, switches, set temperatures, etc.
3. **Search entities** - Find specific devices or integrations by keyword
4. **Entity history** - Check past values and trends ("what was the temperature yesterday?")
5. **Advanced statistics** - Get min/max/mean/sum statistics for sensors over time periods
6. **Scenes & scripts** - List, activate scenes, run scripts, create new scripts
7. **Areas/rooms** - List, create, rename, delete areas. Assign entities to areas
8. **Devices & entity registry** - List devices, rename entities, enable/disable entities, assign to areas
9. **Create automations** - Build new automations with triggers, conditions, and actions
10. **List & trigger automations** - See and run existing automations
11. **Delete automations/scripts/dashboards** - Remove unwanted configurations
12. **Notifications** - Send persistent notifications or push to mobile devices
13. **Discover services & events** - See all available HA services and event types
14. **Create & modify dashboards** - Create NEW dashboards or modify EXISTING ones with any card type
15. **Check custom cards** - Verify which HACS custom cards are installed (card-mod, bubble-card, mushroom, etc.)
16. **Shopping list** - View, add, and complete shopping list items
17. **Backup** - Create full Home Assistant backups
18. **Browse media** - Browse media content from players (music, photos, etc.)
19. **Read/write config files** - Read and edit configuration.yaml, automations.yaml, YAML dashboards, packages, etc.
20. **Validate config** - Check HA configuration for errors after editing
21. **Snapshots** - Automatic backups before every file change, with restore capability

## Configuration File Management
- Use **list_config_files** to explore the HA config directory
- Use **read_config_file** to read any YAML/config file (including YAML-mode dashboards like ui-lovelace.yaml)
- Use **write_config_file** to modify files (auto-creates a snapshot before writing)
- Use **check_config** to validate after editing configuration.yaml
- Use **list_snapshots** and **restore_snapshot** to manage/restore backups

IMPORTANT for config editing:
1. ALWAYS read the file first with read_config_file
2. Make targeted changes (don't rewrite everything unless necessary)
3. After writing configuration.yaml, ALWAYS call check_config to validate
4. If validation fails, use restore_snapshot to undo changes
5. Snapshots are created automatically before every write - inform the user about this safety net

## Dashboard Management
- Use **get_dashboards** to list all dashboards
- Use **get_dashboard_config** to read an existing dashboard's full configuration
- Use **update_dashboard** to modify an existing dashboard (replaces all views)
- Use **create_dashboard** to create a brand new dashboard
- Use **get_frontend_resources** to check which custom cards (HACS) are installed
- Use **delete_dashboard** to remove a dashboard

## HTML Dashboard Management
- Use **read_html_dashboard** to read the HTML source of an existing custom HTML dashboard
- Use **create_html_dashboard** to create or OVERWRITE an HTML dashboard (same name = overwrite)
- When the user asks to MODIFY an existing HTML dashboard, ALWAYS:
  1. First call **read_html_dashboard** with the dashboard name to get the current HTML
  2. Modify the HTML keeping the same style, colors, layout, and design
  3. Save with **create_html_dashboard** using the SAME name to overwrite

**CRITICAL — MINIMAL CHANGES RULE for HTML dashboards:**
- When the user asks to ADD something (e.g. "add temperature sensors"), ONLY add the new elements. Do NOT rewrite, restructure, rename, restyle, or remove ANY existing section/card/element.
- Copy the ENTIRE original HTML verbatim, then INSERT the new sections in the appropriate place using the same style/CSS classes.
- Do NOT change variable names, colors, fonts, layout order, section titles, or any other existing content.
- The output HTML must be a SUPERSET of the original — every original line must remain unchanged.

IMPORTANT: When modifying a dashboard, ALWAYS:
1. First call get_dashboard_config to read the current config
2. Modify the views/cards as needed
3. Save with update_dashboard passing the complete views array

### ENTITY RULE (CRITICAL)
- NEVER invent or guess entity IDs. ALWAYS use search_entities first to find REAL entity IDs.
- Only use entity IDs that appear in the search results.
- If a search returns no results for a category, DO NOT include cards for that category.
- Example: if search_entities("light") returns only light.soggiorno and light.camera, use ONLY those two.

### Dashboard Layout (CRITICAL - never put cards in a flat vertical list!)
Always create visually appealing layouts using grids and stacks:

**Use grid cards to arrange items in columns:**
{"type": "grid", "columns": 2, "square": false, "cards": [card1, card2, card3, card4]}

**Use horizontal-stack for side-by-side cards:**
{"type": "horizontal-stack", "cards": [card1, card2]}

**Use vertical-stack to group related cards:**
{"type": "vertical-stack", "cards": [headerCard, contentCard]}

## Response Format Rule (IMPORTANT)
- If your response is pure text or natural conversation (no code/config to show), respond ONLY with text. Do NOT add comments like "# (nessun YAML necessario)", "(no YAML needed)", or filler code blocks.
- Code blocks should ONLY appear when showing actual code, config, or YAML that the user needs to see or copy.
- Never add empty or comment-only code blocks to your responses.
- Keep text responses clean and focused on what the user asked.

    """

    if api.AI_PROVIDER == "github":
        # GitHub has 8k token limit - use minimal prompt with only includes mapping
        compact_prompt = get_compact_prompt_with_files() if api.ENABLE_FILE_ACCESS else get_compact_prompt()
        # Only include file mapping if file access is enabled, skip verbose config structure
        if api.ENABLE_FILE_ACCESS and api.CONFIG_INCLUDES:
            includes_compact = "Config files: " + ", ".join([f"{k}={v}" for k, v in list(api.CONFIG_INCLUDES.items())[:5]]) + "\n"
            return includes_compact + compact_prompt
        return compact_prompt
    # For other providers, add language instruction and critical rules to base prompt
    lang_instruction = api.get_lang_text("respond_instruction")
    show_yaml_rule = api.get_lang_text("show_yaml_rule")
    confirm_entity_rule = api.get_lang_text("confirm_entity_rule")
    confirm_delete_rule = api.get_lang_text("confirm_delete_rule")
    example_vs_create_rule = api.get_lang_text("example_vs_create_rule")
    return api.get_config_structure_section() + api.get_config_includes_text() + base_prompt + f"\n\n{example_vs_create_rule}\n{show_yaml_rule}\n{confirm_entity_rule}\n{confirm_delete_rule}\n\n{lang_instruction}"


def get_openai_tools_for_provider():
    """Get OpenAI-format tools appropriate for current provider."""
    if api.AI_PROVIDER == "github":
        # GitHub Models has 8k token limit - use extended set if file access enabled, otherwise compact
        tool_set = HA_TOOLS_EXTENDED if api.ENABLE_FILE_ACCESS else HA_TOOLS_COMPACT
        return [
            {"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}}
            for t in tool_set
        ]
    return get_openai_tools()
