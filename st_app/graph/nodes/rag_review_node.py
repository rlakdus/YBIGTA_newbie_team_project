import json
from st_app.rag.llm import get_llm
from st_app.rag.retriever import get_balanced_search_results
from st_app.rag.prompt import REVIEW_PROMPT
from st_app.utils.state import ChatState, DocumentInfo
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

#llm = get_llm()

# 질문 재작성용 체인
# 작은 모델 (질문 재작성 전용)
small_llm = get_llm(model="solar-mini", temperature=0)

# 큰 모델 (최종 답변 생성용)
big_llm = get_llm(model="solar-pro", temperature=0)

# 질문 재작성 체인 (검색 정확도 향상용)
rephrase_prompt = ChatPromptTemplate.from_messages([
    ("system", "대화 이력을 참고해 마지막 사용자 질문을 검색 가능한 구체적인 한국어 질문으로 재작성해."),
    MessagesPlaceholder("chat_history"),
    ("human", "{user_input}")
])
rephrase_chain = rephrase_prompt | small_llm


def rag_review_node(state: ChatState):
    """
    도서 리뷰 기반 RAG 처리를 수행하는 LangGraph 노드.

    사용자 질문을 먼저 LLM을 통해 검색에 용이한 질문으로 재작성한 뒤,
    FAISS 벡터 DB에서 관련 리뷰를 검색하고, 검색된 리뷰들을 Context로
    사용하여 최종 LLM 응답을 생성한다.

    작은 모델(solar-mini)은 답변 속도 향상을 위해 질문 재작성 전용으로, 
    큰 모델(solar-pro)은 최종 답변 생성 전용으로 사용한다.

    Args:
        state (ChatState): 현재 LangGraph 상태 객체
            - user_input (str): 사용자의 최신 질문
            - messages (List[Dict]): 대화 히스토리

    Returns:
        dict:
            - messages (List[AIMessage]): 생성된 최종 답변
            - retrieved_docs (List[DocumentInfo]): 검색된 리뷰 문서 정보
            - rag_response (str): LLM이 생성한 답변 텍스트
    """
    user_input = state["user_input"]

    # 1️⃣ 대화 이력 변환
    history = []
    for msg in state.get("messages", []):
        if isinstance(msg, dict):
            if msg.get("role") == "user":
                history.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                history.append(AIMessage(content=msg["content"]))
        else:
            history.append(msg)

    # 2️⃣ 질문 재작성
    rewritten_query = rephrase_chain.invoke({
        "chat_history": history,
        "user_input": user_input
    }).content.strip()

    # 3️⃣ FAISS 검색
    source_docs = get_balanced_search_results(rewritten_query)

    # 4️⃣ 리뷰 Context 구성
    review_context = "\n\n".join([
        f"[출처: {doc.metadata.get('source', '알 수 없음')} | 평점: {doc.metadata.get('rate', 'N/A')}]\n{doc.page_content}"
        for doc in source_docs
    ])

    # 5️⃣ 최종 LLM 호출
    response = big_llm.invoke([
        SystemMessage(content=REVIEW_PROMPT + "\n\n" + review_context),
        *history,
        HumanMessage(content=rewritten_query)
    ])

    # 6️⃣ 검색 문서 정보 저장
    retrieved_info = [
        DocumentInfo(
            content=doc.page_content,
            source=doc.metadata.get('source', 'unknown'),
            text_len=len(doc.page_content),
            cat=doc.metadata.get('cat', 'short'),
            rate=doc.metadata.get('rate', 0.0)
        ) for doc in source_docs
    ]

    return {
        "messages": [response],
        "retrieved_docs": retrieved_info,
        "rag_response": response.content
    }