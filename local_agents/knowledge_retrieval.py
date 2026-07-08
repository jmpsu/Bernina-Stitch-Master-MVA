"""knowledge_retrieval.py — the EMBIZ knowledge-retrieval router.

Serves Multimodal Knowledge Objects (see ``knowledge_ingest.py`` for the
schema) to the agent personas, enforces HARD KNOWLEDGE GATES, and writes
retrieval PROOF for every call to ``reports/retrieval_log.jsonl``.

    from knowledge_retrieval import route
    result = route("mila", job_id="cr_img_0293",
                   task_type="vectorization",
                   query="preserve source silhouette during tracing")
    result["selected_records"]   # scored knowledge objects (dicts)
    result["retrieval_proof"]    # the proof line appended to the log

Corpus roots are discovered by ``knowledge_ingest.discover_library_roots()``:
the spec's /root/web-archive + /root/EMBIZ_EXPORTS paths are PRIMARY when
they exist (the user's local machine); the in-repo ``knowledge/library`` is
the portable fallback. A corpus may exist in several roots — all copies are
consulted.

HARD KNOWLEDGE GATES: every specialist persona has REQUIRED corpora. When a
required corpus cannot be found under any root, the router logs
``MISSING_REQUIRED_CORPUS: <names>`` in the proof (status="gate_failed") and,
with ``strict=True``, raises ``KnowledgeGateError``. A gate failure is never
silently converted into a pass.
"""

from __future__ import annotations

import datetime
import json
import re
from pathlib import Path

from knowledge_ingest import discover_library_roots

REPO_ROOT = Path(__file__).resolve().parent.parent
RETRIEVAL_LOG = REPO_ROOT / "reports" / "retrieval_log.jsonl"

DEFAULT_TOP_K = 5

# --------------------------------------------------------------------------
# Corpus registry: corpus name -> relative directory under a library root.
# --------------------------------------------------------------------------
CORPUS_PATHS: dict[str, str] = {
    "raster-to-vector":
        "5-agent-architecture/raster-to-vector-agent",
    "vector-design":
        "5-agent-architecture/vector-design-agent",
    "visual-semantics":
        "5-agent-architecture/visual-semantics-corpus",
    "svg-specification":
        "9-knowledge-management-architecture/svg-specification-corpus",
    "inkscape":
        "9-knowledge-management-architecture/inkscape-corpus",
    "svg-conformance":
        "9-knowledge-management-architecture/svg-conformance-corpus",
    "ink-stitch-docs":
        "14-ink-stitch-automation-framework/documents",
    "embroidery-techniques":
        "14-ink-stitch-automation-framework/embroidery-techniques",
    "bernina-b700":
        "10-machine-integration/bernina-b700-corpus",
    "visual-qa":
        "12-quality-assurance/visual-qa-corpus",
    "global": ".",  # global_knowledge_objects.jsonl at the root
}

# --------------------------------------------------------------------------
# Agent -> corpora map (spec). Specialists first, then the existing run
# personas mapped onto the specialist corpora.
# --------------------------------------------------------------------------
AGENT_CORPORA: dict[str, dict[str, list[str]]] = {
    # specialists (spec)
    "mila": {  # raster-to-vector specialist
        "required": ["raster-to-vector", "vector-design"],
        "optional": ["visual-semantics", "global"],
    },
    "melanie": {  # vector-design / SVG specialist
        "required": ["vector-design", "svg-specification"],
        "optional": ["inkscape", "svg-conformance", "global"],
    },
    "mckenna": {  # ink/stitch digitization specialist
        "required": ["ink-stitch-docs", "embroidery-techniques"],
        "optional": ["bernina-b700", "global"],
    },
    "meredith": {  # ink/stitch automation specialist
        "required": ["ink-stitch-docs", "embroidery-techniques"],
        "optional": ["global"],
    },
    "miranda": {  # bernina b700 machine specialist
        "required": ["bernina-b700"],
        "optional": ["embroidery-techniques", "global"],
    },
    "mackenzie": {  # visual QA specialist
        "required": ["visual-qa"],
        "optional": ["visual-semantics", "global"],
    },
    "monica": {  # knowledge operations / corpus curator
        "required": ["global"],
        "optional": list(CORPUS_PATHS),
    },
    # existing run personas -> specialist corpora
    "maya": {  # vectorization  -> Mila's corpora
        "required": ["raster-to-vector", "vector-design"],
        "optional": ["visual-semantics", "global"],
    },
    "marnie": {  # digitization -> Mckenna's + Miranda's corpora
        "required": ["ink-stitch-docs", "embroidery-techniques",
                     "bernina-b700"],
        "optional": ["global"],
    },
    "mercy": {  # QA -> Mackenzie's corpora
        "required": ["visual-qa"],
        "optional": ["visual-semantics", "global"],
    },
    "mabel": {  # knowledge librarian -> global
        "required": ["global"],
        "optional": list(CORPUS_PATHS),
    },
    "mira": {"required": [], "optional": ["global"]},
    "margo": {"required": [], "optional": ["global"]},
    "minerva": {"required": [], "optional": ["global"]},
}

