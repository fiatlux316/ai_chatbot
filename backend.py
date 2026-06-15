from typing import List
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
from typing import Dict, List, Optional, Tuple
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

from vs_manager import VectorStoreManager
vs_manager = VectorStoreManager(provider=os.getenv("VS_TYPE", "chroma"))

from llm import get_llm
llm = get_llm()

class Turn(BaseModel):
    role: str
    content: str

class Messages(BaseModel):
    messages: List[Turn]  

app = FastAPI()

# 기본 프롬프트 구성
base_prompt = "당신은 이마트 고객만족센터 7년 차 선임 매니저(32세)입니다. \n현장 경험이 풍부하여 상품권, 결제, 환불 규정에 능통하며, 고객의 문제를 스마트하고 노련하게 해결합니다."
cs_guide = ''

# Guide prompt content is loaded once at startup and reused for every request.
try:
    with open('./docs/guide.md', 'r', encoding='utf-8') as f:
        cs_guide = f.read()
        print('guide.md loaded successfully.')
except FileNotFoundError:
    cs_guide = ''
    print('Warning: docs/guide.md not found, continuing without guide prompt.')

system_prompt = base_prompt + '\n\n' + cs_guide
#print("system_prompt :", system_prompt)

# 1. 프롬프트 템플릿 생성
prompt = PromptTemplate.from_template(
    """
    Answer the Question based on the CS_Guide, retrieved RAG_Context, and Chat_history.

    CS_Guide : {system_prompt}
    Chat_history: {chat_history}
    RAG_Context : {retrieved_context}
    Question: {question}
    """
)

# 부분 질문을 합치기 위해 저장
query_history = []

# 과거 대화 기록을 저장하기 위한 리스트
chat_history = []

@app.post("/chat", response_model=Turn)
def chat(messages: Messages) :
    
    print("chat :", messages)

    messages_list = messages.dict()['messages']
    #print("====> messages_list :", messages_list)

    brand_id = 'EM'
    index = brand_id + '_chunk'
    response = None

    query = messages_list[-1]['content'] # 대화 이력 중 가장 마지막 메시지(최신 질문)를 가져옵니다.
    print("query :", query)

    # 고객요청 메세지를 최근 순으로 최대 지정된 갯수만큼 저장하여,  멀티턴 대화에 대응할 수 있도록 합니다.
    # 메제기가 넘어올때마다 저장하여 최근 대화 이력을 유지하는 방식으로, 고객의 추가 질문이나 보완 질문이 있을 때 이전 맥락을 고려하여 연속성 있는 답변을 제공할 수 있습니다.
    query_history.append(query)

    # 최근 3개 질문을 하나의 스트링으로 저장 
    query = ' '.join(query_history[-3:])
    print("query_final :", query)

    try:    
        # provider 파라미터를 "opensearch" 또는 "chroma"로 변경하여 검색 DB를 전환할 수 있습니다.
        chunks = vs_manager.search_chunks(
            query=query.lower(), 
            index_name=index, 
            top_k=3
        )
        
        #print("chunks :", chunks)
        if not chunks:
            response = "죄송합니다. 일치하는 FAQ 항목이 없습니다"
            print("response :", response)
            
        else :
            context_text = ''
            for chunk in chunks:
                context_text += f'##참조문서_Chunk:\n{chunk}\n\n'

            #print("context_text :", context_text)   

            if context_text == '' :
                response = '죄송합니다. 질문에 대해서 적정한 답변이 준비되지 않았습니다. 문의 유형에 따라 아래 메뉴를 이용해 보세요 \n\n - 상품문의 : 상품검색 \n\n - AS관련 문의 : AS 문의 \n\n - 기타 : 매장전화문의'
                print("response :", response)
            else :
                rendered = prompt.format(
                    system_prompt=system_prompt,
                    retrieved_context="[검색된 FAQ Context]\n\n" + context_text,
                    question=query,
                    chat_history=chat_history
                )                
                # invoke 방식 (한 번에 전체 응답)
                resp = llm.invoke(rendered)
                text = resp.content if hasattr(resp, "content") else str(resp)
                response = text.strip()
                print("response :", response)

                # 대화 기록에 현재 대화 추가
                chat_history.append(HumanMessage(content=query))
                chat_history.append(AIMessage(content=response))
                #print("Updated chat_history:", chat_history)

    except Exception as e:
        err = str(e) #.split(" ")[0]
        print(f"Error occurred: {err}")
        response = "예기치 않은 에러가 발생했습니다.  잠시 후  다시 시도해 주세요." + '\n' + f'(에러: {err})'
        pass

    return {"role": "assistant", "content": response}


