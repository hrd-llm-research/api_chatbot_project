from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from app.utils import get_db
from app.db_connection.schemas import UserCreate
from app.auth import dependencies
from app.auth.crud import create_user
from app.mail.dependencies import send_mail


ACCESS_TOKEN_EXPIRE_MINUTES = 432003

router = APIRouter(
    prefix="/auth",
    tags={"auth"}
)


@router.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    user_response = dependencies.create_user(db, user)
    
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "You registered successfully",
                 "success": True,
                 "payload": user_response
        }
    )
    
@router.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()] , db: Session = Depends(get_db)):
    user = dependencies.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = dependencies.create_access_token(
        data={"email": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/reset-password")
async def reset_password(
    password: str = Query(...),
    email: str = Query(...),
    db: Session = Depends(get_db)
):
    user = dependencies.validate_existing_email(db, email)
    dependencies.reset_password(db, password, user)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Password has been reset successfully.",
                 "success": True,
        }
    )

@router.post("/code-verify")
async def code_verify(
    code: str = Query("000000",min_length=6, max_length=6),
    email: str = Query("example@example.com", description="User's email"),  
    db: Session = Depends(get_db)
):
    user = dependencies.validate_existing_email(db, email)
    is_true = dependencies.verify_account(db, code, user)
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Code is verified.",
                 "success": is_true,
        }
    )
    
@router.post("/resend-code")
async def resend_code(
    email: str = Query("example@example.com", description="User's email"),
    db: Session = Depends(get_db)  
):
    user = dependencies.validate_existing_email(db, email)
    code = dependencies.generate_opt(db, user.id)
    
    send_mail(user.email, 'Verify Code to activate the account', f'Here is the {code} for account activation. Please enter your code.')
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": f"Code have been sent to {email}. Please check your email address.",
                "success": True
        }
    )