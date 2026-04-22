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

# 💡 [핵심 1] 텔레그램 화질 압축을 피하기 위해 '문서(Document)' API를 사용합니다.
def send_document(file_path, caption=""):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
    try:
        with open(file_path, 'rb') as doc:
            # files={"document": doc} 로 변경하여 원본 화질을 100% 유지
            requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"document": doc})
    except Exception as e:
        send_message(f"📁 파일 전송 에러: {e}")

def main():
    kst_now = datetime.utcnow() + timedelta(hours=9)
    today_str = kst_now.strftime('%Y.%m.%d') 

    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    # 💡 [핵심 2] 비서의 모니터 해상도 자체를 1.5배 선명하게(Retina) 강제 세팅합니다.
    chrome_options.add_argument('force-device-scale-factor=1.5') 
    
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
            time.sleep(10)
            
            try:
                tab_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '보고서짱')]"))
                )
                driver.execute_script("arguments[0].click();", tab_element)
                time.sleep(5)
            except:
                pass
            
            report_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '[주요보고서]')]")
            
            for el in report_elements:
                try:
                    parent_text = el.find_element(By.XPATH, "./../../../../..").text
                except:
                    parent_text = el.text
                    
                if today_str in parent_text or today_str in el.text:
                    try:
                        driver.execute_script("arguments[0].click();", el)
                        time.sleep(8)
                        
                        driver.set_window_size(1200, 5000)
                        time.sleep(2)
                        
                        screenshot_path = "report_detail.png"
                        driver.save_screenshot(screenshot_path)
                        
                        # 사진 대신 원본 무손실 '파일'로 전송합니다.
                        send_document(screenshot_path, f"💡 {kst_now.strftime('%m월 %d일')} LS증권 [주요보고서] 고화질 원본입니다.")
                        found_and_sent = True
                        break
                    except Exception as inner_e:
                        print("클릭 또는 캡처 중 에러:", inner_e)
                        continue
            
            current_kst = datetime.utcnow() + timedelta(hours=9)
            
            if found_and_sent:
                break
                
            elif current_kst >= target_end_time:
                screenshot_path = "debug_screenshot.png"
                driver.save_screenshot(screenshot_path)
                message = "오늘 자 주요보고서를 찾지 못했습니다.\n\n📸 봇이 마지막으로 확인한 화면 사진을 첨부합니다."
                send_document(screenshot_path, message)
                break
                
            else:
                time.sleep(30)
                driver.refresh()
                
        driver.quit()
        
    except Exception as e:
        send_message(f"❌ LS증권 수집 에러: {str(e)[:500]}")

if __name__ == "__main__":
    main()
