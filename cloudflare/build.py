import json, base64, re, pathlib
here = pathlib.Path(__file__).parent
src = (here.parent / "site-schedule.html").read_text()

def R(a, b):
    global src
    assert src.count(a) == 1, a[:60]
    src = src.replace(a, b)

# --- storage: talk to the Worker's /api instead of the Claude artifact db
R('''function save(job){
  if(col){const {id,...body}=job;col.doc(id).set(JSON.parse(JSON.stringify(body))).catch(e=>setStatus("Couldn't save: "+(e&&e.message||"try again")))}
  else ls.set("ss.jobs",jobs);
}
function remove(id){
  jobs=jobs.filter(j=>j.id!==id);
  if(col)col.doc(id).delete().catch(()=>setStatus("Couldn't delete, try again"));else ls.set("ss.jobs",jobs);
  render();
}''', '''let pinAsked=false;
async function api(method,path,body){
  const h={"content-type":"application/json"};const pin=ls.get("ss.pin");if(pin)h["x-pin"]=pin;
  const r=await fetch("/api/"+path,{method,headers:h,body:body?JSON.stringify(body):undefined,cache:"no-store"});
  if(r.status===401){askPin();throw new Error("PIN needed")}
  if(!r.ok){let m="server error "+r.status;try{m=(await r.json()).error||m}catch(e){}throw new Error(m)}
  return r.status===204?null:r.json();
}
function save(job){
  ls.set("ss.jobs",jobs);
  const {id,...body}=job;
  api("PUT","jobs/"+encodeURIComponent(id),JSON.parse(JSON.stringify(body))).then(()=>setStatus("Saved")).catch(e=>setStatus("Couldn't save: "+e.message));
}
function remove(id){
  jobs=jobs.filter(j=>j.id!==id);ls.set("ss.jobs",jobs);
  api("DELETE","jobs/"+encodeURIComponent(id)).then(()=>setStatus("Deleted")).catch(e=>setStatus("Couldn't delete: "+e.message));
  render();
}
function askPin(){
  if(pinAsked)return;pinAsked=true;
  const f=modal(`<h2>Enter PIN</h2><div class="sub" style="margin:0">This schedule is locked. Enter the PIN you set in Cloudflare.</div>
    <div class="f"><label for="pin">PIN</label><input id="pin" type="password" inputmode="numeric" autocomplete="current-password" required></div>
    <div class="wd" id="pin-msg"></div>
    <div class="acts"><div></div><div><button type="submit" class="primary">Unlock</button></div></div>`,"Enter PIN");
  f.addEventListener("submit",async e=>{e.preventDefault();ls.set("ss.pin",$("#pin").value);
    const h={"x-pin":$("#pin").value};const r=await fetch("/api/jobs",{headers:h,cache:"no-store"}).catch(()=>null);
    if(r&&r.ok){pinAsked=false;closeModal();load(true)}else{$("#pin-msg").textContent=r&&r.status===401?"That PIN didn’t match. Try again.":"Couldn’t reach the server. Check your connection."}});
  $("#pin").focus();
}
async function load(force){
  if(!force&&(drag||rdrag||mdrag||$("#modal").innerHTML))return;
  try{const list=await api("GET","jobs");jobs=list.map(norm);ls.set("ss.jobs",jobs);render();
    const t=new Date();setStatus("Synced "+t.getHours()+":"+pad(t.getMinutes()))}
  catch(e){if(!pinAsked)setStatus("Offline: showing the last copy on this device")}
}''')
R('''// data
jobs=(ls.get("ss.jobs")||[]).map(norm);render();scrollToToday();
(async()=>{
  let db=null;
  try{if(window.claude&&window.claude.use)db=await window.claude.use("db")}catch(e){db=null}
  if(!db){setStatus("Saved in this browser only");return}
  col=db.collection("jobs");
  col.onSnapshot(snap=>{if(drag||rdrag||mdrag)return;jobs=snap.docs.map(d=>norm({id:d.id,...d.data()}));render();setStatus("Synced")},
    err=>setStatus("Couldn't load saved jobs: "+(err&&err.message||"reload to retry")));
})();''', '''// data: show the copy on this device straight away, then fetch the latest and keep checking
jobs=(ls.get("ss.jobs")||[]).map(norm);render();scrollToToday();
load(true);
setInterval(()=>{if(!document.hidden)load()},30000);
document.addEventListener("visibilitychange",()=>{if(!document.hidden)load()});''')

head = '''<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#1F2A26">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Schedule">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="apple-touch-icon" href="/icon-180.png">
<link rel="icon" href="/icon-180.png">
<style>html{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}[hidden]{display:none!important}</style>
'''
title_end = src.index("</title>") + len("</title>")
style_end = src.index("</style>") + len("</style>")
page = head + src[:style_end] + "\n</head>\n<body>\n" + src[style_end:] + "\n</body>\n</html>\n"
(here / "index.html").write_text(page)

