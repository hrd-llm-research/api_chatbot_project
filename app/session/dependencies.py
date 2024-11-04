import os
import json

from sqlalchemy.orm import Session
from . import crud
from fastapi import HTTPException, status

from app.minIO import dependencies as minio_dependencies
from app.session import crud as session_crud
from app.minIO import dependencies as minio_dependencies
from app.session import dependencies as session_dependencies
from app.chroma import crud as chroma_crud

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_DIR = os.path.join(CURRENT_DIR, '..', 'chatbot', 'history')

def get_all_sessions(db: Session, user_id: int):
    all_session_records = crud.get_all_session(db, user_id)
    if all_session_records is False:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return all_session_records

def is_session_available(db: Session, user_id: int, session):
    session_record = crud.find_session(db, user_id, session)
    if session_record is False:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session_record

def is_session_available_by_session_id(db: Session, user_id: int, session_id: int):
    session_record = crud.find_session_by_session_id(db,session_id)
    if session_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session_record

def get_session(db: Session, user_id: int, session):
    session_record = crud.find_session(db, user_id, session)
    return session_record


def save_internal_session(db: Session, user, session_id: int):
    try:
        session_record = session_crud.find_session_by_session_id(db, session_id)
        history_file_name = str(user.id)+'@'+str(session_record.session)
        
        history_record = is_history_exist(db, history_file_name)

        if history_record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="History not found"
            )
        """declare file variables"""
        # history_text_file = history_record.history_name+'.txt'
        history_json_file = history_record.history_name +'.json'
        
        # history_text_file_dir = os.path.join(HISTORY_DIR, history_text_file)
        history_json_file_dir = os.path.join(HISTORY_DIR,"json", history_json_file)
        
        # minio_dependencies.upload_file(user.username, history_text_file, history_text_file_dir)
        minio_dependencies.upload_file(user.username, history_json_file, history_json_file_dir)
        
        os.remove(history_json_file_dir)
        # os.remove(history_text_file_dir)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

def is_history_exist(db: Session, history_filename: str):
    history_record = crud.find_history(db, history_filename)
    return history_record
       
       
def get_history(db: Session, user, session_id: int, page: int, limit: int):
    try:
        history_record = crud.get_history_by_session_id(db, session_id)
        history_name = history_record.history_name
        username = user.username
        
        history_json_filename = history_name + ".json"
        history_json_file_dir = os.path.join(HISTORY_DIR, "json", history_json_filename)
        
        if not os.path.exists(history_json_file_dir):
            minio_dependencies.download_file(username, history_name, history_json_file_dir)
            
        with open(history_json_file_dir, 'r') as json_file:
            docs = json.load(json_file)
            docs = docs[-(page+limit):]
            
        return docs
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
def delete_session(db: Session, user, session_id: int):
    try:
        session_record = session_dependencies.is_session_available_by_session_id(db, user.id, session_id)
        history_file_name = str(user.id)+'@'+str(session_record.session)
        history_json_file_name = history_file_name+'.json'
        history_file_name_dir = os.path.join(HISTORY_DIR, "json", history_json_file_name)
        
        if os.path.exists(history_file_name_dir):
            os.remove(history_file_name_dir)
            
        minio_dependencies.delete_file_from_minIO(user.username, history_json_file_name)
        crud.delete_history_by_history_name(db, history_file_name)
        files = chroma_crud.get_all_files(db, session_id)
        for file in files:
            chroma_crud.delete_file(db, file.get('id'))
            
        crud.delete_session_by_session_id(db, session_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
def get_session_by_session_id(db: Session, session_id: int):
    try:
        session_record = crud.find_session_by_session_id(db, session_id)
        return session_record
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        