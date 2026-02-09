from pydantic import BaseModel, Field
from typing import TypedDict, List, Optional, Dict, Any, Literal

class DocumentInfo(TypedDict):
    """검색된 문서 정보"""
    content: str
    source: str
    text_len: int
    cat: Literal["short", "mid", "long"]
    rate: float

class ChatState(TypedDict, total=False):
    """LangGraph 상태 클래스 (TypedDict 사용)"""
    user_input: str
    messages: List[Dict[str, Any]]
    next_node: Optional[str]
    retrieved_docs: List[DocumentInfo]
    meta: Dict[str, Any]
    rag_response: Optional[str]