# backend/core/models.py
from pydantic import BaseModel
from typing import List, Optional

class SpotObservation(BaseModel):
    spotId: Optional[str] = None
    name: str
    latitude: float
    longitude: float
    birds: Optional[str] = None
    description: Optional[str] = None
    image_data_url: Optional[str] = None
    audio_data_url: Optional[str] = None


class RouteData(BaseModel):
    name: Optional[str] = None
    points: List[dict]


class AnalysisScript(BaseModel):
    id: str
    name: str
    description: str

class JobRequest(BaseModel):
    script_id: str
    spot_names: List[str]
    input_files: List[str]

class Job(BaseModel):
    job_id: str
    script_id: str
    status: str
    submitted_at: str
    spot_names: List[str]
    payload: Optional[dict] = None
    results: Optional[dict] = None