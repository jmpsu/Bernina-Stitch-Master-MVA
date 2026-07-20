# GLOSSARY — #AUTH-04_GLOSSARY

- **Worker** — the model executing one step at a time under the contract.
- **Supervisor** — `engine/supervisor.py`; owns the loop, routing, retries, hashes.
- **Step** — one narrowly scoped instruction file with the fixed anatomy.
- **STEP id / hashtag** — e.g. `#S04-07_POTRACE_PARAM_SWEEP`; globally unique.
- **Route** — the declared `ON SUCCESS →` / `ON FAILURE →` destination of a step.
- **Classification** — the single token `SUCCESS` or `FAILURE` a step ends with.
- **Evidence artifact** — `evidence/<STEP>.json`; real commands + output + files.
- **Hash chain** — `state/hash_chain.jsonl`; append-only SHA-256 of each evidence
  artifact linked to the previous hash (Temporal-style durable audit history).
- **Attempt ledger** — `state/attempts.jsonl`; every attempt at every step id.
- **Recovery branch** — `recovery/` diagnosis→repair→verify steps that return to
  the exact failed step (AWS Step Functions-style catcher after retries).
- **Canonical artifact** — a durable pipeline output consumed downstream
  (e.g. `job.json`, `production.svg`, `stitch_plan.json`, `*.pes`).
- **Idle work** — prescribed autonomous improvement executed when no job is active
  (Airflow-style task lifecycle; never truly idle).
- **Acceptance predicate** — a binary condition; all must hold for `SUCCESS`.
- **Binary evidence question** — a YES/NO question the worker must answer verbatim.

## Design lineage (why the machinery looks the way it does)
- **Temporal** → append-only event/hash history; recovery from recorded state;
  continue-as-new style idle loop before history grows unmanageable.
- **AWS Step Functions** → bounded retries then a mandatory catcher destination;
  typed failure routes (`States.ALL`, `States.Timeout`, etc.) → recovery classes.
- **W3C SCXML** → named states, guarded transitions, `onentry`/`onexit` actions;
  no destination is ever inferred from prose — only declared routes are legal.
- **Apache Airflow** → observable task lifecycle states (`up_for_retry`,
  `failed`, `success`) mapped onto the attempt ledger and dashboards.
