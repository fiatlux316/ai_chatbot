import streamlit as st
from streamlit_chat import message
import requests
from dotenv import load_dotenv
import os
load_dotenv()

response_mode = os.getenv("RESPONSE_MODE")

# Initialize chat history
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

if 'pre_messages' not in st.session_state:
    st.session_state['pre_messages'] = ['']

chat_url = "http://localhost:8000/chat"
#chat_url = "http://10.147.134.114:8000/chat"

def chat(text):
    #print(st.session_state['pre_messages'])
    prev_text = st.session_state['pre_messages'][-1]
    print('prev_text :'+prev_text)
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
        st.title("AI 챗봇 서비스")
        st.markdown("**FAQ 문서 기반으로 고객의 질문에 답변하는 AI 챗봇입니다.** \n\r **무엇이든 물어보세요!**")
    with col2:
        st.image('./erody_ai.png', width=200)

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# React to user input
if prompt := st.chat_input("안녕하세요. 무엇을 도와드릴까요?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    if response_mode == "stream":
        # stream 방식 (토큰 단위로 스트리밍)
        full_response = ""
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""

            user_turn = {"role": "user", "content": prompt}
            response = requests.post(chat_url + "_stream", 
                                    json={"messages": [user_turn]}, 
                                    stream=True)
            for chunk in response.iter_content(decode_unicode=True):
                if chunk:
                    full_response += chunk
                    placeholder.markdown(full_response + "▌")

            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

    elif response_mode == "normal":
        # 결과를 한번에 출력
        response = chat(prompt)
        with st.chat_message("assistant"):
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

    else:
        st.error("지원하지 않는 응답 모드입니다. 환경변수 RESPONSE_MODE를 확인하세요.")
