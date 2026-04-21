import streamlit as st
from streamlit_chat import message
import requests

# Initialize chat history
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

if 'pre_messages' not in st.session_state:
    st.session_state['pre_messages'] = ['']

chat_url = "http://localhost:8000/chat"


def chat(text):
    #print(st.session_state['pre_messages'])
    prev_text = st.session_state['pre_messages'][-1]
    print('prev_text :'+prev_text)
    #full_text = prev_text + ' ' + text
    full_text = text
    print('full_text :'+full_text)
    user_turn = {"role": "user", "content": full_text}
    resp = requests.post(chat_url, json={"messages": [user_turn]})
    assistant_turn = resp.json()

    st.session_state['pre_messages'].append(text)
    return assistant_turn['content']

row1 = st.container()
col1, col2 = st.columns([6,4])

with row1:
    with col1:
        st.title("이로디 챗봇 서비스")
    with col2:
        st.image('./erody.png', width=100)

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# React to user input
if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    response = chat(prompt)
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})