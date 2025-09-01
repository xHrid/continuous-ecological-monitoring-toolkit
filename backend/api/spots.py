# backend/api/spots.py
import json
import uuid
from pathlib import Path
from datetime import datetime

import aiofiles
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

# NOTE: These imports assume you will create the core/utils.py, core/file_handler.py,
# and core/models.py files as planned.
from ..core.models import SpotObservation
from ..core.file_handler import save_media_file_refactored, add_name_to_lookup, is_name_unique
from ..core.utils import validate_name, slugify

router = APIRouter()

# Constants
DATA_DIR = Path("data")
SPOT_DIR = DATA_DIR / "spots"
SPOT_NAMES_FILE = DATA_DIR / "spot_names.json"


@router.post("/save-spot", tags=["Spots"])
async def save_spot(spot: SpotObservation):
    """
    Saves a new spot or adds a new observation to an existing spot.
    """
    try:
        is_new_spot = not spot.spotId
        if is_new_spot:
            # Logic for creating a NEW spot
            validate_name(spot.name)
            if not await is_name_unique(spot.name, SPOT_NAMES_FILE):
                raise HTTPException(status_code=409, detail="A spot with this name already exists.")

            spot_name_slug = slugify(spot.name)
            spot_dir = SPOT_DIR / spot_name_slug
            spot_dir.mkdir(exist_ok=True)
            spot_file_path = spot_dir / "_data.json"

            image_path = await save_media_file_refactored(spot.image_data_url, spot_name_slug)
            audio_path = await save_media_file_refactored(spot.audio_data_url, spot_name_slug)

            new_observation = {"observationId": str(uuid.uuid4()), "createdAt": datetime.now().isoformat(), "birds": spot.birds, "description": spot.description, "imagePath": image_path, "audioPath": audio_path}
            spot_data = {"spotId": spot_name_slug, "name": spot.name, "latitude": spot.latitude, "longitude": spot.longitude, "observations": [new_observation]}
            await add_name_to_lookup(spot.name, SPOT_NAMES_FILE)
        else:
            # Logic for adding an observation to an EXISTING spot
            spot_name_slug = spot.spotId
            spot_file_path = SPOT_DIR / spot_name_slug / "_data.json"
            if not spot_file_path.exists():
                raise HTTPException(status_code=404, detail="Spot not found.")

            image_path = await save_media_file_refactored(spot.image_data_url, spot_name_slug)
            audio_path = await save_media_file_refactored(spot.audio_data_url, spot_name_slug)
            new_observation = {"observationId": str(uuid.uuid4()), "createdAt": datetime.now().isoformat(), "birds": spot.birds, "description": spot.description, "imagePath": image_path, "audioPath": audio_path}

            async with aiofiles.open(spot_file_path, 'r') as f:
                spot_data = json.loads(await f.read())
            spot_data["observations"].append(new_observation)

        # Save the JSON file
        async with aiofiles.open(spot_file_path, 'w') as f:
            await f.write(json.dumps(spot_data, indent=2))

        return {"message": "Observation saved successfully!", "spotData": spot_data}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred in save_spot: {e}")
        return JSONResponse(status_code=500, content={"message": "An internal server error occurred."})


@router.get("/get-spots", tags=["Spots"])
async def get_spots():
    """
    Retrieves data for all saved spots.
    """
    all_spots = []
    for spot_dir in SPOT_DIR.iterdir():
        if spot_dir.is_dir():
            spot_file = spot_dir / "_data.json"
            if spot_file.exists():
                async with aiofiles.open(spot_file, 'r') as f:
                    all_spots.append(json.loads(await f.read()))
    return all_spots
