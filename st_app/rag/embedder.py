import pandas as pd
import os
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
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
            documents.append(Document(page_content=content, metadata={**base_meta, "is_chunked": False}))
        else:
            split_docs = text_splitter.create_documents([content])
            for doc in split_docs:
                doc.metadata = {**base_meta, "text_len": len(doc.page_content), "is_chunked": True}
                documents.append(doc)

    print(f"indexing 시작... (총 문서 수: {len(documents)}개)")
    
    embedding = HuggingFaceEmbeddings(model_name="snunlp/KR-SBERT-V40K-klueNLI-augSTS", model_kwargs={'device': 'cpu'})
    
    if not os.path.exists(save_path):
        os.makedirs(save_path)
        
    vectordb = FAISS.from_documents(documents, embedding)
    vectordb.save_local(save_path)

if __name__ == "__main__":
    build_faiss_index()
    print("faiss index 저장 완료: st_app/db/faiss_index/")