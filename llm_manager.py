import json
import boto3
import os

from openai import OpenAI
#import google.generativeai as genai
import google.genai as genai

from dotenv import load_dotenv
load_dotenv()

class LLMManager:
    def __init__(self, provider: str = "claude"):

        self.provider = provider.lower()
        self.llm_client = None

        self.bedrock_model_id = os.environ.get("BEDROCK_MODEL")
        self.aws_region = os.environ.get("BEDROCK_REGION")
        self.inference_config = {}
        self.additional_model_fields = {}

        if self.provider == "claude":
            print("LLM Provider로 claude이 선택되었습니다.")
            # AWS Bedrock Client (claude)
            self.llm_client = boto3.client(
                service_name='bedrock-runtime', 
                region_name=os.environ.get("BEDROCK_REGION")
            )
            temperature = 0.0
            top_p = 0.1
            top_k = int(os.environ.get("BEDROCK_TOP_K", 5))
            self.inference_config = {"temperature": temperature, "topP": top_p , "maxTokens": 8000 }
            self.additional_model_fields = {"top_k": top_k}
            if self.aws_region == "us-east-1":
                self.additional_model_fields["anthropic_beta"] = ["context-1m-2025-08-07"]

        elif self.provider == "chatgpt":
            print("LLM Provider로 ChatGPT가 선택되었습니다.")
            api_key = os.environ.get("OPENAI_API_KEY")
            print("chatgpt api_key:", api_key)
            self.llm_client = OpenAI(api_key=api_key)

        elif self.provider == "gemini":
            print("LLM Provider로 Gemini가 선택되었습니다.")
            api_key = os.environ.get("GEMINI_API_KEY")
            print("gemini api_key:", api_key)
            genai.configure(api_key=api_key)
            self.llm_client = genai

        else:
            raise ValueError(f"지원하지 않는 LLM 제공자입니다: {self.provider}")


    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        if self.provider == "claude":
            return self._call_bedrock_claude(system_prompt, user_prompt)
        elif self.provider == "chatgpt":
            return self._call_openai_chatgpt(system_prompt, user_prompt)
        elif self.provider == "gemini":
            return self._call_gemini(system_prompt, user_prompt)
        else:
            raise ValueError(f"지원하지 않는 LLM 제공자입니다: {self.provider}")


    def _call_bedrock_claude(self, system_prompt: str, user_prompt: str) -> str:
        print('_call_bedrock_claude - system_prompt :', system_prompt)
        print('_call_bedrock_claude - user_prompt :', user_prompt)
            
        response = self.llm_client.converse(
            modelId=self.bedrock_model_id,
            messages=[{"role": "user", "content": [{"text": user_prompt}]}],
            system=[{"text": system_prompt}],
            inferenceConfig=self.inference_config,
            additionalModelRequestFields=self.additional_model_fields
        )
        return response['output']['message']['content'][0]['text']
    

    def _call_openai_chatgpt(self, system_prompt: str, user_prompt: str) -> str:

        if not self.llm_client:
            raise Exception("OpenAI 패키지가 설치되지 않았거나, API Key가 설정되지 않았습니다.")
        
        try:
            model_id = os.getenv("CHATGPT_MODEL", "gpt-3.5-turbo")
            print('_call_openai_chatgpt - model_id :', model_id)
            response = self.llm_client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
                max_tokens=1024
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API 호출 중 오류 발생: {e}")
            return "죄송합니다. 답변을 생성하는 중 오류가 발생했습니다." 

    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        print('_call_gemini - system_prompt :', system_prompt)  
        print('_call_gemini - user_prompt :', user_prompt)
        if not self.llm_client:
            raise Exception("Gemini 패키지가 설치되지 않았거나 구성되지 않았습니다.")
        
        try:
            # gemini-1.5-flash 모델 사용 (필요에 따라 gemini-1.5-pro 등으로 변경 가능)
            model = self.llm_client.GenerativeModel(
                model_name=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
                system_instruction=system_prompt
            )
            response = model.generate_content(
                user_prompt,
                generation_config=self.llm_client.types.GenerationConfig(
                    temperature=0.0,
                    max_output_tokens=4096,
                )
            )
            return response.text
        except Exception as e:
            print(f"Gemini API 호출 중 오류 발생: {e}")
            return "죄송합니다. 답변을 생성하는 중 오류가 발생했습니다."