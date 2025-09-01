# backend/core/file_handler.py
import json
import re
import base64
import os
from pathlib import Path
from typing import Optional

import aiofiles
from ..core.utils import get_timestamp_filename

# This file contains all functions that directly interact with the filesystem,
# such as reading, writing, and checking files.

# --- Constants ---
DATA_DIR = Path("data")
SPOT_DIR = DATA_DIR / "spots"

# --- Name Lookup Functions ---

def init_lookup_file(file_path: Path):
    """Creates an empty JSON list file if it doesn't exist."""
    if not file_path.exists():
        with open(file_path, 'w') as f:
            json.dump([], f)


async def is_name_unique(name: str, lookup_file: Path) -> bool:
    """Checks if a name is unique by looking in the specified JSON file."""
    async with aiofiles.open(lookup_file, 'r') as f:
        content = await f.read()
        existing_names = json.loads(content)
    return name.lower() not in [n.lower() for n in existing_names]


async def add_name_to_lookup(name: str, lookup_file: Path):
    """Adds a new name to the specified lookup file, preventing corruption."""
    async with aiofiles.open(lookup_file, 'r+') as f:
        content = await f.read()
        existing_names = json.loads(content)
        if name.lower() not in [n.lower() for n in existing_names]:
            existing_names.append(name)
            await f.seek(0)
            await f.write(json.dumps(existing_names, indent=2))
            await f.truncate()


# --- Media File Saving ---

async def save_media_file_refactored(base64_data: str, spot_name_slug: str) -> Optional[str]:
    """
    Decodes a base64 media string and saves it to the correct spot subfolder.
    Returns the public URL path for the saved file.
    """
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
