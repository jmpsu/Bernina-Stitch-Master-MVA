#!/usr/bin/env python3
import os,json,re,base64,mimetypes,subprocess,shutil
from pathlib import Path
from datetime import datetime
from email import policy
from email.parser import BytesParser
ROOT=Path("/root/embroidery_business_agent_system"); JOBS=ROOT/"jobs"; LOGS=ROOT/"logs"; DASH=ROOT/"dashboard"; LIB=Path("/root/.openclaw/workspace")
for p in [JOBS,LOGS,DASH,ROOT/"reports",ROOT/"backups"]: p.mkdir(parents=True,exist_ok=True)
IMG_EXT={".png",".jpg",".jpeg",".gif",".webp",".svg",".pdf"}
STAGE_SOURCES={"requirements":["embroidery-business-build-request","source-driven-development","spec-driven-development"],"artwork_prep":["inkstitch","embroidery-business-build-request","source-driven-development"],"digitizer":["inkstitch","using-agent-skills","source-driven-development"],"qa":["inkstitch","test-driven-development","security-and-hardening"],"customer_reply":["embroidery-business-build-request","security-and-hardening"]}
STATUSES=["new_intake","requirements_extracted","needs_customer_info","artwork_needed","artwork_received","artwork_review","artwork_approved","digitizing_plan","digitizing_in_progress","stitch_file_ready","qa_review","qa_passed","customer_approval_needed","approved_for_production","with_sarah_for_embroidery","embroidering_on_bernina","embroidered_complete","ready_for_pickup_or_shipping","sent_to_customer","project_complete","blocked","cancelled"]
OWNER={"new_intake":"requirements_agent","requirements_extracted":"joey_review","needs_customer_info":"customer","artwork_needed":"customer","artwork_received":"artwork_prep_agent","artwork_review":"artwork_prep_agent","artwork_approved":"digitizer_agent","digitizing_plan":"digitizer_agent","digitizing_in_progress":"digitizer_agent","stitch_file_ready":"qa_agent","qa_review":"qa_agent","qa_passed":"joey_review","customer_approval_needed":"customer","approved_for_production":"sarah_embroidery","with_sarah_for_embroidery":"sarah_embroidery","embroidering_on_bernina":"sarah_embroidery","embroidered_complete":"customer_delivery","ready_for_pickup_or_shipping":"customer_delivery","sent_to_customer":"complete","project_complete":"complete","blocked":"joey_review","cancelled":"complete"}
NEXT={"artwork_review":"Create simplified embroidery mockup before digitizing.","artwork_received":"Review artwork quality and stitch feasibility.","requirements_extracted":"Review requirements and draft reply.","artwork_needed":"Request logo/artwork file from customer.","qa_review":"Run QA review before approval.","with_sarah_for_embroidery":"Sarah needs to start embroidery.","embroidering_on_bernina":"Sarah is embroidering on Bernina.","project_complete":"Done."}
def now(): return datetime.now().isoformat()
def read(p):
    try:return Path(p).read_text(encoding="utf-8",errors="replace")
    except Exception:return ""
def jread(p):
    try:return json.loads(read(p))
    except Exception:return {}
def jwrite(p,d):
    p=Path(p); tmp=p.with_name(p.name+".tmp"); tmp.write_text(json.dumps(d,indent=2,ensure_ascii=False)); tmp.replace(p)
def log(s):
    with open(LOGS/"low_hanging_fruit_full.log","a") as f:f.write(now()+" "+s+"\n")
def safe(s): return re.sub(r"[^A-Za-z0-9._-]+","_",s or "attachment.bin")
def extract(job):
    raw=jread(job/"raw_email.json"); txt=raw.get("raw") or raw.get("text") or raw.get("body") or ""; saved=[]; (job/"attachments").mkdir(exist_ok=True); (job/"artwork").mkdir(exist_ok=True)
    if txt:
        try:
            msg=BytesParser(policy=policy.default).parsebytes(txt.encode("utf-8","surrogateescape"))
            for part in msg.walk():
                fn=part.get_filename(); cd=part.get_content_disposition(); ct=part.get_content_type()
                if cd=="attachment" or fn:
                    fn=safe(fn or ("attachment_"+str(len(saved)+1)+(mimetypes.guess_extension(ct) or ".bin")))
                    payload=part.get_payload(decode=True)
                    if not payload and isinstance(part.get_payload(),str):
                        try: payload=base64.b64decode(re.sub(r"\s+","",part.get_payload()),validate=False)
                        except Exception: payload=None
                    if payload:
                        out=job/"attachments"/fn; out.write_bytes(payload); saved.append({"filename":fn,"content_type":ct,"bytes":len(payload),"path":str(out)})
                        if ct.startswith("image/") or Path(fn).suffix.lower() in IMG_EXT: (job/"artwork"/fn).write_bytes(payload)
        except Exception as e: log("EXTRACT_ERR "+job.name+" "+repr(e))
    (job/"attachments_manifest.json").write_text(json.dumps({"extracted_at":now(),"attachments":saved},indent=2))
    return saved
def find_sources(stage):
    hits=[]
    for key in STAGE_SOURCES.get(stage,[]):
        for base in [LIB/"local-source-indexes",LIB/"agent-skills-indexes",LIB]:
            for f in base.glob("*.md"):
                if key.lower() in f.name.lower(): hits.append(f)
    return hits[:8]
def load_library(job):
    for stage in ["requirements","artwork_prep","digitizer","qa","customer_reply"]:
        sd=job/"pipeline"/stage; sd.mkdir(parents=True,exist_ok=True); refs=[]; chunks=[]
        for f in find_sources(stage):
            refs.append(str(f)); chunks.append("## SOURCE: "+str(f)+"\n\n"+read(f)[:3500])
        (sd/"source_references.json").write_text(json.dumps({"stage":stage,"loaded_at":now(),"sources":refs},indent=2))
        (sd/"source_context.md").write_text("# Source Context\n\n"+"\\n\\n---\\n\\n".join(chunks) if chunks else "# Source Context\n\nNo matching local source index found.\n")
def artwork_review(job):
    files=[p for p in (job/"artwork").glob("*") if p.is_file()]; out=job/"pipeline/artwork_prep/artwork_review.md"; out.parent.mkdir(parents=True,exist_ok=True)
    lines=["# Artwork Review","","Status: artwork_review","","Files reviewed:"]
    for p in files:
        ext=p.suffix.lower(); lines += [f"- {p.name}",f"  - Bytes: {p.stat().st_size}",f"  - Type: {vector/PDF if ext in [.svg,.pdf] else raster/sketch/photo
