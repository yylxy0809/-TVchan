"""HTTP composition root for the independently bootable application."""

from fastapi import FastAPI

app = FastAPI(title="TVchan", version="0.0.1")


@app.get("/health")
def health() -> dict[str, str]:
    """Report process liveness without consulting external dependencies."""
    return {"status": "ok"}
