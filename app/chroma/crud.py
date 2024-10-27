from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db_connection.models import FileMetadata, ExternalFile


def create_chroma(db: Session, session_id, collection_name: str, file_name: str):
    file_data = FileMetadata(
        session_id = session_id,
        collection_name = collection_name,
        file_name = file_name
    )
    
    db.add(file_data)
    db.commit()
    db.refresh(file_data)
    
    return file_data

def get_file_by_file_id(db: Session, file_id: int):
    file_record = db.query(FileMetadata).filter(FileMetadata.id == file_id).first()
    
    return file_record

def get_all_files(db: Session, session_id: int):
    file_records = db.query(FileMetadata).filter(FileMetadata.session_id == session_id).all()

    file_records_dict = [file_record.to_dict() for file_record in file_records]
    
    return file_records_dict

def create_external_file(db: Session, project_id: int, file_name: str):
    file_data = ExternalFile(
        project_id = project_id,
        file_name = file_name
    )
    
    db.add(file_data)
    db.commit()
    db.refresh(file_data)
    
    return file_data

def delete_file(db: Session, file_id: int):
    return db.query(FileMetadata).filter(FileMetadata.id == file_id).delete()

def delete_file_by_session_id(db: Session, session_id: int):
    return db.query(FileMetadata).filter(FileMetadata.session_id == session_id).delete()


def delete_external_file_by_project_id(db: Session, project_id: int):
    db.query(ExternalFile).filter(ExternalFile.project_id == project_id).delete()
    db.commit()