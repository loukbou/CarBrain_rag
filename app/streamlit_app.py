import streamlit as st
import requests

# Config
API_URL = "http://localhost:8000/ask"  # Docker service name if using compose

st.title("🚗 Car Manual RAG Chatbot")
st.write("Ask questions about car manuals, specs, and parts!")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Ask about cars..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Call FastAPI backend
    try:
        response = requests.post(API_URL, json={"question": prompt})
        answer = response.json().get("answer", "No answer found")
    except Exception as e:
        answer = f"Error: {str(e)}"
    
    # Add bot response
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)