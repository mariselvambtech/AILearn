from fastapi import FastAPI
from langchain_groq import ChatGroq # Import the ChatGroq class for Groq model interaction
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langserve import add_routes # Import add_routes for integrating LangServe with FastAPI
import os
from dotenv import load_dotenv  # Load environment variables from a .env file




load_dotenv()  # Load the environment variables
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY","")  # Retrieve the OpenAI API key from the environment variables
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY","")  # Retrieve the LangChain API key from the environment variables
os.environ["LANGCHAIN_TRACING_V2"] = "true"  # Enable LangChain tracing for debugging and monitoring
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT","")  # Set the LangChain project name for organization
os.environ["GROQ_API_KEY"]= os.getenv("GROQ_API_KEY","")  # Retrieve the GROQ API key from the environment variables

llm = ChatGroq(model="openai/gpt-oss-20b")  # Initialize the ChatGroq model with the specified model name

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{question}")
])  
chain = prompt | llm | StrOutputParser()  # Create a processing chain with the prompt, model, and string output parser
app = FastAPI(title="Fast api",version="1.0",description="A simple GROQ api")  # Create a FastAPI application instance
add_routes(app, chain,path="/chain")  # Add LangServe routes to the FastAPI application for handling model requests

@app.get("/")
async def root():
    return {"message": "Hello, World!"}


# This code sets up a FastAPI application that integrates with the LangServe framework to serve a Groq model.
# The application uses a chat model from Groq, processes input through a prompt template, and outputs the result using a string parser.
# The FastAPI application is configured to handle requests at the "/chain" endpoint, allowing users to interact with the Groq model through a structured chat interface.
if __name__ == "__main__":
    import uvicorn  # Import Uvicorn for running the FastAPI application
    uvicorn.run(app, host="localhost", port=8000)  # Run the FastAPI application on localhost at port 8000
