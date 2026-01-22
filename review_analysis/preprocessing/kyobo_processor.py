import pandas as pd
import re
import os
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer # type: ignore
from review_analysis.preprocessing.base_processor import BaseDataProcessor # type: ignore

# 형태소 분석기
try:
    from konlpy.tag import Okt # type: ignore
except ImportError:
    print("Warning: konlpy가 설치되지 않았습니다. pip install konlpy를 실행하세요.")
    Okt = None

class KyoboProcessor(BaseDataProcessor):
    def __init__(self, input_path: str, output_dir: str):
        super().__init__(input_path, output_dir)
        self.df = None
        self.site_name = "kyobo"
        
        # Okt 초기화
        jvm_path = os.environ.get('JVM_PATH')
        try:
            if Okt:
                if jvm_path:
                    self.okt = Okt(jvmpath=jvm_path)
                else:
                    self.okt = Okt()
            else:
                self.okt = None
        except Exception as e:
            print(f"Warning: KoNLPy 초기화 실패 ({e}). 형태소 분석이 제한될 수 있습니다.")
            self.okt = None

    # 계절 변수 로직
    def season(self, month: int) -> str:
        if 3 <= month <= 5:
            return 'Spring'
        elif 6 <= month <= 8:
            return 'Summer'
        elif 9 <= month <= 11:
            return 'Fall'
        else:
            return 'Winter'

    # 만족도 변수 로직 (5점 만점 기준)
    def satisfaction(self, rating: float) -> str:
        if rating >= 4:
            return 'Positive'
        elif rating >= 3: # 3점은 Neutral 
            return 'Neutral'
        else:
            return 'Negative'

    def preprocess(self):
        print(f"[{self.site_name}] Preprocessing started...")
        
        # 1. 데이터 로드
        try:
            self.df = pd.read_csv(self.input_path, encoding='utf-8-sig')
        except:
            self.df = pd.read_csv(self.input_path, encoding='cp949')

        # 2. 컬럼 이름 강제 통일
        self.df.columns = [str(col).strip().lower() for col in self.df.columns]
        rename_map = {
            'content': 'review', 'comment': 'review', '내용': 'review', 
            'score': 'rating', '평점': 'rating', '점수': 'rating',
            'reg_date': 'date', '작성일': 'date', '날짜': 'date'
        }
        self.df.rename(columns=rename_map, inplace=True)
        
        # 컬럼 이름 
        self.df.rename(columns={'review': 'content'}, inplace=True)

        # 3. 필수 컬럼 체크
        required_cols = ['content', 'rating', 'date']
        self.df.dropna(subset=required_cols, inplace=True)

        # 0~5점 필터링
        self.df = self.df[(self.df['rating'] >= 0) & (self.df['rating'] <= 5)]

        # 4. 텍스트 정제
        self.df['content'] = self.df['content'].apply(self._clean_text)
        self.df = self.df[self.df['content'].str.len() >= 2] # 빈 문자열 제거
        
        print(f"[{self.site_name}] Preprocessing done. (Rows: {len(self.df)})")

    def _clean_text(self, text):
        if not isinstance(text, str):
            return ""
        # 특수문자 제거
        text = re.sub(r'[^가-힣a-zA-Z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def feature_engineering(self):
        print(f"[{self.site_name}] Feature Engineering started...")
        
        if self.df is None:
            raise ValueError("Run preprocess() first.")

        # 1. 시계열 변수 (Year, Month, Season)
        try:
            self.df['date'] = self.df['date'].astype(str).str.replace('.', '-')
            self.df['date'] = pd.to_datetime(self.df['date'])
            
            self.df['year'] = self.df['date'].dt.year
            self.df['month'] = self.df['date'].dt.month
            self.df['season'] = self.df['month'].apply(self.season) # 계절 추가
        except Exception as e:
            print(f"Date parsing warning: {e}")

        # 2. 만족도 (Satisfaction)
        self.df['satisfaction'] = self.df['rating'].apply(self.satisfaction)

        # 3. [Yes24 스타일] 형태소 분석 및 키워드 추출
        print("형태소 분석 및 키워드 추출 중... (시간이 걸릴 수 있습니다)")
        
        def extract_keywords(text):
            if not self.okt or not text.strip():
                return text # Okt 없으면 원본 반환
            try:
                # 어간 추출(stem=True), 정규화(norm=True)
                pos_tokens = self.okt.pos(text, stem=True, norm=True)
                allowed_tags = ['Noun', 'Verb', 'Adjective', 'Adverb']
                meaningless_words = {'것', '수', '등', '거', '좀', '막', '뭐', '이', '그', '저', '하다', '있다'}
                
                keywords = []
                for word, tag in pos_tokens:
                    if tag in allowed_tags and word not in meaningless_words:
                        if len(word) > 1: # 1글자 제외
                            keywords.append(word)
                return ' '.join(keywords)
            except Exception:
                return text

        self.df['keywords'] = self.df['content'].apply(extract_keywords)
        self.df['text_len'] = self.df['content'].apply(len)

        # 4. TF-IDF 
        try:
            vectorizer = TfidfVectorizer(max_features=100)
            # 키워드가 있는 행만 골라서 벡터화 시도
            valid_content = self.df[self.df['keywords'].str.strip() != '']['keywords']
            
            if not valid_content.empty:
                tfidf_matrix = vectorizer.fit_transform(valid_content)
                print(f"TF-IDF 벡터화 완료. Matrix Shape: {tfidf_matrix.shape}")
                
            else:
                print("TF-IDF 건너뜀 (유효한 텍스트 없음)")
        except Exception as e:
            print(f"TF-IDF 실패: {e}")

        print(f"[{self.site_name}] Feature Engineering done.")

    def save_to_database(self):
        # 저장할 컬럼 지정
        save_cols = ['content', 'keywords', 'rating', 'satisfaction', 'date', 'year', 'month', 'season', 'text_len']
        
        # 존재하는 컬럼만 선택
        final_cols = [col for col in save_cols if col in self.df.columns]
        self.df = self.df[final_cols]

        output_filename = f"preprocessed_reviews_{self.site_name}.csv"
        output_path = os.path.join(self.output_dir, output_filename)
        
        self.df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"[{self.site_name}] Saved to {output_path}")