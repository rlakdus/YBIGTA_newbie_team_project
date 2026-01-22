from review_analysis.crawling.base_crawler import BaseCrawler

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import time
import os
import csv

class RidiBooksCrawler(BaseCrawler):
    '''
    RidiBooks 도서 리뷰를 수집하는 크롤러 클래스.
    '''
    def __init__(self, output_dir: str):
        super().__init__(output_dir)
        self.driver = None
        self.reviews: list[dict[str, str | int]] = []
        
    def start_browser(self):
        '''
        Selenium Chrome WebDriver를 초기화하고 브라우저를 실행한다.
        '''
        print("리디북스 크롤러: 브라우저 시작 중...")
        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--lang=ko-KR")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        )
        options.add_argument("--window-size=1200,900")
        
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()), 
                options=options
            )
        except Exception as e:
            print(f"브라우저 실행 실패: {e}")
            self.driver = None
    
    def scrape_reviews(self):
        if self.driver is None:
            self.start_browser()

        if self.driver is None:
            print("오류: 드라이버 초기화 실패로 크롤링을 중단합니다.")
            return

        product_url = "https://ridibooks.com/books/1648000309"
        target_count = 685

        try:
            self.driver.get(product_url)
            time.sleep(5)
            
            self.reviews = []
            seen_reviews = set()
            
            while len(self.reviews) < target_count:
                review_items = self.driver.find_elements(By.CSS_SELECTOR, "li")
                
                if not review_items:
                    time.sleep(1)
                    continue

                for li in review_items:
                    try:
                        stars = li.find_elements(By.CSS_SELECTOR,"div.rigrid-16snxvd svg")
                        rating = sum(1 for star in stars if "5pz" in star.get_attribute("class"))
                        if rating == 0:
                            continue
                        
                        content = li.find_element(By.CSS_SELECTOR,"p.rigrid-d7duv1").text.strip()
                        date = li.find_element(By.CSS_SELECTOR,"div.rigrid-1gtkt0l > div").text.strip()
                        
                        review_key = (rating, date, content)
                        if review_key in seen_reviews:
                            continue

                        seen_reviews.add(review_key)
                        self.reviews.append({
                            "rating": rating,
                            "date": date,
                            "content": content
                        })

                        if len(self.reviews) >= target_count:
                            break
                    except Exception:
                        continue
                
                print(f"현재 수집: {len(self.reviews)} / {target_count}")
                if len(self.reviews) >= target_count:
                    break

                try:
                    more_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.rigrid-15zefso"))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", more_btn)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", more_btn)
                    time.sleep(3)
                except Exception:
                    print("더보기 버튼 없음 → 종료")
                    break
            
            print(f"리디북스 수집 완료: 총 {len(self.reviews)}개")

        except Exception as e:
            print(f"크롤링 중 에러 발생: {e}")

    def save_to_database(self):
        if not self.reviews:
            return

        os.makedirs(self.output_dir, exist_ok=True)
        file_path = os.path.join(self.output_dir, "reviews_ridibooks.csv")
        
        with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            for r in self.reviews:
                content = r["content"].replace("\n", " ").strip()
                writer.writerow([r["rating"], r["date"], content])
        print(f"저장 완료: {file_path}")