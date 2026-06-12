# ai_chatbot

FAQ 문서 및 스타일 가이드 기반으로 질문에 대한 답변을 LLM 을 연동하여 제공하는 챗봇 서비스 (RAG 기반)

## 설정

1. 파이썬 및 venv 설치 
- brew install python@3.13
- python -m venv venv313
- source venv313/bin/activate

2. package 설치
- pip install -r requirements.txt

3. 시크릿 정보 설정 :  env/secret.env
- OPENAI_API_KEY=
- GEMINI_API_KEY=
- BEDROCK_MODEL=
- BEDROCK_REGION=
- AWS_ACCESS_KEY_ID=
- AWS_SECRET_ACCESS_KEY=

4. FAQ 임베딩 등록 : insert_chunks.py
- Vector Store 설정 : opensearch or chroma
- FAQ 추가 : docs/faq.txt
- chuck 단위 임베딩 등록 : python insert_chunks.py

5. 답변 가이드 설정 : docs/guide.md
- 챗봇 답변 스타일/제약 사항 등을 markdown 형태로 작성

## 실행
1. LLM 및 Vector Store 설정 : backend.py
- llm_provider = "sonnet" # "sonnet", "chatgpt" 또는 "gemini"
- vs_provider = "chroma" # "opensearch" 또는 "chroma"

2. 서비스 기동
- 백엔드 : ./start_api.sh
- 프론트 : ./start_st.sh

## 문의
- 조춘기 jck@shinsegae.com