# task_type -> extra low-weight query terms (minimum-viable task awareness)
TASK_TYPE_TERMS: dict[str, tuple[str, ...]] = {
    "vectorization": ("trace", "polygon", "corner", "curve", "path"),
    "digitization": ("satin", "density", "fill", "underlay", "stitch"),
    "stitch-planning": ("satin", "density", "spacing", "hoop"),
    "qa": ("quality", "compare", "fidelity", "artifact"),
    "svg-authoring": ("svg", "path", "viewbox", "fill-rule", "stroke"),
    "machine-setup": ("hoop", "bernina", "thread", "needle"),
    "knowledge-ops": ("corpus", "index", "ingest"),
    "finalization": ("density", "satin", "corner", "fidelity"),
}


class KnowledgeGateError(RuntimeError):
    """A specialist task ran without its required corpus available."""


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9\-]{1,}")


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


# --------------------------------------------------------------------------
# Corpus loading
# --------------------------------------------------------------------------
def find_corpus_files(corpus: str) -> list[Path]:
    """Every JSONL file backing `corpus`, across ALL discovered roots."""
    rel = CORPUS_PATHS.get(corpus)
    if rel is None:
        return []
    files: list[Path] = []
    for root in discover_library_roots():
        if corpus == "global":
            for name in ("global_knowledge_objects.jsonl",
                         "global_knowledge_objects.multimodal.jsonl"):
                p = root / name
                if p.exists():
                    files.append(p)
            continue
        d = root / rel
        if d.is_dir():
            files.extend(sorted(d.glob("*.jsonl")))
    return files


def load_corpus(corpus: str) -> list[dict]:
    """All knowledge objects of a corpus (deduped by id; missing fields
    tolerated — records are plain dicts, never validated away)."""
    records, seen = [], set()
    for f in find_corpus_files(corpus):
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            oid = obj.get("id") or f"{f}:{len(seen)}"
            if oid in seen:
                continue
            seen.add(oid)
            obj.setdefault("id", oid)
            records.append(obj)
    return records


def corpus_exists(corpus: str) -> bool:
    return bool(find_corpus_files(corpus))


# --------------------------------------------------------------------------
# Scoring (spec minimum-viable search: exact terms + title/section/tag/
# source-path relevance + agent_relevance + task_type awareness)
# --------------------------------------------------------------------------
def score_record(rec: dict, query_terms: list[str], agent: str,
                 task_terms: tuple[str, ...] = (),
                 source_file: str | None = None) -> float:
    text = (rec.get("text") or "").lower()
    title = (rec.get("title") or "").lower()
    section = (rec.get("section") or "").lower()
    source = (rec.get("source_path") or "").lower()
    caption = (rec.get("caption") or "").lower()
    tags = [t.lower() for t in (rec.get("tags") or [])]
    score = 0.0
    for term in query_terms:
        if term in text:
            score += 3.0
        if term in caption:
            score += 2.0
        if term in title:
            score += 2.0
        if term in tags:
            score += 2.0
        if term in section:
            score += 1.5
        if term in source:
            score += 1.0
    for term in task_terms:
        if term in text or term in tags:
            score += 0.5
    if agent in (rec.get("agent_relevance") or []):
        score += 2.0
    if source_file:
        stem = Path(source_file).stem.lower()
        if stem and (stem in source or stem in text):
            score += 1.0
    return score


