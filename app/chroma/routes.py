from fastapi import APIRouter, File, UploadFile, status, Depends, Query, Path, HTTPException
from fastapi.responses import JSONResponse
from app.auth.dependencies import get_current_active_user
from typing import Annotated
from app.utils import get_db
from sqlalchemy.orm import Session
from fastapi.security import APIKeyHeader

from . import dependencies
from app.auth.dependencies import validate_existing_email
from app.db_connection.schemas import User
from app.api_generation import project_dependencies

MAX_SZIE_FILE_SIZE = 52428800
router = APIRouter(
    prefix="/files",
    tags=["files"]
)


API_KEY_HEADER = "REST-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_HEADER)

async def verify_api_key(
    db: Session = Depends(get_db),
    api_key: str = Depends(api_key_header)
) -> None:
    api_key = project_dependencies.verify_api_key(db, api_key)
 

@router.post("/upload")
async def file_upload(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session = Query(..., description="Chat Session"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user = validate_existing_email(db, current_user.email)
    chroma_data = dependencies.upload_file_to_chroma(db, file, user, session)
    
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "File uploaded successfully.",
                 "success": True,
                 "payload": chroma_data.to_dict()
                })


@router.get("/get_all_files/{session_id}")
async def get_all_files(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session_id: int = Path(..., ge=1, description="Session ID"), 
    db: Session = Depends(get_db)
):
    user = validate_existing_email(db, current_user.email)
    file_records = dependencies.get_all_file_records(db, session_id, user.id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Retrieve all file records successfully.",
                 "success": True,
                 "payload": file_records
                })
   
   
@router.post("/api_generation/upload")
async def external_file_upload(
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_id: int = Query(..., ge=1, description="Project ID"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    chroma_data = dependencies.upload_external_file_to_chroma(db, file, project_id)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": f"File {chroma_data} uploaded successfully.",
                 "success": True,
                 "file_name": chroma_data
                })
    

@router.get("/api_generation/get_all_files/{project_id}")
def get_all_files(
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_id: int = Path(..., ge=1, description="Project ID"),
    db: Session = Depends(get_db)
):
    file_list = project_dependencies.get_all_external_files(db, project_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Files retrieved successfully.",
                 "payload": file_list}
    )
    
@router.delete("/delete_all_files/{session_id}")
def delete_files(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session_id: int = Path(..., ge=1, description="Session ID"),
    db: Session = Depends(get_db)
):
    user = validate_existing_email(db, current_user.email)
    dependencies.delete_all_files(db, user, session_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Files deleted successfully.",
                     "success": True}
    )

@router.post("/upload_file_HRDBot")
def upload_file_HRDBot(
    file: UploadFile = File(...),
): 
    if file.size > MAX_SZIE_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 50MB."
        )

    dependencies.upload_to_HRDBot(file)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "File uploaded successfully.",
                 "success": True}
    )
