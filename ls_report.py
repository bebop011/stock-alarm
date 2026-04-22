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
    # 한국 시간(KST) 오늘 날짜 구하기
    kst_now = datetime.utcnow() + timedelta(hours=9)
    today_str = kst_now.strftime('%Y.%m.%d') # 사진의 2026.04.22 형식

    # 가상 브라우저 옵션 설정
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('window-size=1920x1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # LS증권 리포트 페이지 접속
        url = 'https://wts.ls-sec.co.kr/#0018'
        driver.get(url)
        
        # 무거운 금융 사이트이므로 데이터가 화면에 전부 그려질 때까지 넉넉히 10초 대기
        time.sleep(10)
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        driver.quit()
        
        message = f"💡 {kst_now.strftime('%m월 %d일')} LS증권 [주요보고서]\n\n"
        
        # '[주요보고서]' 라는 텍스트가 포함된 문장들을 화면 전체에서 긁어모읍니다.
        report_elements = soup.find_all(string=lambda text: text and '[주요보고서]' in text)
        
        seen_reports = set()
        count = 0
        
        for el in report_elements:
            title = el.strip()
            # 중복 제거 및 너무 짧은 텍스트(예: 버튼 등) 제외
            if title and len(title) > 8 and title not in seen_reports:
                seen_reports.add(title)
                message += f"▪️ {title}\n\n"
                count += 1
                
        if count == 0:
            message += "아직 오늘 업데이트된 [주요보고서]가 없거나, 사이트 지연으로 불러오지 못했습니다."
            
        send_message(message)
        
    except Exception as e:
        send_message(f"❌ LS증권 수집 에러: {str(e)[:500]}")

if __name__ == "__main__":
    main()
