import sys
import json
import asyncio
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from langchain_groq import ChatGroq
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse
from langserve import add_routes
from app.db_connection import models, database
from app.db_connection.models import Base
from fastapi.middleware.cors import CORSMiddleware
from app.chatbot.chain import chain
from app.chatbot.suggestionQ_chain import chain as suggestion_chain
from app.chatbot.project_chain import chain as external_chain
from app.chatbot.hrd_chain import chain as conversational_rag_chain
from typing import Annotated
from app.auth.dependencies import get_current_active_user, get_current_user
from app.db_connection.schemas import User
from app.utils import get_db

from fastapi import FastAPI, Request, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.chatbot.dependencies import save_ai_response, save_playground_ai_response
from app.auth.routes import router as auth_routes
from app.session.routes import router as session_routes
from app.chroma.routes import router as chroma_routes
from app.api_generation.routes import router as api_generation_routes
from app.api_generation.routes import verify_api_key
from app.model_provider.routes import router as model_provider_routes
from app.chatbot.routes import router as chatbot_routes
from app.chatbot.project_stream import chain as streaming_chain
from app.chatbot.chain_stream import chain as playground_streaming_chain
from app.api_generation.routes import verify_api_key

from app.db_connection.database import SessionLocal
llm = ChatGroq(
    model="Llama3-8b-8192",
    temperature=1,
    api_key="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"
)

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
app.include_router(chatbot_routes, prefix="/api/v1")

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
    suggestion_chain,
    path="/suggestion_chatbot",
    enabled_endpoints=["invoke"],
    dependencies=[Depends(get_current_active_user)],
)

add_routes(
    app,
    external_chain,
    path="/external_chain",
    enabled_endpoints=["invoke", "stream"],
    dependencies=[Depends(verify_api_key)]
)

add_routes(
    app,
    conversational_rag_chain,
    path="/hrd_chain",
    enabled_endpoints=["invoke"],
)

# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     return JSONResponse(
#         status_code=400,
#         content={"message": "Validation failed!", "details": exc.errors()},
#     )

@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")

add_routes(
    app,
    playground_streaming_chain,
    path="/socket",
    # enabled_endpoints=["invoke", "stream"],
    # dependencies=[Depends(verify_api_key)]
)

async def generate_chunked_stream(prompt: dict):
    try:
        db = SessionLocal()
        ai_response = ""
        # yield json.dumps({"type": "title", "content": "Response Title"})
        await asyncio.sleep(0.05)
        
        stream = streaming_chain.stream(prompt)
        for chunk in stream:
            # Check content and tag accordingly for better structure
            content_type = "paragraph"
            if "•" in chunk:  # Assume bullets denote list items
                content_type = "list_item"
            elif "```" in chunk:  # Assume code blocks with ```
                content_type = "code"
            
            ai_response += chunk
            yield json.dumps({"type": content_type, "content": chunk})
            await asyncio.sleep(0.05)

        save_ai_response(db, prompt['input']['external_session_id'],prompt['input']['project_id'], ai_response)
        # yield json.dumps({"type": "paragraph", "content": "End of response."})
    except Exception as e:
        yield json.dumps({"type": "error", "content": f"Error generating response: {str(e)}"})


@app.websocket("/ws/generate-response")
async def websocket_endpoint(websocket: WebSocket,
    # db: Annotated[Session, Depends(get_db)]
    ):
    await websocket.accept()
    try:
        # token = websocket.headers.get("REST-API-KEY")
        # # Validate the token using your existing `get_current_user`
        # current_user = await verify_api_key(api_key=token, db=db)
        data = await websocket.receive_json()
        print("data: ",data)
        while True:  # Continuous loop to handle multiple messages
              # Wait for each new message from the client
            async for chunk in generate_chunked_stream(data):
                await websocket.send_text(chunk)
        
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_text(json.dumps({"type": "error", "content": f"Error: {str(e)}"}))


