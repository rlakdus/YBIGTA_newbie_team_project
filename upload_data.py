# upload_all_reviews.py
from pymongo import MongoClient
import csv

# MongoDB 연결
client = MongoClient(
    "mongodb://admin:password123@localhost:27017/"
    "?authSource=admin"
)

db = client["ybigta_reviews"]
collection = db["reviews"]

# CSV 파일 경로
SOURCES = {
    "kyobo": "database/reviews_kyobo.csv",
    "ridibooks": "database/reviews_ridibooks.csv",
    "yes24": "database/reviews_yes24.csv",
}

total = 0

for source, path in SOURCES.items():
    # CSV 파일 읽기
    with open(path, "r", encoding="utf-8") as f:
        csv_reader = csv.DictReader(f)  # ← CSV를 딕셔너리로 읽기
        data = list(csv_reader)
    
    # 각 리뷰에 source 추가
    for d in data:
        d["source"] = source  # ⭐️ 핵심
    
    # MongoDB에 업로드
    if data:  # 데이터가 있을 때만
        result = collection.insert_many(data)
        print(f"✅ {source}: {len(result.inserted_ids)}개 업로드")
        total += len(result.inserted_ids)
    else:
        print(f"⚠️ {source}: 데이터 없음")

print(f"\n🎉 총 {total}개 리뷰 업로드 완료")
client.close()