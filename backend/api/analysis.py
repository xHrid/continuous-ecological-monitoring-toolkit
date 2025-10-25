# backend/api/analysis.py

import os
import sys
import json
import shutil
import psutil

import subprocess
import aiofiles
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ANALYSIS_DIR = PROJECT_ROOT / "backend" / "analysis"
JOBS_DIR = PROJECT_ROOT / "data" / "processing" / "jobs"
DATA_DIR = PROJECT_ROOT / "data"

ACTIVE_JOBS: Dict[str, subprocess.Popen] = {}

class JobRequest(BaseModel):
    script_id: str
    input_files: List[str]
    parameters: Dict[str, Any] = Field(default_factory=dict)

def get_job_dir(job_id: str) -> Path:
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    return JOBS_DIR / job_id

def run_job_process(job_id: str, payload: dict):
    """This function runs in the background and executes the correct wrapper script."""
    job_dir = get_job_dir(job_id)
    payload_path = job_dir / "payload.json"
    results_path = job_dir / "results.json"
    stdout_path = job_dir / "stdout.log"
    stderr_path = job_dir / "stderr.log"

    script_id = payload.get("script_id")
    script_dir = ANALYSIS_DIR / script_id
    wrapper_path = script_dir / "wrapper.py"

    output_file_path = job_dir / "results.csv"
    payload['output_file'] = str(output_file_path)

    with open(payload_path, 'w') as f:
        json.dump(payload, f, indent=4)
        
    with open(results_path, 'r+') as f:
        status_data = json.load(f)
        status_data['status'] = 'running'
        f.seek(0)
        json.dump(status_data, f, indent=4)

    command = [sys.executable, str(wrapper_path), str(payload_path)]
    
    with open(stdout_path, 'w') as stdout_file, open(stderr_path, 'w') as stderr_file:
        process = subprocess.Popen(command, stdout=stdout_file, stderr=stderr_file, text=True)
        ACTIVE_JOBS[job_id] = process
        process.wait()

    if job_id in ACTIVE_JOBS:
        del ACTIVE_JOBS[job_id]

    with open(results_path, 'r+') as f:
        status_data = json.load(f)
        if process.returncode == 0:
            status_data['status'] = 'completed'
            status_data['output_file'] = str(output_file_path) # Add output file path on success
        else:
            status_data['status'] = 'failed'
            status_data['message'] = f"Process exited with code {process.returncode}"
        f.seek(0)
        f.truncate()
        json.dump(status_data, f, indent=4)

@router.get("/analysis/scripts", tags=["Analysis"])
async def get_available_scripts():
    """Scans the analysis directory for manifest.json files and returns their contents."""
    scripts = []
    if not ANALYSIS_DIR.exists():
        return []
    for script_dir in ANALYSIS_DIR.iterdir():
        if script_dir.is_dir():
            manifest_path = script_dir / "manifest.json"
            if manifest_path.exists():
                async with aiofiles.open(manifest_path, 'r') as f:
                    manifest_data = json.loads(await f.read())
                    manifest_data['id'] = script_dir.name # Use directory name as the unique ID
                    scripts.append(manifest_data)
    return scripts

@router.get("/analysis/external-files", tags=["Analysis"])
async def get_external_files():
    """Finds all WAV files in the external_data directories of all spots."""
    wav_files = []
    spots_dir = DATA_DIR / "spots"
    if not spots_dir.exists():
        return []
    for spot_folder in spots_dir.iterdir():
        if spot_folder.is_dir():
            external_data_dir = spot_folder / "external_data"
            if external_data_dir.exists():
                for root, _, files in os.walk(external_data_dir):
                    for file in files:
                        if file.lower().endswith('.wav'):
                            full_path = Path(root) / file
                            # Make the path relative to the project root for consistency
                            relative_path = full_path.relative_to(PROJECT_ROOT)
                            wav_files.append(str(relative_path))
    return sorted(wav_files)


@router.post("/analysis/run", tags=["Analysis"])
async def run_analysis(job_request: JobRequest, background_tasks: BackgroundTasks):
    job_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
    job_dir = get_job_dir(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)
    
    payload = job_request.dict()
    payload['job_id'] = job_id
    payload['submitted_at'] = datetime.now().isoformat()

    initial_status = {
        "job_id": job_id, "script_id": payload['script_id'],
        "submitted_at": payload['submitted_at'], "status": "queued"
    }
    async with aiofiles.open(job_dir / "results.json", 'w') as f:
        await f.write(json.dumps(initial_status, indent=4))

    background_tasks.add_task(run_job_process, job_id, payload)
    return {"message": "Job started successfully", "job_id": job_id}

@router.get("/analysis/jobs", tags=["Analysis"])
async def get_jobs():
    jobs = []
    if not JOBS_DIR.exists():
        return []
    for job_dir in JOBS_DIR.iterdir():
        results_path = job_dir / "results.json"
        if results_path.exists():
            async with aiofiles.open(results_path, 'r') as f:
                try:
                    jobs.append(json.loads(await f.read()))
                except json.JSONDecodeError:
                    jobs.append({"job_id": job_dir.name, "status": "corrupted"})
    return sorted(jobs, key=lambda j: j.get('submitted_at', ''), reverse=True)

@router.post("/analysis/jobs/{job_id}/cancel", tags=["Analysis"])
async def cancel_job(job_id: str):
    if job_id not in ACTIVE_JOBS:
        raise HTTPException(status_code=404, detail="Job not found or is not currently running.")
    
    process = ACTIVE_JOBS[job_id]
    try:
        parent = psutil.Process(process.pid)
        for child in parent.children(recursive=True):
            child.terminate()
        parent.terminate()
        
        gone, alive = psutil.wait_procs([parent], timeout=3)
        if alive:
            for p in alive:
                p.kill()

    except Exception as e:
        process.kill() # Fallback

    del ACTIVE_JOBS[job_id]
    
    results_path = get_job_dir(job_id) / "results.json"
    if results_path.exists():
        async with aiofiles.open(results_path, 'r+') as f:
            status_data = json.loads(await f.read())
            status_data['status'] = 'cancelled'
            await f.seek(0)
            await f.truncate()
            await f.write(json.dumps(status_data, indent=4))
            
    return {"message": "Job cancelled successfully."}

@router.delete("/analysis/jobs/{job_id}", tags=["Analysis"])
async def delete_job(job_id: str):
    if job_id in ACTIVE_JOBS:
        raise HTTPException(status_code=400, detail="Cannot delete a running job. Please cancel it first.")
    
    job_dir = get_job_dir(job_id)
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="Job not found.")
        
    shutil.rmtree(job_dir)
    return {"message": "Job deleted successfully."}


@router.get("/analysis/audio-sources", tags=["Analysis"])
async def get_audio_sources():
    """
    Finds all directories within data/spots that contain .wav files.
    """
    audio_sources = set()
    spots_dir = DATA_DIR / "spots"
    if not spots_dir.exists():
        return []

    for spot_folder in spots_dir.iterdir():
        if not spot_folder.is_dir():
            continue

        for root, _, files in os.walk(spot_folder):
            for file in files:
                if file.lower().endswith('.wav'):
                    # Add the directory path, relative to the project root
                    dir_path = Path(root).relative_to(PROJECT_ROOT)
                    audio_sources.add(str(dir_path))
                    # We found a WAV file, no need to check other files in this dir
                    break 

    return sorted(list(audio_sources))