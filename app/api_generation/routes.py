import jwt

from fastapi import APIRouter, Depends, status, Query, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi.security import APIKeyHeader

from app.utils import get_db
from app.db_connection.schemas import User, ProjectDescription
from app.auth.dependencies import get_current_active_user
from app.auth.dependencies import validate_existing_email
from app.api_generation import project_dependencies
from app.api_generation import project_crud

router = APIRouter(
    prefix="/api_generation",
    tags=["api_generation"],
)

API_KEY_HEADER = "REST-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_HEADER)

async def verify_api_key(
    db: Session = Depends(get_db),
    api_key: str = Depends(api_key_header)
):
    try:
        
        api_key_record = project_dependencies.verify_api_key(db, api_key)
        payload = jwt.decode(api_key, project_dependencies.SECRET_KEY, algorithms=[project_dependencies.ALGORITHM])
        project_name: str = payload.get("project_name")
        project_record = project_crud.get_project_by_project_name(db, project_name)
        return project_record
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    

@router.get("/get_project")
def get_project(
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_id: int,
    db: Session = Depends(get_db),
):
    project_record = project_dependencies.get_project_detail(db, project_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Project retrieved successfully.",
                 "success": True,
                 "project_id": project_record.to_dict(),
        }
    )

@router.delete("/delete")
def delete_project(
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_id: int,
    db: Session = Depends(get_db),
):
    project_dependencies.delete_project(db, project_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Project deleted successfully.",
                 "success": True}
    )

@router.post("/create_project")
def create_project(
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_name: str = Query(...),
    db: Session = Depends(get_db)
):
    user = validate_existing_email(db, current_user.email)
    project_record = project_dependencies.create_project(db, project_name, user)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "Project created successfully.",
                 "success": True,
                 "project_id": project_record.to_dict(),
        }
    )


@router.get("/get_all_projects")
def get_projects(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
):
    user = validate_existing_email(db, current_user.email)  
    project_lists = project_dependencies.get_all_projects(db, user.id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Projects retrieved successfully.",
                 "success": True,
                 "payload": project_lists
        }
    )

@router.patch("/description")
def update_description(
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_id: int,
    project_description: ProjectDescription,
    db: Session = Depends(get_db),
):
    project_record = project_dependencies.update_project_description(db, project_id, project_description.description)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Project description updated successfully.",
                 "success": True,
                 "paylaod":project_record}
    )


@router.post("/create_session")
async def create_new_chat(
    db: Session = Depends(get_db),
    project: str = Depends(verify_api_key)
):
    session_record = project_dependencies.create_external_session(db, project.id)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": "New chat session started with session ID: {}".format(session_record.session),
            "success": True,
            "session_id": session_record.to_dict(),
        }
    )
 
@router.get("/get_all_sessions")   
async def get_all_sessions(
    db: Session = Depends(get_db),
    project: str = Depends(verify_api_key)
):
    session_resposne = project_dependencies.get_all_session(db, project.id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "All chat sessions retrieved successfully.",
            "success": True,
            "payload": session_resposne
        }
    )
    

@router.delete("/delete/{external_session_id}")
def delete_session(
    db: Session = Depends(get_db),
    project: str = Depends(verify_api_key)
):
    project_dependencies.delete_external_session(db, project.id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Chat session deleted successfully.",
            "success": True
        }
    )

    
