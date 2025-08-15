import streamlit as st
from backend import chatbot, generate_title, retrieve_all_threads, store_thread_name, get_thread_name, get_all_thread_names
from langchain_core.messages import HumanMessage
import uuid

# ********************utility functions********************
def generate_thread_id():
    return uuid.uuid4()

def generate_thread_name(user_message):
    """Generate a meaningful name for the thread using the backend AI"""
    if not user_message or len(user_message.strip()) == 0:
        return "New Chat"
    
    try:
        # Use the backend to generate a meaningful title
        thread_name = generate_title(user_message)
        
        # Clean and truncate the title if needed
        clean_title = thread_name.strip()
        if len(clean_title) > 40:
            clean_title = clean_title[:40] + "..."
        
        # Return the generated title, or fallback to "New Chat" if empty
        return clean_title if clean_title and clean_title != "New Chat" else "New Chat"
            
    except Exception as e:
        st.error(f"Error generating title: {e}")
        # Fallback to simple truncation if AI generation fails
        clean_message = user_message.strip()
        if len(clean_message) > 30:
            clean_message = clean_message[:30] + "..."
        return clean_message

def add_thread(thread_id, thread_name=None):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)
        if thread_name:
            # Store in both session state and database
            st.session_state['thread_names'][thread_id] = thread_name
            store_thread_name(thread_id, thread_name)

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state["thread_id"] = thread_id
    add_thread(thread_id, "New Chat")
    st.session_state['message_history'] = []

def load_conversation(thread_id):
    return chatbot.get_state(config={"configurable": {"thread_id": thread_id}}).values['messages']

def update_thread_name(thread_id, user_message):
    """Update the thread name based on the first user message using AI"""
    # Check if thread name needs updating (either from session state or database)
    current_name = st.session_state['thread_names'].get(thread_id, get_thread_name(thread_id))
    
    # Only update if it's still "New Chat" and user has actually sent a message
    if current_name == "New Chat" and user_message.strip():
        thread_name = generate_thread_name(user_message)
        # Update both session state and database
        st.session_state['thread_names'][thread_id] = thread_name
        store_thread_name(thread_id, thread_name)

# ********************session setup********************
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()
if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()
if 'thread_names' not in st.session_state:
    # Load thread names from database instead of starting with empty dict
    st.session_state['thread_names'] = get_all_thread_names()
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []
    
add_thread(st.session_state['thread_id'], "New Chat")

# ********************sidebar UI********************

st.sidebar.title("Langraph Chatbot")

if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("My conversations")

for thread_id in st.session_state['chat_threads'][::-1]:
    # Get thread name from session state first, fallback to database
    thread_name = st.session_state['thread_names'].get(thread_id, get_thread_name(thread_id))
    if st.sidebar.button(thread_name, key=f"thread_{thread_id}"):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_msgs = []

        for msg in messages:
            if isinstance(msg,HumanMessage):
                role = 'user'
            else:
                role = 'assistant'
            temp_msgs.append({'role': role, 'content': msg.content})
        
        st.session_state['message_history'] = temp_msgs


# *********************Main UI************************

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])


user_input = st.chat_input("Type here")

if user_input:

    #first add it to message history
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    # Update thread name if this is the first message
    update_thread_name(st.session_state['thread_id'], user_input)

    CONFIG = {"configurable": {"thread_id": st.session_state['thread_id']}}

    with st.chat_message('assistant'):
        ai_message = st.write_stream(
            message_chunk.content for message_chunk,metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            )
        )

    st.session_state['message_history'].append({'role':'assistant','content': ai_message})