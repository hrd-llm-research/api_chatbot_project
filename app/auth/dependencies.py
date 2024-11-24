from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from app.auth import crud
from app.db_connection import schemas
from typing import Annotated
from fastapi import Depends,HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.utils import get_db
from datetime import datetime
from app.mail.dependencies import send_mail

import random
import jwt

SECRET_KEY="7c8df4aab2ee154c02677be42f5dd08b0f20726a493786548898729a499da682"
ALGORITHMS = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db: Session, email: str, password: str):
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="User is not found."
        )
    
    if user.is_active == False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="User is not authorized."
        )
    if not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="User is not authorized."
        )
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHMS)
    return encoded_jwt

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)]
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate":"Bearer"}
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHMS])
        email: str = payload.get("email")
        
        if email is None:
            raise credentials_exception
        
        token_data = schemas.TokenData(email=email)
        user = crud.get_user_by_email(db, email=token_data.email)
        
        if user is None:
            raise credentials_exception
        print("get user: ",user.to_dict())
        return user
        
    except Exception as e:
        raise credentials_exception

async def get_current_active_user(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
):
    print("current is active: ",current_user)
    if current_user.is_active == False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


def generate_opt(db: Session, user_id:int) -> None:
    try: 
        random_number = random.randint(100001, 999999)
        crud.create_opt(db, user_id, random_number)
        return random_number
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
def verify_account(db: Session, code: str, user):
    current_date = datetime.now()
    
    if user.is_active == True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is already active"
        )
    
    opt = crud.get_code_by_userId(db, user.id)
    
    if opt.code == code and current_date < opt.expired_at:
        crud.update_active_account(db, user.id)
        return True
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid code or expired"
    )

def verify_code(db: Session, code: str, user):
    try:
        current_date = datetime.now()
        opt = crud.get_code_by_userId(db, user.id)
    
        if opt.code == code and current_date < opt.expired_at:
            return True
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid code or expired"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
def validate_existing_email(db:Session, email: str):
    user = crud.get_user_by_email(db, email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email is not found"
        )
    return user

def reset_password(db: Session, password: str, user):
    is_true = crud.update_password(db,user.id, password)
    if is_true is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password isn't updated successfully"
        )
        
def find_user(db: Session, user_id: int):
    user = crud.get_user_by_user_id(db, user_id)
    if user is False:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user.username

def validate_email(db: Session, email: str):
    user = crud.get_user_by_email(db, email)
    if user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    return True

def create_user(
    db:Session,
    user
):
    try:
        validate_email(db, user.email)
        
        user = crud.create_user(db, user)
        code = generate_opt(db, user.id)
        
        send_mail(user.email, 'Verify Code to activate the account', f'Here is the {code} for account activation. Please enter your code.')
        return user.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
