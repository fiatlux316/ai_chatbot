# ai_chatbot

FAQ 문서 및 스타일 가이드 기반으로 질문에 대한 답변을 LLM 을 연동하여 제공하는 챗봇 서비스 (RAG 기반)

## 설정

1. UV (파이썬 프로젝트 관리도구) 설치 및 가상환경 설정
- brew install uv
- uv sync

2. 환경변수 설정 :  .env
- OPENAI_API_KEY=
- GEMINI_API_KEY=
- BEDROCK_MODEL=
- BEDROCK_REGION=
- AWS_ACCESS_KEY_ID=
- AWS_SECRET_ACCESS_KEY=

3. FAQ 임베딩 등록 : insert_chunks.py
- Vector Store 설정 (환경변수) : opensearch or chroma
- FAQ 추가 : docs/faq.txt
- chuck 단위 임베딩 등록 : uv run insert_chunks.py

4. 답변 가이드 설정 : docs/guide.md
- 챗봇 답변 스타일/제약 사항 등을 markdown 형태로 작성


## 실행

1. 환경 변수 확인
- VS_TYPE : chroma or opensearch
- LLM_MODEL : claude or gemini or chatgpt

2. 서비스 기동
- 백엔드 : ./start_api.sh
- 프론트 : ./start_st.sh

## 문의
- 조춘기 jck@shinsegae.com