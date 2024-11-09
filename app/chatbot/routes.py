from fastapi import APIRouter, Depends, status, Query, Path, HTTPException
from fastapi.responses import JSONResponse
from app.db_connection.schemas import ExternalChatbotSchema, SuggestionBotSchema, TexBotSchema, ChatbotPlaygroundSchema
from app.api_generation.routes import verify_api_key
from app.auth.dependencies import get_current_active_user
from typing import Annotated
from app.db_connection.schemas import User

from app.chatbot.project_chain import chain as external_chain
from app.chatbot.suggestionQ_chain import chain as suggestion_chain
from app.chatbot.chain import chain as playground_chain
from app.chatbot.hrd_chain import chain as texbot_chain

router = APIRouter(
    prefix="/chatbot",
    tags=["chatbot"],
)

@router.post("/external_chatbot/invoke")
async def invoke_chain(request: ExternalChatbotSchema, project: str = Depends(verify_api_key)):
    response = external_chain.invoke({
          "input": {
                "input": request.input,
                "external_session_id": request.external_session_id,
                "project_id": request.project_id
        }
    })
    return JSONResponse(
        status_code=status.HTTP_200_OK,
                content={
                "message": "Retrieved message sucessfully.",
                "success": True,
                "payload": response,
        }
    )

@router.post("/suggestion_chain/invoke")    
async def invoke_suggestion_chain(
    request: SuggestionBotSchema,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    print("Received user_id:", request.user_id)
    print("Received session_id:", request.session_id)
    print("Received file_id:", request.file_id) 


    response = suggestion_chain.invoke(
        {
            "user_id": request.user_id,
            "session_id": request.session_id,
            "file_id": request.file_id  # Pass file_id as received, it should be None if not provided
        }
    )

    return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Retrieved message sucessfully.",
                "success": True,
                "payload": response
        }
    )


@router.post("/playground_chain/invoke")
async def invoke_playground_chain(
    request: ChatbotPlaygroundSchema,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    response = playground_chain.invoke({
        "input": {
            "input": request.input,
            "user_id": request.user_id,
            "session_id": request.session_id,
            "file_id": request.file_id
        }
    })
    
    return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Retrieved message sucessfully.",
                "success": True,
                "payload": response
        }
    )
    
    
    
@router.post("")
async def invoke_texbot_chain(
    request: TexBotSchema
):
    response = texbot_chain.invoke({
        "input": {
            "input": request.input,
            "session_id": request.session_id
        }
    })
    return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Retrieved message sucessfully.",
                "success": True,
                "payload": response
        }
    )