import os
from langchain_upstage import ChatUpstage

def get_llm(model="solar-pro", temperature=0):
    api_key = os.getenv("UPSTAGE_API_KEY")

    if not api_key:
        raise ValueError("UPSTAGE_API_KEY가 설정되지 않았습니다. 환경 변수를 확인해주세요.")
       
    return ChatUpstage(api_key=api_key, model=model, temperature=temperature)