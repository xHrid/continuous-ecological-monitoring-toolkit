# backend/core/utils.py
import re
from datetime import datetime
from fastapi import HTTPException

# This file contains general-purpose helper functions that don't interact
# directly with the filesystem or specific data models.

def slugify(name: str) -> str:
    """
    Converts a user-provided string into a safe version for a directory or file name.
    Example: "Spot at Gate / Road" -> "Spot_at_Gate_Road"
    """
    name = name.strip().replace(" ", "_")
    # Remove any characters that are not alphanumeric, underscores, hyphens, or periods.
    name = re.sub(r'(?u)[^-\w.]', '', name)
    return name


def get_timestamp_filename() -> str:
    """
    Generates a 'yymmdd-hhmmss' timestamp string for unique filenames.
    """
    return datetime.now().strftime("%y%m%d-%H%M%S")


def validate_name(name: str):
    """
    Validates a name against a set of permitted characters.
    Raises an HTTPException if the name is invalid, which FastAPI handles automatically.
    """
    # Allows alphanumeric characters, spaces, underscores, and hyphens.
    if not re.match(r"^[a-zA-Z0-9\s_-]+$", name):
        raise HTTPException(
            status_code=400,
            detail="Name contains invalid characters. Only letters, numbers, spaces, underscores, and hyphens are allowed."
        )
