import jwt
import uuid
import os

from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from dotenv import load_dotenv

from app.api_generation import project_crud

load_dotenv()
SECRET_KEY=os.environ.get('API_KEY_SECRET')
ALGORITHM="HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_api_key(db: Session, api_key: str):
    api_key_record = project_crud.get_api_key(db, api_key)
    if api_key_record is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    return api_key_record

def get_project_detail(db: Session, project_id: int):
    project_record = project_crud.get_project_by_project_id(db, project_id)
    if project_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project_record

def generate_api_key(project_name, email: str):
    data = {
        "project_name": project_name,
        "email": email
    }
    to_encode = data.copy()
    ALGORITHM = "HS256" 
    api_key = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return api_key

    
def create_project(db: Session, project_name: str, user):
    try:
        api_key = generate_api_key(project_name, user.email)
        project_record = project_crud.insert_project(db, project_name, user.id, api_key)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return project_record

def get_all_projects(db: Session, user_id: int):
    try:
        project_records = project_crud.get_all_projects(db, user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return project_records


def delete_project(db: Session, project_id: int):
    try:
        project_crud.delete_project(db, project_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    db.commit()
    

def update_project_description(db: Session, project_id: int,project_description: str):
    try:
        print("description : ", project_description)
        project_record = project_crud.update_description(db, project_id,project_description)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return project_record


def get_all_external_files(db: Session, project_id: int):
    try:
        file_list = project_crud.get_all_filenames(db, project_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return file_list


def create_external_session(db: Session, project_id: int):
    try:
        session = str(uuid.uuid4())
        session_record = project_crud.get_external_session_by_session_id(db, session)
        
        while session_record is not None:
            session = str(uuid.uuid4())
            session_record = project_crud.get_external_session_by_session_id(db, session)
            print("create session")
            
        external_session_record = project_crud.create_external_session(db, project_id, session)
        return external_session_record
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    

def get_all_session(db: Session, project_id=int):
    try:
        session_data = project_crud.get_all_session_by_project_id(db, project_id)
        return session_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    

def delete_external_session(db: Session, project_id: int, session_id: int):
    try:
        """verify project if available"""
        get_project_detail(db, project_id)
        project_crud.delete_external_session(db, session_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    