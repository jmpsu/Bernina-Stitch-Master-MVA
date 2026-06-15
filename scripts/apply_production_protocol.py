#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime
ROOT=Path("/root/embroidery_business_agent_system")
JOBS=ROOT/"jobs"
def readj(p):
    try: return json.loads(p.read_text())
    except Exception: return {}
def write(p,s): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(s)
def writej(p,d):
    t=p.with_name(p.name+".tmp"); t.write_text(json.dumps(d,indent=2,ensure_ascii=False)); t.replace(p)
def imginfo(p):
    try:
        from PIL import Image
        im=Image.open(p); return {"width_px":im.width,"height_px":im.height}
    except Exception: return {}
for job in sorted(JOBS.glob("JOB-*")):
    art=list((job/"artwork").glob("*")) if (job/"artwork").exists() else []
    manifest={"protocol":"embroidery_production_protocol_v1","created":datetime.now().isoformat(),"aspect_ratio_locked":True,"no_warping":True,"variants":[],"source_artwork":[str(x) for x in art],"stitch_files_generated":False}
    for a in art:
        base=a.stem
        manifest["variants"].append({"variant":"standard","max_box_in":"2.5 x 2.5","scale_policy":"uniform_fit_longest_dimension","planned_dst":base+"_2.5in.dst","planned_pes":base+"_2.5in.pes","status":"planned_not_generated","image_info":imginfo(a)})
        manifest["variants"].append({"variant":"expanded","max_box_in":"6.0 x 6.0","scale_policy":"uniform_fit_longest_dimension","planned_dst":base+"_6.0in.dst","planned_pes":base+"_6.0in.pes","status":"planned_not_generated","image_info":imginfo(a)})
    writej(job/"production_manifest.json",manifest)
    write(job/"pipeline/digitizer/production_protocol.md","# Production Protocol Applied\n\n- Dual output required: 2.5 in and 6.0 in variants.\n- Aspect ratio locked.\n- No stretching or warping.\n- Satin-column planning default for cleaned hand-drawn line art.\n- DST/PES are planned only until real stitch files exist.\n")
    write(job/"pipeline/qa/production_protocol_check.md","# Production Protocol QA\n\n- [ ] Standard 2.5 in variant planned\n- [ ] Expanded 6.0 in variant planned\n- [ ] Aspect ratio preserved\n- [ ] No fake DST/PES claimed\n- [ ] Real stitch files verified before stitch_file_ready\n")
    st=readj(job/"job_state.json")
    st.update({"production_protocol":"embroidery_production_protocol_v1","dual_size_pipeline_required":True,"standard_variant_required":"2.5x2.5in","expanded_variant_required":"6.0x6.0in","aspect_ratio_locked":True,"fake_digitizing_outputs_allowed":False,"stitch_files_generated":False,"protocol_updated":datetime.now().isoformat()})
    writej(job/"job_state.json",st)
print("PRODUCTION_PROTOCOL_APPLIED")
