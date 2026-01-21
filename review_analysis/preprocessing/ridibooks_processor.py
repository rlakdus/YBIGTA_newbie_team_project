from review_analysis.preprocessing.base_processor import BaseDataProcessor
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
import re
import os
from konlpy.tag import Okt



class RidibooksProcessor(BaseDataProcessor):
    """
    Ridibooks 리뷰 데이터를 전처리하고 파생변수 생성하는 클래스
    """
    def __init__(self, input_path: str, output_dir: str):
        """
        RidibooksProcessor 초기화 함수.

        Args:
            input_path (str): 원본 리뷰 CSV 파일 경로
            output_dir (str): 전처리 결과를 저장할 디렉토리 경로

        Returns:
            None
        """
        super().__init__(input_path, output_dir)
        self.okt = Okt()

    def preprocess(self):
        """
        리뷰 데이터 전처리를 수행한다.

        수행 내용:
        - CSV 파일 로드
        - rating, date, content 컬럼 기준 결측치 제거
        - 별점 이상치 제거 (1~5 범위)
        - 날짜 문자열을 datetime 타입으로 변환
        - 이모지 제거, 텍스트 정제, 형태소 분석을 통한 리뷰 전처리 컬럼 생성

        Args:
            None

        Returns:
            None
        """
        # 데이터 로드
        self.df = pd.read_csv(self.input_path, header=None, names=['rating','date','content'])

        # 결측치 제거
        missing_cnt = self.df[["rating", "date", "content"]].isnull().sum()
        total_missing = missing_cnt.sum()
        if total_missing > 0:
            print(f"결측치 {total_missing}개 제거")
            self.df = self.df.dropna(subset=["rating", "date", "content"])
        else:
            print("결측치 없음")

        # 별점 이상치 제거
        before_cnt = len(self.df)
        self.df = self.df[self.df["rating"].between(1, 5)]
        after_cnt = len(self.df)
        removed_cnt = before_cnt - after_cnt
        if removed_cnt > 0:
            print(f"별점 이상치 {removed_cnt}개 제거")
        else:
            print("별점 이상치 없음")

        # 날짜 변환
        self.df["date"] = pd.to_datetime(self.df["date"], format="%Y.%m.%d",errors="coerce")
        self.df = self.df.dropna(subset=["date"])

        # 날짜 이상치 제거 (발매일 이전)
        RELEASE_DATE = pd.to_datetime("2020-04-21")
        before_cnt = len(self.df)
        self.df = self.df[self.df["date"] >= RELEASE_DATE]
        removed_cnt = before_cnt - len(self.df)
        if removed_cnt > 0:
            print(f"발매일 이전 리뷰 {removed_cnt}개 제거")
        else:
            print("발매일 이전 리뷰 없음")
        
        # 리뷰 문자 수 이상치
        self.df["content_len"] = self.df["content"].str.len()
        print(len(self.df[self.df["content_len"] < 10]))
        
        # 텍스트 전처리
        self.df["content_preprocess"] = (
            self.df["content"]
            .apply(self._remove_emoji)
            .apply(self._clean_korean_text)
            .apply(self._tokenize_korean)
            .apply(lambda x: " ".join(x))
        )


    def _remove_emoji(self, text: str) -> str:
        """
        문자열에서 이모지 제거

        Args:
            text (str): 이모지가 포함된 원본 텍스트

        Returns:
            str: 이모지가 제거된 텍스트
        """
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  
            u"\U0001F300-\U0001F5FF"  
            u"\U0001F680-\U0001F6FF"  
            u"\U0001F1E0-\U0001F1FF"  
                               "]+", flags=re.UNICODE)
        return emoji_pattern.sub("", text) 

    def _clean_korean_text(self, text: str) -> str:
        """
        한국어 텍스트 정제 함수.

        수행 내용:
        - 반복 문자 축약 (ㅋㅋㅋㅋ → ㅋㅋ)
        - 불필요한 특수문자 제거
        - 공백 정리

        Args:
            text (str): 원본 텍스트

        Returns:
            str: 정제된 텍스트
        """
        # 반복 문자 정규화 
        text = re.sub(r"(ㅋ)\1{2,}", r"\1\1", text)
        text = re.sub(r"(ㅎ)\1{2,}", r"\1\1", text)
        text = re.sub(r"(ㅠ)\1{2,}", r"\1\1", text)
        text = re.sub(r"(ㅜ)\1{2,}", r"\1\1", text)
        text = re.sub(r"(!)\1{2,}", r"\1\1", text)
        text = re.sub(r"(.)\1{2,}", r"\1\1", text)

        # 불필요한 특수문자 제거 
        text = re.sub(r"[^가-힣a-zA-Z0-9\s!?\.]", "", text)

        # 공백 정리
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _tokenize_korean(self, text: str) -> list[str]:
        """
        한국어 형태소 분석 및 불용어 제거를 수행한다.

        Okt 형태소 분석기를 사용하여 명사, 동사, 형용사, 숫자만 추출

        Args:
            text (str): 정제된 텍스트

        Returns:
            list[str]: 형태소 분석 및 불용어 제거 후 토큰 리스트
        """
        # 불용어 제거 및 형태소 분석 + 원형화
        STOPWORDS  = ["이", "그", "저", "것", "수", "등", "더", "정말", "너무", "이런", "같은", 
        "책","있다","없다","않다","햐다","이다","보다","읽다","같다","싶다","만",
        "나오다","느끼다","느낌","하다","아니다","되다","들다",'소설','이야기','점','부분',"좀","정말","자다"]
        tokens = self.okt.pos(text, stem=True)
        return [word for word, pos in tokens if pos in ("Noun", "Verb", "Adjective","Number") and word not in STOPWORDS]   

    
    def feature_engineering(self):
        """
        전처리된 리뷰 데이터를 기반으로 파생 변수를 생성한다.

        생성되는 변수:
        - 리뷰 길이 및 단어 수
        - 연/월/요일 파생 변수
        - rating 기반 감정 레이블 (negative / neutral / positive)
        - Bag-of-Words 기반 키워드 특징

        Args:
            None

        Returns:
            None
        """
        # 리뷰 파생 변수: 원래 리뷰 단어 수
        self.df["content_word_count"] = self.df["content"].apply(
            lambda x: len(x.split())
        )

        # 날짜 파생 변수: 연/ 월
        self.df["year"] = self.df["date"].dt.year
        self.df["month"] = self.df["date"].dt.month

        # 파생 변수: 감정 분석 - postive/neutral/negative 
        self.df["sentiment"] = self.df["rating"].apply(
            lambda x: "negative" if x <= 2 else
              "neutral"  if x == 3 else
              "positive"
        )

        # 텍스트 벡터화 
        self.vectorizer = CountVectorizer(
            max_features=30,    
            ngram_range=(1, 1)   
        )

        bow_matrix = self.vectorizer.fit_transform(self.df["content_preprocess"])

        bow_df = pd.DataFrame(
            bow_matrix.toarray(),
            columns=[f"bow_{c}" for c in self.vectorizer.get_feature_names_out()])

        self.df = pd.concat(
            [self.df.reset_index(drop=True), bow_df],
            axis=1
        )

    def save_to_database(self):
        """
        전처리 및 특징 생성이 완료된 데이터를 CSV 파일로 저장한다.

        저장 파일:
        - preprocessed_reviews_ridibooks.csv
        - UTF-8-SIG 인코딩 (엑셀 호환)

        Args:
            None

        Returns:
            None
        """
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir,"preprocessed_reviews_ridibooks.csv")
        self.df.to_csv(output_path, index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    preprocessor = RidibooksProcessor(
        input_path="database/reviews_ridibooks.csv",
        output_dir="database"
    )
    preprocessor.preprocess()
    preprocessor.feature_engineering()
    preprocessor.save_to_database()




