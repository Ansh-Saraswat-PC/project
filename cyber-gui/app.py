import os
import uuid
import json
import streamlit as st
import requests

# Fetch the backend URL from environment variables during deployment
AGENT_API_URL = os.getenv("AGENT_API_URL", "https://cyber-security-agent-972312916640.europe-west3.run.app/run_sse")

# Extract the base URL to call the session creation API
BASE_URL = AGENT_API_URL.replace("/run_sse", "")

st.set_page_config(page_title="CyberSecurity Triage Agent", page_icon="🛡️")
st.title("🛡️ CyberSecurity Triage Agent")
st.caption("Describe an IT situation, code snippet, or network condition to check for vulnerabilities.")

# Initialize chat history and a stable session ID
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    
    # CRITICAL FIX: Explicitly create the session on the ADK backend to prevent 404s
    session_create_url = f"{BASE_URL}/apps/agent/users/ansh-saraswat/sessions/{st.session_state.session_id}"
    try:
        requests.post(session_create_url, json={})
    except Exception as e:
        st.error(f"Warning: Could not register session with backend: {e}")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("e.g., Is it safe to store passwords in a plain text DB column?"):
    
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Prepare payload. appName must be "agent" because your backend file is agent.py
    payload = {
        "appName": "agent",
        "userId": "ansh-saraswat",
        "sessionId": st.session_state.session_id,
        "newMessage": {
            "role": "user",
            "parts": [{"text": prompt}]
        },
        "streaming": False
    }

    with st.chat_message("assistant"):
        with st.spinner("Analyzing threat vectors..."):
            try:
                response = requests.post(AGENT_API_URL, json=payload)
                
                if response.status_code != 200:
                    st.error(f"Backend Error {response.status_code}: {response.text}")
                
                response.raise_for_status()
                
                # The endpoint is /run_sse, so it returns Server-Sent Events (text), not pure JSON
                raw_text = response.text
                agent_reply = ""
                
                try:
                    # Attempt standard JSON first just in case
                    data = response.json()
                    agent_reply = data.get("newMessage", {}).get("parts", [{}])[0].get("text", "")
                except Exception:
                    # If JSON fails, it is an SSE stream! Let's parse the text.
                    for line in raw_text.splitlines():
                        if line.startswith("data:"):
                            json_str = line.replace("data:", "").strip()
                            if json_str == "[DONE]":
                                continue
                            try:
                                chunk = json.loads(json_str)
                                # ADK chunks can hold the text in either 'newMessage' or 'content'
                                part = chunk.get("newMessage", chunk.get("content", {}))
                                text_chunk = part.get("parts", [{}])[0].get("text", "")
                                agent_reply += text_chunk
                            except json.JSONDecodeError:
                                pass
                
                # Fallback if the response was completely empty
                if not agent_reply.strip():
                    agent_reply = f"⚠️ Agent executed, but response was empty. Raw output: {raw_text[:100]}"
                
                st.markdown(agent_reply)
                st.session_state.messages.append({"role": "assistant", "content": agent_reply})
                
            except requests.exceptions.RequestException as req_err:
                st.error(f"Connection failed: Ensure your Cloud Run service is active. Error: {req_err}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")