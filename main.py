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
    # 💡 한국 시간(KST) 오늘 날짜 구하기 (형식: YY/MM/DD)
    kst_now = datetime.utcnow() + timedelta(hours=9)
    today_str = kst_now.strftime('%y/%m/%d')

    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('window-size=1920x1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        url = 'https://comp.fnguide.com/SVO2/ASP/SVD_Report_Summary.asp'
        driver.get(url)
        time.sleep(3)
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        driver.quit()
        
        rows = soup.find_all('tr')
        message = f"📈 {kst_now.strftime('%m월 %d일')} 목표주가 [상향] 리포트\n\n"
        count = 0
        seen_stocks = set()
        
        for row in rows:
            cols = row.find_all(['th', 'td'])
            if len(cols) >= 6:
                date_text = cols[0].text.strip()
                
                # 🚨 핵심 필터: 표의 날짜가 '오늘 날짜'가 아니면 무조건 건너뜁니다!
                if date_text != today_str:
                    continue

                raw_info = cols[1].text.strip().replace('\n', ' ').replace('\r', '')
                report_info = ' '.join(raw_info.split()) 
                stock_name = report_info.split('-')[0].strip()
                
                opinion = cols[2].text.strip()
                target_price_td = cols[3]
                target_price_text = target_price_td.text.strip()
                target_html = str(target_price_td).lower()

                is_upgraded = False
                
                if '▲' in target_price_text or '↑' in target_price_text:
                    is_upgraded = True
                elif 'up' in target_html or 'red' in target_html:
                    is_upgraded = True

                if is_upgraded:
                    if stock_name in seen_stocks:
                        continue
                    seen_stocks.add(stock_name)
                    message += f"▪️ {report_info}\n- 목표가: {target_price_text} (의견: {opinion})\n\n"
                    count += 1
        
        if count == 0:
            message += "아직 오늘 자(상향) 리포트가 올라오지 않았거나 조건에 맞는 종목이 없습니다."
                
        if len(message) > 4000:
            message = message[:3900] + "\n... (생략)"
            
        send_message(message)
        
    except Exception as e:
        send_message(f"❌ 실행 에러: {str(e)[:500]}")

if __name__ == "__main__":
    main()
