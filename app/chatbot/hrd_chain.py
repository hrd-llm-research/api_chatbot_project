import os

import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_chroma import Chroma
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_core.messages import HumanMessage        
from langchain.pydantic_v1 import BaseModel, Field
from fastapi import HTTPException, status  
from langchain_ollama import OllamaLLM
from langchain_community.llms import Ollama

load_dotenv()

# Create embeddings without GPU
embeddings = FastEmbedEmbeddings()

# llm = ChatGroq(
#     model="Llama3-8b-8192",
#     temperature=1,
#     api_key="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"
# )

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
            You are a Korea Software HRD Center AI designed to help users answer the question about our website. 
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

persistent_dir = os.path.join(current_dir, "..", "chroma", "chroma_db", "HRDBot_chroma_db")

### Statefully manage chat history ###
store = {}
        
class HRDBotRAGChain(Runnable):
    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """
        Retrieves the chat history for a given session ID.
        """
        if session_id not in store:
            store[session_id] = ChatMessageHistory()
        return store[session_id]
    
    def invoke(self, inputs: dict, *args, **kwargs) -> str:
        """
        Processes the input through the RAG chain and returns the response.
        """
        session_id = inputs.get("session_id")
        user_input = inputs.get("input")
        
        # Initialize vector store and retriever
        vector_store = Chroma(
            collection_name="HRDBot_collection",
            embedding_function=embeddings,
            persist_directory=persistent_dir
        )

        retriever = vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": 5, "score_threshold": 0.2},
        )

        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, contextualize_q_prompt
        )
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        # Create a conversational RAG chain with message history management
        conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

        # return conversational_rag_chain
        # Invoke the chain with input and session_id
        result = conversational_rag_chain.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": session_id}},
        )
        return result['answer']
    
# chain = (HRDBotRAGChain)

def get_hrd_history(id: str, limit:int,page:int):
    
    if id not in store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No chat history found for session ID {id}"
        )

    # Extract the messages from the chat history for the given session ID
    messages = store[id].messages
    formatted_history = []

    # Iterate through each message and format it
    for message in messages:
        role = "user" if isinstance(message, HumanMessage) else "ai"
        formatted_message = {
            "role": role,
            "content": message.content
        }
        formatted_history.append(formatted_message)

    # Print or return the formatted history
    return formatted_history[-(limit*page):]

class InputModel(BaseModel):
    input: str
    session_id: str = Field(...)
    
chain = RunnableLambda(lambda x: HRDBotRAGChain())
chain = chain.with_types(input_type=InputModel)


