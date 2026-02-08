import json
from st_app.rag.llm import get_llm
from st_app.rag.prompt import SUBJECT_INFO_PROMPT
from st_app.utils.state import ChatState
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

def subject_info_node(state: ChatState):
    # 1. JSON 파일 로드 (경로 확인 필수)
    with open("st_app/db/subject_information/subjects.json", "r", encoding="utf-8") as f:
        subject_data = json.load(f)

    # 2. 책 정보 가져오기
    b_info = subject_data.get("달러구트 꿈 백화점", {})

    # 3. 프롬프트 포맷팅 
    sys_msg = SystemMessage(content=SUBJECT_INFO_PROMPT.format(book_info=json.dumps(b_info, ensure_ascii=False)))
    
    # 4. 메시지 기록 변환 
    history = []
    for msg in state.messages:
        if isinstance(msg, dict):
            if msg.get("role") == "user":
                history.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                history.append(AIMessage(content=msg["content"]))
        else:
            history.append(msg)

    # 5. LLM 호출 
    llm = get_llm()
    response = llm.invoke([sys_msg] + history + [HumanMessage(content=f"질문: {state.user_input}\n필요한 정보만 골라 답해.")])
    
    # 6. 결과 반환
    return {"messages": [response],"rag_response": response.content}