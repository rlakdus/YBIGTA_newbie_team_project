import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

from st_app.graph.router import create_graph


# 페이지 설정
st.set_page_config(
    page_title="달러구트 꿈 백화점 챗봇",
    page_icon="📚",
    layout="wide"
)

# 타이틀
st.title("📚 달러구트 꿈 백화점 리뷰 챗봇")
st.caption("책 정보와 독자 리뷰를 바탕으로 질문에 답변해드립니다!")

# API 키 확인 (Streamlit Cloud용)
if not os.getenv("UPSTAGE_API_KEY"):
    st.error("⚠️ UPSTAGE_API_KEY가 설정되지 않았습니다. Streamlit Cloud Secrets에서 설정해주세요!")
    st.stop()

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

if "graph" not in st.session_state:
    with st.spinner("챗봇 초기화 중..."):
        try:
            st.session_state.graph = create_graph()
            st.success("✅ 챗봇 준비 완료!", icon="🤖")
        except Exception as e:
            st.error(f"❌ 챗봇 초기화 실패: {str(e)}")
            st.stop()

# 사이드바
with st.sidebar:
    st.header("💡 사용 가이드")
    st.markdown("""
    ### 질문 예시
    
    **📖 책 기본 정보**
    - 이 책 작가가 누구야?
    - 가격이 얼마야?
    - 줄거리 알려줘
    
    **⭐ 리뷰 & 평가**
    - 리뷰 보여줘
    - 평점이 낮은 이유가 뭐야?
    - 이 책 재밌어?
    
    **💬 일반 대화**
    - 안녕?
    - 오늘 기분 어때?
    """)
    
    st.divider()
    
    # 대화 초기화 버튼
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    # 통계 표시
    if st.session_state.messages:
        st.divider()
        st.metric("총 대화 수", len([m for m in st.session_state.messages if m["role"] == "user"]))

# 메인 채팅 영역
st.divider()

# 채팅 히스토리 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # 검색된 리뷰가 있으면 표시
        if message["role"] == "assistant" and message.get("retrieved_docs"):
            with st.expander("📄 참고한 리뷰 보기", expanded=False):
                for i, doc in enumerate(message["retrieved_docs"][:3], 1):
                    st.markdown(f"**리뷰 {i}** - {doc.get('source', '알 수 없음')} (평점: {doc.get('rate', 'N/A')})")
                    st.text(doc.get('content', '')[:200] + "..." if len(doc.get('content', '')) > 200 else doc.get('content', ''))
                    if i < len(message["retrieved_docs"][:3]):
                        st.divider()

# 사용자 입력
if prompt := st.chat_input("질문을 입력하세요..."):
    # 사용자 메시지 추가 및 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # AI 응답 생성
    with st.chat_message("assistant"):
        with st.spinner("답변 생성 중..."):
            try:
                # 상태 구성
                state = {
                    "user_input": prompt,
                    "messages": st.session_state.messages.copy(),
                    "retrieved_docs": [],
                    "rag_response": None,
                    "next_node": None,
                    "meta": {}
                }
                
                # LangGraph 실행
                result = st.session_state.graph.invoke(state)
                
                # 응답 추출
                if result.get("messages") and len(result["messages"]) > 0:
                    last_message = result["messages"][-1]
                    
                    # 응답 텍스트 추출
                    if hasattr(last_message, 'content'):
                        response_text = last_message.content
                    elif isinstance(last_message, dict):
                        response_text = last_message.get('content', '응답을 생성할 수 없습니다.')
                    else:
                        response_text = str(last_message)
                else:
                    response_text = "죄송합니다. 응답을 생성할 수 없습니다."
                
                # 응답 표시
                st.markdown(response_text)
                
                # 검색된 문서 정보 표시
                retrieved_docs = result.get("retrieved_docs", [])
                if retrieved_docs and len(retrieved_docs) > 0:
                    with st.expander("📄 참고한 리뷰 보기", expanded=False):
                        for i, doc in enumerate(retrieved_docs[:3], 1):
                            doc_dict = doc if isinstance(doc, dict) else doc.__dict__
                            st.markdown(f"**리뷰 {i}** - {doc_dict.get('source', '알 수 없음')} (평점: {doc_dict.get('rate', 'N/A')})")
                            content = doc_dict.get('content', '')
                            st.text(content[:200] + "..." if len(content) > 200 else content)
                            if i < len(retrieved_docs[:3]):
                                st.divider()
                
                # 세션에 저장
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "retrieved_docs": [
                        {
                            "content": doc.get('content') if isinstance(doc, dict) else doc.content,
                            "source": doc.get('source') if isinstance(doc, dict) else doc.source,
                            "rate": doc.get('rate', 0.0) if isinstance(doc, dict) else getattr(doc, 'rate', 0.0)
                        } for doc in retrieved_docs[:3]
                    ] if retrieved_docs else []
                })
                
            except Exception as e:
                error_msg = f"오류가 발생했습니다: {str(e)}"
                st.error(error_msg)
                st.exception(e)  # 디버깅용 상세 에러
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

# 푸터
st.divider()
st.caption("💡 Tip: 책 정보, 리뷰, 일반 대화 모두 가능합니다!")