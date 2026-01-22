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
        # 타입 힌트 추가 (mypy 오류 방지)
        self.reviews: List[Dict[str, Union[str, int]]] = []
        
    def start_browser(self):
        """
        크롬 브라우저를 실행합니다.
        """
        try:
            options = Options()
            # 필요 시 headless 모드 사용 가능 (현재는 주석 처리)
            # options.add_argument("--headless") 
            options.add_argument("--disable-gpu")
            options.add_argument("--lang=ko-KR")
            options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36")
            
            options.add_argument("--window-size=1200,900")
            
            self.driver = webdriver.Chrome(options=options)
        except Exception as e:
            print(f"❌ 브라우저 실행 중 오류 발생: {e}")
            self.driver = None
    
    def scrape_reviews(self):
        """
        리디북스 상품 리뷰를 '더보기 버튼' 기반으로 수집한다.
        (별점, 날짜, 리뷰 내용)
        """
        # [중요] 브라우저가 안 켜져 있으면 여기서 실행!
        if self.driver is None:
            self.start_browser()

        # 그래도 안 켜졌으면(설치 문제 등) 중단
        if self.driver is None:
            print("❌ 오류: 브라우저가 실행되지 않아 크롤링을 중단합니다.")
            return

        product_url = "https://ridibooks.com/books/1648000309"
        target_count = 685  # 목표 수집 개수

        try:
            print(f"🚀 리디북스 이동 중: {product_url}")
            self.driver.get(product_url)
            time.sleep(5)
            
            self.reviews = []
            seen_reviews = set()
            
            while len(self.reviews) < target_count:
                # 리뷰 리스트 가져오기
                review_items = self.driver.find_elements(By.CSS_SELECTOR, "li")
                
                if not review_items:
                    time.sleep(1)
                    continue

                for li in review_items:
                    try:
                        # 별점 (SVG 개수로 파악)
                        stars = li.find_elements(By.CSS_SELECTOR,"div.rigrid-16snxvd svg")
                        rating = sum(1 for star in stars if "5pz" in star.get_attribute("class"))
                        
                        # 별점이 0이면 리뷰가 아닐 확률이 높음
                        if rating == 0:
                            continue
                        
                        # 리뷰 내용
                        try:
                            content = li.find_element(By.CSS_SELECTOR,"p.rigrid-d7duv1").text.strip()
                        except:
                            continue # 내용 없으면 스킵

                        # 날짜
                        try:
                            date = li.find_element(By.CSS_SELECTOR,"div.rigrid-1gtkt0l > div").text.strip()
                        except:
                            date = "2020.01.01" # 예외 처리
                        
                        # 중복 방지 키
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
            
                # 더보기 버튼 클릭 로직
                try:
                    more_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.rigrid-15zefso"))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", more_btn)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", more_btn)
                    time.sleep(3)
                except Exception:
                    print("⚠️ 더보기 버튼 없음(또는 끝) → 수집 종료")
                    break
            
            print(f"✅ 리디북스 최종 수집 완료: 총 {len(self.reviews)}개")

        except Exception as e:
            print(f"❌ 크롤링 중 에러 발생: {e}")

    def save_to_database(self):
        """
        수집한 리뷰 데이터를 CSV 파일로 저장한다.
        """
        if not self.reviews:
            print("⚠️ 저장할 데이터가 없습니다.")
            return

        os.makedirs(self.output_dir, exist_ok=True)
        file_path = os.path.join(self.output_dir, "reviews_ridibooks.csv")
        
        try:
            with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                # 헤더 없이 데이터만 저장 (필요하면 writerow(['rating','date','content']) 추가)
                for r in self.reviews:
                    # 내용에 줄바꿈이 있으면 한 줄로 변환
                    content = str(r["content"]).replace("\n", " ").strip()
                    writer.writerow([r["rating"], r["date"], content])
            print(f"💾 저장 완료: {file_path}")
        except Exception as e:
            print(f"❌ 저장 실패: {e}")

if __name__ == "__main__":
    crawler = RidiBooksCrawler(output_dir="database")
    crawler.start_browser()
    crawler.scrape_reviews()
    crawler.save_to_database()