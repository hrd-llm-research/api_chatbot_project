import os
import json

from typing import Optional 
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import Runnable , RunnableSequence, RunnableBranch, RunnableParallel, RunnableLambda
from langchain.schema.output_parser import StrOutputParser
from langchain_chroma import Chroma
from fastapi import HTTPException, status
from app.db_connection.database import SessionLocal
from langchain.pydantic_v1 import BaseModel, Field
from app.auth.dependencies import find_user
from app.chroma.dependencies import get_chroma_name, is_file_available
from app.chatbot import crud
from app.db_connection.schemas import MessageHistoryCreate
from app.session import dependencies as session_dependencies
from app.minIO import dependencies as minio_dependencies
from .dependencies import write_history_as_json, write_history_as_text
from app.db_connection import models
from app.model_provider.routes import llm_cache
from app.model_provider.dependencies import get_lm_from_cache

load_dotenv()

# Create embeddings without GPU
embeddings = FastEmbedEmbeddings()

# llm = ChatGroq(
#     model=os.environ.get('OPENAI_MODEL_NAME'),
#     temperature=1,
# )
# llm = ChatGroq(
#     model="Llama3-8b-8192",
#     temperature=1,
#     api_key="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"
# )

# from langchain_ollama import OllamaLLM
# llm = OllamaLLM(
#     model="llama3.1",
#     temperature=0.7,
# )

from langchain_community.llms import Ollama
llm = Ollama(
    base_url="http://ollama:11434",
    model="llama3.1",
    temperature=0.7,
    # timeout=30,  # Increase the timeout to 30 seconds
)

current_dir = os.path.dirname(os.path.abspath(__file__))
history_dir = os.path.join(current_dir, 'history')

# Contextualize question system prompt
contextualize_q_system_prompt = (
        """
            You are a helpful assistant designed to assist users by answering questions based on the content of documents they have uploaded.
            Additionally, you have access to the chat history to provide context for the current conversation.

            Your task is to formulate a standalone question based on the user's current question and any relevant information from the chat history.
            Ensure that the reformulated question is clear, concise, and understandable without any need for the previous chat history.

            If the user's question refers to something mentioned earlier in the conversation, incorporate that information into the new question.
            Always aim to create a question that fully captures the user's intent in a way that is independent of the conversation's context.
            """
        )

# Create a prompt template for contextualizing the questions
contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ]
    )

qa_system_prompt = (
        """
            You are a knowledgeable assistant designed to help users find information from documents they have uploaded. 
            You have access to the content of the document and can provide precise answers based on the text within the document. 
            Always base your responses solely on the information available in the document. 
            If the answer to a user's question is not found in the document, respond by letting them know that the information is not available. 
            Keep your answers clear, concise, and relevant to the user's query.

            {context}
        """
    )

# Create a prompt template for answering questions
qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ]
    )


class CreateRAGChainRunnable(Runnable):
    
    def invoke(self, inputs: dict, *args, **kwargs):
        try:
            db = SessionLocal()
            """declare variables from inputs"""
            question = inputs['input']['input']
            user_id = inputs['input']['user_id']
            session_id = inputs['input']['session_id']
            file_id = inputs['input']['file_id']
            
            # input_data = inputs.get('input')
            # question = input_data.get('input')
            # user_id = input_data.get('user_id')
            # session_id = input_data.get('session_id')
            # file_id = input_data.get('file_id')
            
            """declare variables"""
            session_record = session_dependencies.is_session_available_by_session_id(db, user_id, session_id)

            if file_id is not None:
                file_record = is_file_available(db, file_id)
                collection_name = file_record.collection_name  
            else:
                collection_name = "my_collection" 
            
            username = find_user(db, user_id)
            chroma_db = get_chroma_name(user_id, session_id)
                                                                                                            
            history_file_name = str(user_id)+'@'+str(session_record.session)
            
            """declare file variables"""
            history_json_file = history_file_name+'.json'
            
            history_json_file_dir = os.path.join(history_dir, "json", history_json_file)
            persistent_dir = os.path.join(current_dir, "..", "chroma", "chroma_db", chroma_db)
            
            if not os.path.exists(persistent_dir):
                raise HTTPException(
                    status_code=404,
                    detail=f"Chroma database '{chroma_db}' does not exist in the directory."
                )
            
            """check if history exists"""
            history_record = crud.get_history_by_session(db, session_id)
            chat_history=[]
            
            """if history exists"""
            if not history_record == None: 
                """If history dir exists then download from minIO server"""
                if not os.path.exists(history_json_file_dir):
                    minio_dependencies.download_file(username, history_json_file, history_json_file_dir)
                if os.path.exists(history_json_file_dir):
                    with open(history_json_file_dir, 'r') as json_file:
                        docs = json.load(json_file)
                        chat_history = docs
 
            """If history not found, insert message into database"""
            if history_record == None:
                request = models.MessageHistory(
                        session_id=session_id,
                        history_name=history_file_name
                )
                history_record = crud.create_history(db, request)
                    

            vector_store = Chroma(
                    collection_name=collection_name,
                    embedding_function=embeddings,
                    persist_directory=persistent_dir
                )
                
            retriever = vector_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={
                    "k":5,
                    "score_threshold":0.2
                }
            )
            
            llm = get_lm_from_cache(user_id)
            print("llm: ", llm)
            if llm is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No llm found. Please use /api/v1/model_provider/llm to get your llm."
                )
            retrieved_docs = RunnableBranch(
                (
                    # Both empty string and empty list evaluate to False
                    lambda x: not x.get("chat_history", False),
                    # If no chat history, then we just pass input to retriever
                    (lambda x: x["input"]) | retriever,
                ),
                # If chat history, then we pass inputs to LLM chain, then to retriever
                contextualize_q_prompt | llm | StrOutputParser() | retriever,
            )
                
            contextual = retrieved_docs.invoke(
                {
                    "input": question,
                    "chat_history":chat_history[-6:]
                }
            )    
                
            """Write file to local"""
            new_history = []
            new_history.append(HumanMessage(content=question))
            
            write_history_as_json(history_json_file_dir, new_history)
            
            return {
                "input": question,
                "context": contextual,
                "chat_history": chat_history[-6:],
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
# def get_llm(user_id):
#     print("user_id", user_id)
#     llm = get_lm_from_cache(int(user_id))
#     if llm is None:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="No LLM found. Please use /api/v1/model_provider/llm to get your LLM."
#         )
#     return llm

chain = RunnableSequence(
    CreateRAGChainRunnable()
    | (lambda x: {
        "input": x['input'],
        "context": x['context'],
        "chat_history": x['chat_history']
    })
    | qa_prompt
)


class Request(BaseModel):
    input: str = Field(
        ...,
        description="The user's question."
    )
    user_id: int = Field(
        ..., ge=1,
        description="User ID for identifying the user."
    )
    session_id: int = Field(
        ..., ge=1,
        description="Session ID for identifying the session."
    )
    file_id: Optional[int] = Field(
        description="If you want to chat with all documents you can set it to null.",
    )
    
chain = chain.with_types(input_type=Request)
