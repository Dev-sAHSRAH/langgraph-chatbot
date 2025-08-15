from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv
from typing import TypedDict,Annotated
import sqlite3


load_dotenv()

model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
parser = StrOutputParser()

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    title: str


def chat_node(state: State) -> State:
    history = state["messages"]
    prompt = f"""
    You are a helpful assistant that can answer questions and help with tasks.
    You are given a conversation history and a new message.
    You need to respond to the new message based on the conversation history.
    Conversation history:
    {history}
    """
    response = model.invoke(prompt)
    return {"messages": [response]}

def generate_title(user_message):
    
    prompt = PromptTemplate(
        template=" Based on the following user message, generate a suitable title of  maximum 3 to 5 words:\n{user_message}",
        input_variables=['user_message']
    )
    chain  = prompt | model | parser
    response = chain.invoke({'user_message': user_message})
    return response

conn = sqlite3.connect(database='chatbot.db',check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

# Create table for thread metadata if it doesn't exist
def init_thread_metadata_table():
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS thread_metadata (
            thread_id TEXT PRIMARY KEY,
            thread_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

# Initialize the table
init_thread_metadata_table()

def store_thread_name(thread_id, thread_name):
    """Store thread name in the database"""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO thread_metadata (thread_id, thread_name)
        VALUES (?, ?)
    ''', (str(thread_id), thread_name))
    conn.commit()

def get_thread_name(thread_id):
    """Retrieve thread name from the database"""
    cursor = conn.cursor()
    cursor.execute('SELECT thread_name FROM thread_metadata WHERE thread_id = ?', (str(thread_id),))
    result = cursor.fetchone()
    return result[0] if result else "Unnamed Chat"

def get_all_thread_names():
    """Retrieve all thread names from the database"""
    cursor = conn.cursor()
    cursor.execute('SELECT thread_id, thread_name FROM thread_metadata ORDER BY created_at DESC')
    results = cursor.fetchall()
    return {thread_id: thread_name for thread_id, thread_name in results}

graph = StateGraph(State)
graph.add_node("chat_node",chat_node)

graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_all_threads():
    all_threads= set()

    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])

    return list(all_threads)
