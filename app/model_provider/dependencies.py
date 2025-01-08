from sqlalchemy.orm import Session

from app.db_connection.schemas import ModelCustomizationCreate
from app.model_provider import crud
from fastapi import HTTPException, status
from app.model_provider import routes
from langchain_groq import ChatGroq
from langchain_community.llms import OpenAI

def update_llm(db: Session, request: ModelCustomizationCreate, user):
    try:
        model_record = is_lm_available(db, user.id)
        if model_record:
            customed_model = crud.update_customed_model(db, user.id, request)
        else:
            customed_model = crud.create_model_customization(db, request, user.id)
        return customed_model
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
def is_lm_available(db: Session, user_id:int):
    try:
        model = crud.get_customed_model(db, user_id)
        return model
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No custom model found for this user"
        )
        

def get_llm(db:Session, user):
    try:
        llm_record = crud.get_llm_by_user_id(db, user.id)
        
        return llm_record
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
def get_lm_from_cache(user_id: int):
    try:
        lm = routes.llm_cache[int(user_id)]
        print("llm ==",lm)
        if lm['provider_info']['provider_id'] == 1:
            # llm = ChatGroq(
            #     model=lm['provider_info']['model_name'],
            #     temperature=lm['temperature'],
            #     api_key=lm['provider_api_key']
            # )
            from langchain_ollama import OllamaLLM
            llm = OllamaLLM(
                model=lm['provider_info']['model_name'],
                temperature=lm['temperature'],
            )
            print("is working")
        elif lm['provider_info']['provider_id'] == 2:
            llm = OpenAI(
                model=lm['provider_info']['model_name'],
                temperature=lm['temperature'],
                api_key=lm['provider_api_key']
            )
        return llm
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No LLM found. Please use /api/v1/model_provider/llm to get your LLM." + str(e)
        )
    
def get_all_models(db: Session):
    try:
        models = crud.get_models(db)
        return models
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
def get_all_providers(db: Session):
    try:
        providers = crud.get_providers(db)
        return providers
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )