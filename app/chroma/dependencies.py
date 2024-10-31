import os 

from sqlalchemy.orm import Session
from fastapi import UploadFile, status, HTTPException
from dotenv import load_dotenv
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from . import crud
# from app.db_connection import schemas
from app.session.crud import create_session
from app.session.dependencies import get_session, is_session_available_by_session_id
from app.api_generation.project_crud import update_chroma_name, get_all_filenames
from app.api_generation.project_dependencies import get_project_detail
from app.chroma import dependencies as chroma_dependencies
from app.chroma import crud as chroma_crud
from app.minIO import dependencies as minio_dependencies

current_dir = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(current_dir, "resources")
        
load_dotenv()

embedding = FastEmbedEmbeddings()

def _store_file(file: UploadFile, upload_dir: str) -> str:
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, 'wb') as f:
        f.write(file.file.read())
    return file.filename

def is_file_available(db, file_id):
    file_record = crud.get_file_by_file_id(db, file_id)
    if file_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    return file_record
        
def get_all_file_records(db, session_id: int, user_id: int):
    session_available = is_session_available_by_session_id(db, user_id, session_id)
    if session_available is not None:
        file_records = crud.get_all_files(db, session_id)
    if file_records is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no file records available."
        )
    return file_records

def get_collection_name(username, file_name):
    return username + '_' + file_name[:-4]

def get_chroma_name(user_id, session_id):
    return str(user_id) + '@' +str(session_id)+ '_chroma_db'

def get_external_chroma_name(project_id):
    return str(project_id) + '@' + '_external_chroma_db'

def create_chunk(file_name: str):
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    file_dir = os.path.join(UPLOAD_DIR, file_name)
        
    if file_name.endswith(".txt"):
        loader = TextLoader(file_dir)
    elif file_name.endswith(".pdf"):
        loader = PyPDFLoader(file_dir)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid file format. Only.txt and.pdf are supported."
        )
        
    documents = loader.load()
        
    """
    create chroma database
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
        
    chunks = text_splitter.split_documents(documents)
    return chunks

def upload_file_to_chroma(db: Session, file, user, session):

    try:
        collection_name = get_collection_name(user.username,file.filename)

        """check if session is already created"""
        session_record = get_session(db, user.id, session)
        if session_record is None:
            session_record = create_session(db, session,user.id)
        
        session_id = session_record.id
        chroma_name =  get_chroma_name(user.id, session_id)
        chroma_dir = os.path.join(current_dir,"chroma_db")
        if not os.path.exists(chroma_dir):
            os.mkdir(chroma_dir)
        
        persistent_dir = os.path.join(chroma_dir, chroma_name)
        
        """
        store file upload
        """
        if not os.path.exists(UPLOAD_DIR):
            os.mkdir(UPLOAD_DIR)
            
        file_name = _store_file(file, UPLOAD_DIR)
        
        chunks = create_chunk(file_name)
        
        """"
        create instance of chroma class
        """

        chroma_data = crud.create_chroma(db, session_id, collection_name, file_name)
        
        all_docs_chroma = Chroma(
            collection_name="my_collection",
            embedding_function=embedding
        )
        all_docs_chroma.from_documents(
            documents=chunks,
            persist_directory=persistent_dir,
            embedding=embedding,
            collection_name="my_collection"
        )
        all_docs_chroma.add_documents(chunks)
        
        chroma_instance = Chroma(
            collection_name=collection_name, 
            embedding_function=embedding
        )
         
        chroma_instance.from_documents(
            documents=chunks,
            persist_directory=persistent_dir,
            embedding=embedding,
            collection_name=collection_name
        )
        
        """"
        remove file from the directory
        """
        os.remove(os.path.join(UPLOAD_DIR, file_name))
        
        return chroma_data
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        
        
def upload_external_file_to_chroma(db: Session, file, project_id):
    try:
        """Insert chroma name into database"""
        chroma_name = get_external_chroma_name(project_id)
        update_chroma_name(db, project_id, chroma_name)
               
        chroma_dir = os.path.join(current_dir,"chroma_db")
        if not os.path.exists(chroma_dir):
            os.mkdir(chroma_dir) 
        persistent_dir = os.path.join(chroma_dir, chroma_name)
        
        """
        store file upload
        """
        file_name = _store_file(file, UPLOAD_DIR)
        
        """
        insert external file to database
        """
        file_record = crud.create_external_file(db, project_id, file_name)
        
        chunks = create_chunk(file_record.file_name)
        
        """"
        create instance of chroma class
        """
        chroma_instance = Chroma(
            collection_name="my_collection", 
            embedding_function=embedding
        )
        chroma_instance.from_documents(
            documents=chunks,
            persist_directory=persistent_dir,
            embedding=embedding,
            collection_name="my_collection"
        )
        chroma_instance.add_documents(chunks)
        """"
        remove file from the directory
        """
        os.remove(os.path.join(UPLOAD_DIR, file_name))
        
        return file_name
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
def get_all_external_files(db: Session, project_id: int):
    try:
        project_record = get_project_detail(db, project_id)
        files_list = get_all_filenames(db, project_record.project_id)
        return files_list
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    
def delete_all_files(db: Session, user, session_id: int):
    try:
        """Clear collection in chroma database"""
        chroma_name = chroma_dependencies.get_chroma_name(user.id, session_id)
        chroma_dir = os.path.join(current_dir, "..", "chroma", "chroma_db")
        
        if not os.path.exists(chroma_dir):
            os.mkdir(chroma_dir) 
        # persistent_dir = os.path.join(chroma_dir, chroma_name)
        
        """delete all files in the database"""
        all_files = chroma_crud.get_all_files(db,session_id)
        
        if all_files is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No files found in the session."
            )
        """delete collection name in chroma & database"""
        for file in all_files:
            """create instance of chroma class"""
            chroma_instance = Chroma(
                collection_name=file.get('collection_name'), 
                embedding_function=embedding
            ) 
            chroma_instance.delete_collection()
            chroma_crud.delete_file(db, file.get('id'))
        Chroma(
            collection_name="my_collection", 
            embedding_function=embedding
        ).delete_collection()
        db.commit()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
        
def upload_to_HRDBot(
    file
):
    try:
        chroma_name = "HRDBot_chroma_db"
        collection_name = "HRDBot_collection"
        file_name = _store_file(file, UPLOAD_DIR)
        chunks = create_chunk(file_name)
        
        chroma_dir = os.path.join(current_dir,"chroma_db")
        if not os.path.exists(chroma_dir):
            os.mkdir(chroma_dir) 
        persistent_dir = os.path.join(chroma_dir, chroma_name)
        
        """"
        create instance of chroma class
        """
        chroma_instance = Chroma(
            collection_name=collection_name, 
            embedding_function=embedding
        )
        chroma_instance.from_documents(
            documents=chunks,
            persist_directory=persistent_dir,
            embedding=embedding,
            collection_name=collection_name
        )
        chroma_instance.add_documents(chunks)
        
        """"
        remove file from the directory
        """
        os.remove(os.path.join(UPLOAD_DIR, file_name))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    