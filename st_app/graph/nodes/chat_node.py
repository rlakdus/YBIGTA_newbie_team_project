from rag.llm import get_llm
from utils.state import ChatState

def chat_node(state: State):
    llm = get_llm

    # 일반적인 대화 프롬프트 설정
    prompt = "당신은 친절한 도서 상담원입니다. 일상적인 대화를 나누거나, 질문에 대해 답변을 해주세요."
    response = llm.invoke(state["messages"])

    return {"messages": [response]}