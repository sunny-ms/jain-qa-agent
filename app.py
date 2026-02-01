import streamlit as st
import requests
import uuid
import os

#API_URL = "http://127.0.0.1:8000"
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Digambar Jain QA", page_icon="📿")

# Sidebar for Setup
with st.sidebar:
    st.title("Settings")
    user_key = st.text_input("Gemini API Key", type="password")
    if not user_key:
        st.warning("Please enter your API key to proceed.")
        st.stop()
    
    headers = {"x-api-key": user_key}
    
    st.divider()
    st.header("Admin: Knowledge Feed")
    uploaded_file = st.file_uploader("Upload .txt file", type=["txt"])
    if st.button("Index Document") and uploaded_file:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/plain")}
        r = requests.post(f"{API_URL}/upload", files=files, headers=headers)
        st.success(r.json().get("message"))

# Chat Logic
if "messages" not in st.session_state: st.session_state.messages = []
if "sid" not in st.session_state: st.session_state.sid = str(uuid.uuid4())

for m in st.session_state.messages:
    st.chat_message(m["role"]).write(m["content"])

if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    r = requests.post(
        f"{API_URL}/chat", 
        params={"query": prompt, "session_id": st.session_state.sid},
        headers=headers
    )
    
    answer = r.json().get("answer", "Error: Check API key or connection.")
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.chat_message("assistant").write(answer)