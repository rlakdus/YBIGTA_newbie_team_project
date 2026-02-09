from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage 
from langgraph.graph import StateGraph, END
from st_app.rag.llm import get_llm
from st_app.utils.state import ChatState

# 노드 import
from st_app.graph.nodes.chat_node import chat_node
from st_app.graph.nodes.subject_info_node import subject_info_node
from st_app.graph.nodes.rag_review_node import rag_review_node


# 1. LLM 응답 형식 정의
class RouteQuery(BaseModel):
    """사용자의 질문 의도를 분석하여 적절한 노드를 선택"""
    topic: Literal["subject_info", "rag_review", "general_chat"] = Field(
        description=(
            "도서 '달러구트 꿈 백화점'의 작가, 가격, 줄거리, 출판사 등 객관적 정보는 'subject_info', "
            "실제 독자들의 리뷰 내용이나 평판, 감상평, 추천 여부 등 분석은 'rag_review', "
            "단순 인사나 일상적인 대화, 책과 관련 없는 주제는 'general_chat'으로 분류하세요."
        )
    )


# 2. 라우터 함수
def smart_router(state: ChatState) -> str:
    """
    LLM 판단에 따른 조건부 라우팅 함수
    """
    #llm = get_llm(temperature=0)
    llm = get_llm(model="solar-mini")

    
    # LLM 응답 형식 지정
    structured_llm = llm.with_structured_output(RouteQuery)
    
    system_prompt = "너는 질문의 의도를 분석해 최적의 작업 노드를 결정하는 지능형 라우터야."
    
    # LLM 호출 
    result = structured_llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["user_input"])  # TypedDict 사용
    ])
    
    # 결과 반환
    return result.topic


# 3. 그래프 생성 함수
def create_graph():
    """
    LangGraph 생성 및 반환
    """
    # StateGraph 초기화
    workflow = StateGraph(ChatState)
    
    # 노드 추가
    workflow.add_node("general_chat", chat_node)
    workflow.add_node("subject_info", subject_info_node)
    workflow.add_node("rag_review", rag_review_node)
    
    # 조건부 엔트리 포인트 (라우터 연결)
    workflow.set_conditional_entry_point(
        smart_router,  # 라우팅 함수
        {
            "general_chat": "general_chat",
            "subject_info": "subject_info",
            "rag_review": "rag_review"
        }
    )
    
    # 각 노드 처리 후 종료
    workflow.add_edge("general_chat", END)
    workflow.add_edge("subject_info", END)
    workflow.add_edge("rag_review", END)
    
    # 컴파일 후 반환
    return workflow.compile()