# PROHIBITIONS — #AUTH-02_PROHIBITIONS

> Authority file. Each prohibition below, if violated, forces an immediate
> `FAILURE` on the current step and routes to that section's `recovery/` diagnosis
> step. The verifier and transition guard enforce these mechanically where they
> can; the rest are enforced by the contract you are bound to.

| # | Prohibited behavior | Why it exists (failure mode it closes) | Detected by |
|---|---------------------|----------------------------------------|-------------|
| P1 | Placeholder / stub / mock where real is required | False completion, fragmentation | `evidence_verifier.py` token scan |
| P2 | Claiming `SUCCESS` without a hashed evidence file | Unsupported completion | `hash_chain.py` + verifier |
| P3 | Doing more than the one declared action | Scope creep, unrequested rewrites | Contract clause 6; diff review in evidence |
| P4 | Editing files not named as the step target | Fragmentation, regressions | Evidence must list changed paths; guard compares |
| P5 | Choosing a destination not declared by the step | Autonomous direction-picking | `transition_guard.py` route allow-list |
| P6 | Deleting/"cleaning up" working code not targeted | Loss of working production behavior | Evidence diff review |
| P7 | Continuing past a `FAILURE` | Skipping recovery, compounding errors | Supervisor forces failure route |
| P8 | Stopping / idling when a route exists | Idle drift, context loss | Never-idle rule; supervisor re-loads |
| P9 | Fabricating command output | False completion | Verifier requires captured real stdout/stderr |
| P10 | Using customer artwork before test artwork is proven (Ink/Stitch) | Production risk | Step gating in `07_stitch_validation` |
| P11 | Large heredoc for large files | Transmission corruption (BRD-documented) | Steps require file-based writes + `py_compile` preflight |
| P12 | Skipping mandatory knowledge retrieval before an implementation decision | Static-library risk (BRD-documented) | `01_knowledge_library` gate + decision-trace requirement |
| P13 | Merging or reordering the ten contract clauses | Erodes auditability | Contract clause order is fixed |
| P14 | Sending outward-facing messages without the approval gate | Irreversible external action | Slack/customer steps gate on approval |

## Documented rationalizations that are NOT acceptable
- "It's basically done, I'll add the evidence later." → P2 FAILURE.
- "The test artwork is trivial, I'll just use the real logo." → P10 FAILURE.
- "While fixing this I noticed a nearby bug and fixed it too." → P3/P4 FAILURE.
- "The command clearly would pass, no need to run it." → P9 FAILURE.
- "This step's route is obviously wrong, I'll go where it makes sense." → P5 FAILURE.
- "I'll stub the vectorizer and wire the real one next iteration." → P1 FAILURE.

## Red flags that mean you are about to violate a prohibition
- You are typing a file path into an edit that the step did not list as its target.
- You are about to write `SUCCESS` but `evidence/<step>.json` does not yet exist.
- You are about to pick a "next step" that is not clause-2 or clause-3.
- You are about to reason "the requirement is vague so I'll decide the scope."
  (Scope is never yours to decide; if a step is ambiguous, that ambiguity is a
  `FAILURE` that routes to recovery, which sharpens the step — it does not let you
  freelance.)
