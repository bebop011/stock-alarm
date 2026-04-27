import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_message(text):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def send_photo(photo_path, caption=""):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": photo})
    except Exception as e:
        send_message(f"📷 사진 전송 에러: {e}")

def main():
    kst_now = datetime.utcnow() + timedelta(hours=9)
    # 날짜 포맷 2가지 준비 (26/04/27 또는 2026/04/27 모두 잡아내기)
    today_yymmdd = kst_now.strftime('%y/%m/%d')
    today_yyyymmdd = kst_now.strftime('%Y/%m/%d')

    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('window-size=1920x1080')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(180)
        
        url = 'https://comp.fnguide.com/SVO2/ASP/SVD_Report_Summary.asp'
        
        try:
            driver.get(url)
        except Exception:
            send_message(f"⚠️ 에프앤가이드 접속 지연 발생(180초 초과).")
            return

        # 💡 [핵심 보완] 사이트 껍데기만 열린 게 아니라, 실제 데이터(표)가 화면에 뜰 때까지 끈질기게 기다립니다.
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table tr td"))
            )
            time.sleep(5) # 데이터가 뜬 후 완전히 렌더링 될 때까지 5초 추가 대기
        except:
            driver.save_screenshot("fnguide_debug.png")
            send_photo("fnguide_debug.png", "⚠️ 에프앤가이드 데이터(표)를 불러오지 못했습니다. 봇이 본 화면입니다.")
            driver.quit()
            return
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        rows = soup.find_all('tr')
        message = f"📈 {kst_now.strftime('%m월 %d일')} 에프앤가이드 [상향] 리포트\n\n"
        count = 0
        seen_stocks = set()
        
        first_date_seen = "없음"
        
        for row in rows:
            cols = row.find_all(['th', 'td'])
            if len(cols) >= 6:
                date_text = cols[0].text.strip()
                
                # 리포트 최상단의 날짜를 기록
                if first_date_seen == "없음" and date_text and ("/" in date_text or "-" in date_text):
                    first_date_seen = date_text
                
                # 오늘 날짜 필터링 (두 가지 포맷 모두 대응)
                if today_yymmdd not in date_text and today_yyyymmdd not in date_text:
                    continue

                raw_info = cols[1].text.strip().replace('\n', ' ').replace('\r', '')
                report_info = ' '.join(raw_info.split()) 
                stock_name = report_info.split('-')[0].strip()
                
                opinion = cols[2].text.strip()
                target_price_td = cols[3]
                target_price_text = target_price_td.text.strip()
                target_html = str(target_price_td).lower()

                # '상향' 조건 체크
                is_upgraded = False
                if '▲' in target_price_text or '↑' in target_price_text or 'up' in target_html or 'red' in target_html:
                    is_upgraded = True

                if is_upgraded:
                    if stock_name in seen_stocks: continue
                    seen_stocks.add(stock_name)
                    message += f"▪️ {report_info}\n- 목표가: {target_price_text} (의견: {opinion})\n\n"
                    count += 1
        
        # 💡 [핵심 보완] 상향 리포트가 없다고 판단되면 핑계 대지 말고 스크린샷을 찍어 보냅니다.
        if count == 0:
            message += f"아직 오늘 자 상향 리포트가 없거나 조건에 맞는 종목이 없습니다.\n(최상단 날짜: [{first_date_seen}])"
            driver.save_screenshot("fnguide_empty.png")
            send_photo("fnguide_empty.png", message)
        else:
            send_message(message)
            
        driver.quit()
        
    except Exception as e:
        send_message(f"❌ 에프앤가이드 실행 에러: {str(e)[:500]}")

if __name__ == "__main__":
    main()
