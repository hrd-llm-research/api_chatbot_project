from sqlalchemy.orm import Session
from . import crud
from fastapi import HTTPException, status

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
    session_record = crud.find_session_by_session_id(db, user_id, session_id)
    if session_record is False:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session_record

def get_session(db: Session, user_id: int, session):
    session_record = crud.find_session(db, user_id, session)
    return session_record