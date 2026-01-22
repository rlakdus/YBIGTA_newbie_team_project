from review_analysis.crawling.base_crawler import BaseCrawler

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import time
import os
import csv


class RidiBooksCrawler(BaseCrawler):
    '''
    RidiBooks 도서 리뷰를 수집하는 크롤러 클래스.

    BaseCrawler를 상속받아 출력 디렉토리 관리 기능을 사용하며,
    Selenium WebDriver를 통해 리뷰 페이지를 동적으로 탐색
    '''
    def __init__(self, output_dir: str):
        super().__init__(output_dir)
        self.driver = None
        self.reviews: list[dict[str, str | int]] = []
        
    def start_browser(self):
        '''
        Selenium Chrome WebDriver를 초기화하고 브라우저를 실행한다.
        
        브라우저 설정에는 다음이 포함된다:
        - GPU 비활성화
        - 한글 페이지 로딩을 위한 언어 설정
        - User-Agent 지정
        - 브라우저 창 크기 설정
        
        Returns: None
        '''
        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--lang=ko-KR")
        options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36")
        
        options.add_argument("--window-size=1200,900")
        self.driver = webdriver.Chrome(options=options)
    
    def scrape_reviews(self):
        """
        리디북스 도서 페이지에서 리뷰 데이터를 수집한다.

        각 리뷰에서 다음 정보를 추출한다: 
        - 별점 (rating)
        - 작성일 (date)
        - 리뷰 내용 (content)
        중복 리뷰는 (별점, 날짜, 내용) 기준으로 제거된다.
        목표 리뷰 개수에 도달하기 전까지 더보기 버튼을 눌러 수집을 진행한다.

        Returns: None
        """
        product_url = "https://ridibooks.com/books/1648000309"
        target_count=685

        # 상품 페이지 접속
        self.driver.get(product_url)
        time.sleep(5)
        
        self.reviews = []
        seen_reviews = set()
        
        while len(self.reviews) < target_count:

            review_items = self.driver.find_elements(
                By.CSS_SELECTOR,
                "li"
            )
            for li in review_items:
                try:
                    # 별점
                    stars = li.find_elements(By.CSS_SELECTOR,"div.rigrid-16snxvd svg")
                    rating = sum(1 for star in stars if "5pz" in star.get_attribute("class"))
                    if rating == 0:
                        continue
                    
                    # 리뷰 내용
                    content = li.find_element(By.CSS_SELECTOR,"p.rigrid-d7duv1").text.strip()

                    # 날짜
                    date = li.find_element(By.CSS_SELECTOR,"div.rigrid-1gtkt0l > div").text.strip()
                    
                    review_key = (rating, date, content)
                    if review_key in seen_reviews:
                        continue

                    seen_reviews.add(review_key)
                    self.reviews.append({
                        "rating": rating,
                        "date": date,
                        "content": content})

                    if len(self.reviews) >= target_count:
                        break
                
                except Exception:
                    continue
            
            # 더보기 버튼 클릭
            try:
                more_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button.rigrid-15zefso")
                    )
                )
                
                self.driver.execute_script("arguments[0].scrollIntoView(true);", more_btn)
                time.sleep(1)
                self.driver.execute_script("arguments[0].click();", more_btn)
                time.sleep(3)
            except Exception:
                print("더보기 버튼 없음 → 종료")
                break
        print(f"리뷰 수집 완료: 총 {len(self.reviews)}개")


    def save_to_database(self):
        """
        수집한 리뷰 데이터를 CSV 파일로 저장한다.
        
        출력 디렉토리가 존재하지 않을 경우 자동으로 생성하며, CSV 파일은 UTF-8-SIG 인코딩으로 저장된다.

        CSV 파일 컬럼 순서:
        - rating
        - date
        - content
        
        Returns: None
        """
        os.makedirs(self.output_dir, exist_ok=True)
        file_path = os.path.join(self.output_dir, "reviews_ridibooks.csv")
        
        with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            for r in self.reviews:
                content = r["content"].replace("\n", " ").strip()
                writer.writerow([r["rating"], r["date"], content])
        print(f"리뷰 데이터 저장 완료 → {file_path}")

