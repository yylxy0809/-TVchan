# TVchan

## Documentation

- [Project state and handover](PROJECT_STATE.md) — current verified repository state, active work, risks, and recovery steps.
- [Project command brief](PROJECT.md) — architecture boundaries and working rules.
- [Wave 1 market contract](docs/WAVE1_MARKET_CONTRACT.md) — implementation admission contract.

Wave 0 provides the clean Python package boundary for the TVchan rebuild. It deliberately
contains no StockDB, chan.py, TradingView, strategy, replay, or lifecycle implementation.

## Local setup

Use Python 3.12 or later:

```powershell
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m mypy
python scripts/check_dependency_boundaries.py
uvicorn tvchan.bootstrap.api:app --app-dir backend/src --reload
```

The independent health endpoint is available at `GET /health`; it does not initialize any
external service.
