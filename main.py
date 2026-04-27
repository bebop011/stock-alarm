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
    if not TOKEN or not CHAT_ID: 
        print("⚠️ 텔레그램 토큰이 없습니다.")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    # 💡 [핵심 보완] 텔레그램 글자 수 제한(4096자)을 피하기 위해 3000자씩 잘라서 전송
    max_length = 3000
    for i in range(0, len(text), max_length):
        chunk = text[i:i+max_length]
        res = requests.post(url, data={"chat_id": CHAT_ID, "text": chunk})
        print(f"💬 메시지 전송 결과: {res.status_code}")
        time.sleep(1) # 연속 전송 시 텔레그램 서버의 차단을 막기 위해 1초 대기

def send_photo(photo_path, caption=""):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            res = requests.post(url, data={"chat_id": CHAT_ID, "caption": caption[:1000]}, files={"photo": photo})
            print(f"📷 사진 전송 결과: {res.status_code}")
    except Exception as e:
        print(f"❌ 사진 전송 에러 발생: {e}")

def main():
    print("🚀 에프앤가이드 수집 시작...")
    kst_now = datetime.utcnow() + timedelta(hours=9)
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
        print(f"🌐 접속 시도 중...: {url}")
        driver.get(url)

        print("⏳ 데이터(표) 화면에 뜰 때까지 대기 (최대 30초)...")
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table tr td"))
            )
            print("✅ 표 로딩 확인 완료! 추가 5초 대기...")
            time.sleep(5)
        except Exception as e:
            print("⚠️ 30초 대기 초과: 사이트가 느리거나 구조가 변경되었습니다.")
            send_message("⚠️ 에프앤가이드 접속은 했으나 데이터를 찾지 못했습니다.")
            driver.save_screenshot("fnguide_debug.png")
            send_photo("fnguide_debug.png", "봇이 본 현재 에프앤가이드 화면입니다.")
            driver.quit()
            return
        
        print("📝 데이터 긁어오기 시작...")
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
                if first_date_seen == "없음" and date_text and ("/" in date_text or "-" in date_text):
                    first_date_seen = date_text
                
                if today_yymmdd not in date_text and today_yyyymmdd not in date_text:
                    continue

                raw_info = cols[1].text.strip().replace('\n', ' ').replace('\r', '')
                report_info = ' '.join(raw_info.split()) 
                stock_name = report_info.split('-')[0].strip()
                opinion = cols[2].text.strip()
                target_price_td = cols[3]
                target_price_text = target_price_td.text.strip()
                target_html = str(target_price_td).lower()

                is_upgraded = False
                if '▲' in target_price_text or '↑' in target_price_text or 'up' in target_html or 'red' in target_html:
                    is_upgraded = True

                if is_upgraded:
                    if stock_name in seen_stocks: continue
                    seen_stocks.add(stock_name)
                    message += f"▪️ {report_info}\n- 목표가: {target_price_text} (의견: {opinion})\n\n"
                    count += 1
        
        print(f"📊 찾은 상향 리포트 개수: {count}개 (사이트 최상단 날짜: {first_date_seen})")
        
        if count == 0:
            msg = f"아직 오늘 자 상향 리포트가 없거나 조건에 맞는 종목이 없습니다.\n(최상단 날짜: [{first_date_seen}])"
            send_message(msg)
            driver.save_screenshot("fnguide_empty.png")
            send_photo("fnguide_empty.png", "빈 화면 증거 사진입니다.")
        else:
            send_message(message)
            
        driver.quit()
        print("🏁 작업 끝!")
        
    except Exception as e:
        print(f"❌ 치명적 에러 발생: {e}")
        send_message(f"❌ 에프앤가이드 실행 에러: {str(e)[:500]}")

if __name__ == "__main__":
    main()
