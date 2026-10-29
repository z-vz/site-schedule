"""Build the GitHub Pages test site (index.html) from site-schedule.html.

The test site has no server, so jobs are saved in each browser only.
It adds a test banner with "Load sample jobs" and "Clear all".
Run from the repo root:  python3 tools/build_pages.py
"""
import json, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
src = (root / "site-schedule.html").read_text()
version = json.loads((root / "version.json").read_text())["version"]

def R(a, b):
    global src
    assert src.count(a) == 1, a[:60]
    src = src.replace(a, b)

# test banner at the top of the page
R('<div class="wrap">', f'''<div class="wrap">
  <div class="testbar" role="note"><b>Test {version}</b><span class="tm">Saved on this device only. Never touches the live app.</span>
    <span class="tb"><button type="button" id="loadSample">Load sample jobs</button><button type="button" id="clearAll">Clear all</button></span></div>''')

R('.status{font-size:12px;color:var(--muted)}', '''.status{font-size:12px;color:var(--muted)}
.testbar{display:flex;flex-wrap:wrap;align-items:center;gap:4px 10px;background:color-mix(in srgb,var(--c3) 16%,var(--panel));border:1px dashed var(--c3);border-radius:6px;padding:6px 10px;font-size:12px;color:var(--ink)}
.testbar .tb{display:flex;gap:6px;margin-left:auto}
.testbar button{padding:3px 8px;font-size:12px}
@media (max-width:640px){.testbar{padding:4px 8px;font-size:11px}.testbar .tm{display:none}}''')

# sample jobs, dated around today so they always show up
R('// data\n', '''// test site: sample jobs built around today's date
function sampleJobs(){
  const d=n=>addDays(TODAY,n),m=mondayOf(TODAY);
  const w=(wk,day)=>addDays(m,wk*7+day);
  return [
    {id:"s1",title:"Kitchen fit-out",client:"Example client",color:"c2",order:0,notes:"Sample job",
     visits:[{start:w(0,1),end:w(0,3),label:"Carcasses",status:"booked"},{start:w(1,2),end:w(1,4),label:"Doors & fit-off",status:"booked"}],
     events:[{date:w(0,0),label:"Cabinets delivered",status:"booked"},{date:w(1,1),label:"Benchtop template",status:"tentative"}]},
    {id:"s2",title:"Deck & stairs",client:"Example client",color:"c1",order:1,notes:"Sample job",
     visits:[{start:w(1,0),end:w(1,4),label:"",status:"tentative"}],events:[{date:w(0,4),label:"Timber delivery",status:"booked"}]},
    {id:"s3",title:"Laundry",client:"",color:"c3",order:2,notes:"Sample job",
     visits:[{start:w(2,0),end:w(2,2),label:"",status:"booked"}],events:[]},
    {id:"s4",title:"Wardrobes",client:"",color:"c4",order:3,notes:"Sample job",
     visits:[{start:w(-1,1),end:w(-1,3),label:"Install",status:"done"},{start:w(3,1),end:w(3,1),label:"Defects",status:"booked"}],events:[]},
    {id:"s5",title:"Annual leave",client:"",color:"c6",order:4,notes:"Sample job",
     visits:[{start:w(4,0),end:w(4,4),label:"",status:"booked"}],events:[]}
  ];
}
$("#loadSample").onclick=()=>{const ids=new Set(jobs.map(j=>j.id));sampleJobs().forEach(j=>{if(!ids.has(j.id))jobs.push(norm(j))});ls.set("ss.jobs",jobs);render();setStatus("Sample jobs loaded")};
let clearArmed=false;
$("#clearAll").onclick=e=>{if(!clearArmed){clearArmed=true;e.target.textContent="Tap again to clear";setTimeout(()=>{clearArmed=false;e.target.textContent="Clear all"},3000);return}
  jobs=[];ls.set("ss.jobs",jobs);render();clearArmed=false;e.target.textContent="Clear all";setStatus("All test jobs cleared")};

// data
''')

head = f'''<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#1F2A26">
<meta name="robots" content="noindex">
<link rel="apple-touch-icon" href="icons/icon-180.png">
<link rel="icon" href="icons/icon-180.png">
<style>html{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0}}[hidden]{{display:none!important}}</style>
'''
style_end = src.index("</style>") + len("</style>")
page = head + src[:style_end].replace("<title>Site Schedule</title>", f"<title>Site Schedule {version} (test)</title>") + "\n</head>\n<body>\n" + src[style_end:] + "\n</body>\n</html>\n"
(root / "index.html").write_text(page)
print("index.html", len(page), "bytes, version", version)
