from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

def get_balanced_search_results(query, path="st_app/db/faiss_index"):
    embedding = HuggingFaceEmbeddings(model_name="snunlp/KR-SBERT-V40K-klueNLI-augSTS")
    vectordb = FAISS.load_local(path, embedding, allow_dangerous_deserialization=True)

    short_docs = vectordb.similarity_search(query, k=5, filter={"cat": "short"})
    
    mid_docs = vectordb.similarity_search(query, k=5, filter={"cat": "mid"})
    
    long_docs = vectordb.similarity_search(query, k=2, filter={"cat": "long"})

    # 5/5/2 총 12개
    final_docs = short_docs + mid_docs + long_docs
    return final_docs