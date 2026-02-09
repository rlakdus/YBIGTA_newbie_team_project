from st_app.rag.llm import get_llm
from st_app.rag.prompt import CHAT_PROMPT
from st_app.utils.state import ChatState
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

def chat_node(state: ChatState):
    """
    일반 대화를 처리하는 LangGraph 노드 함수.

    기존 대화 히스토리를 유지한 상태에서 LLM을 통해 자연스러운 대화 응답을 생성한다.
    System Prompt(CHAT_PROMPT)를 기반으로 대화 스타일을 제어한다.

    Args:
        state (ChatState): 현재 LangGraph 상태 객체.
            - user_input (str): 사용자의 최신 입력 문장
            - messages (List[Dict]): 이전 대화 기록 (role: user/assistant)

    Returns:
        dict:
            - messages (List[AIMessage]): 생성된 AI 응답 메시지 (LangGraph가 상태에 추가)
    """
    llm = get_llm()
    
    current_messages = state.get("messages", [])
    
    history = []
    for msg in current_messages:
        if isinstance(msg, dict):
            if msg.get("role") == "user":
                history.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                history.append(AIMessage(content=msg["content"]))
        else:
            history.append(msg)
        
    #response = llm.invoke([SystemMessage(content=CHAT_PROMPT), *history,
                           #HumanMessage(content=f"사용자 질문: {state.user_input}\n질문에 맞춰서 센스 있게 대답해줘.")])
    response = llm.invoke([
        SystemMessage(content=CHAT_PROMPT),
        *history,
        HumanMessage(content=state["user_input"])
    ])
    
    return {"messages": [response]}
