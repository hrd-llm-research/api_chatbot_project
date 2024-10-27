from sqlalchemy.orm import Session
from app.db_connection.models import MessageHistory

def get_history_by_session(db: Session, session_id: int):
    history_record = db.query(MessageHistory).filter(MessageHistory.session_id == session_id).first()
    return history_record

def create_history(db: Session, request):
    db.add(request)
    db.commit()
    db.refresh(request)
    return request
