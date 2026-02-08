import os
from langchain_upstage import ChatUpstage

def get_llm(model="solar-pro", temperature=0):
    api_key = os.getenv("UPSTAGE_API_KEY")
    return ChatUpstage(api_key=api_key, model=model, temperature=temperature)