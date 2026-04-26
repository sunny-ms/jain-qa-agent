import streamlit as st
import requests
import uuid
import os
import re

#API_URL = "http://127.0.0.1:8000"
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Digambar Jain QA", page_icon="📿")

YT_LINK_PATTERN = re.compile(r'https?://(?:www\.)?youtube\.com/watch\?v=([A-Za-z0-9_-]+)&t=(\d+)')

def render_message_with_video(content):
    """Render message text and add expandable YouTube video embeds for any citations."""
    st.markdown(content)
    # Find all unique YouTube links in the response
    matches = YT_LINK_PATTERN.findall(content)
    seen = set()
    for video_id, t in matches:
        key = f"{video_id}_{t}"
        if key in seen:
            continue
        seen.add(key)
        minutes, seconds = divmod(int(t), 60)
        label = f"▶ Watch at {minutes:02d}:{seconds:02d}"
        with st.expander(label):
            st.video(f"https://www.youtube.com/watch?v={video_id}", start_time=int(t))

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
        try:
            if r.status_code == 200:
                st.success(r.json().get("message"))
            else:
                st.error(f"Error: {r.status_code} - {r.text}")
        except requests.exceptions.JSONDecodeError:
            st.error(f"Error: Invalid response from server - {r.text}")

# Chat Logic
if "messages" not in st.session_state: st.session_state.messages = []
if "sid" not in st.session_state: st.session_state.sid = str(uuid.uuid4())

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        if m["role"] == "assistant":
            render_message_with_video(m["content"])
        else:
            st.write(m["content"])

if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    r = requests.post(
        f"{API_URL}/chat", 
        params={"query": prompt, "session_id": st.session_state.sid},
        headers=headers
    )
    
    try:
        if r.status_code == 200:
            answer = r.json().get("answer", "Error: No answer provided.")
        else:
            answer = f"Error: {r.status_code} - {r.text}"
    except requests.exceptions.JSONDecodeError:
        answer = f"Error: Invalid response from server - {r.text}"
    
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        render_message_with_video(answer)