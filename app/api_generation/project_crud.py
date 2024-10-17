from sqlalchemy.orm import Session
from app.db_connection import models
from app.api_generation import project_dependencies

def insert_project(db: Session, project_name: str, user_id: int, api_key: str):

    project_data = models.Project(
            user_id=user_id,
            project_name=project_name,
            api_key=api_key
    )
    db.add(project_data)
    db.commit()
    db.refresh(project_data)

    return project_data

def get_api_key(db: Session, api_key: str):
    project_record = db.query(models.Project).filter(models.Project.api_key == api_key).first()
    return project_record

def get_all_projects(db: Session, user_id: int):
    project_records = db.query(models.Project).filter(models.Project.user_id == user_id).all()
    project_records_dict = [project_record.to_dict() for project_record in project_records]
    return project_records_dict

def get_project_by_project_id(db: Session, project_id: int):
    project_record = db.query(models.Project).filter(models.Project.id == project_id).first()
    return project_record

def delete_project(db: Session, project_id: int):
    return db.query(models.Project).filter(models.Project.id == project_id).delete()

def update_description(db: Session, project_id: int, description: str):
    project_record = project_dependencies.get_project_detail(db, project_id)
    project_record.description = description
    db.commit()
    db.refresh(project_record)
    return project_record.to_dict()

def update_chroma_name(db: Session, project_id: int, chroma_name: str):
    project_record = project_dependencies.get_project_detail(db, project_id)
    project_record.chroma_name = chroma_name
    db.commit()
    db.refresh(project_record)
    return project_record.to_dict()

def get_all_filenames(db: Session, project_id: int):
    external_file_records = db.query(models.ExternalFile).filter(models.ExternalFile.project_id == project_id).all()
    external_file_lists = [file.to_dict() for file in external_file_records]
    return external_file_lists


def create_external_session(db: Session, project_id: int, session):
    external_session_record = models.ExternalSession(
        project_id=project_id,
        session=session
    )
    db.add(external_session_record)
    db.commit()
    db.refresh(external_session_record)
    return external_session_record

def get_external_session_by_session_id(db: Session, session):
    session = db.query(models.ExternalSession).filter(models.ExternalSession.session == session).first()
    return session

def get_project_by_project_name(db: Session, project_name: str):
    project_record = db.query(models.Project).filter(models.Project.project_name == project_name).first()
    return project_record


def get_all_session_by_project_id(db: Session, project_id: int):
    session_records = db.query(models.ExternalSession).filter(models.ExternalSession.project_id == project_id).all()
    session_records_dict = [session_record.to_dict() for session_record in session_records]
    return session_records_dict


def delete_external_session(db: Session, session_id: int):
    return db.query(models.ExternalSession).filter(models.ExternalSession.id == session_id).delete()