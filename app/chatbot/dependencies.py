import os
import json

from . import crud
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_chroma import Chroma
from app.api_generation.project_dependencies import is_external_session_available, get_project_detail, create_external_history, is_external_history_exist
from app.api_generation.project_crud import get_project_by_project_id
from app.chroma.dependencies import get_external_chroma_name
from app.minIO import dependencies as minio_dependencies
from app.session import dependencies as session_dependencies
from app.auth.dependencies import find_user
from app.db_connection import models

current_dir = os.path.dirname(os.path.abspath(__file__))
history_dir = os.path.join(current_dir, 'history')
embedding = FastEmbedEmbeddings()

def write_history_as_json(file_path, message_list):
    
    if not os.path.exists(history_dir):
        os.makedirs(history_dir)
        
    """Format list of histories with type and content."""
    message_list = [{"role": "user" if isinstance(message, HumanMessage) else "ai","content": message.content} for message in message_list]
    
    if not os.path.exists(os.path.join(history_dir, "json")):
        os.mkdir(os.path.join(history_dir, "json"))
    
    """Check if the file exists and has valid content, otherwise initialize an empty list"""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as as_file:
                """load existing history json file from local dir"""
                existing_history = json.load(as_file)
        except json.JSONDecodeError:
            existing_history = []
    else:
        existing_history = []
    
    """Append the history to the existing history"""
    existing_history.extend(message_list)
    
    """Write update history to existing history"""
    with open(file_path, 'w+') as as_file:
        json.dump(existing_history, as_file, indent=4)

def write_history_as_text(file_path, message_list):
    with open(file_path, 'a+') as as_file:
        for message in message_list:
            as_file.write(f"{message.__class__.__name__}(content='{message.content}'),")
            
def save_ai_response(db: Session, external_session_id: int, project_id: int, ai_response):
    try:
        """Check if project & session available"""
        session_data = is_external_session_available(db, external_session_id)
        project_data = get_project_by_project_id(db, project_id)
        
        if project_data is None:
            raise HTTPException(
                status_code=404,
                detail=f"Project '{project_id}' is not found."
            )
        chroma_db = get_external_chroma_name(project_id)
        external_history = is_external_history_exist(db, external_session_id)
    
        
        """declare file variables"""
        history_filename = str(external_session_id)+'@'+project_data.project_name+'_history'
        history_json_file = history_filename+'.json'
        history_json_file_dir = os.path.join(history_dir, "json", history_json_file)
        
        """If history not found, insert message into database"""
        if external_history is None: 
            history_record = create_external_history(db, history_filename, external_session_id)
        else:
            if not os.path.exists(history_json_file_dir):
                minio_dependencies.download_file(project_data.project_name, history_json_file, history_json_file_dir)
                
        """Write file to local"""
        new_history = []
        new_history.append(SystemMessage(content=ai_response))
            
        write_history_as_json(history_json_file_dir, new_history)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to write AI response in file as history."
        )
        
def save_playground_ai_response(db: Session, user_id, session_id, ai_response):
    try:
        session_record = session_dependencies.is_session_available_by_session_id(db, user_id, session_id)
        username = find_user(db, user_id)
        history_file_name = str(user_id)+'@'+str(session_record.session)
            
        """declare file variables"""
        history_json_file = history_file_name+'.json'
            
        history_json_file_dir = os.path.join(history_dir, "json", history_json_file)
            
        """check if history exists"""
        history_record = crud.get_history_by_session(db, session_id)

        """If history not found, insert message into database"""
        if history_record == None:
            request = models.MessageHistory(
                    session_id=session_id,
                    history_name=history_file_name
            )
            history_record = crud.create_history(db, request)    
        """if history exists"""
        if not history_record == None: 
                
            """If history dir exists then download from minIO server"""
            if not os.path.exists(history_json_file_dir):
                minio_dependencies.download_file(username, history_json_file, history_json_file_dir)  
                
        """Write file to local"""
        new_history = []
        new_history.append(SystemMessage(content=ai_response))
                
        write_history_as_json(history_json_file_dir, new_history)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )