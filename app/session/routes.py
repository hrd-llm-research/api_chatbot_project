from fastapi import APIRouter, Depends, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.utils import get_db
from typing import Annotated
from app.db_connection.schemas import User
from app.auth.dependencies import get_current_active_user
from . import dependencies
from app.auth.dependencies import validate_existing_email

import uuid

router = APIRouter(
    prefix="/session",
    tags=["session"]
)

@router.post("/create_session")
async def create_new_chat(
    current_user: Annotated[User, Depends(get_current_active_user)], 
):
    session_id = str(uuid.uuid4())
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": "New chat session started with session ID: {}".format(session_id),
            "success": True,
            "session_id": session_id,
        }
    )

@router.get('/all_sessions')
async def get_all_sessions(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    user = validate_existing_email(db, current_user.email)
    list_of_sessions = dependencies.get_all_sessions(db, user.id)
    return {"payload" : list_of_sessions}