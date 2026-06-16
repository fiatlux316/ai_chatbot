import streamlit as st
from streamlit_chat import message
import requests
from dotenv import load_dotenv
import os
import uuid 

load_dotenv()

response_mode = os.getenv("RESPONSE_MODE")

# 접속자의 고유세션 형성 (uuid)
if 'UUID' not in st.session_state:
    st.session_state['UUID'] = str(uuid.uuid4())
UUID = st.session_state['UUID']
#print("UUID :", UUID)
#print("st.session_state :", st.session_state)

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
    #full_text = text
    print('text :'+text)
    user_turn = {"role": "user", "content": text}
    resp = requests.post(chat_url, 
                         json={"messages": [user_turn], "uuid": UUID}
                         )
    assistant_turn = resp.json()

    st.session_state['pre_messages'].append(text)
    return assistant_turn['content']


row1 = st.container()
col1, col2 = st.columns([6,4])

with row1:
    with col1:
        st.title("AI 상담 서비스")
        st.markdown("**나만의 쇼핑 에이전트 AI 챗봇입니다.** \n\r **서비스/영업 관련 전반적인 문의 및 주문/배송/상품/포인트/프로모션/편의시설 등 무엇이든 물어보세요!**")
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
        response = ""
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""

            user_turn = {"role": "user", "content": prompt}
            res_stream = requests.post(chat_url + "_stream", 
                                    json={"messages": [user_turn], "uuid": UUID}, 
                                    stream=True)
            for chunk in res_stream.iter_content(decode_unicode=True):
                if chunk:
                    response += chunk
                    placeholder.markdown(response + "▌")

            placeholder.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

    elif response_mode == "normal":
        # 결과를 한번에 출력
        response = chat(prompt)
        with st.chat_message("assistant"):
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

    else:
        st.error("지원하지 않는 응답 모드입니다. 환경변수 RESPONSE_MODE를 확인하세요.")
