# LangGraph Chatbot - Frontend & Backend Documentation

This project implements a conversational AI chatbot using LangGraph with a Streamlit frontend and SQLite persistence. The system consists of two main Python files that work together to provide a chat interface with persistent conversation history.

## File Structure

- `frontend.py` - Streamlit web interface and session management
- `backend.py` - LangGraph chatbot logic and database operations
- `chatbot.db` - SQLite database for conversation persistence

## Backend (`backend.py`)

### Overview
The backend handles the core chatbot functionality using LangGraph, Google's Gemini AI model, and SQLite for conversation persistence.

### Key Components

#### AI Model Setup
```python
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
```
- Uses Google's Gemini 2.5 Flash model for natural language processing
- Requires `GOOGLE_API_KEY` environment variable

#### State Management
```python
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    title: str
```
- Defines the conversation state structure
- `messages`: List of conversation messages
- `title`: Thread title (currently unused in chat logic)

#### Chat Node
```python
def chat_node(state: State) -> State:
```
- Core conversation processing function
- Takes conversation history and generates AI responses
- Uses a simple prompt template for context-aware responses

#### Title Generation
```python
def generate_title(user_message):
```
- Generates meaningful conversation titles using AI
- Creates 3-5 word titles based on user input
- Used for sidebar conversation labeling

#### Database Operations
```python
# Thread metadata table
CREATE TABLE thread_metadata (
    thread_id TEXT PRIMARY KEY,
    thread_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Key Functions:**
- `init_thread_metadata_table()` - Creates the metadata table
- `store_thread_name(thread_id, thread_name)` - Saves thread names
- `get_thread_name(thread_id)` - Retrieves thread names
- `get_all_thread_names()` - Gets all thread names with timestamps

#### LangGraph Setup
```python
graph = StateGraph(State)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)
chatbot = graph.compile(checkpointer=checkpointer)
```
- Simple linear graph: START → chat_node → END
- Uses SQLite checkpointing for conversation persistence

#### Thread Retrieval
```python
def retrieve_all_threads():
```
- Extracts all conversation thread IDs from the database
- Used for populating the sidebar conversation list

## Frontend (`frontend.py`)

### Overview
The frontend provides a Streamlit-based web interface for user interaction, session management, and conversation display.

### Key Components

#### Session State Management
```python
# Core session variables
st.session_state['thread_id']      # Current conversation ID
st.session_state['chat_threads']   # List of all conversation IDs
st.session_state['thread_names']   # Thread ID to name mapping
st.session_state['message_history'] # Current conversation messages
```

#### Utility Functions

**Thread Generation:**
```python
def generate_thread_id():
    return uuid.uuid4()
```
- Creates unique identifiers for each conversation

**Title Generation:**
```python
def generate_thread_name(user_message):
```
- Wraps backend AI title generation
- Includes fallback logic for error handling
- Truncates long titles for UI display

**Thread Management:**
```python
def add_thread(thread_id, thread_name=None):
def reset_chat():
def load_conversation(thread_id):
```
- `add_thread`: Adds new conversations to both session state and database
- `reset_chat`: Creates new conversation and resets message history
- `load_conversation`: Retrieves conversation history from database

**Name Updates:**
```python
def update_thread_name(thread_id, user_message):
```
- Updates conversation titles when first message is sent
- Only updates "New Chat" titles to avoid overwriting custom names
- Persists changes to both session state and database

#### User Interface

**Sidebar:**
- New Chat button for starting conversations
- Scrollable list of existing conversations
- Each conversation shows its AI-generated title
- Clicking a conversation loads its history

**Main Chat Area:**
- Displays conversation history with role-based styling
- User messages in user bubbles
- AI responses in assistant bubbles
- Chat input at bottom for new messages

#### Message Processing Flow
1. User types message in chat input
2. Message added to session state and displayed
3. Thread name updated if this is the first message
4. Message sent to LangGraph backend via `chatbot.stream()`
5. AI response streamed back to user
6. Response added to conversation history

## Data Flow

```
User Input → Frontend → Backend AI → Response → Frontend Display
     ↓
Thread Name Update → Database Storage → Sidebar Update
```

## Database Schema

### Conversations (LangGraph Checkpoints)
- Stored in SQLite via LangGraph's SqliteSaver
- Contains full message history for each thread
- Managed automatically by LangGraph

### Thread Metadata
```sql
CREATE TABLE thread_metadata (
    thread_id TEXT PRIMARY KEY,    -- UUID of conversation
    thread_name TEXT NOT NULL,     -- AI-generated title
    created_at TIMESTAMP           -- Creation timestamp
);
```

## Environment Requirements

```bash
# Required environment variables
GOOGLE_API_KEY=your_google_api_key_here

# Required packages (see requirements.txt)
streamlit
langchain-google-genai
langgraph
python-dotenv
```

## Usage

1. Set your Google API key in `.env` file
2. Run `python frontend.py`
3. Open browser to the displayed Streamlit URL
4. Start chatting - titles will be generated automatically
5. Conversations persist across browser refreshes

## Key Features

- **Persistent Storage**: All conversations saved to SQLite database
- **AI-Generated Titles**: Automatic conversation naming based on content
- **Session Management**: Maintains conversation state across interactions
- **Real-time Streaming**: AI responses stream back to user
- **Responsive UI**: Clean Streamlit interface with sidebar navigation

## Error Handling

- Fallback to simple message truncation if AI title generation fails
- Graceful handling of missing thread names
- Database connection error handling
- Session state validation and initialization 