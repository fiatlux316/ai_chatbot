# ai_chatbot

FAQ 문서 및 스타일 가이드 기반으로 질문에 대한 답변을 LLM 을 연동하여 제공하는 챗봇 서비스 (RAG 기반)

## 개발 환경 설정

1. python 3.13 설치
- brew install python@3.13
2. UV (파이썬 프로젝트 관리도구) 설치
- brew install uv
3. 설치할 패키지 등록 및 가상환경 설정
- pyproject.toml
- uv sync

## 환경변수 설정 :  .env

1. 공통
- LLM_MODEL="claude" #claude, chatgpt, gemini
- VS_TYPE="chroma" #opensearch, chroma
- RESPONSE_MODE="stream" #normal, stream
2. Gemini 관련 설정
- GEMINI_MODEL="gemini-2.5-flash" #gemini-2.5-flash, gemini-2.5-pro
- GEMINI_API_KEY="xxxx"
3. Chatgpt 관련 설정
- CHATGPT_MODEL="gpt-3.5-turbo" #gpt-3.5-turbo, gpt-4o 등으로 변경 가능
- OPENAI_API_KEY="xxxx" 
4. Claude(AWS) 관련 설정
- BEDROCK_MODEL="apac.anthropic.claude-sonnet-4-20250514-v1:0"
- BEDROCK_REGION="ap-northeast-2"
- AWS_ACCESS_KEY_ID="xxxx"
- AWS_SECRET_ACCESS_KEY="xxxx"
- BEDROCK_TOP_K=1   # 1~5 사이 권장 (작을수록  엄격한 결정성,  항상 최빈 토큰 선택)
5. OpenSearch 관련 설정
- OPENSEARCH_HOST_DEV="vpc-dev-apne2-erody-search-vmaetfnjqtuhscfl3spvc6zhmm.ap-northeast-2.es.amazonaws.com"
- OPENSEARCH_HOST_STG="vpc-dev-apne2-erody-search-vmaetfnjqtuhscfl3spvc6zhmm.ap-northeast-2.es.amazonaws.com"
- OPENSEARCH_HOST_PRD="vpc-prd-apne2-erody-search-iny3phj6yhlz6kfgqsiyrtn7cq.ap-northeast-2.es.amazonaws.com"
- OPENSEARCH_USER="xxxx"
- OPENSEARCH_PASSWORD="xxxx"

## FAQ 임베딩 등록
- Vector Store 설정 (환경변수) : opensearch or chroma
- FAQ 추가 : docs/faq.txt
- chuck 단위 임베딩 등록 : ./create_index.sh

## 답변 가이드 설정 : docs/guide.md
- 챗봇 답변 스타일/제약 사항 등을 markdown 형태로 작성


## 실행

1. 환경 변수 확인
- VS_TYPE : chroma or opensearch
- LLM_MODEL : claude or gemini or chatgpt

2. 서비스 기동
- 백엔드 : ./start_api_fc.sh
- 프론트 : ./start_st.sh

## 문의
- 조춘기 jck@shinsegae.com