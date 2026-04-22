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
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# 💡 텔레그램으로 현장 사진을 보내는 새로운 기능
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
    today_str = kst_now.strftime('%Y.%m.%d') 

    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('window-size=1920x1080')
    
    # 🕵️ 강력한 봇 탐지 우회 옵션들 (사람인 척 위장)
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 브라우저에 봇 식별자(webdriver) 제거 스크립트 실행
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })
        
        url = 'https://wts.ls-sec.co.kr/#0018'
        driver.get(url)
        
        # 테스트를 위해 마감 시간을 아주 짧게(1분 뒤) 잡아 바로 결과를 보게 합니다.
        target_end_time = kst_now + timedelta(minutes=1)
            
        while True:
            time.sleep(15) 
            
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            seen_reports = set()
            count = 0
            message = f"💡 {kst_now.strftime('%m월 %d일')} LS증권 [주요보고서]\n\n"
            
            strings = list(soup.stripped_strings)
            
            for i, text in enumerate(strings):
                if '[주요보고서]' in text and len(text) < 200:
                    title = text.strip()
                    start_idx = max(0, i - 15)
                    end_idx = min(len(strings), i + 15)
                    neighborhood = " ".join(strings[start_idx:end_idx])
                    
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
                # 🚨 시간 초과 시, 현재 봇이 보고 있는 화면을 사진으로 찍습니다!
                screenshot_path = "debug_screenshot.png"
                driver.save_screenshot(screenshot_path)
                
                message += "오늘 자 주요보고서를 찾지 못했습니다.\n\n📸 봇이 마지막으로 확인한 화면 사진을 첨부합니다. (보안 차단 여부 확인용)"
                
                # 메시지와 함께 사진을 텔레그램으로 발송!
                send_photo(screenshot_path, message)
                break
                
            else:
                time.sleep(30)
                driver.refresh()
                
        driver.quit()
        
    except Exception as e:
        send_message(f"❌ LS증권 수집 에러: {str(e)[:500]}")

if __name__ == "__main__":
    main()
