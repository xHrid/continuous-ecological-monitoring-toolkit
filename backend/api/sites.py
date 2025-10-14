# backend/api/sites.py
import json
import uuid
import aiofiles
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse

from ..gee_processor import generate_stratification

router = APIRouter()

DATA_DIR = Path("data")
SITES_DIR = DATA_DIR / "sites"


@router.post("/add-site", tags=["Sites"])
async def add_site(
    siteName: str = Form(...),
    clusters: int = Form(...),
    kml: UploadFile = File(...)
):

    try:
        results_list = generate_stratification(
            kml_content=await kml.read(),
            max_clusters=clusters
        )

        SITES_DIR.mkdir(parents=True, exist_ok=True)
        site_id = str(uuid.uuid4())
        site_data = {
            "siteId": site_id,
            "siteName": siteName,
            "createdAt": datetime.now().isoformat(),
            "stratifications": results_list
        }

        site_file_path = SITES_DIR / f"{site_id}.json"
        async with aiofiles.open(site_file_path, 'w') as f:
            await f.write(json.dumps(site_data, indent=2))

        print(f"Site '{siteName}' data saved to {site_file_path}")

        site_data["message"] = f"Site '{siteName}' generated and saved successfully!"
        return site_data
    except Exception as e:
        print(f"Error during GEE processing for site '{siteName}': {e}")
        return JSONResponse(
            status_code=500,
            content={"message": "An error occurred during GEE processing."}
        )


@router.get("/get-sites", tags=["Sites"])
async def get_sites():

    SITES_DIR.mkdir(exist_ok=True)
    all_sites = []
    try:
        files = sorted(SITES_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        for file_path in files:
            async with aiofiles.open(file_path, 'r') as f:
                all_sites.append(json.loads(await f.read()))
        return all_sites
    except Exception as e:
        print(f"Error loading sites: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": "Failed to load sites."}
        )
