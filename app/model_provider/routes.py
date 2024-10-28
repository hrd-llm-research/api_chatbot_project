from fastapi import APIRouter, Depends
from typing import Annotated
from sqlalchemy.orm import Session

from app.db_connection.schemas import ModelCustomizationCreate
from app.db_connection.schemas import User
from app.auth.dependencies import get_current_active_user
from app.utils import get_db
from app.auth.dependencies import validate_existing_email
from app.model_provider import dependencies
from fastapi.responses import JSONResponse

router = APIRouter(
    prefix="/model_provider",
    tags=["model_provider"]
)

llm_cache={}

@router.put("/update_llm")
async def update_llm(
    request: ModelCustomizationCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
):
    user = validate_existing_email(db, current_user.email)
    model_record = dependencies.update_llm(db, request, user)
    return JSONResponse(
        status_code=200,
        content={"message": "LLM updated successfully.",
                 "success": True,
                 "model_id": model_record.to_dict()})

@router.get("/llm")
async def get_llm(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
):
    DEFAULT_LM = {
        "provider_api_key": "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",
        "temperature": 0,
        "max_token": 1000,
        "created_at": "2024-10-25T00:04:25.399377",
        "provider_info": {
            "model_id": 1,
            "model_name": "Llama3-8b-8192",
            "provider_id": 1
        }
    }
    user = validate_existing_email(db, current_user.email)
    llm_record = dependencies.get_llm(db, user)
    if not llm_record is None:
        llm_cache[user.id] = llm_record.to_dict()
        return JSONResponse(
        status_code=200,
        content={"message": "LLM retrieved successfully.",
                 "success": True,
                 "payload": llm_record.to_dict()}
    )
    else: 
        llm_cache[user.id] = DEFAULT_LM
        return JSONResponse(
        status_code=200,
        content={"message": "LLM retrieved successfully.",
                 "success": True,
                 "payload": DEFAULT_LM}
    )


@router.get("/all__models")
async def get_all_models(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
):
    user = validate_existing_email(db, current_user.email)
    model = dependencies.get_all_models(db)
    return JSONResponse(
        status_code=200,
        content={"message": "All models retrieved successfully.",
                 "success": True,
                 "models": model}
    )


