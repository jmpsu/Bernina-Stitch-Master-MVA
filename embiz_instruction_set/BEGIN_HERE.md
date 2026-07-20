# BEGIN_HERE — #BEGIN

<!-- This is the single entry point. A worker dropped into this Project folder
     starts here and nowhere else. This file is authority-adjacent: it only ever
     routes you INTO the supervised loop. It does not itself do pipeline work. -->

## ROUTING HEADER
- STEP: #BEGIN
- FILE: BEGIN_HERE.md
- ON SUCCESS →: #S00-01_TOOLING_INVENTORY @ workflows/00_bootstrap_environment/S00-01_TOOLING_INVENTORY.md
- ON FAILURE →: #REC-BOOT_DIAGNOSE @ recovery/REC-BOOT_DIAGNOSE.md
- SECTION: BOOT

## READ THESE FIRST (in this order), THEN STOP READING AND ACT
1. `authority/00_MASTER_CONTRACT.md` — the ten-clause step contract that binds you.
2. `authority/01_OBJECTIVE_HIERARCHY.md` — how ties break.
3. `authority/02_PROHIBITIONS.md` — what forces an immediate FAILURE.
4. `authority/03_STEP_ANATOMY.md` — the fixed shape of every step.
5. `authority/04_GLOSSARY.md` — vocabulary + design lineage.

You do NOT read the whole `workflows/` tree. You read one step at a time, only
when the supervisor hands it to you.

## THE ONE ACTION
Initialize the supervised loop and obtain your first step:

```bash
cd embiz_instruction_set
python3 engine/supervisor.py --init
python3 engine/supervisor.py --current
```

`--init` verifies the manifest exists (regenerating it if needed via
`engine/generate_steps.py`), seeds `state/CURRENT_STEP` with `#S00-01_TOOLING_INVENTORY`,
and prints the path of the step file to open next.

## ACCEPTANCE PREDICATES (ALL true → SUCCESS)
- [ ] `manifest/steps_index.json` exists and parses.
- [ ] `state/CURRENT_STEP` contains `#S00-01_TOOLING_INVENTORY`.
- [ ] The supervisor printed the path
      `workflows/00_bootstrap_environment/S00-01_TOOLING_INVENTORY.md`.

## BINARY EVIDENCE QUESTIONS (YES/NO only)
- Q1: Was a hash-tagged evidence file saved to `evidence/BEGIN.json`? 
- Q2: Do the results satisfying the immediate objective classify as a SUCCESS?
- Q3: Does `state/CURRENT_STEP` now name the first pipeline step?

## EXECUTION CONTRACT
1. State this step id: `#BEGIN`.
2. State SUCCESS route: `#S00-01_TOOLING_INVENTORY` @
   `workflows/00_bootstrap_environment/S00-01_TOOLING_INVENTORY.md`.
3. State FAILURE route: `#REC-BOOT_DIAGNOSE` @ `recovery/REC-BOOT_DIAGNOSE.md`.
4. Immediate objective (your words): bring the supervised loop online and get step one.
5. Overall objective (your words): stand up the closed, never-idle execution loop.
6. Perform ONLY the one action above.
7. Write `evidence/BEGIN.json`; append its hash to `state/hash_chain.jsonl`.
8. Answer Q1–Q3 YES/NO.
9. Emit exactly `SUCCESS` or `FAILURE`.
10. Run `python3 engine/supervisor.py --resolve '#BEGIN' --classification SUCCESS`
    (or `FAILURE`) and proceed to the destination it prints. Do not stop.
