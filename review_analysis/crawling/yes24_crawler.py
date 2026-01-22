import pandas as pd
import time
import os
from typing import List, Dict, Optional, Any, cast

from bs4 import BeautifulSoup
from bs4.element import Tag

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from .base_crawler import BaseCrawler 

class Yes24Crawler(BaseCrawler):
    """
    Yes24 도서 리뷰(한줄평)를 수집하는 크롤러 클래스
    BaseCrawler를 상속받아 구현
    """
    
    def __init__(self, output_dir: str) -> None:
        """
        Yes24Crawler 인스턴스를 초기화

        Args:
            output_dir (str): 수집된 데이터(CSV)가 저장될 폴더 경로
        """
        super().__init__(output_dir)
        self.base_url: str = "https://www.yes24.com/product/goods/91065309"
        self.target_count: int = 1200
        self.driver: Optional[WebDriver] = None
        self.results: List[Dict[str, str]] = []
        
    def start_browser(self) -> None:
        """
        Selenium WebDriver를 실행하고 대상 URL로 이동
        """
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless") 
        self.driver = webdriver.Chrome(options=options)
        self.driver.get(self.base_url)
        time.sleep(2)
        
        assert self.driver is not None
        
        # 시작 후 가장 아래로
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        
        # 한줄평 구역 로딩 대기 및 이동
        try:
            target_div = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "infoset_oneCommentList"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_div)
            time.sleep(1)
        except Exception as e:
            print(f"한줄평 구역을 못 찾았습니다. (페이지 로딩 문제): {e}")

    def scrape_reviews(self) -> List[Dict[str, str]]:
        """
        실제 크롤링 진행
        """
        if self.driver is None:
            self.start_browser()
        
        assert self.driver is not None
        
        print(f"크롤링 시작 (목표: 한줄평 {self.target_count}개)")
        
        # 탭 클릭 로직
        try:
            review_tab = self.driver.find_element(By.CSS_SELECTOR, "#yDetailTabNavWrap > div > ul > li:nth-child(2) > a")
            self.driver.execute_script("arguments[0].click();", review_tab)
            time.sleep(1)
        except Exception:
            pass

        page_num: int = 1
        
        while len(self.results) < self.target_count:
            try:
                time.sleep(1.5) 
                
                if self.driver is None:
                    break

                html = self.driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                
                one_comment_zone = soup.select_one("#infoset_oneCommentList")
                
                if not isinstance(one_comment_zone, Tag):
                    print("한줄평 구역 로딩 중...")
                    time.sleep(1)
                    continue

                # 구역 안에서 리뷰 박스들 찾기
                review_boxes = one_comment_zone.select("div.cmtInfoGrp")
                
                print(f"[{page_num}페이지] 한줄평 수집 중... (발견: {len(review_boxes)}개 / 누적: {len(self.results)}개)")

                if not review_boxes and page_num > 1:
                    print("더 이상 한줄평이 없습니다.")
                    break

                for box in review_boxes:
                    try:
                        content: str = ""
                        txt_tag = box.select_one(".cmt_cont .txt")
                        
                        if isinstance(txt_tag, Tag): 
                            content = txt_tag.text.strip()
                        
                        if not content: 
                            continue 

                        date: str = ""
                        date_tag = box.select_one("div.cmt_etc em.txt_date")
                        if isinstance(date_tag, Tag): 
                            date = date_tag.text.strip()

                        rating: str = "Unknown"
                        rating_tag = box.select_one(".cmt_rating .rating")
                        
                        if isinstance(rating_tag, Tag):
                            class_val = rating_tag.get("class")
                            if isinstance(class_val, list):
                                for c in class_val:
                                    if "rating_" in c and c != "rating_on":
                                        rating = c.replace("rating_", "") 
                                        break
                        
                        content = content.replace("\n", " ").replace("\r", " ")
                        
                        self.results.append({
                            "rating": rating,
                            "date": date,
                            "content": content
                        })

                        if len(self.results) >= self.target_count:
                            print(f"목표 달성! 종료합니다.")
                            break
                    except Exception:
                        continue
                
                if len(self.results) >= self.target_count:
                    break

                try:
                    next_page_num = page_num + 1
                    css_selector_num = f"#infoset_oneCommentList .yesUI_pagenS a"
                    page_buttons: List[WebElement] = self.driver.find_elements(By.CSS_SELECTOR, css_selector_num)
                    
                    target_btn: Optional[WebElement] = None
                    for btn in page_buttons:
                        if btn.text == str(next_page_num):
                            target_btn = btn
                            break
                    
                    if target_btn:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_btn)
                        time.sleep(0.5)
                        self.driver.execute_script("arguments[0].click();", target_btn)
                        page_num += 1
                    else:
                        css_arrow = "#infoset_oneCommentList a.bgYUI.next"
                        print(f"[{next_page_num}]번 버튼 없음. 화살표(>) 이동 시도...")
                        next_arrow = self.driver.find_element(By.CSS_SELECTOR, css_arrow)
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_arrow)
                        time.sleep(0.5)
                        self.driver.execute_script("arguments[0].click();", next_arrow)
                        page_num += 1
                        
                except Exception:
                    print("더 이상 넘길 페이지가 없습니다. (완료)")
                    break

            except Exception as e:
                print(f"에러 발생: {e}")
                break

        print(f"최종 수집 완료: 총 {len(self.results)}개")
        if self.driver:
            self.driver.quit()
        return self.results
        
    def save_to_database(self) -> None:
        """
        수집된 데이터(self.results)를 CSV 파일로 저장합니다.
        """
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        if not self.results:
            print("데이터가 없습니다.")
            return

        file_name: str = "reviews_yes24.csv"
        full_path: str = os.path.join(self.output_dir, file_name)
        
        df = pd.DataFrame(self.results)
        if not df.empty:
            df = df[['rating', 'date', 'content']]
        
        df.to_csv(full_path, index=False, encoding='utf-8-sig')
        print(f"저장 완료: {full_path}")