"""knowledge_ingest.py — Multimodal Knowledge Object ingestion for the EMBIZ
knowledge library.

Converts source documents (PDF, HTML pages/URLs, ZIP bundles of html/md) into
knowledge-object JSONL corpora that the retrieval router
(``knowledge_retrieval.py``) serves to the agents.

Knowledge-object schema (every record; retrieval tolerates missing fields):

    id               stable readable id: "<corpus>/<doc-slug>#p<page>c<chunk>"
    source_path      original document path or URL
    source_type      "pdf" | "html" | "url" | "markdown" | "image"
    section          corpus section (e.g. "raster-to-vector-agent")
    title            document title (PDF filename stem / HTML <title>)
    page             1-based page number (PDFs) or None
    chunk            0-based chunk index within the page/document
    text             the chunk text (extracted, never synthesized)
    summary          first ~200 chars of the chunk (lead sentence heuristic)
    visual_summary   text describing a visual element (figure captions found
                     in the source; None for plain text chunks)
    image_path       local path of an associated image, when one was saved
    caption          extracted figure/image caption or alt text
    tags             content-keyword tags (satin, density, bezier, ...)
    agent_relevance  persona keys this object primarily serves
    retrieval_modes  ["keyword", "tag", "agent"] (+"visual" for visual objects)
    related_objects  ids of sibling chunks (prev/next) for context expansion
    created_at       ISO-8601 UTC ingestion timestamp

Library-root discovery (the spec's primary roots exist on the user's local
machine, not necessarily in every container):

    1. $EMBIZ_KNOWLEDGE_ROOTS       colon-separated override, highest priority
    2. /root/web-archive/ai_agents_skills_library   (spec PRIMARY root)
    3. /root/EMBIZ_EXPORTS                          (spec secondary root)
    4. <repo>/knowledge/library                     (in-repo portable fallback)

CLI:
    python3 knowledge_ingest.py pdf  <file.pdf> <corpus-rel-dir> [--section S]
    python3 knowledge_ingest.py url  <https://...> <corpus-rel-dir>
    python3 knowledge_ingest.py zip  <bundle.zip> <corpus-rel-dir>
    python3 knowledge_ingest.py aggregate
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shutil
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------
# Library-root discovery
# --------------------------------------------------------------------------
SPEC_PRIMARY_ROOTS = (
    Path("/root/web-archive/ai_agents_skills_library"),
    Path("/root/EMBIZ_EXPORTS"),
)
REPO_LIBRARY_ROOT = REPO_ROOT / "knowledge" / "library"


def discover_library_roots(must_exist: bool = True) -> list[Path]:
    """All knowledge-library roots, primary first. The spec's /root paths are
    PRIMARY when present (the user's local machine); the in-repo
    ``knowledge/library`` is the portable fallback and is always last."""
    roots: list[Path] = []
    env = os.environ.get("EMBIZ_KNOWLEDGE_ROOTS", "")
    for part in env.split(":"):
        if part.strip():
            roots.append(Path(part.strip()))
    roots.extend(SPEC_PRIMARY_ROOTS)
    roots.append(REPO_LIBRARY_ROOT)
    seen, out = set(), []
    for r in roots:
        if r in seen:
            continue
        seen.add(r)
        if not must_exist or r.exists():
            out.append(r)
    return out


def writable_library_root() -> Path:
    """Root that ingestion writes into: the first discovered root that is
    writable, else the in-repo fallback (created on demand)."""
    for r in discover_library_roots(must_exist=True):
        if os.access(r, os.W_OK):
            return r
    REPO_LIBRARY_ROOT.mkdir(parents=True, exist_ok=True)
    return REPO_LIBRARY_ROOT


# --------------------------------------------------------------------------
# Chunking + tagging
# --------------------------------------------------------------------------
CHUNK_CHARS = 800
CHUNK_OVERLAP = 120

# content-keyword -> tag vocabulary (embroidery + vector domains)
TAG_KEYWORDS: dict[str, tuple[str, ...]] = {
    "satin": ("satin",),
    "density": ("density", "stitches per", "spacing"),
    "fill": ("fill", "tatami"),
    "path": ("path", "polyline", "subpath", " d="),
    "bezier": ("bezier", "bézier", "curve", "spline"),
    "trace": ("trace", "tracing", "potrace", "vectoriz", "bitmap"),
    "corner": ("corner", "sharp turn", "alphamax"),
    "pull-compensation": ("pull compensation", "pull-comp", "fabric pull"),
    "hoop": ("hoop",),
    "underlay": ("underlay",),
    "jump-stitch": ("jump stitch", "jump-stitch", "trim"),
    "thread": ("thread",),
    "svg": ("svg", "scalable vector"),
    "viewbox": ("viewbox", "view box"),
    "fill-rule": ("fill-rule", "fill rule", "evenodd", "nonzero"),
    "stroke": ("stroke",),
    "polygon": ("polygon", "polygonal"),
    "raster": ("raster", "bitmap", "pixel"),
    "anchor": ("anchor", "node", "control point"),
    "color": ("color", "colour", "palette"),
    "lettering": ("letter", "font", "text element", "typograph"),
    "machine": ("machine", "bernina", "b700", "b 700"),
    "despeckle": ("despeckle", "turdsize", "speckle", "noise"),
    "threshold": ("threshold", "blacklevel", "bilevel"),
    "smoothing": ("smooth", "opttolerance", "opticurve"),
    "gradient": ("gradient",),
    "layers": ("layer",),
    "stabilizer": ("stabilizer", "stabiliser", "interfacing"),
}

_FIGURE_RE = re.compile(
    r"(Figure\s+\d+[a-z]?\s*[:.–-]\s*[^\n]{3,240})", re.IGNORECASE)
_WS_RE = re.compile(r"[ \t ]+")


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _slug(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-")
    return s[:80] or "doc"


def _clean(text: str) -> str:
    text = text.replace("\r", "")
    text = _WS_RE.sub(" ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def tag_text(text: str) -> list[str]:
    low = text.lower()
    return sorted(t for t, kws in TAG_KEYWORDS.items()
                  if any(k in low for k in kws))


def chunk_text(text: str, size: int = CHUNK_CHARS,
               overlap: int = CHUNK_OVERLAP) -> list[str]:
    """~`size`-char chunks with `overlap`, preferring sentence/whitespace
    boundaries near the cut point."""
    text = _clean(text)
    if not text:
        return []
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            window = text[start:end]
            cut = max(window.rfind(". "), window.rfind(".\n"),
                      window.rfind("\n"))
            if cut > size // 2:
                end = start + cut + 1
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def _summary(text: str, limit: int = 200) -> str:
    first = text.split(". ")[0].strip()
    if len(first) < 40 and len(text) > len(first):
        first = text[:limit]
    return (first[:limit].rstrip() + ("…" if len(first) > limit else ""))


def make_object(*, corpus: str, doc_slug: str, source_path: str,
                source_type: str, section: str, title: str,
                page: int | None, chunk: int, text: str,
                agent_relevance: list[str],
                visual_summary: str | None = None,
                image_path: str | None = None,
                caption: str | None = None) -> dict:
    modes = ["keyword", "tag", "agent"]
    if visual_summary or image_path or caption:
        modes.append("visual")
    pg = f"p{page}" if page is not None else "p0"
    return {
        "id": f"{corpus}/{doc_slug}#{pg}c{chunk}",
        "source_path": source_path,
        "source_type": source_type,
        "section": section,
        "title": title,
        "page": page,
        "chunk": chunk,
        "text": text,
        "summary": _summary(text),
        "visual_summary": visual_summary,
        "image_path": image_path,
        "caption": caption,
        "tags": tag_text(text + " " + (caption or "")),
        "agent_relevance": agent_relevance,
        "retrieval_modes": modes,
        "related_objects": [],
        "created_at": _utcnow(),
    }


def _link_siblings(objects: list[dict]) -> None:
    for i, obj in enumerate(objects):
        rel = []
        if i > 0:
            rel.append(objects[i - 1]["id"])
        if i + 1 < len(objects):
            rel.append(objects[i + 1]["id"])
        obj["related_objects"] = rel


def _append_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _load_existing_ids(path: Path) -> set[str]:
    ids = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                ids.add(json.loads(line).get("id"))
            except ValueError:
                continue
    return ids


# --------------------------------------------------------------------------
# PDF ingestion
# --------------------------------------------------------------------------
def ingest_pdf(pdf_path: str | Path, corpus_rel: str,
               agent_relevance: list[str], section: str | None = None,
               library_root: Path | None = None,
               copy_source: bool = True) -> dict:
    """Extract per-page text with pypdf, chunk, tag, and append to
    <root>/<corpus_rel>/knowledge_objects.jsonl. Figure captions found in the
    page text become visual objects in visual_captions.jsonl (extracted, not
    synthesized). Embedded-image counts per page are recorded factually."""
    from pypdf import PdfReader

    pdf_path = Path(pdf_path)
    root = library_root or writable_library_root()
    corpus_dir = root / corpus_rel
    corpus = corpus_rel.rstrip("/").split("/")[-1]
    section = section or corpus
    title = re.sub(r"^[0-9a-f]{8}-", "", pdf_path.stem).replace("_", " ")
    doc_slug = _slug(title)

    reader = PdfReader(str(pdf_path))
    objects: list[dict] = []
    visuals: list[dict] = []
    for pno, pdfpage in enumerate(reader.pages, start=1):
        try:
            text = pdfpage.extract_text() or ""
        except Exception:
            text = ""
        try:
            n_images = len(pdfpage.images)
        except Exception:
            n_images = 0
        captions = _FIGURE_RE.findall(text)
        for ci, cap in enumerate(captions):
            cap = _clean(cap)
            visuals.append(make_object(
                corpus=corpus, doc_slug=doc_slug + "-fig",
                source_path=str(pdf_path), source_type="pdf",
                section=section, title=title, page=pno, chunk=ci,
                text=cap, agent_relevance=agent_relevance,
                visual_summary=cap, caption=cap))
        for ci, piece in enumerate(chunk_text(text)):
            obj = make_object(
                corpus=corpus, doc_slug=doc_slug, source_path=str(pdf_path),
                source_type="pdf", section=section, title=title, page=pno,
                chunk=ci, text=piece, agent_relevance=agent_relevance)
            if n_images:
                obj["visual_summary"] = (
                    f"page {pno} of '{title}' embeds {n_images} image(s) "
                    f"alongside this text")
                if "visual" not in obj["retrieval_modes"]:
                    obj["retrieval_modes"].append("visual")
            objects.append(obj)
    _link_siblings(objects)

    out = corpus_dir / "knowledge_objects.jsonl"
    existing = _load_existing_ids(out)
    new_objs = [o for o in objects if o["id"] not in existing]
    _append_jsonl(out, new_objs)
    if visuals:
        vout = corpus_dir / "visual_captions.jsonl"
        vexist = _load_existing_ids(vout)
        _append_jsonl(vout, [v for v in visuals if v["id"] not in vexist])

    src_copy = None
    if copy_source:
        sources = root / "sources"
        sources.mkdir(parents=True, exist_ok=True)
        src_copy = sources / pdf_path.name
        if not src_copy.exists():
            shutil.copy2(pdf_path, src_copy)
    return {"source": str(pdf_path), "corpus": corpus_rel,
            "pages": len(reader.pages), "objects": len(new_objs),
            "visual_captions": len(visuals), "output": str(out),
            "source_copy": str(src_copy) if src_copy else None}


# --------------------------------------------------------------------------
# HTML ingestion
# --------------------------------------------------------------------------
class _TextExtractor(HTMLParser):
    """Tag-stripping text extractor that also collects <title>, headings and
    image alt/figcaption text."""

    _SKIP = {"script", "style", "noscript", "template", "head"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.title = ""
        self.images: list[dict] = []
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True
        if tag == "img":
            a = dict(attrs)
            self.images.append({"src": a.get("src", ""),
                                "alt": a.get("alt", ""),
                                "title": a.get("title", "")})
        if tag in {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4",
                   "section", "article", "figcaption"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self._SKIP and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._in_title:
            self.title += data
        else:
            self.parts.append(data)

    @property
    def text(self) -> str:
        return _clean("".join(self.parts))


def fetch_url(url: str, timeout: int = 45) -> tuple[bytes | None, str | None]:
    """Fetch a URL honoring the container's HTTPS proxy + CA bundle. Returns
    (content, error). Never raises."""
    import requests
    verify = os.environ.get("REQUESTS_CA_BUNDLE") \
        or ("/root/.ccr/ca-bundle.crt"
            if os.path.exists("/root/.ccr/ca-bundle.crt") else True)
    try:
        resp = requests.get(url, timeout=timeout, verify=verify, headers={
            "User-Agent": "Mozilla/5.0 (EMBIZ knowledge_ingest)"})
        if resp.status_code != 200:
            return None, f"HTTP {resp.status_code}"
        return resp.content, None
    except Exception as exc:  # noqa: BLE001 — callers log honestly
        return None, f"{type(exc).__name__}: {exc}"


def ingest_html(source: str, corpus_rel: str, agent_relevance: list[str],
                section: str | None = None, library_root: Path | None = None,
                html_text: str | None = None) -> dict:
    """Ingest an HTML document from a URL, local file, or literal text.
    Image alt/figcaption text is stored into visual_captions.jsonl."""
    root = library_root or writable_library_root()
    corpus_dir = root / corpus_rel
    corpus = corpus_rel.rstrip("/").split("/")[-1]
    section = section or corpus

    source_type = "url" if source.startswith("http") else "html"
    if html_text is None:
        if source.startswith("http"):
            content, err = fetch_url(source)
            if err:
                return {"source": source, "corpus": corpus_rel,
                        "objects": 0, "error": err}
            html_text = content.decode("utf-8", errors="replace")
        else:
            html_text = Path(source).read_text(encoding="utf-8",
                                               errors="replace")

    parser = _TextExtractor()
    try:
        parser.feed(html_text)
    except Exception as exc:  # malformed markup: keep whatever was parsed
        parser.parts.append(f"\n[parser stopped: {exc}]")
    title = _clean(parser.title) or _slug(source.rsplit("/", 1)[-1])
    doc_slug = _slug(source.rstrip("/").rsplit("/", 1)[-1] or title)

    objects = [make_object(
        corpus=corpus, doc_slug=doc_slug, source_path=source,
        source_type=source_type, section=section, title=title, page=None,
        chunk=ci, text=piece, agent_relevance=agent_relevance)
        for ci, piece in enumerate(chunk_text(parser.text))]
    _link_siblings(objects)

    visuals = []
    for vi, img in enumerate(parser.images):
        cap = _clean(img.get("alt") or img.get("title") or "")
        if not cap:
            continue
        visuals.append(make_object(
            corpus=corpus, doc_slug=doc_slug + "-img", source_path=source,
            source_type="image", section=section, title=title, page=None,
            chunk=vi, text=cap, agent_relevance=agent_relevance,
            visual_summary=cap, caption=cap,
            image_path=img.get("src") or None))

    out = corpus_dir / "knowledge_objects.jsonl"
    existing = _load_existing_ids(out)
    new_objs = [o for o in objects if o["id"] not in existing]
    _append_jsonl(out, new_objs)
    if visuals:
        vout = corpus_dir / "visual_captions.jsonl"
        vexist = _load_existing_ids(vout)
        _append_jsonl(vout, [v for v in visuals if v["id"] not in vexist])
    return {"source": source, "corpus": corpus_rel, "title": title,
            "objects": len(new_objs), "visual_captions": len(visuals),
            "output": str(out)}


def ingest_image_caption(url: str, corpus_rel: str, caption: str,
                         agent_relevance: list[str],
                         library_root: Path | None = None,
                         download: bool = True,
                         max_bytes: int = 2_000_000) -> dict:
    """Caption entry for a standalone image URL; downloads the image into
    <root>/sources/ when reachable and small."""
    root = library_root or writable_library_root()
    corpus_dir = root / corpus_rel
    corpus = corpus_rel.rstrip("/").split("/")[-1]
    image_path, err = None, None
    if download:
        content, err = fetch_url(url)
        if content and len(content) <= max_bytes:
            dest = root / "sources" / url.rsplit("/", 1)[-1]
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)
            image_path = str(dest)
    obj = make_object(
        corpus=corpus, doc_slug=_slug(url.rsplit("/", 1)[-1]),
        source_path=url, source_type="image", section=corpus,
        title=url.rsplit("/", 1)[-1], page=None, chunk=0, text=caption,
        agent_relevance=agent_relevance, visual_summary=caption,
        caption=caption, image_path=image_path)
    vout = corpus_dir / "visual_captions.jsonl"
    if obj["id"] not in _load_existing_ids(vout):
        _append_jsonl(vout, [obj])
    return {"source": url, "corpus": corpus_rel, "objects": 1,
            "image_saved": image_path, "fetch_error": err,
            "output": str(vout)}


# --------------------------------------------------------------------------
# ZIP ingestion
# --------------------------------------------------------------------------
def ingest_zip(zip_path: str | Path, corpus_rel: str,
               agent_relevance: list[str],
               library_root: Path | None = None) -> dict:
    """Extract a ZIP (e.g. inkstitch-gh-pages.zip) and ingest every
    .html/.htm/.md file inside it."""
    zip_path = Path(zip_path)
    root = library_root or writable_library_root()
    extract_dir = root / "sources" / (zip_path.stem + "_extracted")
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_dir)
    results, total = [], 0
    for p in sorted(extract_dir.rglob("*")):
        if p.suffix.lower() not in {".html", ".htm", ".md", ".markdown"}:
            continue
        if p.suffix.lower() in {".md", ".markdown"}:
            text = p.read_text(encoding="utf-8", errors="replace")
            res = ingest_html(str(p), corpus_rel, agent_relevance,
                              library_root=root,
                              html_text=f"<title>{p.stem}</title>" + text)
        else:
            res = ingest_html(str(p), corpus_rel, agent_relevance,
                              library_root=root)
        results.append(res)
        total += res.get("objects", 0)
    return {"source": str(zip_path), "corpus": corpus_rel,
            "files_ingested": len(results), "objects": total}


# --------------------------------------------------------------------------
# Aggregation
# --------------------------------------------------------------------------
def aggregate(library_root: Path | None = None) -> dict:
    """Rebuild <root>/global_knowledge_objects.jsonl (every object in every
    corpus under the root) and global_knowledge_objects.multimodal.jsonl
    (objects with visual fields)."""
    root = library_root or writable_library_root()
    all_objs: list[dict] = []
    for p in sorted(root.rglob("*.jsonl")):
        if p.name.startswith("global_knowledge_objects"):
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                all_objs.append(json.loads(line))
            except ValueError:
                continue
    seen, unique = set(), []
    for o in all_objs:
        oid = o.get("id") or json.dumps(o, sort_keys=True)[:64]
        if oid in seen:
            continue
        seen.add(oid)
        unique.append(o)
    multimodal = [o for o in unique if o.get("visual_summary")
                  or o.get("image_path") or o.get("caption")]
    gpath = root / "global_knowledge_objects.jsonl"
    mpath = root / "global_knowledge_objects.multimodal.jsonl"
    with gpath.open("w", encoding="utf-8") as fh:
        for o in unique:
            fh.write(json.dumps(o, ensure_ascii=False) + "\n")
    with mpath.open("w", encoding="utf-8") as fh:
        for o in multimodal:
            fh.write(json.dumps(o, ensure_ascii=False) + "\n")
    return {"root": str(root), "objects": len(unique),
            "multimodal_objects": len(multimodal),
            "global": str(gpath), "multimodal": str(mpath)}


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("pdf", "url", "zip"):
        sp = sub.add_parser(name)
        sp.add_argument("source")
        sp.add_argument("corpus_rel")
        sp.add_argument("--section", default=None)
        sp.add_argument("--agents", default="mabel",
                        help="comma-separated persona keys")
    sub.add_parser("aggregate")
    args = ap.parse_args(argv)
    if args.cmd == "aggregate":
        print(json.dumps(aggregate(), indent=2))
        return 0
    agents = [a.strip() for a in args.agents.split(",") if a.strip()]
    if args.cmd == "pdf":
        res = ingest_pdf(args.source, args.corpus_rel, agents,
                         section=args.section)
    elif args.cmd == "zip":
        res = ingest_zip(args.source, args.corpus_rel, agents)
    else:
        res = ingest_html(args.source, args.corpus_rel, agents,
                          section=args.section)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
