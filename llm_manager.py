import json
import boto3
import os

from openai import OpenAI
import google.generativeai as genai


class LLMManager:
    def __init__(self, provider: str = "sonnet"):

        self.provider = provider.lower()
        self.llm_client = None

        if self.provider == "sonnet":
            print("LLM Provider로 Sonnet이 선택되었습니다.")
            # AWS Bedrock Client (Sonnet)
            self.llm_client = boto3.client(
                service_name='bedrock-runtime', 
                region_name='us-west-2'
            )
        elif self.provider == "chatgpt":
            print("LLM Provider로 ChatGPT가 선택되었습니다.")
            self.llm_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        elif self.provider == "gemini":
            print("LLM Provider로 Gemini가 선택되었습니다.")
            api_key = os.environ.get("GEMINI_API_KEY")
            genai.configure(api_key=api_key)
            self.llm_client = genai
        else:
            raise ValueError(f"지원하지 않는 LLM 제공자입니다: {self.provider}")


    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        if self.provider == "sonnet":
            return self._call_bedrock_sonnet(system_prompt, user_prompt)
        elif self.provider == "chatgpt":
            return self._call_openai_chatgpt(system_prompt, user_prompt)
        elif self.provider == "gemini":
            return self._call_gemini(system_prompt, user_prompt)
        else:
            raise ValueError(f"지원하지 않는 LLM 제공자입니다: {self.provider}")

    def _call_bedrock_sonnet(self, system_prompt: str, user_prompt: str) -> str:
        print('_call_bedrock_sonnet - user_prompt :', user_prompt)
        
        model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "temperature": 0.0,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}]
        })

        llm_response = self.llm_client.invoke_model(
            body=body,
            modelId=model_id,
            accept="application/json",
            contentType="application/json"
        )
        
        response_body = json.loads(llm_response.get('body').read())
        return response_body.get('content')[0].get('text')

    def _call_openai_chatgpt(self, system_prompt: str, user_prompt: str) -> str:

        if not self.llm_client:
            raise Exception("OpenAI 패키지가 설치되지 않았거나, API Key가 설정되지 않았습니다.")
        
        try:
            #model_id = "gpt-4o-mini" 
            # 상황에 따라 "gpt-3.5-turbo", "gpt-4o" 등으로 변경 가능
            model_id = "gpt-3.5-turbo"
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
        print('_call_gemini - user_prompt :', user_prompt)
        if not self.llm_client:
            raise Exception("Gemini 패키지가 설치되지 않았거나 구성되지 않았습니다.")
        
        try:
            # gemini-1.5-flash 모델 사용 (필요에 따라 gemini-1.5-pro 등으로 변경 가능)
            model = self.llm_client.GenerativeModel(
                model_name='gemini-2.5-flash',
                #model_name='gemini-2.5-pro', # 유료
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