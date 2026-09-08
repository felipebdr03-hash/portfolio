# Developer ↔ Auditor Protocol

## Objective
Create a controlled review loop between two Codex chats working on the same repository.

## Roles
- Developer: `.codex/DEVELOPER.md`
- Auditor: `.codex/AUDITOR.md`

## Shared state
The Git repository is the source of truth.

The auditor should inspect:
- current files;
- git status;
- git diff;
- tests;
- AUDIT.md when present.

## Cycle

### Phase 1: Developer
1. Implement the change.
2. Run tests.
3. Review the diff.
4. Tell the user it is ready for audit.

### Phase 2: Auditor
1. Inspect the repository.
2. Inspect the diff.
3. Run relevant tests/checks.
4. Attack the methodology.
5. Report PASS, PASS WITH WARNINGS, or FAIL.

### Phase 3: Developer correction
If FAIL or actionable warnings exist:
1. Read the audit.
2. Fix valid findings.
3. Rerun tests.
4. Prepare for another audit.

## Safety
- Maximum 3 correction/audit cycles for one change.
- Never accept an audit merely because code executes.
- Never hide findings to obtain PASS.
- Do not commit automatically.
- If agents disagree, stop and explain the disagreement.

## Developer command
Read `.codex/DEVELOPER.md` and `.codex/PROTOCOL.md`. Inspect the repository and implement the requested task.

## Auditor command
Read `.codex/AUDITOR.md` and `.codex/PROTOCOL.md`. Audit the current repository and latest changes. Be adversarial, especially about temporal leakage and walk-forward validity.

## Correction command
Read `AUDIT.md`, address every valid CRITICAL and MAJOR finding, run tests, and prepare the corrected version for another audit.
