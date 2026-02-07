from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal

class DocumentInfo(BaseModel):
    content: str
    source: str
    text_len: int
    cat: Literal["short", "mid", "long"]  
    rate: float = 0.0

class ChatState(BaseModel):
    user_input: str = ""
    messages: List[Dict[str, Any]] = Field(default_factory=list) 
    next_node: Optional[str] = None 
    retrieved_docs: List[DocumentInfo] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    rag_response: Optional[str] = None 