# --------------------------------------------------------------------------
# The router
# --------------------------------------------------------------------------
def route(agent_name: str, job_id: str, task_type: str, query: str,
          source_file: str | None = None, current_phase: str | None = None,
          top_k: int = DEFAULT_TOP_K, strict: bool = False) -> dict:
    """Route a retrieval request for `agent_name`.

    Returns {required_corpora, optional_corpora, selected_records,
    retrieval_proof}. Consults every required corpus plus any optional corpus
    that exists; scores records per the minimum-viable-search rules; appends
    the proof line to reports/retrieval_log.jsonl.

    HARD GATE: missing required corpora set status
    "MISSING_REQUIRED_CORPUS: <names>" (gate_failed). With strict=True this
    raises KnowledgeGateError AFTER the proof is logged — a gate failure is
    recorded, never hidden.
    """
    agent = agent_name.lower()
    spec = AGENT_CORPORA.get(agent, {"required": [], "optional": ["global"]})
    required = list(spec["required"])
    optional = list(spec["optional"])

    missing_required = [c for c in required if not corpus_exists(c)]
    consulted: list[dict] = []
    candidates: list[dict] = []
    for corpus in required + optional:
        if corpus in missing_required:
            consulted.append({"corpus": corpus, "required": True,
                              "present": False, "records": 0})
            continue
        recs = load_corpus(corpus)
        if not recs and corpus in optional and not corpus_exists(corpus):
            continue  # absent optional corpora are simply skipped
        consulted.append({"corpus": corpus,
                          "required": corpus in required,
                          "present": bool(recs), "records": len(recs)})
        for r in recs:
            r = dict(r)
            r["_corpus"] = corpus
            candidates.append(r)

    query_terms = _tokens(query)
    task_terms = TASK_TYPE_TERMS.get(task_type, ())
    scored = []
    seen_ids = set()
    for rec in candidates:
        if rec["id"] in seen_ids:
            continue
        seen_ids.add(rec["id"])
        s = score_record(rec, query_terms, agent, task_terms, source_file)
        if s > 0:
            scored.append((s, rec))
    scored.sort(key=lambda t: (-t[0], t[1]["id"]))
    selected = []
    for s, rec in scored[:top_k]:
        rec = dict(rec)
        rec["_score"] = round(s, 3)
        selected.append(rec)

    if missing_required:
        status = ("MISSING_REQUIRED_CORPUS: "
                  + ", ".join(sorted(missing_required)))
    else:
        status = "ok"
    proof = {
        "timestamp": _utcnow(),
        "job_id": job_id,
        "agent": agent,
        "task_type": task_type,
        "query": query,
        "source_file": source_file,
        "current_phase": current_phase,
        "corpora_consulted": consulted,
        "records_considered": len(candidates),
        "records_selected": [r["id"] for r in selected],
        "decision_supported": bool(selected) and not missing_required,
        "status": "gate_failed" if missing_required else "ok",
        "gate": status,
    }
    RETRIEVAL_LOG.parent.mkdir(parents=True, exist_ok=True)
    with RETRIEVAL_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(proof, ensure_ascii=False) + "\n")

    if missing_required and strict:
        raise KnowledgeGateError(status)

    return {"required_corpora": required, "optional_corpora": optional,
            "selected_records": selected, "retrieval_proof": proof}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="EMBIZ retrieval router")
    ap.add_argument("agent")
    ap.add_argument("query")
    ap.add_argument("--job-id", default="cli")
    ap.add_argument("--task-type", default="vectorization")
    ap.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    res = route(a.agent, a.job_id, a.task_type, a.query,
                top_k=a.top_k, strict=a.strict)
    print(json.dumps({
        "gate": res["retrieval_proof"]["gate"],
        "selected": [{"id": r["id"], "score": r["_score"],
                      "snippet": (r.get("text") or "")[:160]}
                     for r in res["selected_records"]],
    }, indent=2, ensure_ascii=False))