manifest = {"name": "Site Schedule", "short_name": "Schedule", "start_url": "/", "display": "standalone",
            "background_color": "#F1F2EE", "theme_color": "#1F2A26",
            "icons": [{"src": "/icon-180.png", "sizes": "180x180", "type": "image/png"},
                      {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"}]}
seed = []  # no bundled jobs: updates must never touch the live data
icons = {n: base64.b64encode((here / f"icon-{n}.png").read_bytes()).decode() for n in (180, 512)}

worker = f'''// Site Schedule — Cloudflare Worker
// One file: serves the app and stores jobs in a D1 database.
// Setup: bind a D1 database with the variable name DB. Optional: add a secret APP_PIN to lock the app.

const HTML = {json.dumps(page)};
const MANIFEST = {json.dumps(json.dumps(manifest))};
const ICONS = {json.dumps({"/icon-180.png": icons[180], "/icon-512.png": icons[512]})};
// No bundled jobs. Your jobs live in the D1 database and are never changed by a code update.
const SEED = {json.dumps(seed)};

const json = (data, status = 200) => new Response(JSON.stringify(data), {{
  status, headers: {{ "content-type": "application/json", "cache-control": "no-store" }}
}});

let ready = false;
async function init(db) {{
  if (ready) return;
  await db.prepare("CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, data TEXT NOT NULL, updated INTEGER NOT NULL)").run();
  await db.prepare("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)").run();
  const seeded = await db.prepare("SELECT v FROM meta WHERE k = 'seeded'").first();
  if (!seeded) {{
    const now = Date.now();
    const stmts = SEED.map(({{ id, ...body }}) =>
      db.prepare("INSERT OR IGNORE INTO jobs (id, data, updated) VALUES (?, ?, ?)").bind(id, JSON.stringify(body), now));
    stmts.push(db.prepare("INSERT OR REPLACE INTO meta (k, v) VALUES ('seeded', ?)").bind(String(now)));
    await db.batch(stmts);
  }}
  ready = true;
}}

async function handleApi(request, env, url) {{
  if (env.APP_PIN && request.headers.get("x-pin") !== env.APP_PIN) return json({{ error: "PIN needed" }}, 401);
  if (!env.DB) return json({{ error: "Database not connected. Add a D1 binding called DB." }}, 500);
  await init(env.DB);

  const m = url.pathname.match(/^\\/api\\/jobs(?:\\/([A-Za-z0-9_-]{{1,64}}))?$/);
  if (!m) return json({{ error: "Not found" }}, 404);
  const id = m[1];

  if (request.method === "GET" && !id) {{
    const {{ results }} = await env.DB.prepare("SELECT id, data FROM jobs").all();
    return json(results.map(r => ({{ id: r.id, ...JSON.parse(r.data) }})));
  }}
  if (request.method === "PUT" && id) {{
    const text = await request.text();
    if (text.length > 100000) return json({{ error: "Job is too large" }}, 413);
    let body;
    try {{ body = JSON.parse(text); }} catch {{ return json({{ error: "Bad data" }}, 400); }}
    if (!body || typeof body !== "object" || Array.isArray(body)) return json({{ error: "Bad data" }}, 400);
    delete body.id;
    await env.DB.prepare("INSERT OR REPLACE INTO jobs (id, data, updated) VALUES (?, ?, ?)")
      .bind(id, JSON.stringify(body), Date.now()).run();
    return json({{ ok: true }});
  }}
  if (request.method === "DELETE" && id) {{
    await env.DB.prepare("DELETE FROM jobs WHERE id = ?").bind(id).run();
    return json({{ ok: true }});
  }}
  return json({{ error: "Method not allowed" }}, 405);
}}

export default {{
  async fetch(request, env) {{
    const url = new URL(request.url);
    try {{
      if (url.pathname.startsWith("/api/")) return await handleApi(request, env, url);
    }} catch (err) {{
      return json({{ error: "Server error: " + (err && err.message || err) }}, 500);
    }}
    if (url.pathname === "/manifest.webmanifest")
      return new Response(MANIFEST, {{ headers: {{ "content-type": "application/manifest+json" }} }});
    if (ICONS[url.pathname]) {{
      const bytes = Uint8Array.from(atob(ICONS[url.pathname]), c => c.charCodeAt(0));
      return new Response(bytes, {{ headers: {{ "content-type": "image/png", "cache-control": "public, max-age=86400" }} }});
    }}
    return new Response(HTML, {{ headers: {{
      "content-type": "text/html; charset=utf-8", "cache-control": "no-cache",
      "x-content-type-options": "nosniff", "referrer-policy": "same-origin"
    }} }});
  }}
}};
'''
(here / "worker.js").write_text(worker)
print("worker.js", len(worker), "bytes")
