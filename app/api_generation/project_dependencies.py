import jwt
import uuid
import os
import json

from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from dotenv import load_dotenv

from app.api_generation import project_crud
from app.minIO import dependencies as minio_dependencies
from app.chroma import crud as chroma_crud

load_dotenv()
# SECRET_KEY=os.environ.get('API_KEY_SECRET')
SECRET_KEY = "21d7c112103f59812997858795276d45507c204f893922b0dcd251eb76013d12"
ALGORITHM="HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_DIR = os.path.join(CURRENT_DIR, '..', 'chatbot', 'history')


def verify_api_key(db: Session, api_key: str):
    
    api_key_record = project_crud.get_api_key(db, api_key)
    if api_key_record is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    api_key = api_key_record
    return api_key.to_dict().get('api_key')

def get_project_detail(db: Session, project_id: int):
    project_record = project_crud.get_project_by_project_id(db, project_id)
    if project_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project_record

def generate_api_key(project_name, email: str, project_id:int):
    try: 
        data = {
            "project_name": project_name,
            "email": email,
            "project_id": project_id
        }
        to_encode = data.copy()
        ALGORITHM = "HS256" 
        api_key = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return api_key
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="api key generation error"
        )

    
def create_project(db: Session, project_name: str, user):
    try:
        project_record = project_crud.insert_project(db, project_name, user.id)
        api_key = generate_api_key(project_name, user.email, project_record.id)
        project_crud.update_project_api_key(db, project_record.id, api_key)
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


def delete_project(db: Session, user, project_id: int):
    try:
        project_record = get_project_detail(db, project_id)
        history_file_name = str(project_record.id)+'@'+str(project_record.project_name)+'_history'
        history_json_file_name = history_file_name+'.json'
        history_file_name_dir = os.path.join(HISTORY_DIR, "json", history_json_file_name)
        
        if os.path.exists(history_file_name_dir):
            os.remove(history_file_name_dir)
        
        minio_dependencies.delete_file_from_minIO(project_record.project_name.lower(), history_file_name)

        external_list = project_crud.get_all_external_session_by_project_id(db, project_record.id)
        for external_session in external_list:
            delete_external_session(db, project_record.id, project_record.project_name, external_session.get('id'))
            
        chroma_crud.delete_external_file_by_project_id(db, project_record.id)
        project_crud.delete_project(db, project_record.id)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    db.commit()
    

def update_project_description(db: Session, project_id: int,project_description: str):
    try:
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
        session_record = project_crud.get_external_session_by_session(db, session)
        
        project_record = get_project_detail(db, project_id)
        if project_record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        while session_record is not None:
            session = str(uuid.uuid4())
            session_record = project_crud.get_external_session_by_session(db, session)
            
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
    

def delete_external_session(db: Session, project_id, project_name, external_session_id: int):
    try:
        """verify project if available"""
        project_record = get_project_detail(db, project_id)
        if project_record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"REST-API-KEY doesn't have {external_session_id}."
            )
            
        external_session_record = project_crud.get_external_session_by_session_id(db, external_session_id)
        if external_session_record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"REST-API-KEY doesn't have {external_session_id}. Delete failed."
            )
        
        external_history_record = project_crud.get_external_history_by_session_id(db, external_session_id)
        
        if external_history_record is None:
            deleted_external_session = project_crud.delete_external_session(db, external_session_id, project_id)
            if deleted_external_session == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Delete failed."
                )
        
        else:
            
            external_history_json_file = external_history_record.history_name+'.json'
            external_history_json_file_dir = os.path.join(HISTORY_DIR, "json", external_history_json_file)
            
            if os.path.exists(external_history_json_file_dir):
                os.remove(external_history_json_file_dir)
                
            """delete from minIO"""
            minio_dependencies.delete_file_from_minIO(project_name.lower(), external_history_record.history_name)
                

            project_crud.delete_external_history(db, external_session_id)
                
            deleted_external_session = project_crud.delete_external_session(db, external_session_id, project_id)
            if deleted_external_session == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Delete failed."
                )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


def is_external_session_available(db: Session, project_id: int):
    print("checking ", project_id)
    session_record = project_crud.get_external_session_by_session_id(db, project_id)
    if session_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

def create_external_history(db: Session, history_name: str, session_id:int):
    try:
        external_history_record = project_crud.insert_external_history(db, history_name, session_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return external_history_record
        
def is_external_history_exist(db: Session, session_id: int):
    history_record = project_crud.get_external_history_by_session_id(db, session_id)
    return history_record

def save_external_session(db: Session, external_session_id: int, project_name: str):
    try:
        history_filename = str(external_session_id)+'@'+project_name+'_history'
        
        history_record = project_crud.get_external_history_by_session_id(db, external_session_id)
        
        """declare file variables"""
        history_json_file = history_record.history_name+'.json'
        
        history_json_file_dir = os.path.join(HISTORY_DIR, "json", history_json_file)
        if not os.path.exists(history_json_file_dir):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="History Directory not found"
            )
        
        minio_dependencies.upload_file(project_name.lower(), history_json_file, history_json_file_dir)
        
        os.remove(history_json_file_dir)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
        
        
def get_history_by_external_session_id(db: Session, project, external_session_id: int, limit, page):
    try:
        external_history = is_external_history_exist(db, external_session_id)
        if external_history is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="History not found"
            )
        history_json_filename = external_history.history_name+'.json'
        history_json_filename_dir = os.path.join(HISTORY_DIR, "json", history_json_filename)
        
        if not os.path.exists(history_json_filename_dir):
            minio_dependencies.download_file(project.project_name.lower(), history_json_filename, history_json_filename_dir)

        if os.path.exists(history_json_filename_dir):    
            with open(history_json_filename_dir, 'r') as json_file:
                docs = json.load(json_file)
                chat_history = docs
        return chat_history[-(page*limit):]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) 
    
