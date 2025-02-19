import streamlit as st
import random
import time
from streamlit_pdf_viewer import pdf_viewer


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Let's start chatting! 👇"}]

showPdf = False
for message in st.session_state.messages:
    if message["role"] == "user" and message["content"] == "pdf":
        showPdf = True
    if message["role"] == "user" and message["content"] == "exitpdf":
        showPdf = False

messageContainer = None
inputContainer = None
if showPdf:
    col1, col2 = st.columns([2, 1])
    messageContainer = col1.container(height=250)
    inputContainer = col1.container()
    with col2.container(height=300):
        pdf_viewer("frontend/NeurIPS-2023-openagi-when-llm-meets-domain-experts-Paper-Datasets_and_Benchmarks.pdf",scroll_to_page=2)
else:
    messageContainer = st.container()
    inputContainer = st.container()

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with messageContainer.chat_message(message["role"]):
        st.markdown(message["content"])
        st.link_button(message["content"],"www.google.com")
# Accept user input
if prompt := inputContainer.chat_input("What is up?", disabled=False):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with messageContainer.chat_message("user"):
        st.markdown(prompt)
    # Display assistant response in chat message container
    with messageContainer.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        assistant_response = random.choice(
            [
                "Hello there! How can I assist you today?",
                "Hi, human! Is there anything I can help you with?",
                "Do you need help?",
            ]
        )
        st.session_state.messages.append({"role": "assistant", "content": ""})
        # Simulate stream of response with milliseconds delay
        for chunk in assistant_response.split():
            full_response += chunk + " "
            time.sleep(0.1)
            # Add a blinking cursor to simulate typing
            message_placeholder.markdown(full_response + "▌")
            st.session_state.messages[len(st.session_state.messages) - 1] = {"role": "assistant", "content": full_response}
        message_placeholder.markdown(full_response)
    st.rerun()