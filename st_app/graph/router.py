from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage 
from st_app.rag.llm import get_llm
from st_app.utils.state import ChatState

# 1. LLM이 답변 형식 
class RouteQuery(BaseModel):
    """사용자의 질문 의도를 분석하여 적절한 노드를 선택"""
    topic: Literal["subject_info", "rag_review", "general_chat"] = Field(
        description=(
            "도서 '달러구트 꿈 백화점'의 작가, 가격, 줄거리, 출판사 등 객관적 정보는 'subject_info', "
            "실제 독자들의 리뷰 내용이나 평판, 감상평, 추천 여부 등 분석은 'rag_review', "
            "단순 인사나 일상적인 대화, 책과 관련 없는 주제는 'general_chat'으로 분류하세요."
        )
    )

def smart_router(state: ChatState) -> str:
    """
    LLM 판단에 따른 조건부 라우팅 함수
    """
    llm = get_llm()
    
    # 2. LLM 답변 형식 RouteQuery로 지정
    structured_llm = llm.with_structured_output(RouteQuery)
    
    system_prompt = "너는 질문의 의도를 분석해 최적의 작업 노드를 결정하는 지능형 라우터야."
    
    # 3. LLM 호출 
    result = structured_llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=state.user_input)
    ])
    
    # 4. 결과 반환
    return result.topic