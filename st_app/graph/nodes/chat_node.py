from st_app.rag.llm import get_llm
from st_app.rag.prompt import CHAT_PROMPT
from st_app.utils.state import ChatState
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

def chat_node(state: ChatState):
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
