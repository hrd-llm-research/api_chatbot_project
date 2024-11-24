from sqlalchemy.orm import Session
from app.db_connection import models

def create_session(db: Session, session, user_id: int):
    session_data = models.Session(session=session, user_id=user_id)
    db.add(session_data)
    db.commit()
    db.refresh(session_data)
    return session_data

def update_session_name(db: Session, session_name: str, session_id: int):
    session_record = get_session_by_session_id(db, session_id)
    print("session_record: ", session_record.to_dict())
    if session_record.session_name is None: 
        session_record.session_name = session_name
        db.commit()
        db.refresh(session_record)
        return session_record

def get_all_session(db: Session, user_id: int):
    session_records = db.query(models.Session).filter(models.Session.user_id == user_id).all()
    session_list = [session.to_dict() for session in session_records]
    return session_list

def find_session(db: Session, user_id: int, session):
    session_record = db.query(models.Session).filter(models.Session.session == session and models.Session.user_id == user_id).first()
    return session_record

def find_session_by_session_id(db: Session, session_id:int):
    session_record = db.query(models.Session).filter(models.Session.id == session_id).first()
    return session_record


def create_history(db: Session, session_id: int, history_name: str):
    history_data = models.MessageHistory(
        session_id=session_id,
        history_name=history_name
    )
    db.add(history_data)
    db.commit()
    db.refresh(history_data)
    return history_data

def find_history(db: Session, history_name: str):
    history_record = db.query(models.MessageHistory).filter(models.MessageHistory.history_name == history_name).first()
    return history_record

def get_history_by_session_id(db: Session, session_id: int):
    history_record = db.query(models.MessageHistory).filter(models.MessageHistory.session_id == session_id).first()
    return history_record

def delete_history_by_history_name(db: Session, history_name: str):
    db.query(models.MessageHistory).filter(models.MessageHistory.history_name == history_name).delete()
    db.commit()

def delete_session_by_session_id(db: Session, session_id: int):
    
    db.query(models.Session).filter(models.Session.id == session_id).delete()
    db.commit()
    
def get_session_by_session_id(db: Session, session_id: int):
    session_record = db.query(models.Session).filter(models.Session.id == session_id).first()
    return session_record