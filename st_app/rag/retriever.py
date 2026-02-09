from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

def get_balanced_search_results(query, path="st_app/db/faiss_index"):
    """
    FAISS 벡터 DB에서 유사 리뷰를 검색하고,
    리뷰 길이 카테고리(short/mid/long)별 균형을 맞춰 결과를 반환하는 함수.

    전체 유사도 상위 문서 중에서:
        - short 리뷰 5개
        - mid 리뷰 5개
        - long 리뷰 2개
    를 선별하여 총 12개의 문서를 반환한다.

    이는 다양한 길이의 리뷰 정보를 RAG Context로 제공하기 위함이다.

    Args:
        query (str): 사용자 질문 또는 검색 문장
        path (str): FAISS 인덱스가 저장된 경로

    Returns:
        List[Document]: 길이 균형이 적용된 리뷰 문서 리스트
    """
    embedding = HuggingFaceEmbeddings(model_name="snunlp/KR-SBERT-V40K-klueNLI-augSTS")
    vectordb = FAISS.load_local(path, embedding, allow_dangerous_deserialization=True)
    all_docs = vectordb.similarity_search(query, k=30)

    # short_docs = vectordb.similarity_search(query, k=5, filter={"cat": "short"})
    # mid_docs = vectordb.similarity_search(query, k=5, filter={"cat": "mid"})
    # long_docs = vectordb.similarity_search(query, k=2, filter={"cat": "long"})
    short_docs = [d for d in all_docs if d.metadata.get("cat") == "short"][:5]
    mid_docs = [d for d in all_docs if d.metadata.get("cat") == "mid"][:5]
    long_docs = [d for d in all_docs if d.metadata.get("cat") == "long"][:2]

    # 5/5/2 총 12개
    final_docs = short_docs + mid_docs + long_docs
    return final_docs

