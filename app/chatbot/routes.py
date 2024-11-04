from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from project_chain import chain
from app.db_connection.schemas import ExternalChatbotSchema
from app.api_generation.routes import verify_api_key

router = APIRouter(
    prefix="/chatbot",
    tags=["chatbot"],
)

@router.post("/external_chatbot/invoke")
async def invoke_chain(request_data: ExternalChatbotSchema, project: str = Depends(verify_api_key)):
    request = await request_data.json()
    response = await chain.invoke({
          "input": {
                "input": request.input,
                "external_session_id": request.external_session_id,
                "project_id": request.project_id
        }
    })
    print("response: ", response)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
                content={"message": "Project retrieved successfully.",
                 "success": True,
                 "project_id": response,
        }
    )