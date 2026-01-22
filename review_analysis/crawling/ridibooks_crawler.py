from review_analysis.crawling.base_crawler import BaseCrawler

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import time
import os
import csv
from typing import List, Dict, Union


class RidiBooksCrawler(BaseCrawler):
    def __init__(self, output_dir: str):
        super().__init__(output_dir)
        self.driver = None
        self.reviews: List[Dict[str, Union[str, int]]] = []
        
    def start_browser(self):
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
        리디북스 상품 리뷰를 '더보기 버튼' 기반으로 수집한다.
        (별점, 날짜, 리뷰 내용)
        """
        product_url = "https://ridibooks.com/books/1648000309"
        target_count=500

        # 1️⃣ 상품 페이지 접속
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
            
            # 3️⃣ 더보기 버튼 클릭
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
                print("❌ 더보기 버튼 없음 → 종료")
                break
        print(f"✅ 리뷰 수집 완료: 총 {len(self.reviews)}개")


    def save_to_database(self):
        """
        수집한 리뷰 데이터를 CSV 파일로 저장한다.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        file_path = os.path.join(self.output_dir, "reviews_ridibooks.csv")
        
        with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            for r in self.reviews:
                content = r["content"].replace("\n", " ").strip()
                writer.writerow([r["rating"], r["date"], content])
        print(f"💾 리뷰 데이터 저장 완료 → {file_path}")

if __name__ == "__main__":
    crawler = RidiBooksCrawler(output_dir="database")
    crawler.start_browser()
    crawler.scrape_reviews()
    crawler.save_to_database()
