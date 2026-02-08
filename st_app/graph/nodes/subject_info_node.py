import json
from rag.llm import get_llm
from rag.prompt import SUBJECT_INFO_PROMPT
from utils.state import ChatState

def subject_info_node(state: ChatState):
    # 1. subjects.json 데이터 로드
    with open("subject_information/subjects.json", "r", encoding="utf-8") as f:
        subject_data = json.load(f)

    # 2. 정보 가져오기
    b_info = subject_data.get("달러구트 꿈 백화점", {})

    # 3. 프롬프트 구성
    llm = get_llm()

    formatted_prompt = SUBJECT_INFO_PROMPT.format(book_info=json.dumps(book_info, ensure_ascii=False))

    # 4. LLM 호출 및 응답 반환
    response = llm.invoke([{"role": "system", "content": info_prompt}] + state["messages"])

    return {"messages": [response]}