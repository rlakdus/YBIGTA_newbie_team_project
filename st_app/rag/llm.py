import os
from langchain_upstage import ChatUpstage

def get_llm(model="solar-pro", temperature=0):
    """
    Upstage Solar LLM 객체를 생성하여 반환하는 함수.

    환경 변수에 설정된 UPSTAGE_API_KEY를 사용해 ChatUpstage 모델을 초기화한다.
    Args:
        model (str): 사용할 Solar 모델 이름
                     - "solar-pro"
                     - "solar-mini"
        temperature (float): 생성 다양성 조절 값 

    Raises:
        ValueError: UPSTAGE_API_KEY 환경 변수가 설정되지 않은 경우

    Returns:
        ChatUpstage: 초기화된 LLM 객체
    """
    api_key = os.getenv("UPSTAGE_API_KEY")

    if not api_key:
        raise ValueError("UPSTAGE_API_KEY가 설정되지 않았습니다. 환경 변수를 확인해주세요.")
       
    return ChatUpstage(api_key=api_key, model=model, temperature=temperature)