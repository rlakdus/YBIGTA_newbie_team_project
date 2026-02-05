# app/review/review_router.py 추가
from fastapi import APIRouter, HTTPException
from database.mongodb_connection import mongo_db
from review_analysis.preprocessing.yes24_processor import Yes24Processor
from review_analysis.preprocessing.ridibooks_processor import RidibooksProcessor
from review_analysis.preprocessing.kyobo_processor import KyoboProcessor


router = APIRouter(prefix="/review", tags=["review"])

@router.post("/preprocess/{site_name}")
async def preprocess_reviews(site_name: str):
    """
    크롤링한 리뷰 데이터를 전처리하는 API
    
    site_name: kyobo, ridibooks, yes24 중 하나
    """
    try:
        # 1. MongoDB 연결
        db = mongo_db
        collection = db["reviews"]
        
        # 2. 해당 사이트의 리뷰만 가져오기
        raw_reviews = list(collection.find({"source": {"$regex": site_name.strip(), "$options": "i"}}))
        
        if not raw_reviews:
            raise HTTPException(
                status_code=404, 
                detail=f"{site_name} 리뷰 데이터가 없습니다"
            )
        
        # 3. 사이트별로 적절한 Processor 선택
        if site_name == "kyobo":
            processor = KyoboProcessor()  # ⭐ 인자 없이 생성 가능!
        elif site_name == "ridibooks":
            processor = RidibooksProcessor()
        elif site_name == "yes24":
            processor = Yes24Processor()
        else:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 사이트: {site_name}. kyobo, ridibooks, yes24 중 하나를 입력하세요."
            )
        
        # 4. 전처리 수행
        processed_reviews = []
        
        for review in raw_reviews:
            actual_content = None
            for key in review.keys():
                if key.strip() in ["content", "review", "text"]:
                    actual_content = review[key]
                    break
            
            if actual_content:
                processed_text = processor.preprocess_text(actual_content)
                
                processed_reviews.append({
                    "original_id": str(review["_id"]),
                    "site_name": site_name,
                    "original_content": review.get("content", ""),
                    "processed_content": processed_text,
                    "rating": review.get("rating", ""),
                    "date": review.get("date", "")
                })
        
        # 5. 전처리된 데이터를 MongoDB에 저장
        processed_collection = db[f"{site_name}_processed"]
        
        # 기존 데이터 삭제
        processed_collection.delete_many({})
        
        # 새 데이터 삽입
        if processed_reviews:
            processed_collection.insert_many(processed_reviews)
        
        return {
            "success": True,
            "message": f"{site_name} 리뷰 {len(processed_reviews)}개 전처리 완료",
            "site_name": site_name,
            "processed_count": len(processed_reviews),
            "original_count": len(raw_reviews)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"전처리 중 오류: {str(e)}")