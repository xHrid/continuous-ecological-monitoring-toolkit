from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from typing import List
from ..core.file_handler import import_external_files_to_spots

router = APIRouter()

@router.post("/import-external-media", tags=["Importer"])
async def import_media(
    files: List[UploadFile] = File(...),
    spot_names: List[str] = Form(...)
):
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")
    if not spot_names:
        raise HTTPException(status_code=400, detail="No spots were selected.")

    try:
        result = await import_external_files_to_spots(
            files=files,
            spot_names=spot_names
        )
        return {"status": "success", "detail": "Media imported successfully.", "result": result}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")