import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from langserve import add_routes
from app.db_connection import models, database
from app.db_connection.models import Base
from fastapi.middleware.cors import CORSMiddleware
from app.chatbot.chain import chain
from app.chatbot.suggestionQ_chain import llm_chain
from app.chatbot.project_chain import chain as external_chain
from app.chatbot.hrd_chain import chain as conversational_rag_chain

from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.auth.dependencies import get_current_active_user
from app.auth.routes import router as auth_routes
from app.session.routes import router as session_routes
from app.chroma.routes import router as chroma_routes
from app.api_generation.routes import router as api_generation_routes
from app.api_generation.routes import verify_api_key
from app.model_provider.routes import router as model_provider_routes

app = FastAPI(
    title="Chroma API",
    description="API for managing Chroma projects and sessions",
)

Base.metadata.create_all(bind=database.engine)
    
# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth_routes, prefix="/api/v1")
app.include_router(session_routes, prefix="/api/v1")
app.include_router(chroma_routes, prefix="/api/v1")
app.include_router(api_generation_routes, prefix="/api/v1")
app.include_router(model_provider_routes, prefix="/api/v1")

"""require manually write history"""

"file can be null for chatting with all documents"
add_routes(
    app,
    chain,
    path="/chatbot",
    enabled_endpoints=["invoke"],
    dependencies=[Depends(get_current_active_user)]
)

add_routes(
    app,
    llm_chain,
    path="/suggestion_chatbot",
    enabled_endpoints=["invoke"],
    dependencies=[Depends(get_current_active_user)],
)

add_routes(
    app,
    external_chain,
    path="/external_chain",
    enabled_endpoints=["invoke"],
    dependencies=[Depends(verify_api_key)]
)

add_routes(
    app,
    conversational_rag_chain,
    path="/hrd_chain",
    enabled_endpoints=["invoke"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"message": "Validation failed!", "details": exc.errors()},
    )

@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="localhost", port=8000)
