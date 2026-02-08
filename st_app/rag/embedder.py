import pandas as pd
import os
import json
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
#from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

def build_faiss_index(save_path="st_app/db/faiss_index"):
    BASE_PATH = "database"
    kyobo_path = os.path.join(BASE_PATH, "preprocessed_reviews_kyobo.csv")
    ridi_path = os.path.join(BASE_PATH, "preprocessed_reviews_ridibooks.csv")
    yes24_path = os.path.join(BASE_PATH, "preprocessed_reviews_yes24.csv")

    df_list = []
    for path, source_name in zip([kyobo_path, ridi_path, yes24_path], ["교보문고", "리디북스", "YES24"]):
        if os.path.exists(path):
            tmp_df = pd.read_csv(path)
            content_col = 'content' if 'content' in tmp_df.columns else 'review'
            
            tmp_df = tmp_df[[content_col, 'rating']].rename(columns={content_col: 'review', 'rating': 'rate'})
            tmp_df['source'] = source_name
            df_list.append(tmp_df)

    df = pd.concat(df_list, ignore_index=True).dropna(subset=["review"])
    df = df.drop_duplicates(subset=["review"])
    df = df[df['review'].str.len() >= 5]

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=150, 
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
    )

    documents = []
    metadata_list = []  # meta.json용 리스트 추가
    doc_id = 0  # 문서 ID 카운터
    
    for _, row in df.iterrows():
        content = str(row['review'])
        source = row['source']
        rate = float(row['rate']) 
        curr_len = len(content)
        
        cat = "short" if curr_len < 50 else ("mid" if curr_len < 100 else "long")
        
        base_meta = {
            "source": source,
            "text_len": curr_len,
            "cat": cat,
            "rate": rate
        }
        
        if curr_len < 100:
            doc_meta = {
                "id": doc_id,
                "text": content,
                "source": source,
                "rating": rate,
                "length": curr_len,
                "category": cat,
                "is_chunked": False
            }
            metadata_list.append(doc_meta)
            
            documents.append(Document(
                page_content=content, 
                metadata={**base_meta, "is_chunked": False, "doc_id": doc_id}
            ))
            doc_id += 1
        else:
            split_docs = text_splitter.create_documents([content])
            for chunk_idx, doc in enumerate(split_docs):
                doc_meta = {
                    "id": doc_id,
                    "text": doc.page_content,
                    "source": source,
                    "rating": rate,
                    "length": len(doc.page_content),
                    "category": cat,
                    "is_chunked": True,
                    "chunk_index": chunk_idx,
                    "original_text": content  # 원본 리뷰도 포함
                }
                metadata_list.append(doc_meta)
                
                doc.metadata = {
                    **base_meta, 
                    "text_len": len(doc.page_content), 
                    "is_chunked": True,
                    "doc_id": doc_id
                }
                documents.append(doc)
                doc_id += 1

    print(f"indexing 시작... (총 문서 수: {len(documents)}개)")
    
    embedding = HuggingFaceEmbeddings(
        model_name="snunlp/KR-SBERT-V40K-klueNLI-augSTS", 
        model_kwargs={'device': 'cpu'}
    )
    
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    
    # FAISS 인덱스 저장
    vectordb = FAISS.from_documents(documents, embedding)
    vectordb.save_local(save_path)
    
    # meta.json 저장 추가
    meta_path = os.path.join(save_path, "meta.json")
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata_list, f, ensure_ascii=False, indent=2)
    
    print(f"meta.json 저장 완료: {meta_path} (총 {len(metadata_list)}개 항목)")

if __name__ == "__main__":
    build_faiss_index()
    print("faiss index 및 meta.json 저장 완료: st_app/db/faiss_index/")