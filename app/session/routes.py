from fastapi import APIRouter, Depends, status, Query, HTTPException, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.utils import get_db
from typing import Annotated
from app.db_connection.schemas import User
from app.auth.dependencies import get_current_active_user
from . import dependencies
from app.auth.dependencies import validate_existing_email
from app.session import dependencies as session_dependencies
from app.chatbot import hrd_chain
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
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Retrieve all sessions successfully.",
                 "success": True,
                 "payload": list_of_sessions}
    )

@router.get('/all_session_histories')
async def get_all_session_histories(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    user = validate_existing_email(db, current_user.email)
    list_of_sessions = dependencies.get_all_sessions(db, user.id)
 
    all_histories = []
    for session in list_of_sessions:
        print("session: ",session['id'])
        docs = dependencies.get_history(db, user, session['id'])
        all_histories.append(
            {
                "id": session['id'],
                "session" : session['session'],
                "history": docs
            }
        )
    
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Retrieve all sessions successfully.",
                 "success": True,
                 "payload": all_histories}
    )

@router.post('/save/{session_id}')
async def save_session(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session_id: int = Path(..., ge=1, description="Session ID"),
    db: Session = Depends(get_db)
):
    user = validate_existing_email(db, current_user.email)
    session_dependencies.save_internal_session(db, user, session_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Session saved successfully.",
                 "success": True}
    )


@router.get('/history/{session_id}')
async def get_history(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session_id: int = Path(..., ge=1, description="Session ID"),
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, description="Number of results to return per page"),
    page: int = Query(1, ge=0, description="Page number of results to return, starting from 1"),
):
    user = validate_existing_email(db, current_user.email)
    docs = dependencies.get_history(db, user, session_id, page, limit)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Get session history successfully.",
                 "success": True,
                 "payload": docs}
    )

@router.get('/get_session_detail')
async def get_session_detail(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session,
    db: Session = Depends(get_db),
):
    user = validate_existing_email(db, current_user.email)
    session_record = dependencies.is_session_available(db, user.id, session)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Get session detail successfully.",
                 "success": True,
                 "payload": session_record.to_dict()
                 }
    )

@router.get('/history')
async def get_history_by_session(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session,
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, description="Number of results to return per page"),
    page: int = Query(1, ge=0, description="Page number of results to return, starting from 1"),
):
    user = validate_existing_email(db, current_user.email)
    docs = dependencies.get_history_by_session(db, user, session, page, limit)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Get session history successfully.",
                 "success": True,
                 "payload": docs
                 }
    )

@router.delete('/delete/{session_id}')
def delete_session(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session_id: int = Path(..., ge=1, description="Session ID"),
    db: Session = Depends(get_db)
):
    user = validate_existing_email(db, current_user.email)
    dependencies.delete_session(db, user, session_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Session deleted successfully.",
                 "success": True}
    )
    

  
@router.get('/session/{session_id}')  
def get_session_by_session_id(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session_id: int = Path(..., ge=1, description="Session ID"),
    db: Session = Depends(get_db)
):
    user = validate_existing_email(db, current_user.email)
    session_record = dependencies.get_session_by_session_id(db, session_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Get session by session ID successfully.",
                 "success": True,
                 "payload": session_record.to_dict()}
    )
    
@router.get('/chat/{session_id}')
def get_chat_history(
    session_id: str = Path(..., description="Session ID get from UI"),
    limit: int = Query(10, ge=1, description="Number of results to return per page"),
    page: int = Query(1, ge=0, description="Page number of results to return, starting from 1"),
):
    history = hrd_chain.get_hrd_history(session_id, limit, page)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Get chat history successfully.",
                 "success": True,
                 "payload": history})