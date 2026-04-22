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

    # 가상 브라우저 설정 (봇 탐지 우회 옵션 추가)
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('window-size=1920x1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled') # 봇 차단 방어막 해제
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        url = 'https://wts.ls-sec.co.kr/#0018'
        driver.get(url)
        
        target_end_time = kst_now.replace(hour=8, minute=55, second=0, microsecond=0)
        # 지금 시간이 8시 55분이 넘었다면, 바로 1번만 돌고 끝내도록 시간 조정
        if kst_now >= target_end_time:
            target_end_time = kst_now + timedelta(minutes=1)
            
        while True:
            # 💡 사이트가 무거우므로 로딩 시간을 15초로 넉넉하게 줍니다.
            time.sleep(15) 
            
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            seen_reports = set()
            count = 0
            message = f"💡 {kst_now.strftime('%m월 %d일')} LS증권 [주요보고서]\n\n"
            
            # 💡 무적 파싱 로직: HTML 칸막이를 다 부수고, 오직 '순서대로 나열된 글자들'만 뽑아옵니다.
            strings = list(soup.stripped_strings)
            
            for i, text in enumerate(strings):
                # 조건 1: 글자에 '[주요보고서]'가 있고, 본문 내용이 아니라 제목일 정도로 짧을 것 (200자 이내)
                if '[주요보고서]' in text and len(text) < 200:
                    title = text.strip()
                    
                    # 조건 2: 찾은 제목의 앞뒤로 15개의 글자 덩어리를 긁어모아 '동네(Neighborhood)'를 만듭니다.
                    start_idx = max(0, i - 15)
                    end_idx = min(len(strings), i + 15)
                    neighborhood = " ".join(strings[start_idx:end_idx])
                    
                    # 조건 3: 그 동네 안에 '오늘 날짜'가 떨어져 있으면 무조건 오늘 자 리포트가 맞습니다!
                    if today_str in neighborhood:
                        if title not in seen_reports:
                            seen_reports.add(title)
                            message += f"▪️ {title}\n\n"
                            count += 1
            
            current_kst = datetime.utcnow() + timedelta(hours=9)
            
            if count > 0:
                send_message(message)
                break
                
            elif current_kst >= target_end_time:
                all_text = soup.get_text()
                message += "8시 55분까지 새로고침하며 기다렸으나 오늘 자 주요보고서를 찾지 못했습니다.\n"
                # 만약 화면에 오늘 날짜 자체가 없었다면, 리포트가 안 올라왔거나 로딩이 덜 된 것입니다.
                if today_str not in all_text:
                    message += f"(디버그: 화면에서 {today_str} 날짜 자체를 찾지 못했습니다.)"
                send_message(message)
                break
                
            else:
                time.sleep(60)
                driver.refresh()
                
        driver.quit()
        
    except Exception as e:
        send_message(f"❌ LS증권 수집 에러: {str(e)[:500]}")

if __name__ == "__main__":
    main()
