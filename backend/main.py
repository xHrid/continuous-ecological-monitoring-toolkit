from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api import sites, spots, routes, importer, analysis
# Create the main FastAPI application
app = FastAPI(
    title="Field Data Collector API",
    description="API for managing sites, spots, and routes.",
    version="1.0.0"
)

app.include_router(sites.router, prefix="/api")
app.include_router(spots.router, prefix="/api")
app.include_router(routes.router, prefix="/api")
app.include_router(importer.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")


app.mount("/data", StaticFiles(directory="data"), name="data")
app.mount("/", StaticFiles(directory="public", html=True), name="public")

@app.get("/health", tags=["Health Check"])
def read_root():
    return {"status": "ok"}
