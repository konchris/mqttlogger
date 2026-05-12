# Speckit-INCOSE Skill Pack — Upstream Feedback

**Feature:** 002-mqttlogger-baseline
**Date:** 2026-05-10
**Author:** Chris (christopher.r.espy@gmail.com)
**Context:** First end-to-end run of the SE skill sequence through Phase 2 (planning), prior to `/se-architecture`. Issues discovered during actual use, not during review.

---

## Issue 1 — `se-architecture` pre-condition path mismatch for `plan.md`

### Symptom

`se-architecture` declares this pre-condition:

```
specs/$FEATURE_ID/07-plan/plan.md must exist.
This is the output of /speckit-plan. Read it.
```

When a user follows the instruction and runs `/speckit-plan`, it does **not** create `07-plan/plan.md`. It creates `plan.md` directly in the feature root:

```
specs/$FEATURE_ID/plan.md      ← what /speckit-plan actually creates
specs/$FEATURE_ID/07-plan/plan.md  ← what /se-architecture expects
```

The user then re-runs `/speckit-plan`, discovers the mismatch, and must manually create the `07-plan/` directory and either move or recreate the file there.

### Root Cause

`/speckit-plan` uses the path template `$FEATURE_DIR/plan.md` (from `common.sh` → `get_feature_paths`). It has no knowledge of the SE numbered-directory convention (`07-plan/`).

### Impact

- Workflow blocks at `/se-architecture` gate with a confusing "file not found" message
- User must diagnose the path mismatch manually; no error message from `/se-architecture` explains the discrepancy between what `/speckit-plan` produces and what is expected
- A stray `plan.md` is created in the feature root and must be removed

### Proposed Fix Options

**Option A (preferred) — Update `/speckit-plan` to respect SE layout:**
Add a convention: if the feature directory contains any numbered SE phase subdirectories (`00-*`, `01-*`, etc.), write the plan to `07-plan/plan.md` instead of the feature root. This makes `/speckit-plan` SE-aware without breaking non-SE projects.

**Option B — Update `/se-architecture` to accept both paths:**
Change the pre-condition to check `07-plan/plan.md` first, then fall back to `plan.md` at the feature root. Document that both locations are acceptable.

**Option C — Introduce `/se-plan` skill:**
Create a dedicated SE planning skill that knows to write to `07-plan/plan.md` and can read SE artifacts (ConOps, NFRs, explore-summary) in place of `spec.md`. The pre-condition in `/se-architecture` would reference `/se-plan` instead of `/speckit-plan`. This cleanly separates the SE workflow from the speckit workflow.

**Workaround (documented in local `se-architecture.md` copy):**
After running `/speckit-plan`, manually move/recreate the output at `07-plan/plan.md`.

---

## Issue 2 — `04-requirements/requirements-register.md` has no creating skill

### Symptom

`se-architecture` declares this pre-condition:

```
specs/$FEATURE_ID/04-requirements/requirements-register.md must exist. Read it.
```

No skill in the SE pack creates this file. There is no `/se-requirements` command. The user is left without a path to satisfy this pre-condition through the documented workflow.

### Root Cause

The requirements register is a Phase 2 artifact in the INCOSE SE process. The SE skill pack appears to be missing the requirements elicitation phase entirely between `/se-nfr` (NFRs) and `/se-architecture` (architecture).

### Impact

- User must manually derive functional requirements from ConOps, NFRs, and the explore convergence decision — a substantial task with no skill scaffolding
- Without guidance, requirements may miss IEEE 29148 quality attributes
- The pre-condition in `/se-architecture` implies this file should exist but provides no path to create it

### Proposed Fix

**Create `/se-requirements` skill** that:
1. Reads ConOps (operational modes, success criteria) to derive functional requirements
2. Reads NFRs to identify driven functional requirements
3. Reads `explore-summary.md` convergence decision to capture new requirements from the selected solution
4. Applies IEEE 29148 quality attribute checks (Necessary, Unambiguous, Verifiable, Consistent, Complete, Singular, Feasible, Traceable) to every derived requirement
5. Writes `04-requirements/requirements-register.md` in a standard format
6. Seeds `09-vv/vv-plan.md` with a V&V entry for every new functional requirement

**Interim workaround (documented in local `se-architecture.md` copy):**
Create `04-requirements/requirements-register.md` manually. Derive FRs from ConOps success criteria and operational modes, NFRs (as driven requirements), and the explore convergence decision. Apply IEEE 29148 quality attributes manually.

---

## Issue 3 — `/speckit-plan` cannot read SE feature directories

### Symptom

`/speckit-plan` expects a `spec.md` file at the feature root (`$FEATURE_DIR/spec.md`). SE features do not have a `spec.md` — they have a set of numbered phase directories (`00-stakeholders/`, `01-conops/`, `02-nfr/`, etc.).

When `/speckit-plan` resolves `FEATURE_SPEC` via `get_feature_paths`, it returns:
```
FEATURE_SPEC = specs/002-mqttlogger-baseline/spec.md   ← does not exist
```

The skill then has no source document to read for technical context.

### Root Cause

`/speckit-plan` was designed for the standard speckit workflow where `spec.md` is the primary input. The SE workflow distributes this information across multiple phase artifacts.

### Impact

