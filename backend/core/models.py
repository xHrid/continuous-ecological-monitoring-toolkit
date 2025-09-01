# backend/core/models.py
from pydantic import BaseModel
from typing import List, Optional

# This file defines the shape of the data that the API expects to receive.
# Pydantic uses these models to automatically validate incoming request bodies.

class SpotObservation(BaseModel):
    """
    Model for a new spot or a new observation for an existing spot.
    The 'name' field is required.
    """
    spotId: Optional[str] = None
    name: str
    latitude: float
    longitude: float
    birds: Optional[str] = None
    description: Optional[str] = None
    image_data_url: Optional[str] = None
    audio_data_url: Optional[str] = None


class RouteData(BaseModel):
    """
    Model for a new route. The 'name' is optional and will be used
    for the filename if provided.
    """
    name: Optional[str] = None
    points: List[dict]
