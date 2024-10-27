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
    user = validate_existing_email(db, current_user.email)
    llm_record = dependencies.get_llm(db, user)
    llm_cache[user.id] = llm_record.to_dict()
    print("llm cache: ", llm_cache)
    return JSONResponse(
        status_code=200,
        content={"message": "LLM retrieved successfully.",
                 "success": True,
                 "llm_id": llm_record.to_dict()}
    )




