from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
import json

from llm_manager import LLMManager
from vs_manager import VectorStoreManager

llm_provider = "gemini" # "sonnet" 또는 "chatgpt", "gemini"로 LLM 제공자를 선택할 수 있습니다.
vs_provider = "chroma" # "opensearch" 또는 "chroma"로 벡터 저장소 제공자를 선택할 수 있습니다.

llm_manager = LLMManager(provider=llm_provider)
vs_manager = VectorStoreManager(provider=vs_provider)

query_history = []

def chat(messages):

    brand_id = 'EM'
    index = brand_id + '_chunk'
    response = None
    #print("messages :", messages)

    #query = messages[0]['content']
    query = messages[-1]['content'] # 대화 이력 중 가장 마지막 메시지(최신 질문)를 가져옵니다.
    print("query :", query)

    # 고객요청 메세지를 최근 순으로 최대 지정된 갯수만큼 저장하여,  멀티턴 대화에 대응할 수 있도록 합니다.
    # 메제기가 넘어올때마다 저장하여 최근 대화 이력을 유지하는 방식으로, 고객의 추가 질문이나 보완 질문이 있을 때 이전 맥락을 고려하여 연속성 있는 답변을 제공할 수 있습니다.
    query_history.append(query)
    print("query_history :", query_history)

    # 최근 5개 질문을 하나의 스트링으로 저장 
    query = ' '.join(query_history[-5:])
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

            if context_text == '' :
                response = '죄송합니다. 질문에 대해서 적정한 답변이 준비되지 않았습니다. 문의 유형에 따라 아래 메뉴를 이용해 보세요 \n\n - 상품문의 : 상품검색 \n\n - AS관련 문의 : AS 문의 \n\n - 기타 : 매장전화문의'
                print("response :", response)
            else :
                # Claude (Sonnet) 프롬프트 구성
                system_prompt = (
                    "당신은 이마트 고객만족센터 7년 차 선임 매니저(32세)입니다. 현장 경험이 풍부하여 상품권, 결제, 환불 규정에 능통하며, 고객의 문제를 스마트하고 노련하게 해결합니다.\n"
                    "최종 답변을 제공하기 위해서 반드시 [Role & Persona],[Task Instructions],[Multi-turn Conversation Management],[CS Rules],[Fact Check Rules],[Final Response Rules] 을 준수해 주세요.\n"
                    "지식DB에서 제공된 [검색된 FAQ Context]만을 기반으로 [사용자 질문]에 답변해 주세요.\n"
                    "Context에 없는 내용은 절대 지어내지 말고, 내용이 부족하면 있는 그대로 안내해 주세요."
                )

                # ./docs/guide.md 파일의 내용을 프롬프트에 추가하여, 모델이 답변을 생성할 때 참고할 수 있도록 합니다.
                with open('./docs/guide.md', 'r', encoding='utf-8') as f:
                    guide = f.read()
                #print("guide :", guide)

                system_prompt = system_prompt + '\n\n' +guide
                #print("system_prompt :", system_prompt)

                user_prompt = f"[검색된 FAQ Context]\n{context_text}\n[사용자 질문]: {query}"
                
                # 모델을 변경하고 싶다면 model_provider 파라미터를 "chatgpt" 또는 "sonnet"으로 변경하세요.
                response = llm_manager.generate_response(
                    system_prompt, 
                    user_prompt 
                )
                print("response :", response)

    except Exception as e:
        err = str(e).split(" ")[0]
        response = "예기치 않은 에러가 발생했습니다.  잠시 후  다시 시도해 주세요." + '\n' + f'(에러: {err})'
        pass

    return {"role": "assistant", "content": response}


app = FastAPI()

class Turn(BaseModel):
    role: str
    content: str

class Messages(BaseModel):
    messages: List[Turn]  


@app.post("/chat", response_model=Turn)
def post_chat(messages: Messages):
    messages = messages.dict()
    assistant_turn = chat(messages=messages['messages'])
    return assistant_turn