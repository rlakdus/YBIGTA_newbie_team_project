import json
from st_app.rag.llm import get_llm
from st_app.rag.retriever import get_balanced_search_results
from st_app.rag.prompt import SUBJECT_INFO_PROMPT
from st_app.utils.state import ChatState, DocumentInfo
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

llm = get_llm()

# 질문 재작성용 체인 설정
rephrase_prompt = ChatPromptTemplate.from_messages([
    ("system", "대화 이력을 참고해 마지막 사용자 질문을 검색 가능한 구체적인 한국어 질문으로 재작성해."),
    MessagesPlaceholder("chat_history"),
    ("human", "{user_input}")
])
rephrase_chain = rephrase_prompt | llm

def rag_review_node(state: ChatState):
    user_input = state.user_input
    
    # 1. 메시지 기록 변환
    history = []
    for msg in state.messages:
        if isinstance(msg, dict):
            if msg.get("role") == "user":
                history.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                history.append(AIMessage(content=msg["content"]))
        else:
            history.append(msg)

    # 2. 질문 재작성
    rewritten_query = rephrase_chain.invoke({
        "chat_history": history,
        "user_input": user_input
    }).content.strip()

    # 3. meta.json에서 도서 기본 정보 로드
    with open("st_app/db/faiss_index/meta.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    book_meta = meta.get("달러구트 꿈 백화점", {})
    meta_context = "[도서 기본 정보]\n" + json.dumps(book_meta, ensure_ascii=False, indent=2)

    # 4. 검색 수행(RAG)
    source_docs = get_balanced_search_results(rewritten_query)

    # 5. 검색된 리뷰를 Context로 합친다
    review_context = "\n\n".join([
        f"[출처: {doc.metadata.get('source', '알 수 없음')} | 평점: {doc.metadata.get('rate', 'N/A')}] {doc.page_content}"
        for doc in source_docs
    ])

    # 6. 도서 기본 정보 + 리뷰를 합쳐서 프롬프트에 주입
    context = meta_context + "\n\n[독자 리뷰]\n" + review_context
    formatted_sys_prompt = SUBJECT_INFO_PROMPT.format(book_info=context)
    
    # 6. LLM 호출
    response = llm.invoke([
        SystemMessage(content=formatted_sys_prompt),
        HumanMessage(content=rewritten_query)
    ])

    # 7. DocumentInfo 객체 리스트 생성 
    retrieved_info = [
        DocumentInfo(
            content=doc.page_content,
            source=doc.metadata.get('source', 'unknown'),
            text_len=len(doc.page_content),
            cat=doc.metadata.get('cat', 'short')
        ) for doc in source_docs
    ]

    # 8. 결과 반환
    return {
        "messages": [response],
        "retrieved_docs": retrieved_info,
        "rag_response": response.content
    }