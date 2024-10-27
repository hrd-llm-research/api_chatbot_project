from sqlalchemy.orm import Session
from app.db_connection.models import ModelCustomization, ModelProvider, Model
from app.db_connection.schemas import ModelCustomizationCreate

def create_model_customization(db: Session, request: ModelCustomizationCreate, user_id: int) -> ModelCustomization:
    model_data = ModelCustomization(
        user_id = user_id,
        model_id = request.model_id,
        provider_api_key = request.provider_api_key,
        temperature = request.temperature,
        max_token = request.max_token,
    )
    db.add(model_data)
    db.commit()
    db.refresh(model_data)
    return model_data

def get_customed_model(db: Session, user_id: int):
    model = db.query(ModelCustomization).filter(ModelCustomization.user_id == user_id).first()
    return model
    
def update_customed_model(db: Session, user_id: int, request):
    model_record = get_customed_model(db, user_id)
    model_record.model_id = request.model_id
    model_record.provider_api_key=request.provider_api_key
    model_record.temperature = request.temperature
    model_record.max_token = request.max_token
    db.commit()
    db.refresh(model_record)
    return model_record
    
    
def get_llm_by_user_id(db: Session, user_id: int):
    llm_record = db.query(ModelCustomization).filter(ModelCustomization.user_id == user_id).first()
    return llm_record