@app.post("/chat_stream", response_model=Turn)
def chat_stream(messages: Messages) :

    print("chat_stream :", messages)
    def generate():

        messages_list = messages.dict()['messages']
        print("messages_list :", messages_list)

        brand_id = 'EM'
        index = brand_id + '_chunk'
        response = None

        query = messages_list[-1]['content'] # 대화 이력 중 가장 마지막 메시지(최신 질문)를 가져옵니다.
        print("query :", query)

        # 고객요청 메세지를 최근 순으로 최대 지정된 갯수만큼 저장하여,  멀티턴 대화에 대응할 수 있도록 합니다.
        # 메제기가 넘어올때마다 저장하여 최근 대화 이력을 유지하는 방식으로, 고객의 추가 질문이나 보완 질문이 있을 때 이전 맥락을 고려하여 연속성 있는 답변을 제공할 수 있습니다.
        query_history.append(query)

        # 최근 3개 질문을 하나의 스트링으로 저장 
        query = ' '.join(query_history[-3:])
        print("query_final :", query)

        try:    
            # provider 파라미터를 "opensearch" 또는 "chroma"로 변경하여 검색 DB를 전환할 수 있습니다.
            chunks = vs_manager.search_chunks(
                query=query.lower(), 
                index_name=index, 
                top_k=3
            )
            
            #print("chunks :", chunks)
            if not chunks:
                response = "죄송합니다. 일치하는 FAQ 항목이 없습니다"
                print("response :", response)
                
            else :
                context_text = ''
                for chunk in chunks:
                    context_text += f'##참조문서_Chunk:\n{chunk}\n\n'

                #print("context_text :", context_text)   

                if context_text == '' :
                    response = '죄송합니다. 질문에 대해서 적정한 답변이 준비되지 않았습니다. 문의 유형에 따라 아래 메뉴를 이용해 보세요 \n\n - 상품문의 : 상품검색 \n\n - AS관련 문의 : AS 문의 \n\n - 기타 : 매장전화문의'
                    yield response
                    print("response :", response)
                else :
                    rendered = prompt.format(
                        system_prompt=system_prompt,
                        retrieved_context="[검색된 FAQ Context]\n\n" + context_text,
                        question=query,
                        chat_history=chat_history
                    )     

                    # stream 방식 (토큰 단위로 스트리밍)
                    full_response = ""
                    for chunk in llm.stream(rendered):
                        full_response += chunk.content
                        yield chunk.content

                    response = full_response.strip()
                    print("response :", response)

                    # 대화 기록에 현재 대화 추가
                    chat_history.append(HumanMessage(content=query))
                    chat_history.append(AIMessage(content=response))

                    #print("Updated chat_history:", chat_history)

        except Exception as e:
            err = str(e) #.split(" ")[0]
            print(f"Error occurred: {err}")
            response = "예기치 않은 에러가 발생했습니다.  잠시 후  다시 시도해 주세요." + '\n' + f'(에러: {err})'
            pass

    return StreamingResponse(generate(), media_type="text/event-stream")
    #return {"role": "assistant", "content": response}

# @app.post("/chat", response_model=Turn)
# def post_chat(messages: Messages):
#     messages = messages.dict()
#     assistant_turn = chat(messages=messages['messages'])
#     return assistant_turn