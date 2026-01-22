from review_analysis.preprocessing.base_processor import BaseDataProcessor
from sklearn.feature_extraction.text import CountVectorizer # type: ignore
import pandas as pd
import re
import os
from konlpy.tag import Okt # type: ignore

class Yes24Processor(BaseDataProcessor):
    """
    Yes24 리뷰 데이터를 전처리하고 파생변수 생성하는 클래스
    """
    def __init__(self, input_path: str, output_dir: str):
        super().__init__(input_path, output_dir)
        
        # 맥북 환경변수나 시스템 경로를 체크해서 Okt에 입력
        jvm_path = os.environ.get('JVM_PATH')
        try:
            if jvm_path:
                self.okt = Okt(jvmpath=jvm_path)
            else:
                self.okt = Okt()
        except Exception as e:
            print(f"Warning: KoNLPy 초기화 실패 ({e}).")
            self.okt = None

    def preprocess(self):
        """
        리뷰 데이터 전처리를 수행한다.
        """
        # 데이터 로드
        self.df = pd.read_csv(self.input_path, header=None, names=['rating', 'date', 'content'])
        
        # rating 컬럼을 숫자로 변환 (숫자가 아닌 값은 에러 없이 처리)
        self.df["rating"] = pd.to_numeric(self.df["rating"], errors="coerce")
        
        # 결측치 제거 (방금 숫자로 변환하며 생긴 NaT/NaN 포함)
        missing_cnt = self.df[["rating", "date", "content"]].isnull().sum()
        total_missing = missing_cnt.sum()
        if total_missing > 0:
            print(f"결측치 {total_missing}개 제거")
            self.df = self.df.dropna(subset=["rating", "date", "content"])
        else:
            print("결측치 없음")

        self.df = self.df[self.df["rating"].between(1, 5)]
        
        # errors="coerce"를 통해 잘못된 형식은 NaT로 바꾸고 제거합니다.
        self.df["date"] = pd.to_datetime(self.df["date"], errors="coerce")
        self.df = self.df.dropna(subset=["date"])
        
        # 텍스트 전처리
        self.df["content_preprocess"] = (
            self.df["content"]
            .apply(self._remove_emoji)
            .apply(self._clean_korean_text)
            .apply(self._tokenize_korean)
            .apply(lambda x: " ".join(x))
        )

    def _remove_emoji(self, text: str) -> str:
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  
            u"\U0001F300-\U0001F5FF"  
            u"\U0001F680-\U0001F6FF"  
            u"\U0001F1E0-\U0001F1FF"  
                                 "]+", flags=re.UNICODE)
        return emoji_pattern.sub("", str(text)) 

    def _clean_korean_text(self, text: str) -> str:
        # 반복 문자 정규화
        text = re.sub(r"(ㅋ|ㅎ|ㅠ|ㅜ|!|.)\1{2,}", r"\1\1", str(text))
        # 불필요한 특수문자 제거
        text = re.sub(r"[^가-힣a-zA-Z0-9\s!?\.]", "", text)
        # 공백 정리
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _tokenize_korean(self, text: str) -> list[str]:
        # 불용어 리스트
        STOPWORDS = ["이", "그", "저", "것", "수", "등", "더", "정말", "너무", "이런", "같은", 
                     "책", "있다","없다","않다","햐다","이다","보다","읽다","같다","보다","싶다",
                     "나오다","느끼다","느낌","하다","아니다","되다","들다", "구매", "예스24", "yes24"]
        tokens = self.okt.pos(text, stem=True)
        return [word for word, pos in tokens if pos in ("Noun", "Verb", "Adjective","Number") and word not in STOPWORDS]   

    def feature_engineering(self):
        """
        파생 변수 생성
        """
        self.df["content_len"] = self.df["content"].str.len()
        self.df["content_word_count"] = self.df["content"].apply(lambda x: len(str(x).split()))

        self.df["year"] = self.df["date"].dt.year
        self.df["month"] = self.df["date"].dt.month
        self.df["weekday"] = self.df["date"].dt.weekday

        self.df["sentiment"] = self.df["rating"].apply(
            lambda x: "negative" if x <= 2 else "neutral" if x == 3 else "positive"
        )

        # 텍스트 벡터화
        self.vectorizer = CountVectorizer(max_features=30, ngram_range=(1, 1))
        bow_matrix = self.vectorizer.fit_transform(self.df["content_preprocess"])
        bow_df = pd.DataFrame(
            bow_matrix.toarray(),
            columns=[f"bow_{c}" for c in self.vectorizer.get_feature_names_out()])

        self.df = pd.concat([self.df.reset_index(drop=True), bow_df], axis=1)

    def save_to_database(self):
        """
        결과 저장
        """
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, "./preprocessed_reviews_yes24.csv")
        self.df.to_csv(output_path, index=False, encoding="utf-8-sig")