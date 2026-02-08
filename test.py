from langgraph.graph import StateGraph, END
from st_app.utils.state import ChatState
from st_app.graph.nodes.chat_node import chat_node
from st_app.graph.nodes.subject_info_node import subject_info_node
from st_app.graph.nodes.rag_review_node import rag_review_node
from st_app.graph.router import smart_router

workflow = StateGraph(ChatState)
workflow.add_node("subject_info", subject_info_node)
workflow.add_node("rag_review", rag_review_node)
workflow.add_node("general_chat", chat_node)

workflow.set_conditional_entry_point(
    smart_router,
    {
        "subject_info": "subject_info",
        "rag_review": "rag_review",
        "general_chat": "general_chat"
    }
)

workflow.add_edge("subject_info", END)
workflow.add_edge("rag_review", END)
workflow.add_edge("general_chat", END)

app = workflow.compile()

if __name__ == "__main__":
    # 1. 테스트하고 싶은 다양한 질문 리스트 (라우팅 확인용)
    test_scenarios = [
        {"input": "안녕? 너는 누구야?", "target": "general_chat"},
        {"input": "이 책 줄거리가 뭐야?", "target": "subject_info"},
        {"input": "독자들 리뷰 평점 어때?", "target": "rag_review"},
        {"input": "달러구트 꿈 백화점 작가 알려줘", "target": "subject_info"},
        {"input": "나 지금 너무 졸린데 어떡하지?", "target": "general_chat"}
    ]
    
    print("="*50)
    print("🚀 LangGraph 에이전트 통합 테스트 시작")
    print("="*50)

    for i, scenario in enumerate(test_scenarios, 1):
        test_input = scenario["input"]
        expected = scenario["target"]
        
        print(f"\n[테스트 {i}] 질문: {test_input}")
        print(f"🎯 예상 노드: {expected}")
        
        # 초기 상태 설정 (이전 대화가 없는 깨끗한 상태로 가정)
        state = ChatState(user_input=test_input, messages=[])
        
        try:
            # 그래프 실행
            result = app.invoke(state)
            
            # 결과 출력
            response = result['messages'][-1].content
            print(f"✅ 최종 답변: {response[:200]}...") # 길면 자름
        except Exception as e:
            print(f"❌ 에러 발생: {e}")
            
        print("-" * 50)