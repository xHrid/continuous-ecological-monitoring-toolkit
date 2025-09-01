# backend/api/routes.py
import json
from pathlib import Path

import aiofiles
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

# NOTE: These imports assume you will create the core/utils.py, core/file_handler.py,
# and core/models.py files as planned.
from ..core.models import RouteData
from ..core.file_handler import add_name_to_lookup, is_name_unique
from ..core.utils import validate_name, slugify, get_timestamp_filename

router = APIRouter()

# Constants
DATA_DIR = Path("data")
ROUTE_DIR = DATA_DIR / "routes"
ROUTE_NAMES_FILE = DATA_DIR / "route_names.json"


@router.post("/save-route", tags=["Routes"])
async def save_route(route_data: RouteData):
    """
    Saves a new route with a unique name or a timestamp-based name.
    """
    try:
        route_name_slug = ""
        if route_data.name:
            validate_name(route_data.name)
            if not await is_name_unique(route_data.name, ROUTE_NAMES_FILE):
                raise HTTPException(status_code=409, detail="A route with this name already exists.")
            route_name_slug = slugify(route_data.name)
            await add_name_to_lookup(route_data.name, ROUTE_NAMES_FILE)

        filename = f"{route_name_slug or get_timestamp_filename()}.json"
        file_path = ROUTE_DIR / filename
        route_json_data = route_data.model_dump(exclude={'name'})

        async with aiofiles.open(file_path, 'w') as f:
            await f.write(json.dumps(route_json_data, indent=2))

        return {"message": "Route saved successfully!"}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred in save_route: {e}")
        return JSONResponse(status_code=500, content={"message": "An internal server error occurred."})


@router.get("/get-routes", tags=["Routes"])
async def get_routes():
    """
    Retrieves all saved routes.
    """
    all_routes = []
    for file_path in ROUTE_DIR.glob("*.json"):
        async with aiofiles.open(file_path, 'r') as f:
            all_routes.append(json.loads(await f.read()))
    return all_routes
