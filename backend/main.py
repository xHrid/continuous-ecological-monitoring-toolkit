# backend/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Import the API routers from the api module
from .api import sites, spots, routes

# Create the main FastAPI application
app = FastAPI(
    title="Field Data Collector API",
    description="API for managing sites, spots, and routes.",
    version="1.0.0"
)

# Include the API Routers
# This tells the main app to use all endpoints defined in the router files.
# The 'prefix' adds "/api" to all paths, e.g., "/add-site" becomes "/api/add-site".
app.include_router(sites.router, prefix="/api")
app.include_router(spots.router, prefix="/api")
app.include_router(routes.router, prefix="/api")


# Mount Static Files
# This serves the 'public' directory (your frontend) and the 'data' directory.
# Assumes you run the server from the project's root directory.
app.mount("/data", StaticFiles(directory="data"), name="data")
app.mount("/", StaticFiles(directory="public", html=True), name="public")

# Optional: Add a root endpoint for health checks
@app.get("/health", tags=["Health Check"])
def read_root():
    return {"status": "ok"}
