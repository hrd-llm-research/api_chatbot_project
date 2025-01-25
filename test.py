# from langchain_community.llms import Ollama

# # Configure Ollama with the base URL of your server
# llm = Ollama(
#     base_url="http://localhost:9001",  # Replace with your server's URL
#     model="llama3.1"  # Replace with your desired model name
# )

# # Test the LLM with a simple prompt
# response = llm.invoke("hi")
# print(response)


from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from langserve import add_routes


app = FastAPI(
    title="Chatbot API",
    description="A simple chatbot API with Langchain and FastAPI",
    version="1.0.0",
)

from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
prompt = ChatPromptTemplate.from_template("tell me a joke about {topic}")
llm = Ollama(
    base_url="http://localhost:9001",
    model="llama3.1",
    temperature=0.7,
    # timeout=30,  # Increase the timeout to 30 seconds
)
add_routes(
    app,
    prompt | llm,
    path="/chat_with_llm"
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8088)