# Bernina-Stitch-Master-MVA
High-Precision Image-to-Embroidery Vectorization Framework

> **Start here:** [`docs/SYSTEM_ATLAS.md`](docs/SYSTEM_ATLAS.md) — the
> definitive system documentation: operation status across branches, graph
> maps of the agents/pipeline/knowledge library, an exact developer
> replication guide, the knowledge-library deep dive with real retrieval
> proofs, and the incremental-improvement evidence (real scores from
> `vectorization_attempts.jsonl`). See also [`OUTPUTS.md`](OUTPUTS.md) for
> every artifact the system produces.

## Architecture & Optimization Loop

This repository runs a closed-loop optimization framework that measures the
SVG/PES corpus, scores it, and records observations so future iterations can
learn which parameters improve quality.

### Components

- **`metrics.py`** — the measurement module (stdlib + `pyembroidery` only).
  - `svg_metrics(path)`: parses an SVG with `xml.etree` (namespace-agnostic) and
    returns `valid`, `path_count`, `node_count` (count of path-command letters
    across all `d` attributes), `group_count`, `element_count`, `bytes`.
  - `pes_metrics(path)`: reads a PES with `pyembroidery` and returns
    `stitch_count`, `jump_count`, `trim_count`, `color_change_count`,
    `color_count`, `width_mm`, `height_mm`, `total_travel_mm`,
    `avg_stitch_length_mm`, `stitch_density_per_cm2`, `bytes`. PES units are
    1/10 mm, so lengths are divided by 10.
  - Both functions are robust: they never raise on a bad file and instead return
    `{"valid": false, "error": "..."}`.

- **`run_iteration.py`** — the CLI runner. It discovers the corpus (all `.svg`
  under `vector_source/`, all `.pes` under `stitch_files/`), measures every file
  while timing it with `time.perf_counter`, computes a weighted
  `OVERALL_SCORE`, writes reports, and appends to the ledgers.

### TEST_BATCH_SIZE

The runner reads the `TEST_BATCH_SIZE` environment variable (default `ALL`).
It accepts an integer (limits each of the SVG and PES lists to that many files)
or `ALL` (measure everything).

```sh
TEST_BATCH_SIZE=ALL python3 run_iteration.py   # measure the whole corpus
TEST_BATCH_SIZE=2   python3 run_iteration.py   # measure 2 SVGs + 2 PES
```

### Outputs and ledger files

- **`reports/iteration_<N>.json`** and **`reports/iteration_<N>.md`** — the
  per-iteration report (auto-incremented `N`), containing the full per-file
  metric tables, sub-scores, and the OVERALL_SCORE.
- **`observations.jsonl`** — one JSON line per measured artifact, each tagged
  with `iteration`, `timestamp`, and `artifact`.
- **`decision_trace.jsonl`** — one record per iteration capturing the
  `objective`, `hypothesis`, `decision`, and `overall_score`.
- **`reward_penalty_ledger.jsonl`** — reward/penalty record per iteration
  (iteration 1 has `reward=0` because there is no prior score to compare).
- **`parameter_correlation_index.json`** — known optimization parameters
  (`min_len_mm=1.2` from `stitchscale_L3.sh`, plus inkstitch defaults
  `collapse_len_mm=3.0` and `min_stitch_len_mm=0.25`) with an empty
  correlation history to be filled by future iterations.

### Scoring weights (`weights.json`)

| Dimension | Weight | Meaning |
|---|---|---|
| `visual_similarity` | 0.40 | How closely the stitched/vector output matches the source raster image (SSIM / RMSE / edge-overlap). |
| `topology_quality` | 0.25 | Structural health of the vector tracing — valid SVG and reasonable node-per-path ratios. |
| `embroidery_suitability` | 0.20 | Whether the stitch density sits in a machine-friendly range (~40-120 st/cm²). |
| `performance` | 0.10 | Measurement/processing runtime — faster is better. |
| `code_reliability` | 0.05 | Fraction of files measured without error. |

### Known limitation (deferred)

`visual_similarity` (SSIM / RMSE / edge-overlap) requires source raster images
in `reference_images/`. That directory is not yet present (it is also
git-ignored), so this dimension cannot be computed yet. The runner records
`visual_similarity` as **null** for the current iteration and **renormalizes**
the remaining weights so they sum to 1.0; no SSIM value is fabricated. Wiring
up real visual-similarity metrics is deferred to a future iteration once
reference images are added.
