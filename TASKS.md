# Task list (mirrors build.md Section 12)

## Phase 0: bootstrap
- [x] Repository layout, `pyproject.toml`, Makefile, ruff and pytest setup
- [x] CI workflow (`.github/workflows/ci.yml`)
- [x] `.gitignore` (data, weights, venv, Mid-Air download token)
- [x] `PROGRESS.md`, `BLOCKED.md`, this task list
- [x] Configs with `null` placeholders and a loader that refuses unresolved values
- [x] `scripts/env_report.py` → `results/env.json`
- [x] `scripts/check_data.py` → `results/data_check.json`
- [x] Exit: lint and tests pass; CI file present; `results/env.json` produced (see PROGRESS.md for the `make` caveat)

## Phase 1: geometry core (test-first)
- [x] 6.1 frames and conventions, pinned by tests
- [x] 6.2 ray and plane intersection, contact-point rules, general plane
- [x] 6.3 uncertainty: numerical Jacobian vs analytic oracles, first order vs Monte Carlo
- [x] 6.4 ground-plane Kalman filter with NEES test
- [x] Exit: all geometry tests pass; coverage of every public function; decisions.md entries
- [ ] Carried forward: AU-AIR body-frame figure check (Phase 4); Mid-Air quaternion convention (Phase 2); verify cited section numbers (Phase 6)

## Phase 2: Mid-Air validation (needs data)
- [ ] Section 7

## Phase 3: tracking baseline (needs data)
- [ ] Section 9

## Phase 4: AU-AIR and integration (needs AU-AIR)
- [ ] Section 8 and 11.1

## Phase 5: edge budget
- [ ] Section 10

## Phase 6: deliverables and polish
- [ ] Section 13 and the release checklist (Section 16)
