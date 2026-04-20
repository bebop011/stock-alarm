import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_message(text):
    if not TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def main():
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
        message = "📈 오늘 아침 목표주가 [상향] 리포트\n\n"
        count = 0
        
        for row in rows:
            cols = row.find_all(['th', 'td'])
            if len(cols) >= 6:
                date_text = cols[0].text.strip()
                if '/' not in date_text:
                    continue

                raw_info = cols[1].text.strip().replace('\n', ' ').replace('\r', '')
                report_info = ' '.join(raw_info.split()) 
                opinion = cols[2].text.strip()
                
                # 4번째 칸(목표주가)만 집중적으로 봅니다.
                target_price_td = cols[3]
                target_price_text = target_price_td.text.strip()
                target_html = str(target_price_td).lower()

                is_upgraded = False
                
                # 🚨 핵심 필터: 'BUY' 글자 검사를 없애고, 오직 '빨간 화살표(상승)' 기호만 찾습니다!
                if '▲' in target_price_text or '↑' in target_price_text:
                    is_upgraded = True
                # 에프앤가이드의 빨간색 화살표 이미지 이름에는 'up'이 들어갑니다.
                elif 'up' in target_html or 'red' in target_html:
                    is_upgraded = True

                if is_upgraded:
                    message += f"▪️ {report_info}\n- 목표가: {target_price_text} (의견: {opinion})\n\n"
                    count += 1
        
        if count == 0:
            if len(rows) < 3:
                message = "⚠️ 에프앤가이드 접속 에러 (데이터를 불러오지 못했습니다)"
            else:
                message += "오늘은 목표주가가 상향된 리포트가 없습니다."
                
        if len(message) > 4000:
            message = message[:3900] + "\n... (내용이 너무 길어 생략되었습니다)"
            
        send_message(message)
        
    except Exception as e:
        send_message(f"❌ 실행 에러: {str(e)[:500]}")

if __name__ == "__main__":
    main()
