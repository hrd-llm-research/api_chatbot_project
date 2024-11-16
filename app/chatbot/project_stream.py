import os

import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_core.runnables import Runnable , RunnableSequence, RunnableBranch, RunnableParallel, RunnableLambda, RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain_chroma import Chroma
from fastapi import HTTPException
from app.db_connection.database import SessionLocal
from langchain.pydantic_v1 import BaseModel, Field
from app.auth.dependencies import find_user
from app.chroma.dependencies import get_chroma_name, is_file_available
from app.chatbot import crud
from app.db_connection.schemas import MessageHistoryCreate
from app.session import dependencies as session_dependencies
from app.minIO import dependencies as minio_dependencies
from .dependencies import write_history_as_json, write_history_as_text
from app.api_generation.project_dependencies import is_external_session_available, get_project_detail, create_external_history, is_external_history_exist
from app.api_generation.project_crud import get_project_by_project_id
from app.chroma.dependencies import get_external_chroma_name
from fastapi import status, HTTPException
from langchain_ollama import OllamaLLM

load_dotenv()

# Create embeddings without GPU
embeddings = FastEmbedEmbeddings()

llm = OllamaLLM(
    model="llama3.1",
    temperature=0.7,
)

# llm = ChatGroq(
#     model="Llama3-8b-8192",
#     temperature=1,
#     api_key="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"
# )


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
        db = SessionLocal()

        """declare variables from inputs"""
        question = inputs['input']['input']
        session_id = inputs['input']['external_session_id']
        project_id = inputs['input']['project_id']
        
        """Check if project & session available"""
        session_data = is_external_session_available(db, session_id)
        project_data = get_project_by_project_id(db, project_id)
        
        if project_data is None:
            raise HTTPException(
                status_code=404,
                detail=f"Project '{project_id}' is not found."
            )
        chroma_db = get_external_chroma_name(project_id)
        external_history = is_external_history_exist(db, session_id)
    
        
        """declare file variables"""
        history_filename = str(session_id)+'@'+project_data.project_name+'_history'
        history_json_file = history_filename+'.json'
        
        history_json_file_dir = os.path.join(history_dir, "json", history_json_file)
        persistent_dir = os.path.join(current_dir, "..", "chroma", "chroma_db", chroma_db)
                
        if not os.path.exists(persistent_dir):
            raise HTTPException(
                status_code=404,
                detail=f"Chroma database '{chroma_db}' does not exist in the directory."
            )
        
        """check if history exists"""
        chat_history=[]
        
        """If history not found, insert message into database"""
        if external_history is None: 
            history_record = create_external_history(db, history_filename, session_id)
        else:
            if not os.path.exists(history_json_file_dir):
                minio_dependencies.download_file(project_data.project_name, history_json_file, history_json_file_dir)
                
            if os.path.exists(history_json_file_dir):
                with open(history_json_file_dir, 'r') as json_file:
                    docs = json.load(json_file)
                    chat_history = docs
        
        vector_store = Chroma(
            collection_name="my_collection",
            embedding_function=embeddings,
            persist_directory=persistent_dir
        )
        
        retriever = vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": 5, "score_threshold": 0.2},
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
        
        # write_history_as_text(history_text_file_dir, new_history)
        write_history_as_json(history_json_file_dir, new_history)
        
        return {
            "input":question,
            "context": contextual,
            "chat_history": chat_history
        }

chain = RunnableSequence(
    CreateRAGChainRunnable()
    | (lambda x: {
        "input":x['input'],
        "context":x['context'],
        "chat_history":x['chat_history'], 
    })
    | qa_prompt | llm | StrOutputParser()
)

class Request(BaseModel):
    input: str = Field(
        ..., description="The question to be answered."
    )
    external_session_id: int = Field(
        ..., ge=1,
        description="External session ID for which the request is being made."
    )
    project_id: int = Field(
        ..., ge=1,
        description="The ID of the project to which the session belongs."
    )
    
chain = chain.with_types(input_type=Request)