async def generate_playground_widget_chunked_stream(prompt: dict):
    try:
        ai_response = ""
        await asyncio.sleep(0.05)
        
        stream = streaming_chain.stream(prompt)
        for chunk in stream:
            
            ai_response += chunk
            yield json.dumps({"content": chunk})
            await asyncio.sleep(0.05)
    except Exception as e:
        yield json.dumps({"type": "error", "content": f"Error generating response: {str(e)}"})


@app.websocket("/ws/generate-response-playground-widget")
async def widget_websocket_endpoint(websocket: WebSocket
    ):
    await websocket.accept()
    try:
        while True:  # Continuous loop to handle multiple messages
            data = await websocket.receive_json()  # Wait for each new message from the client
            async for chunk in generate_chunked_stream(data):
                await websocket.send_text(chunk)
        
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_text(json.dumps({"type": "error", "content": f"Error: {str(e)}"}))


async def generate_playground_chunked_stream(prompt: dict):
    try:
        db = SessionLocal()
        ai_response = ""
        # yield json.dumps({"type": "title", "content": "Response Title"})
        await asyncio.sleep(0.05)
        
        from langchain.schema.output_parser import StrOutputParser
        from app.model_provider.dependencies import get_lm_from_cache
        
        # llm = get_lm_from_cache(prompt['input']['user_id'])
        
        chaining = playground_streaming_chain | llm | StrOutputParser()
        stream = chaining.stream(prompt)
        for chunk in stream:
            # if chunk.strip() == '`':
            #     chunk = "\\`"
            # elif chunk.strip() == '``':
            #     chunk = "\\`\\`"
            # elif chunk.strip() == '```':
            #     chunk = "\\`\\`\\`"
            # Check content and tag accordingly for better structure
            # content_type = "paragraph"
            # if "•" in chunk:  # Assume bullets denote list items
            #     content_type = "list_item"
            # elif "```" in chunk:  # Assume code blocks with ```
            #     content_type = "code"
            ai_response += chunk
            # yield json.dumps({"type": content_type, "content": chunk})
            yield json.dumps({"content":chunk})
            await asyncio.sleep(0.05)
        
        print("ai reponse\n",ai_response)
        save_playground_ai_response(db, prompt['input']['user_id'],prompt['input']['session_id'], ai_response)
        # yield json.dumps({"type": "paragraph", "content": "End of response."})
    except Exception as e:
        yield json.dumps({"type": "error", "content": f"Error generating response: {str(e)}"})

@app.websocket("/ws/playground_generate-response")
async def playground_websocket_endpoint(websocket: WebSocket,
    # db: Annotated[Session, Depends(get_db)]
    ):
    await websocket.accept()
    try:
        
        # token = websocket.headers.get("Authorization")
        # if not token or not token.startswith("Bearer "):
        #     raise WebSocketDisconnect(code=1008)
        
        # # Validate the token
        # token = token.split("Bearer ")[1]
        # # Validate the token using your existing `get_current_user`
        # current_user = await get_current_user(token=token, db=db)

        # # Check if the user is active using your existing `get_current_active_user`
        # active_user = await get_current_active_user(current_user=current_user)
        
        while True:  # Continuous loop to handle multiple messages
            data = await websocket.receive_json()  # Wait for each new message from the client
            generate_playground_chunked_stream(data)
            async for chunk in generate_playground_chunked_stream(data):
                await websocket.send_text(chunk)
        
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(e)
        await websocket.send_text(json.dumps({"type": "error", "content": f"Error: {str(e)}"}))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)



# from fastapi import FastAPI
# from fastapi.responses import RedirectResponse
# from langserve import add_routes


# app = FastAPI(
#     title="Chatbot API",
#     description="A simple chatbot API with Langchain and FastAPI",
#     version="1.0.0",
# )

# from langchain_community.llms import Ollama
# from langchain.prompts import ChatPromptTemplate
# prompt = ChatPromptTemplate.from_template("tell me a joke about {topic}")
# llm = Ollama(
#     base_url="http://ollama:11434",
#     model="llama3.2:1b",
#     temperature=0.7,
#     # timeout=30,  # Increase the timeout to 30 seconds
# )
# add_routes(
#     app,
#     prompt | llm,
#     path="/chat_with_llm"
# )

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="localhost", port=8088)