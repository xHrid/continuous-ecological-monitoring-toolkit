# backend/core/utils.py
import re
from datetime import datetime
from fastapi import HTTPException

def slugify(name: str) -> str:
    name = name.strip().replace(" ", "_")
    name = re.sub(r'(?u)[^-\w.]', '', name)
    return name


def get_timestamp_filename() -> str:
    return datetime.now().strftime("%y%m%d-%H%M%S")


def validate_name(name: str):
    if not re.match(r"^[a-zA-Z0-9\s_-]+$", name):
        raise HTTPException(
            status_code=400,
            detail="Name contains invalid characters. Only letters, numbers, spaces, underscores, and hyphens are allowed."
        )
