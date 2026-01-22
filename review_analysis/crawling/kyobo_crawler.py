from typing import List, Optional # [추가] 타입 힌트용 모듈
from review_analysis.crawling.base_crawler import BaseCrawler
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd # type: ignore
import time
import os
import re

class KyoboCrawler(BaseCrawler):
    def __init__(self, output_dir: str):
        super().__init__(output_dir)
        # 달러구트 꿈 백화점 1 
        self.target_url = "https://product.kyobobook.co.kr/detail/S000001835614"
        self.driver: Optional[webdriver.Chrome] = None 
        self.data: List[List[str]] = [] 

    def start_browser(self):
        options = webdriver.ChromeOptions()
        # 봇 탐지 방지
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()

    def scrape_reviews(self):
        print("크롤링 시작")
        self.start_browser()
        if self.driver: # driver가 None이 아님을 확인
            self.driver.get(self.target_url)
        time.sleep(3)
        
        if self.driver:
            # 1. 리뷰 섹션 이동
            self.driver.execute_script("window.scrollTo(0, 1000);") 
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, 2500);")
            time.sleep(2)

            # 2. 탭 클릭
            try:
                tabs = self.driver.find_elements(By.XPATH, "//li[contains(., 'Klover')] | //a[contains(., 'Klover')]")
                for tab in tabs:
                    try: self.driver.execute_script("arguments[0].click();", tab); time.sleep(1)
                    except: pass
            except: pass

        page_num = 1
        
        while len(self.data) < 500:
            if not self.driver: break
            time.sleep(1.5)
            
            # 리뷰 덩어리 찾기
            review_elements = self.driver.find_elements(By.CSS_SELECTOR, ".comment_list .comment_item, li.item_publish")
            
            # print(f"[{page_num}페이지] 발견된 리뷰: {len(review_elements)}개")
            new_cnt = 0
            
            for review in review_elements:
                if len(self.data) >= 500: break
                try:
                    # (1) 내용 추출 
                    content = ""
                    try:
                        content = review.find_element(By.CSS_SELECTOR, ".comment_text").text.strip()
                    except:
                        try: content = review.find_element(By.CSS_SELECTOR, ".txt_comment").text.strip()
                        except: pass
                    
                    if not content: continue

                    # (2) 날짜 추출 (202X.XX.XX 형식)
                    date = ""
                    try: 
                        info_items = review.find_elements(By.CSS_SELECTOR, "span.info_item")
                        for item in info_items:
                            text = item.text.strip()
                            if re.match(r'^\d{4}\.\d{2}\.\d{2}$', text): 
                                date = text
                                break
                    except: pass
                    
                    if not date:
                         match = re.search(r'\d{4}[.-]\d{2}[.-]\d{2}', review.text)
                         date = match.group() if match else "2024.01.21"

                    # (3) 별점 추출 (width 스타일)
                    rating = "4" 
                    try:
                        star_elem = review.find_element(By.XPATH, ".//*[contains(@style, 'width')]")
                        style_attr = star_elem.get_attribute("style") 
                        if "100%" in style_attr: rating = "5"
                        elif "75%" in style_attr: rating = "4"
                        elif "50%" in style_attr: rating = "3"
                        elif "25%" in style_attr: rating = "2"
                    except:
                        if "5점" in review.text: rating = "5"
                        elif "3점" in review.text: rating = "3"

                    # 저장
                    self.data.append([rating, date, content])
                    new_cnt += 1
                        
                except: continue
            
            print(f"누적: {len(self.data)}/500")
            
            if len(self.data) >= 500: break

            # 다음 페이지
            try:
                next_btns = self.driver.find_elements(By.CSS_SELECTOR, "button.btn_page.next, a.btn_next")
                clicked = False
                for btn in next_btns:
                    if btn.is_displayed() and btn.is_enabled():
                        self.driver.execute_script("arguments[0].click();", btn)
                        clicked = True
                        break
                if clicked:
                    page_num += 1
                    time.sleep(2)
                else:
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(1)
                    self.driver.execute_script("window.scrollTo(0, 2500);")
            except: pass

        print(f"500개 수집 완료")
        if self.driver:
            self.driver.quit()

    def save_to_database(self):
        if not os.path.exists(self.output_dir): os.makedirs(self.output_dir)
        df = pd.DataFrame(self.data, columns=['rating', 'date', 'content'])
        file_path = f"{self.output_dir}/reviews_kyobo.csv"
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        print(f"저장 완료: {file_path}")