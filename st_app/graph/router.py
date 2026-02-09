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
    """
    사용자 질문의 의도를 구조화된 형태로 분류하기 위한 Pydantic 모델.

    LLM의 Structured Output 기능을 사용하여, 자연어 질문을
    사전에 정의된 작업 노드 중 하나로 매핑하기 위해 사용된다.

    Attributes:
        topic (Literal):
            LLM이 판단한 질문의 의도 분류 결과.
            - "subject_info": 도서의 객관적 정보 질문 (작가, 줄거리, 가격 등)
            - "rag_review": 독자 리뷰 기반 평가/감상/추천 여부 관련 질문
            - "general_chat": 인사, 잡담, 도서와 무관한 일반 대화
    """
    topic: Literal["subject_info", "rag_review", "general_chat"] = Field(
        description=(
            "도서 '달러구트 꿈 백화점'의 작가, 가격, 줄거리, 출판사 등 객관적 정보는 'subject_info', "
            "실제 독자들의 리뷰 내용이나 평판, 감상평, 추천 여부 등 분석은 'rag_review', "
            "단순 인사나 일상적인 대화, 책과 관련 없는 주제는 'general_chat'으로 분류하세요."
        )
    )


# 2. 라우터 함수
def router(state: ChatState) -> str:
    """
    사용자 질문의 의도를 LLM을 통해 분석하고,
    해당 질문을 처리할 LangGraph 노드 이름을 반환하는 라우팅 함수.

    LangGraph의 조건부 엔트리 포인트로 사용되며, 대화 흐름의 첫 분기를 담당하는 컴포넌트

    동작 과정:
        1. solar-mini 모델을 사용해 LLM 객체를 생성한다.
        2. Structured Output을 통해 RouteQuery 형식으로 응답을 제한한다.
        3. system prompt로 "지능형 라우터 역할"을 부여한다.
        4. 사용자 입력(state["user_input"])을 기반으로 의도를 분석한다.
        5. 분석 결과(topic)에 따라 다음 실행 노드를 반환한다.

    Args:
        state (ChatState):
            LangGraph 상태 객체
            - user_input (str): 사용자의 최신 질문

    Returns:
        str: 다음에 실행될 노드 이름
            - "general_chat"
            - "subject_info"
            - "rag_review"
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
    LangGraph 기반 AI Agent 워크플로우를 구성하고 컴파일하는 함수.

    사용자 질문의 의도에 따라 서로 다른 처리 노드로 동적으로 분기하는 Agent 구조를 구현한다.

    그래프 구성 요소:

    1. State 정의
       - ChatState(TypedDict)를 기반으로 상태를 관리

    2. 노드(Node)
       - "general_chat": 일반 대화 처리
       - "subject_info": 도서 기본 정보 조회
       - "rag_review": 리뷰 기반 RAG 응답 생성

    3. 조건부 엔트리 포인트
       - router() 함수를 통해 첫 노드를 LLM이 결정

    4. 종료 구조
       - 각 노드는 처리 후 END로 연결되어 단일 턴 응답 구조 형성

    Returns:
        CompiledGraph:
            LangGraph 실행 객체.
            streamlit_app.py에서 invoke(state)로 호출되어 동작한다.
    """
    # StateGraph 초기화
    workflow = StateGraph(ChatState)
    
    # 노드 추가
    workflow.add_node("general_chat", chat_node)
    workflow.add_node("subject_info", subject_info_node)
    workflow.add_node("rag_review", rag_review_node)
    
    # 조건부 엔트리 포인트 (라우터 연결)
    workflow.set_conditional_entry_point(
        router,  # 라우팅 함수
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