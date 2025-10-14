# backend/core/file_handler.py
import json
import re
import base64
import os
from pathlib import Path
from typing import Optional
import csv
from typing import Dict, Any

from .utils import slugify
import aiofiles
from ..core.utils import get_timestamp_filename
from fastapi import UploadFile; from typing import List; from datetime import datetime;
from .utils import slugify

DATA_DIR = Path("data")
SPOT_DIR = DATA_DIR / "spots"

def init_lookup_file(file_path: Path):
    if not file_path.exists():
        with open(file_path, 'w') as f:
            json.dump([], f)


async def is_name_unique(name: str, lookup_file: Path) -> bool:
    async with aiofiles.open(lookup_file, 'r') as f:
        content = await f.read()
        existing_names = json.loads(content)
    return name.lower() not in [n.lower() for n in existing_names]


async def add_name_to_lookup(name: str, lookup_file: Path):
    async with aiofiles.open(lookup_file, 'r+') as f:
        content = await f.read()
        existing_names = json.loads(content)
        if name.lower() not in [n.lower() for n in existing_names]:
            existing_names.append(name)
            await f.seek(0)
            await f.write(json.dumps(existing_names, indent=2))
            await f.truncate()


async def save_media_file_refactored(base64_data: str, spot_name_slug: str) -> Optional[str]:
    if not base64_data:
        return None
    try:
        matches = re.match(r"^data:(.+);base64,(.+)$", base64_data)
        if not matches:
            return None

        mime_type, file_contents_base64 = matches.groups()
        file_contents = base64.b64decode(file_contents_base64)
        media_type = mime_type.split('/')[0]
        extension = mime_type.split('/')[-1].split(';')[0]

        if media_type not in ['image', 'audio']:
            return None

        subfolder = 'images' if media_type == 'image' else 'audio'
        media_dir = SPOT_DIR / spot_name_slug / subfolder
        media_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{get_timestamp_filename()}.{extension}"
        file_path = media_dir / filename

        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_contents)

        relative_path = str(file_path.relative_to(DATA_DIR))
        url_path = relative_path.replace(os.path.sep, '/')
        return f"/data/{url_path}"

    except Exception as e:
        print(f"Error saving media file: {e}")
        return None


async def import_external_files_to_spots(
    files: List[UploadFile],
    spot_names: List[str]
) -> dict:
    base_spots_dir = Path("data/spots")
    date_str = datetime.now().strftime("%y%m%d")
    import_records = {}

    for spot_name in spot_names:
        spot_slug = slugify(spot_name)
        spot_dir = base_spots_dir / spot_slug
        spot_data_file = spot_dir / "_data.json"

        if not spot_data_file.exists():
            raise FileNotFoundError(f"Data file for spot '{spot_name}' not found.")

        dest_dir = spot_dir / "external_data" / date_str

        dest_dir.mkdir(parents=True, exist_ok=True)

        imported_file_paths = []
        for file in files:
            file_path = dest_dir / file.filename
            async with aiofiles.open(file_path, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
            imported_file_paths.append(str(file_path.as_posix()))
            await file.seek(0)

        async with aiofiles.open(spot_data_file, mode='r+') as f:
            content = await f.read()
            data = json.loads(content)
            new_observation = {
                "observationId": f"ext-{int(datetime.now().timestamp())}",
                "timestamp": datetime.now().isoformat(),
                "type": "external_import",
                "notes": "Batch import of external media.",
                "media": [
                    {"type": "external", "path": path} for path in imported_file_paths
                ]
            }
            if "observations" not in data:
                data["observations"] = []
            data["observations"].append(new_observation)
            await f.seek(0)
            await f.truncate()
            await f.write(json.dumps(data, indent=4))

        await append_to_observations_csv({
            "observationId": new_observation["observationId"],
            "spotId": data["spotId"],
            "spotName": data["name"],
            "observationTimestamp": new_observation["timestamp"],
            "latitude": data["latitude"],
            "longitude": data["longitude"],
            "observationType": "External Media Import",
            "description": new_observation.get("notes", ""),
            "externalMediaPaths": ";".join([media["path"] for media in new_observation["media"]])
        })
        import_records[spot_name] = imported_file_paths
    return import_records

async def append_to_observations_csv(observation_data: Dict[str, Any]):
    csv_file_path = DATA_DIR / "observations_summary.csv"
    
    headers = [
        "observationId", "spotId", "spotName", "observationTimestamp",
        "latitude", "longitude", "observationType", "description",
        "birds", "imagePath", "audioPath", "externalMediaPaths"
    ]

    row_data = {header: observation_data.get(header, "") for header in headers}

    file_exists = csv_file_path.exists()

    async with aiofiles.open(csv_file_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        
        if not file_exists:
            await f.write(u'\ufeff')
            await writer.writeheader()
        
        await writer.writerow(row_data)