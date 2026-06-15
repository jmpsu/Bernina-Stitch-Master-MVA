
#!/usr/bin/env python3

import json, re, os, sys

from pathlib import Path

from datetime import datetime



ROOT = Path("/root/embroidery_business_agent_system")

JOBS = ROOT / "jobs"

LOGS = ROOT / "logs"



def now():

    return datetime.now().isoformat()



def log(msg):

    LOGS.mkdir(exist_ok=True)

    with open(LOGS / "phase2_requirements_reply.log", "a") as f:

        f.write(f"{now()} {msg}\n")



def read(p):

    return Path(p).read_text(encoding="utf-8", errors="replace") if Path(p).exists() else ""



def write(p, text):

    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding="utf-8")



def jwrite(p, data):

    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True); tmp=p.with_name(p.name+".tmp"); tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False)); tmp.replace(p)



def parse_summary(job):

    txt = read(job/"intake_summary.md")

    meta = {"from":"","to":"","subject":"","received":""}

    for line in txt.splitlines():

        if line.startswith("- From:"): meta["from"]=line.split(":",1)[1].strip()

        if line.startswith("- To:"): meta["to"]=line.split(":",1)[1].strip()

        if line.startswith("- Subject:"): meta["subject"]=line.split(":",1)[1].strip()

        if line.startswith("- Received:"): meta["received"]=line.split(":",1)[1].strip()

    body = txt.split("## Body",1)[1].strip() if "## Body" in txt else ""

    return meta, body



def find_qty(body):

    m = re.search(r"\b(\d{1,5})\s+(black|navy|white|gray|grey|red|blue|green|gold|silver)?\s*(polo shirts|polos|shirts|hats|caps|hoodies|jackets|pieces|items)\b", body, re.I)

    return m.group(0) if m else ""



def contains_any(s, words):

    sl=s.lower()

    return any(w in sl for w in words)



def extract(job):

    meta, body = parse_summary(job)

    b = body.lower()

    req = {

        "customer_email": meta["from"],

        "to": meta["to"],

        "subject": meta["subject"],

        "quantity": find_qty(body),

        "garment_type": "",

        "placement": "",

        "logo_size": "",

        "thread_colors": "",

        "deadline": "",

        "artwork_status": "",

        "budget": "",

        "shipping_or_pickup": "",

        "confidence": "deterministic extraction only"

    }

    if contains_any(body, ["polo", "shirt"]): req["garment_type"]="polo/shirt mentioned"

    if contains_any(body, ["hat", "cap"]): req["garment_type"]="hat/cap mentioned"

    if "left chest" in b: req["placement"]="left chest"

    elif "front" in b: req["placement"]="front"

    elif "back" in b: req["placement"]="back"

    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:inches|inch|in\.|”|\")\s*wide", body, re.I)

    if m: req["logo_size"]=m.group(0)

    m = re.search(r"thread colors?:?\s*([^\n\.]+)", body, re.I)

    if m: req["thread_colors"]=m.group(1).strip()

    elif contains_any(body, ["white", "silver", "blue", "gold", "black"]): req["thread_colors"]="colors mentioned in body"

    m = re.search(r"(within|in about|about|needed within)\s+(\d+\s+weeks?)", body, re.I)

    if m: req["deadline"]=m.group(0)

    if contains_any(body, ["send the logo", "logo file", "artwork file", "logo"]): req["artwork_status"]="customer says logo/artwork can be sent or is needed"

    missing=[]

    if not req["quantity"]: missing.append("Confirm quantity.")

    if not req["garment_type"]: missing.append("Confirm garment type.")

    if not req["placement"]: missing.append("Confirm embroidery placement.")

    if not req["thread_colors"]: missing.append("Confirm thread colors.")

    if not req["deadline"]: missing.append("Confirm deadline or desired turnaround.")

    if not req["artwork_status"]: missing.append("Request logo/artwork file.")

    if not missing:

        missing.append("Request logo/artwork file in the best available format before quoting final digitizing/production details.")

    return meta, body, req, missing



def draft_reply(req, missing):
    lines = []
    lines.append("Hi,")
    lines.append("")
    lines.append("Thanks for reaching out. I have the basic request noted and can help with an embroidery quote.")
    lines.append("")
    known = []
    if req.get("quantity"):
        known.append("Quantity/garment: " + str(req.get("quantity")))
    elif req.get("garment_type"):
        known.append("Garment: " + str(req.get("garment_type")))
    if req.get("placement"):
        known.append("Placement: " + str(req.get("placement")))
    if req.get("logo_size"):
        known.append("Logo size: " + str(req.get("logo_size")))
    if req.get("thread_colors"):
        known.append("Thread colors: " + str(req.get("thread_colors")))
    if req.get("deadline"):
        known.append("Timing: " + str(req.get("deadline")))
    if known:
        lines.append("What I have so far:")
        for k in known:
            lines.append("- " + k)
        lines.append("")
    lines.append("To quote it accurately, please send:")
    lines.append("- The logo/artwork file, preferably SVG, PDF, AI, EPS, or the highest-resolution PNG/JPG available")
    lines.append("- Confirmation of the garment brand/style if you already have one picked")
    lines.append("- Whether you are supplying the garments or want them sourced")
    if len(missing) > 1:
        for q in missing:
            if "artwork" not in q.lower():
                lines.append("- " + q.replace("Confirm ", "Confirmation of ").rstrip("."))
    lines.append("")
    lines.append("Once I have that, I can confirm stitch feasibility, placement, and the next steps for pricing and turnaround.")
    lines.append("")
    lines.append("Thanks,")
    lines.append("Jupiter Embroidery")
    return "\n".join(lines) + "\n"

def process(job):

    meta, body, req, missing = extract(job)

    write(job/"pipeline/requirements/requirements_extracted.md", "# Requirements Extracted\n\n```json\n"+json.dumps(req, indent=2, ensure_ascii=False)+"\n```\n")

    write(job/"missing_questions.md", "# Missing Questions\n\n" + "\n".join(f"- {m}" for m in missing) + "\n")

    write(job/"pipeline/customer_reply/draft.md", draft_reply(req, missing))

    for stage in ["requirements","customer_reply"]:

        sp=job/"pipeline"/stage/"status.json"

        data=json.loads(read(sp) or "{}")

        data.update({"stage":stage, "status":"draft_ready" if stage=="customer_reply" else "extracted", "updated":now(), "auto_sent":False})

        jwrite(sp,data)

    state=json.loads(read(job/"job_state.json") or "{}")

    state["phase2_requirements_extracted"]=True

    state["customer_reply_draft_ready"]=True

    state["customer_email_auto_send_allowed"]=False

    state["updated"]=now()

    jwrite(job/"job_state.json", state)

    log(f"PROCESSED {job.name}")

    return job.name



if __name__ == "__main__":

    if len(sys.argv)>1:

        jobs=[Path(sys.argv[1])]

    else:

        jobs=sorted(JOBS.glob("JOB-*"), key=lambda p:p.stat().st_mtime)

    for job in jobs:

        if (job/"job_state.json").exists():

            print(process(job))