- `/speckit-plan` cannot execute its Phase 0 (research) or Phase 1 (design) steps for an SE feature
- The user must either manually create a plan or run `/speckit-plan` as a template generator and fill it in from the SE artifacts by hand
- `/se-architecture`'s instruction "If `plan.md` does not exist, run `/speckit-plan` first" implies `/speckit-plan` will work — it does not, for SE features

### Proposed Fix

Same as Issue 1, Option C: introduce `/se-plan` that accepts SE artifacts as its primary inputs. Alternatively, document in both `/speckit-plan` and `/se-architecture` that `/speckit-plan` is not compatible with SE features and that the plan must be created directly.

---

## Summary Table

| Issue | Affected Skills | Severity | Proposed Fix |
|-------|----------------|----------|--------------|
| 1: `plan.md` path mismatch | `/se-architecture`, `/speckit-plan` | High — blocks workflow | Add SE-aware path logic to `/speckit-plan` (Option A) or introduce `/se-plan` (Option C) |
| 2: No skill creates `requirements-register.md` | `/se-architecture` (pre-condition only) | High — significant manual gap | Create `/se-requirements` skill |
| 3: `/speckit-plan` cannot read SE artifacts | `/speckit-plan` | Medium — workaround available | Introduce `/se-plan` or document incompatibility |
| 4: System-level artifacts buried in feature-scoped directories | All SE skills | High — compounds with every feature | Introduce `specs/system/` for system artifacts; feature folders hold only feature-scoped work |

---

---

## Issue 4 — System-level artifacts are buried in feature-scoped directories

### Symptom

The SE skill pack writes all artifacts under `specs/$FEATURE_ID/`, for example:

```
specs/002-mqttlogger-baseline/
  00-stakeholders/
  01-conops/
  02-nfr/
  03-explore/
  04-requirements/
  05-architecture/
  09-vv/
  10-risk/
  rtm.md
```

Most of these artifacts — stakeholders, ConOps, NFRs, architecture, risk register, RTM — describe the **system as a whole**, not the specific feature that initiated the SE process. They are living documents intended to be updated with every subsequent feature iteration.

Placing them under a feature ID directory creates several problems:

1. **Implied ownership**: the path implies these artifacts belong to feature `002`, not to the system. A developer picking up feature `004` has no clear signal that `specs/002-mqttlogger-baseline/rtm.md` is the canonical, authoritative RTM they must update.
2. **Discovery failure**: subsequent SE skills that carry update obligations (e.g., "update the risk register") have no reliable path to the system-level artifacts if they were established in a prior feature's folder.
3. **Naming rot**: the feature folder name (`002-mqttlogger-baseline`) becomes misleading once the system evolves — the baseline stakeholder register is no longer "the baseline", it is simply "the stakeholder register".
4. **No obvious upgrade path**: when the user runs `/se-risk` or `/se-rtm` in feature `003`, does it update `specs/002-mqttlogger-baseline/rtm.md`? Create `specs/003-cicd-pipeline/rtm.md`? The skill pack provides no guidance, so each run potentially fragments the system artifacts across multiple feature folders.

### Root Cause

The skill pack inherits speckit's convention that all artifacts are scoped to the active feature directory. This works well for feature-specific documents (spec, plan, tasks) but is structurally wrong for system-level SE artifacts, which must outlive any individual feature.

### Proposed Fix

Introduce a two-level artifact hierarchy:

```
specs/
  system/                        # System-level SE artifacts — updated in place each feature
    00-stakeholders/
    01-conops/
    02-nfr/
    04-requirements/
    05-architecture/
    09-vv/
    10-risk/
    rtm.md
  features/
    002-mqttlogger-baseline/     # Feature-scoped artifacts only
      spec.md (or se-plan)
      tasks.md
      gate-reports/
    003-cicd-pipeline/
      ...
```

**Rules:**
- System-level skills (`/se-stakeholders`, `/se-conops`, `/se-nfr`, `/se-architecture`, `/se-risk`, `/se-rtm`, `/se-vvplan`) read and write from `specs/system/`.
- Feature-scoped skills (`/speckit-specify`, `/speckit-plan`, `/speckit-tasks`, `/se-gate`) read and write from `specs/features/$FEATURE_ID/`.
- The constitution declares the canonical path for system artifacts so all skills resolve them consistently.

**Alternative (lighter weight):** Keep the current `specs/$FEATURE_ID/` convention for the founding feature, but have the constitution record the canonical system-artifact paths explicitly (e.g., `SYSTEM_SPECS_DIR = specs/002-mqttlogger-baseline`). Subsequent features read from that path and write updates back to it rather than creating their own copies.

### Impact if Not Fixed

- System artifacts fragment across feature folders over time
- Skills with threaded update obligations silently write to the wrong location
- New contributors (or future AI sessions) cannot reliably locate the authoritative risk register, RTM, or architecture without reading the constitution carefully

### Severity

**High** — structural issue that compounds with every feature iteration. Low cost to fix at skill-pack level; high cost to fix after several features have run.

---

## What Worked Well

- The numbered SE directory convention (`00-*` through `10-*`) is clear and consistent across all skills that do produce artifacts
- The threaded artifact update obligations (risk register, V&V plan, RTM) correctly force cross-artifact consistency at every phase
- The explore skill (`/se-explore`) and the gate skill (`/se-gate`) worked correctly and produced high-quality artifacts with no path issues
- The constitution serves as an effective anchor across all SE skills
