# aerial-track-and-range

Status: early build (Phase 1 of 6). Nothing in this repository is a result yet.

Tracking from a drone that reports where things are, how far to trust that estimate, and runs in real time on a Central Processing Unit (CPU).

## Quickstart (development)

```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-lock.txt   # .venv/bin/python on Linux/macOS
.venv/Scripts/python -m pip install -e . --no-deps
make lint test        # or run the commands in the Makefile directly
make data-check       # needs datasets under the data root (configs/data.yaml)
```

## Licence

GNU Affero General Public License v3.0 (AGPL-3.0). See `LICENSE`.
