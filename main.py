import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_message(text):
    if not TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def main():
    # 한국 시간(KST) 오늘 날짜
    kst_now = datetime.utcnow() + timedelta(hours=9)
    today_str = kst_now.strftime('%y/%m/%d')

    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('window-size=1920x1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
    
    # 💡 로딩 성능 향상을 위한 추가 옵션
    chrome_options.add_argument('--disable-gpu')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 💡 [핵심] 페이지가 뜰 때까지 기다리는 한계 시간을 180초(3분)로 늘립니다.
        driver.set_page_load_timeout(180)
        
        url = 'https://comp.fnguide.com/SVO2/ASP/SVD_Report_Summary.asp'
        
        try:
            driver.get(url)
        except Exception as e:
            send_message(f"⚠️ 에프앤가이드 접속 지연 발생(180초 초과). 잠시 후 수동으로 다시 시도해 주세요.")
            return

        # 💡 사이트가 완전히 그려지도록 충분히(15초) 기다립니다.
        time.sleep(15)
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        driver.quit()
        
        rows = soup.find_all('tr')
        message = f"📈 {kst_now.strftime('%m월 %d일')} 에프앤가이드 [상향] 리포트\n\n"
        count = 0
        seen_stocks = set()
        
        first_date_seen = "없음"
        
        for row in rows:
            cols = row.find_all(['th', 'td'])
            if len(cols) >= 6:
                date_text = cols[0].text.strip()
                if first_date_seen == "없음" and date_text and "/" in date_text:
                    first_date_seen = date_text
                
                # 날짜 비교 필터
                if today_str not in date_text:
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
        
        if count == 0:
            message += f"아직 오늘 자 상향 리포트가 없거나 조건에 맞는 종목이 없습니다.\n(최상단 날짜: [{first_date_seen}])"
                
        send_message(message)
        
    except Exception as e:
        send_message(f"❌ 에프앤가이드 실행 에러: {str(e)[:500]}")

if __name__ == "__main__":
    main()
