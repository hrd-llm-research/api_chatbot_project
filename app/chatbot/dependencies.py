import os
import json

from . import crud
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_chroma import Chroma



current_dir = os.path.dirname(os.path.abspath(__file__))
history_dir = os.path.join(current_dir, 'history')
embedding = FastEmbedEmbeddings()

def write_history_as_json(file_path, message_list):
    
    if not os.path.exists(history_dir):
        os.makedirs(history_dir)
        
    """Format list of histories with type and content."""
    message_list = [{"role": "user" if isinstance(message, HumanMessage) else "ai","content": message.content} for message in message_list]
    
    if os.path.exists(file_path):
        os.mkdir(file_path)
    
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
            
