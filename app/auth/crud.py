from app.db_connection import models, schemas
from app.auth import dependencies
from sqlalchemy.orm import Session
from sqlalchemy import desc

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = dependencies.pwd_context.hash(user.password)
    
    user_record = models.User(
        username=user.username,
        email=user.email,
        password=hashed_password,
    )
    
    db.add(user_record)
    db.commit()
    db.refresh(user_record)
    return user_record

def create_third_party_user(db: Session, user: schemas.ThirdPartyUserCreate):
    hashed_password = dependencies.pwd_context.hash(user.sub)
    
    user_record = models.User(
        username=user.username,
        email=user.email,
        password=hashed_password,
        profile_img=user.image,
        is_active=True
    )
    
    db.add(user_record)
    db.commit()
    db.refresh(user_record)
    return user_record


def get_user_by_email(db: Session, email: str):
    user_record = db.query(models.User).filter(models.User.email == email).first()
    # user_response = schemas.UserResponse(
    #     id=user_record.id,
    #     username=user_record.username,
    #     email=user_record.email,
    #     is_active=user_record.is_active
    # )
    # return user_response
    return user_record

def create_opt(db: Session, user_id: int, opt: str):
    db_opt = models.Opt(
        user_id=user_id,
        code=opt,
    )
    db.add(db_opt)
    db.commit()
    db.refresh(db_opt)
    return db_opt

def update_active_account(db: Session, user_id:int):
    user_record = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_record:
        return False

    user_record.is_active = True
    db.add(user_record)
    db.commit()
    db.refresh(user_record)
    return user_record.to_dict()
    
def get_code_by_userId(db: Session, user_id):
    opt_db = db.query(models.Opt).filter(models.Opt.user_id == user_id).order_by(desc(models.Opt.created_at)).first()
    return opt_db
    
def update_password(db: Session, user_id:int, password: str):
    user_record = db.query(models.User).filter(models.User.id == user_id).first()
    if user_record is None: return False
    
    hashed_password = dependencies.pwd_context.hash(password)
    user_record.password = hashed_password
    
    db.add(user_record)
    db.commit()
    db.refresh(user_record)
    return True

def get_user_by_user_id(db: Session, user_id):
    user_record = db.query(models.User).filter(models.User.id == user_id).first() 
    if user_record is None: return False
    
    return user_record