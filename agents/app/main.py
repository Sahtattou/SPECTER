from fastapi import FastAPI

app = FastAPI(title="SPECTER Agent Service")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
