import os
import time
import requests
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
    today_str = kst_now.strftime('%Y.%m.%d') 

    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    # 기본 창 크기
    chrome_options.add_argument('window-size=1200x1080')
    
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })
        
        url = 'https://wts.ls-sec.co.kr/#0018'
        driver.get(url)
        
        target_end_time = kst_now.replace(hour=8, minute=55, second=0, microsecond=0)
        if kst_now >= target_end_time:
            target_end_time = kst_now + timedelta(minutes=1)
            
        found_and_sent = False
            
        while True:
            time.sleep(10) # 사이트 로딩 대기
            
            # 1. '보고서짱' 탭 클릭
            try:
                tab_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '보고서짱')]"))
                )
                driver.execute_script("arguments[0].click();", tab_element)
                time.sleep(5) # 탭 이동 후 목록 뜰 때까지 대기
            except:
                pass
            
            # 2. '[주요보고서]' 글자가 있는 모든 항목 찾기
            report_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '[주요보고서]')]")
            
            for el in report_elements:
                try:
                    # 해당 글자 주변(부모 태그)의 텍스트를 긁어서 '오늘 날짜'가 있는지 확인
                    parent_text = el.find_element(By.XPATH, "./../../../../..").text
                except:
                    parent_text = el.text
                    
                # 3. 오늘 날짜가 맞다면 클릭해서 상세 페이지 열기!
                if today_str in parent_text or today_str in el.text:
                    try:
                        driver.execute_script("arguments[0].click();", el)
                        time.sleep(8) # 상세 이미지가 팝업이나 화면에 완전히 뜰 때까지 넉넉히 8초 대기
                        
                        # 💡 4. 세로로 아주 긴 인포그래픽이 잘리지 않도록 브라우저 창 길이를 5000픽셀로 쭉 늘립니다!
                        driver.set_window_size(1200, 5000)
                        time.sleep(2) # 화면이 늘어난 후 렌더링 될 시간 부여
                        
                        # 💡 5. 화면 전체를 스크린샷 찰칵!
                        screenshot_path = "report_detail.png"
                        driver.save_screenshot(screenshot_path)
                        
                        send_photo(screenshot_path, f"💡 {kst_now.strftime('%m월 %d일')} LS증권 [주요보고서] 상세본입니다.")
                        found_and_sent = True
                        break # 전송 성공했으니 반복문 탈출
                    except Exception as inner_e:
                        print("클릭 또는 캡처 중 에러:", inner_e)
                        continue
            
            current_kst = datetime.utcnow() + timedelta(hours=9)
            
            # 전송에 성공했으면 봇 퇴근!
            if found_and_sent:
                break
                
            # 시간 다 됐는데 못 찾았을 때
            elif current_kst >= target_end_time:
                screenshot_path = "debug_screenshot.png"
                driver.save_screenshot(screenshot_path)
                message = "오늘 자 주요보고서를 찾지 못했습니다.\n\n📸 봇이 마지막으로 확인한 화면 사진을 첨부합니다."
                send_photo(screenshot_path, message)
                break
                
            # 아직 시간 남았으면 새로고침 후 재시도
            else:
                time.sleep(30)
                driver.refresh()
                
        driver.quit()
        
    except Exception as e:
        send_message(f"❌ LS증권 수집 에러: {str(e)[:500]}")

if __name__ == "__main__":
    main()
