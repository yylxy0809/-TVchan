# TVchan

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
