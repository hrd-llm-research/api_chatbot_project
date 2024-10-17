from sqlalchemy.orm import Session
from app.db_connection import models

def create_session(db: Session, session, user_id: int):
    session_data = models.Session(session=session, user_id=user_id)
    db.add(session_data)
    db.commit()
    db.refresh(session_data)
    return session_data


def get_all_session(db: Session, user_id: int):
    session_records = db.query(models.Session).filter(models.Session.user_id == user_id).all()
    
    if not session_records:
        return False
    
    return session_records

def find_session(db: Session, user_id: int, session):
    session_record = db.query(models.Session).filter(models.Session.session == session and models.Session.user_id == user_id).first()
    return session_record

def find_session_by_session_id(db: Session, user_id: int, session_id:int):
    session_record = db.query(models.Session).filter(models.Session.id == session_id and models.Session.user_id == user_id).first()
    return session_record