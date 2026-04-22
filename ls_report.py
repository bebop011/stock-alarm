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
    # 1. 한국 시간(KST) 오늘 날짜 구하기 (예: 2026.04.22)
    kst_now = datetime.utcnow() + timedelta(hours=9)
    today_str = kst_now.strftime('%Y.%m.%d') 

    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('window-size=1920x1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        url = 'https://wts.ls-sec.co.kr/#0018'
        driver.get(url)
        
        # 💡 마감 시간 설정 (아침 8시 55분)
        target_end_time = kst_now.replace(hour=8, minute=55, second=0, microsecond=0)
        if kst_now >= target_end_time:
            target_end_time = kst_now + timedelta(minutes=1)
            
        while True:
            time.sleep(12) # 페이지 로딩 대기 시간 소폭 증가 (12초)
            
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            seen_reports = set()
            count = 0
            message = f"💡 {kst_now.strftime('%m월 %d일')} LS증권 [주요보고서]\n\n"
            
            # 💡 수정 포인트: 모든 리스트 항목(li)을 가져와서 그 안에서 날짜와 제목을 동시에 체크합니다.
            items = soup.find_all(['li', 'div', 'tr']) 
            
            for item in items:
                text_content = item.get_text(separator=' ', strip=True)
                
                # '오늘 날짜'와 '[주요보고서]'가 한 칸 안에 동시에 들어있는지 확인
                if today_str in text_content and '[주요보고서]' in text_content:
                    # 제목 부분만 깔끔하게 추출 (줄바꿈 등 제거)
                    lines = [line.strip() for line in text_content.splitlines() if '[주요보고서]' in line]
                    for title in lines:
                        if title not in seen_reports and len(title) > 10:
                            seen_reports.add(title)
                            message += f"▪️ {title}\n\n"
                            count += 1
            
            current_kst = datetime.utcnow() + timedelta(hours=9)
            
            # 드디어 찾았을 때
            if count > 0:
                send_message(message)
                break
                
            # 시간 다 됐는데 못 찾았을 때
            elif current_kst >= target_end_time:
                # 💡 디버깅 힌트 추가: 봇이 마지막으로 읽은 화면에 어떤 날짜들이 있었는지 알려줍니다.
                all_text = soup.get_text()
                message += "8시 55분까지 새로고침하며 기다렸으나 오늘 자 주요보고서를 찾지 못했습니다.\n"
                if today_str not in all_text:
                    message += f"(참고: 현재 사이트 화면에 {today_str} 날짜 자체가 보이지 않습니다.)"
                send_message(message)
                break
                
            # 아직 시간 남았으면 새로고침 후 재시도
            else:
                time.sleep(60)
                driver.refresh()
                
        driver.quit()
        
    except Exception as e:
        send_message(f"❌ LS증권 수집 에러: {str(e)[:500]}")

if __name__ == "__main__":
    main()
