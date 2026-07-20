# STEP ANATOMY — #AUTH-03_STEP_ANATOMY

> Authority file. Defines the exact shape of every generated step file so the
> worker always knows where to look and the supervisor can parse routes. Every
> file under `workflows/` and `recovery/` conforms to this anatomy. Step bodies
> are produced by `engine/generate_steps.py` from the manifest so the structural
> language is identical across all steps and cannot drift.

A step file has this fixed section order:

```
# <HASHTAG STEP ID> — <Human Title>
<!-- generated: do not hand-edit. Edit engine/generate_steps.py and regenerate. -->

## ROUTING HEADER
- STEP: <#HASHTAG STEP ID>
- FILE: <relative path of this file>
- ON SUCCESS →: <#HASHTAG next step id>  @ <relative path>
- ON FAILURE →: <#HASHTAG recovery step id> @ <relative path>
- SECTION: <section id and name>
- ATTEMPT LEDGER: state/attempts.jsonl (key = this STEP id)

## OBJECTIVES
- IMMEDIATE OBJECTIVE: <one declared sentence>
- OVERALL OBJECTIVE (section): <one declared sentence>

## INPUTS YOU MAY READ
- <explicit file list; you read only these plus this step>

## THE ONE ACTION
<exactly one action, imperative, unambiguous>

## COMMAND(S) TO RUN
```bash
<real command(s) that produce evidence>
```

## EVIDENCE TO PRODUCE
- WRITE: evidence/<STEP>.json  (schema: contracts/evidence_schema.json)
- MUST CONTAIN: commands, real stdout/stderr, files+line ranges, predicate results
- HASH: append SHA-256 to state/hash_chain.jsonl via engine/hash_chain.py

## ACCEPTANCE PREDICATES (ALL must be true for SUCCESS)
- [ ] <predicate 1>
- [ ] <predicate 2>
- ...

## BINARY EVIDENCE QUESTIONS (answer YES or NO only)
- Q1 (mandatory): Was a hash-tagged evidence file saved to evidence/<STEP>.json?
- Q2 (mandatory): Do the results satisfying the immediate objective classify as SUCCESS?
- Q3..Qn: <step-specific YES/NO questions>

## BRD REQUIREMENTS IMPLEMENTED BY THIS STEP
- <verbatim requirement labels / line refs from the BRD>

## EXECUTION CONTRACT (recite clauses 1–10 from authority/00_MASTER_CONTRACT.md)
1. State this step id.
2. State SUCCESS route + location.
3. State FAILURE route + location.
4. State immediate objective in your own words.
5. State overall objective in your own words.
6. Perform ONLY the one action.
7. Produce the hashed evidence artifact.
8. Answer every binary evidence question YES/NO.
9. Emit exactly SUCCESS or FAILURE.
10. Declare the destination and return control to the supervisor immediately.
```

## How you run one step (the only loop you participate in)
1. The supervisor writes the chosen step id to `state/CURRENT_STEP` and prints its
   path. Read that step file and only the inputs it lists.
2. Recite clauses 1–5 (understanding + routes).
3. Perform clause 6 (the one action) and clause 7 (evidence + hash).
4. Recite clause 8 (YES/NO questions), then clause 9 (SUCCESS or FAILURE).
5. Run `python3 engine/supervisor.py --resolve <STEP> --classification <SUCCESS|FAILURE>`.
   The supervisor validates your evidence with the verifier, enforces the route
   with the transition guard, records the attempt + hash, and writes the next
   `state/CURRENT_STEP`. Go to 1. You never select the next id yourself.
