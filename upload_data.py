import os
import csv
from pymongo import MongoClient

# =========================
# 데이터 경로
# =========================
BASE_DIR = os.getenv("DATA_DIR", "/data")

# =========================
# MongoDB URL (env로만 받음)
# =========================
mongo_url = os.getenv("MONGO_URL")
if not mongo_url:
    raise RuntimeError("❌ MONGO_URL 환경변수가 설정되지 않았습니다.")

# =========================
# MongoDB 연결
# =========================
client = MongoClient(mongo_url)
db = client["reviews"]
collection = db["reviews"]

# =========================
# CSV 파일들
# =========================
SOURCES = {
    "kyobo": os.path.join(BASE_DIR, "reviews_kyobo.csv"),
    "ridibooks": os.path.join(BASE_DIR, "reviews_ridibooks.csv"),
    "yes24": os.path.join(BASE_DIR, "reviews_yes24.csv"),
}

# =========================
# 업로드
# =========================
total = 0

for source, path in SOURCES.items():
    if not os.path.exists(path):
        print(f"⚠️ 파일 없음: {path}")
        continue

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data = list(reader)

    if not data:
        print(f"⚠️ {source}: 데이터 없음")
        continue

    for row in data:
        row["source"] = source

    result = collection.insert_many(data)
    print(f"✅ {source}: {len(result.inserted_ids)}개 업로드 완료")
    total += len(result.inserted_ids)

print(f"\n🎉 총 {total}개 리뷰가 저장되었습니다!")
client.close()
