#!/usr/bin/env python3
import json, re, html
from pathlib import Path
from datetime import datetime

ROOT=Path("/root/embroidery_business_agent_system")
JOBS=ROOT/"jobs"
DASH=ROOT/"dashboard"
DASH.mkdir(parents=True,exist_ok=True)

STATUSES=["new_intake","requirements_extracted","needs_customer_info","artwork_needed","artwork_received","artwork_review","artwork_approved","digitizing_plan","digitizing_in_progress","stitch_file_ready","qa_review","qa_passed","customer_approval_needed","approved_for_production","with_sarah_for_embroidery","embroidering_on_bernina","embroidered_complete","ready_for_pickup_or_shipping","sent_to_customer","project_complete","blocked","cancelled"]
OWNER={"new_intake":"requirements_agent","requirements_extracted":"joey_review","needs_customer_info":"customer","artwork_needed":"customer","artwork_received":"artwork_prep_agent","artwork_review":"artwork_prep_agent","artwork_approved":"digitizer_agent","digitizing_plan":"digitizer_agent","digitizing_in_progress":"digitizer_agent","stitch_file_ready":"qa_agent","qa_review":"qa_agent","qa_passed":"joey_review","customer_approval_needed":"customer","approved_for_production":"sarah_embroidery","with_sarah_for_embroidery":"sarah_embroidery","embroidering_on_bernina":"sarah_embroidery","embroidered_complete":"customer_delivery","ready_for_pickup_or_shipping":"customer_delivery","sent_to_customer":"complete","project_complete":"complete","blocked":"joey_review","cancelled":"complete"}
NEXT={"new_intake":"Extract requirements and identify missing customer info.","requirements_extracted":"Review requirements and draft reply.","needs_customer_info":"Wait for customer to answer missing questions.","artwork_needed":"Request logo/artwork file from customer.","artwork_received":"Review artwork quality and stitch feasibility.","artwork_review":"Simplify/review artwork for embroidery.","artwork_approved":"Create digitizing plan.","digitizing_plan":"Begin converting artwork into stitch-file plan.","digitizing_in_progress":"Create embroidery stitch pattern file.","stitch_file_ready":"Run QA review before approval.","qa_review":"Check stitch risks, placement, size, thread colors, and garment compatibility.","qa_passed":"Get Joey/customer approval before production.","customer_approval_needed":"Wait for customer approval.","approved_for_production":"Hand off to Sarah for Bernina embroidery.","with_sarah_for_embroidery":"Sarah needs to start embroidery.","embroidering_on_bernina":"Sarah is embroidering on Bernina.","embroidered_complete":"Mark ready for pickup/shipping.","ready_for_pickup_or_shipping":"Deliver or ship to customer.","sent_to_customer":"Wait for final completion confirmation.","project_complete":"Done.","blocked":"Resolve blocker.","cancelled":"No action."}

def read(p):
    try: return Path(p).read_text(encoding="utf-8",errors="replace")
    except Exception: return ""

def jread(p):
    try: return json.loads(read(p))
    except Exception: return {}

def jwrite(p,d):
    p=Path(p); tmp=p.with_name(p.name+".tmp"); tmp.write_text(json.dumps(d,indent=2,ensure_ascii=False)); tmp.replace(p)

def esc(x): return html.escape(str(x or ""))

def short(x,n=650):
    x=re.sub(r"\s+"," ",x or "").strip()
    return x[:n]+("..." if len(x)>n else "")

def meta(txt):
    out={"from":"","subject":""}
    for line in txt.splitlines():
        if line.startswith("- From:"): out["from"]=line.split(":",1)[1].strip()
        if line.startswith("- Subject:"): out["subject"]=line.split(":",1)[1].strip()
    return out

def infer(job,state):
    missing=read(job/"missing_questions.md").lower()
    draft=read(job/"pipeline/customer_reply/draft.md")
    req=read(job/"pipeline/requirements/requirements_extracted.md")
    st=state.get("pipeline_status") or ""
    if st in STATUSES: return st
    if state.get("customer_reply_draft_ready") or draft.strip() or req.strip(): st="requirements_extracted"
    else: st="new_intake"
    if ("artwork" in missing or "logo" in missing) and not (job/"artwork").exists(): st="artwork_needed"
    return st

cards=[]
for job in sorted(JOBS.glob("JOB-*"), key=lambda p:p.stat().st_mtime, reverse=True):
    state=jread(job/"job_state.json")
    st=infer(job,state)
    state["pipeline_status"]=st
    state["current_owner"]=OWNER.get(st,"joey_review")
    state["next_action"]=NEXT.get(st,"Review job.")
    state["status_updated"]=datetime.now().isoformat()
    hist=state.setdefault("status_history",[])
    if not hist or hist[-1].get("status")!=st:
        hist.append({"time":datetime.now().isoformat(),"status":st,"owner":state["current_owner"],"note":state["next_action"]})
    jwrite(job/"job_state.json",state)
    m=meta(read(job/"intake_summary.md"))
    cards.append({"job_id":job.name,"from":m["from"],"subject":m["subject"],"status":st,"owner":state["current_owner"],"next_action":state["next_action"],"draft_preview":read(job/"pipeline/customer_reply/draft.md"),"requirements_preview":read(job/"pipeline/requirements/requirements_extracted.md"),"missing_questions":read(job/"missing_questions.md"),"path":str(job)})

(DASH/"jobs_status.json").write_text(json.dumps({"generated":datetime.now().isoformat(),"statuses":STATUSES,"jobs":cards},indent=2,ensure_ascii=False))
rows=[]
for c in cards[:100]:
    rows.append("<tr><td><b>"+esc(c["job_id"])+"</b><br><small>"+esc(c["from"])+"</small></td><td>"+esc(c["subject"])+"</td><td><span class=badge>"+esc(c["status"])+"</span><br><small>"+esc(c["owner"])+"</small></td><td>"+esc(c["next_action"])+"</td><td><details><summary>Draft reply</summary><pre>"+esc(c["draft_preview"])+"</pre></details></td><td><details><summary>Requirements / missing</summary><pre>"+esc(c["requirements_preview"])+"</pre><pre>"+esc(c["missing_questions"])+"</pre></details></td></tr>")
html_doc="<!doctype html><html><head><meta charset=utf-8><meta name=viewport content=\"width=device-width,initial-scale=1\"><title>Embiz Pipeline Dashboard</title><style>body{font-family:Arial,sans-serif;background:#111;color:#eee;margin:18px}table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid #333;padding:10px;vertical-align:top}th{background:#222}.badge{display:inline-block;background:#2b6cb0;color:white;padding:4px 8px;border-radius:999px;font-size:12px}pre{white-space:pre-wrap;background:#181818;padding:10px;border-radius:6px;max-width:700px}.statuses{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0}.statuses span{background:#222;border:1px solid #333;border-radius:999px;padding:5px 8px;font-size:12px}small{color:#aaa}</style></head><body><h1>Embiz Pipeline Dashboard</h1><small>Review-only. No auto-send. Generated "+esc(datetime.now().isoformat())+"</small><div class=statuses>"+"".join("<span>"+esc(s)+"</span>" for s in STATUSES)+"</div><table><thead><tr><th>Job</th><th>Subject</th><th>Status / Owner</th><th>Next action</th><th>Draft</th><th>Details</th></tr></thead><tbody>"+"".join(rows)+"</tbody></table></body></html>"
(DASH/"index.html").write_text(html_doc)
print("REFRESHED_DASHBOARD jobs="+str(len(cards)))
