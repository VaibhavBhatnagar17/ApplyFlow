"""Dashboard — Card-based job board with scores, filters, cover letters, and apply links."""

import json
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Dashboard | ApplyFlow", page_icon="📊", layout="wide")

from engine.guard import require_login, get_username, sidebar_user_info
from engine.state import (
    load_profile,
    load_user_saved_jobs,
    load_applications,
)

sidebar_user_info()
require_login()
username = get_username()

profile, prefs = load_profile(username)
if not profile or not profile.is_complete():
    st.warning("Complete your profile first.")
    st.page_link("pages/1_Profile.py", label="Set Up Profile", icon="👤")
    st.stop()

jobs = load_user_saved_jobs(username)
apps = load_applications(username)
applied_keys = {f"{a['company'].lower()}|{a['title'].lower()}" for a in apps}

for j in jobs:
    key = f"{j.get('company','').lower()}|{j.get('title','').lower()}"
    if key in applied_keys:
        j["status"] = "applied"

if not jobs:
    st.markdown("# 📊 Dashboard")
    st.info("No jobs yet. Head to **Find Jobs** to discover your best matches!")
    st.page_link("pages/2_Find_Jobs.py", label="Find Jobs", icon="🔍")
    st.stop()

jobs_json = json.dumps(jobs, default=str)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:transparent;color:#e4e7f0;line-height:1.5}}
.ctr{{max-width:1440px;margin:0 auto;padding:8px 0}}
header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;padding-bottom:14px;border-bottom:1px solid #2a2f3d}}
header h1{{font-size:22px;font-weight:700}}
header h1 span{{color:#22c984}}
.sub{{font-size:12px;color:#8c93a8;margin-top:2px}}
.pill{{padding:5px 12px;border-radius:16px;font-size:11px;font-weight:700;background:rgba(34,201,132,.12);color:#22c984}}

.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin-bottom:18px}}
.st{{background:#13161d;border:1px solid #2a2f3d;border-radius:12px;padding:12px 14px;text-align:center}}
.st-n{{font-size:28px;font-weight:800;line-height:1}}
.st-l{{font-size:10px;color:#8c93a8;text-transform:uppercase;letter-spacing:.8px;margin-top:4px;font-weight:600}}

.tb{{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap;align-items:center}}
.fg{{display:flex;gap:2px;background:#13161d;border-radius:8px;padding:2px;border:1px solid #2a2f3d}}
.fb{{padding:5px 12px;border-radius:6px;border:none;background:transparent;color:#8c93a8;font-size:11px;font-weight:700;cursor:pointer;transition:all .15s}}
.fb:hover{{color:#e4e7f0;background:#1c2029}}
.fb.on{{background:#5b8def;color:#fff}}
.sinp{{flex:1;min-width:180px;padding:7px 12px;border-radius:8px;border:1px solid #2a2f3d;background:#13161d;color:#e4e7f0;font-size:13px;outline:none}}
.sinp:focus{{border-color:#5b8def}}
.sinp::placeholder{{color:#5c6378}}
.rc{{font-size:11px;color:#8c93a8;font-weight:700;white-space:nowrap}}

#joblist{{display:flex;flex-direction:column;gap:8px}}
.card{{background:#13161d;border:1px solid #2a2f3d;border-radius:12px;overflow:hidden;transition:border-color .15s}}
.card:hover{{border-color:#3d4a6a}}
.card.done{{opacity:.55}}
.card-top{{display:flex;align-items:center;gap:12px;padding:14px 18px;cursor:pointer}}
.score{{min-width:44px;height:44px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:900;flex-shrink:0}}
.score-h{{background:rgba(34,201,132,.12);color:#22c984}}
.score-m{{background:rgba(91,141,239,.12);color:#5b8def}}
.score-l{{background:rgba(240,180,41,.12);color:#f0b429}}
.info{{flex:1;min-width:0}}
.co{{font-size:14px;font-weight:700}}
.ti{{font-size:12px;color:#8c93a8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.meta{{display:flex;gap:5px;margin-top:4px;flex-wrap:wrap}}
.t{{padding:2px 7px;border-radius:4px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.3px}}
.t-e{{background:rgba(34,201,132,.1);color:#22c984}}
.t-g{{background:rgba(91,141,239,.1);color:#5b8def}}
.t-s{{background:rgba(240,180,41,.1);color:#f0b429}}
.t-m{{background:#252a35;color:#8c93a8}}
.t-hot{{background:rgba(232,118,58,.1);color:#e8763a}}
.t-sk{{background:#252a35;color:#8c93a8}}
.t-skh{{background:rgba(34,201,132,.08);color:#22c984}}
.btns{{display:flex;gap:6px;flex-shrink:0;align-items:center}}
.btn{{padding:7px 14px;border-radius:7px;border:none;font-size:11px;font-weight:700;cursor:pointer;display:inline-flex;align-items:center;gap:4px;text-decoration:none;white-space:nowrap}}
.btn-a{{background:linear-gradient(135deg,#5b8def,#3d6ad6);color:#fff;box-shadow:0 2px 6px rgba(91,141,239,.2)}}
.btn-a:hover{{transform:translateY(-1px);box-shadow:0 4px 12px rgba(91,141,239,.3)}}
.btn-d{{background:rgba(167,139,250,.1);color:#a78bfa;cursor:default}}
.btn-c{{background:#1c2029;color:#8c93a8;border:1px solid #2a2f3d}}
.btn-c:hover{{color:#e4e7f0}}
.btn-c.ok{{background:rgba(34,201,132,.12);color:#22c984;border-color:#22c984}}
.xbtn{{background:transparent;color:#5c6378;font-size:18px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;border-radius:6px;border:1px solid #2a2f3d;cursor:pointer}}

.panel{{display:none;padding:0 18px 16px;border-top:1px solid #2a2f3d}}
.panel.open{{display:block}}
.panel h4{{font-size:11px;text-transform:uppercase;letter-spacing:.8px;color:#5c6378;margin:14px 0 8px;font-weight:700;display:flex;align-items:center;gap:8px}}
.clbox{{background:#1c2029;border:1px solid #2a2f3d;border-radius:8px;padding:14px;font-size:12px;color:#8c93a8;white-space:pre-wrap;line-height:1.6;max-height:280px;overflow-y:auto}}
.ubox{{background:#1c2029;border:1px solid #2a2f3d;border-radius:6px;padding:8px 12px;display:flex;align-items:center;gap:8px}}
.ubox a{{color:#5b8def;word-break:break-all;font-size:11px;flex:1}}
.mbtn{{padding:6px 14px;border-radius:6px;border:1px solid #2a2f3d;background:#1c2029;color:#8c93a8;font-size:11px;font-weight:600;cursor:pointer;transition:all .15s}}
.mbtn:hover{{border-color:#a78bfa;color:#a78bfa}}
.toast{{position:fixed;bottom:24px;right:24px;background:#1c2029;border:1px solid #22c984;border-radius:10px;padding:12px 20px;font-size:12px;font-weight:700;color:#22c984;z-index:999;transform:translateY(80px);opacity:0;transition:all .25s;box-shadow:0 8px 24px rgba(0,0,0,.4)}}
.toast.show{{transform:translateY(0);opacity:1}}
@media(max-width:700px){{.stats{{grid-template-columns:repeat(2,1fr)}} .tb{{flex-direction:column}} }}
</style>
</head>
<body>
<div class="ctr">
<header>
<div>
<h1>ApplyFlow <span>Dashboard</span></h1>
<div class="sub">Click any card to expand. Copy cover letter, open job page, apply, mark done.</div>
</div>
<div class="pill" id="pill"></div>
</header>
<div class="stats" id="stats"></div>
<div class="tb">
<div class="fg" id="qf">
<button class="fb on" data-v="all">All</button>
<button class="fb" data-v="excellent">Excellent</button>
<button class="fb" data-v="good">Good</button>
<button class="fb" data-v="stretch">Stretch</button>
</div>
<div class="fg" id="sf">
<button class="fb on" data-v="all">All Status</button>
<button class="fb" data-v="new">New</button>
<button class="fb" data-v="applied">Applied</button>
</div>
<input type="text" class="sinp" id="search" placeholder="Search company, title, skill...">
<span class="rc" id="rc"></span>
</div>
<div id="joblist"></div>
</div>
<div class="toast" id="toast"></div>

<script>
var JOBS = {jobs_json};
var HOT = {{"LLM":1,"RAG":1,"Agents":1,"GenAI":1,"PyTorch":1,"NLP":1,"Deep Learning":1,
  "Computer Vision":1,"YOLO":1,"LangChain":1,"Kubernetes":1,"MLOps":1,"TensorFlow":1}};

(function(){{
  var i, j;
  for(i=0;i<JOBS.length;i++){{
    j=JOBS[i];
    var sc=j.match_score||0;
    if(!sc){{
      var base=j.match_quality==="excellent"?85:j.match_quality==="good"?65:45;
      var sk=j.skills_matched||[];
      var bonus=Math.min(sk.length*2.5,15);
      var hotB=0;for(var s=0;s<sk.length;s++)if(HOT[sk[s]])hotB++;
      sc=Math.min(Math.round(base+bonus+hotB),99);
    }}
    j._score=sc;
  }}

  var fQ="all",fS="all",fT="",openIdx=-1;
  var appliedMap={{}};
  try{{appliedMap=JSON.parse(localStorage.getItem("af_applied_v1")||"{{}}");}}catch(e){{}}
  function saveApplied(){{localStorage.setItem("af_applied_v1",JSON.stringify(appliedMap));}}

  function isApp(j){{return j.status==="applied"||appliedMap[j.company+"|"+j.title]===true;}}

  function esc(str){{
    if(!str)return"";
    var d=document.createElement("div");
    d.appendChild(document.createTextNode(str));
    return d.innerHTML;
  }}

  function getFiltered(){{
    var out=[];
    for(var i=0;i<JOBS.length;i++){{
      var j=JOBS[i];
      if(fQ!=="all"&&j.match_quality!==fQ)continue;
      var st=isApp(j)?"applied":"new";
      if(fS!=="all"&&st!==fS)continue;
      if(fT){{
        var q=fT.toLowerCase();
        var hay=(j.company+" "+j.title+" "+j.location+" "+(j.skills_matched||[]).join(" ")).toLowerCase();
        if(hay.indexOf(q)===-1)continue;
      }}
      out.push(j);
    }}
    out.sort(function(a,b){{return b._score-a._score;}});
    return out;
  }}

  function renderStats(){{
    var t=JOBS.length,e=0,g=0,s=0,a=0;
    for(var i=0;i<JOBS.length;i++){{
      if(JOBS[i].match_quality==="excellent")e++;
      if(JOBS[i].match_quality==="good")g++;
      if(JOBS[i].match_quality==="stretch")s++;
      if(isApp(JOBS[i]))a++;
    }}
    document.getElementById("pill").textContent=t+" Jobs Ready";
    var items=[[t,"Total","#e4e7f0"],[e,"Excellent","#22c984"],[g,"Good","#5b8def"],[s,"Stretch","#f0b429"],[a,"Applied","#a78bfa"]];
    var html="";
    for(var i=0;i<items.length;i++){{
      html+='<div class="st"><div class="st-n" style="color:'+items[i][2]+'">'+items[i][0]+'</div><div class="st-l">'+items[i][1]+'</div></div>';
    }}
    document.getElementById("stats").innerHTML=html;
  }}

  function render(){{
    var list=getFiltered();
    document.getElementById("rc").textContent=list.length+" of "+JOBS.length;
    var html="";

    for(var i=0;i<list.length;i++){{
      var j=list[i];
      var idx=JOBS.indexOf(j);
      var sc=j._score;
      var scC=sc>=80?"score-h":sc>=60?"score-m":"score-l";
      var mqC=j.match_quality==="excellent"?"t-e":j.match_quality==="stretch"?"t-s":"t-g";
      var app=isApp(j);
      var isOpen=(openIdx===idx);
      var skills=j.skills_matched||[];
      var fresh=j.freshness||"";
      var isHot=fresh.indexOf("hour")>-1||fresh.indexOf("today")>-1||fresh.indexOf("minute")>-1;

      html+='<div class="card'+(app?" done":"")+'">';
      html+='<div class="card-top" data-idx="'+idx+'">';
      html+='<div class="score '+scC+'">'+sc+'</div>';
      html+='<div class="info">';
      html+='<div class="co">'+esc(j.company)+'</div>';
      html+='<div class="ti">'+esc(j.title)+'</div>';
      html+='<div class="meta">';
      html+='<span class="t '+mqC+'">'+esc(j.match_quality)+'</span>';
      html+='<span class="t t-m">'+esc(j.location)+'</span>';
      if(j.experience)html+='<span class="t t-m">'+esc(j.experience)+'</span>';
      if(fresh)html+='<span class="t '+(isHot?"t-hot":"t-m")+'">'+esc(fresh)+'</span>';
      html+='<span class="t t-m">'+esc(j.platform||"")+'</span>';
      html+='</div></div>';

      html+='<div class="btns">';
      if(j.cover_letter)html+='<button class="btn btn-c" data-copy="'+idx+'">&#128203; Cover Letter</button>';
      if(app){{
        html+='<span class="btn btn-d">&#10003; Applied</span>';
      }}else{{
        html+='<a href="'+esc(j.url)+'" target="_blank" class="btn btn-a" onclick="event.stopPropagation()">&#8599; Apply</a>';
      }}
      html+='<button class="xbtn" data-toggle="'+idx+'">'+(isOpen?'&minus;':'+')+'</button>';
      html+='</div></div>';

      html+='<div class="panel'+(isOpen?" open":"")+'" id="p'+idx+'">';
      html+='<h4>Application URL <button class="btn btn-c" data-copyurl="'+idx+'">Copy URL</button></h4>';
      html+='<div class="ubox"><a href="'+esc(j.url)+'" target="_blank">'+esc(j.url)+'</a></div>';

      html+='<h4>Skills Matched</h4><div class="meta">';
      for(var si=0;si<skills.length;si++){{
        html+='<span class="t '+(HOT[skills[si]]?"t-skh":"t-sk")+'">'+esc(skills[si])+'</span>';
      }}
      html+='</div>';

      html+='<h4>Cover Letter <button class="btn btn-c" data-copy="'+idx+'">Copy</button></h4>';
      html+='<div class="clbox">'+esc(j.cover_letter||"No cover letter generated")+'</div>';

      if(!app){{
        html+='<div style="margin-top:14px;text-align:right"><button class="mbtn" data-mark="'+idx+'">&#10003; Mark as Applied</button></div>';
      }}
      html+='</div></div>';
    }}

    document.getElementById("joblist").innerHTML=html;
  }}

  document.getElementById("joblist").addEventListener("click",function(e){{
    var el=e.target;
    var top=el.closest(".card-top");
    if(top&&!el.closest(".btns")){{
      var idx=parseInt(top.getAttribute("data-idx"));
      openIdx=openIdx===idx?-1:idx;
      render();return;
    }}
    var toggleBtn=el.closest("[data-toggle]");
    if(toggleBtn){{
      e.stopPropagation();
      var idx=parseInt(toggleBtn.getAttribute("data-toggle"));
      openIdx=openIdx===idx?-1:idx;
      render();return;
    }}
    var copyBtn=el.closest("[data-copy]");
    if(copyBtn){{
      e.stopPropagation();
      var idx=parseInt(copyBtn.getAttribute("data-copy"));
      var text=JOBS[idx].cover_letter||"";
      navigator.clipboard.writeText(text).then(function(){{
        copyBtn.classList.add("ok");copyBtn.innerHTML="&#10003; Copied!";
        showToast("Cover letter copied!");
        setTimeout(function(){{copyBtn.classList.remove("ok");copyBtn.innerHTML="&#128203; Copy";}},2000);
      }});return;
    }}
    var urlBtn=el.closest("[data-copyurl]");
    if(urlBtn){{
      e.stopPropagation();
      var idx=parseInt(urlBtn.getAttribute("data-copyurl"));
      navigator.clipboard.writeText(JOBS[idx].url).then(function(){{
        urlBtn.classList.add("ok");urlBtn.innerHTML="&#10003; Copied!";
        showToast("URL copied!");
        setTimeout(function(){{urlBtn.classList.remove("ok");urlBtn.innerHTML="Copy URL";}},2000);
      }});return;
    }}
    var markBtn=el.closest("[data-mark]");
    if(markBtn){{
      e.stopPropagation();
      var idx=parseInt(markBtn.getAttribute("data-mark"));
      var j=JOBS[idx];
      appliedMap[j.company+"|"+j.title]=true;
      saveApplied();renderStats();render();
      showToast(j.company+" marked as applied!");
      return;
    }}
  }});

  function showToast(msg){{
    var t=document.getElementById("toast");
    t.textContent=msg;
    t.classList.add("show");
    setTimeout(function(){{t.classList.remove("show");}},2500);
  }}

  function setupFilter(id,cb){{
    document.getElementById(id).addEventListener("click",function(e){{
      var btn=e.target.closest(".fb");
      if(!btn)return;
      cb(btn.getAttribute("data-v"));
      var all=document.querySelectorAll("#"+id+" .fb");
      for(var i=0;i<all.length;i++)all[i].classList.remove("on");
      btn.classList.add("on");
      openIdx=-1;render();
    }});
  }}
  setupFilter("qf",function(v){{fQ=v;}});
  setupFilter("sf",function(v){{fS=v;}});
  document.getElementById("search").addEventListener("input",function(e){{fT=e.target.value;openIdx=-1;render();}});

  renderStats();
  render();
}})();
</script>
</body>
</html>"""

height = min(max(len(jobs) * 85 + 300, 600), 4000)
components.html(html, height=height, scrolling=True)
