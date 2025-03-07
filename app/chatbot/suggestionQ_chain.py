import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chains.retrieval import create_retrieval_chain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_chroma import Chroma
from langchain_core.runnables import Runnable, RunnableSequence
from langchain.pydantic_v1 import BaseModel, Field
from langchain.chains import LLMChain
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException, status 
from langchain.schema.output_parser import StrOutputParser

from app.db_connection.database import SessionLocal
from app.auth.dependencies import find_user
from app.chroma.dependencies import get_chroma_name, get_collection_name, is_file_available
from app.db_connection.schemas import ChatModel, UserResponse
from app.session import dependencies as session_dependencies
from langchain_ollama import OllamaLLM

load_dotenv()

embeddings = FastEmbedEmbeddings()

current_dir = os.path.dirname(os.path.abspath(__file__))
history_dir = os.path.join(current_dir, "history")

# lm = ChatGroq(
#     model="Llama3-8b-8192",
#     temperature=1,
#     api_key="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"
# )
from langchain_community.llms import Ollama
lm = Ollama(
    base_url="http://ollama:11434",
    model="llama3.1",
    temperature=0.7,
    # timeout=30,  # Increase the timeout to 30 seconds
)

# lm = ChatGroq(
#     model="Llama3-8b-8192",
#     temperature=1,
#     api_key="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"
# )

def retrieve_document_from_chroma(
    chat_request: ChatModel, top_k: int=5, score_threshold: float=0.5  
):

    collection_name = chat_request.collection_name
    chroma_db = chat_request.chroma_db
    persistent_dir = os.path.join(current_dir, "..", "chroma", "chroma_db", chroma_db)
    
    if not os.path.exists(persistent_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Chroma database '{chroma_db}' does not exist in the directory."
        )
        
    vector_store = Chroma(
        embedding_function=embeddings,
        persist_directory=persistent_dir,
        collection_name=collection_name
    )
    
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": top_k, "score_threshold": score_threshold},
    )
    return retriever


_system_prompt = (
        """
            You have access to a set of uploaded documents. Based on the content of these documents, 
            generate four questions that would be relevant or thought-provoking for the user to consider. 
            The questions should be designed to help the user engage more deeply with the material, 
            clarify concepts, or explore important themes discussed in the documents. 
            Please ensure the questions are clear, specific, and varied in their focus to cover different aspects of the content.
            
            {context}
        """
    )

_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _system_prompt)
        ]
    )

prompt_template = PromptTemplate(
        input_variables=["context"],
        template=(
            "Based on the following document content, suggest four questions that is the main understanding of the document that would cover all the document.\n\n"
            "{context}\n\n"
            "Please suggest 4 questions:"
        ),
    )

class RetrieverRunnable(Runnable):
    
    def invoke(self, inputs: dict,*args, **kwargs):
        try:
            db = SessionLocal()
            
            """declare variables getting inputs"""
            user_id = inputs.get("user_id") 
            session_id = inputs.get("session_id")
            file_id = inputs.get("file_id")
            
            print("Received user_id===:", user_id)
            print("Received session_id===:", session_id)
            print("Received file_id===:",file_id) 
        
            """declare variables"""
            file_record = is_file_available(db, file_id)

            chroma_db = get_chroma_name(user_id, session_id)
            collection_name = file_record.collection_name   
            
            persistent_dir = os.path.join(current_dir, "..", "chroma", "chroma_db", chroma_db)
            
            if not os.path.exists(persistent_dir):
                raise HTTPException(
                    status_code=404,
                    detail=f"Chroma database '{chroma_db}' does not exist in the directory."
                )
            
            vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=embeddings,
                persist_directory=persistent_dir
            )
            
            # Step 5: Use the retriever to get relevant documents from the Chroma collection
            retriever = vector_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={"k": 20, "score_threshold": 0.2},
            )
            query = "What are the main topics discussed in the document?"
            retrieved_docs = retriever.invoke(query)

            # Combine the retrieved documents into a single context for the prompt
            context = "\n".join([doc.page_content for doc in retrieved_docs])
            
            return {
                "context": context
            }
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        
    
class Request(BaseModel):
    user_id: int = Field(...)
    session_id: int = Field(...)
    file_id: Optional[int] = None  
    
chain = RunnableSequence(
    RetrieverRunnable()
    | prompt_template 
    | lm
    | StrOutputParser()
)

chain = chain.with_types(input_type=Request)