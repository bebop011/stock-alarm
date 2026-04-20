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
    # 🚀 가상 크롬 브라우저 설정 (백그라운드에서 몰래 실행)
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('window-size=1920x1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
    
    try:
        # 가상 브라우저 설치 및 실행
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 다시 에프앤가이드로 진입!
        url = 'https://comp.fnguide.com/SVO2/ASP/SVD_Report_Summary.asp'
        driver.get(url)
        
        # 사이트가 완전히 켜질 때까지 사람처럼 3초 대기
        time.sleep(3)
        
        # 켜진 브라우저의 화면 HTML을 통째로 긁어오기
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # 브라우저 닫기
        driver.quit()
        
        rows = soup.find_all('tr')
        message = "📈 오늘 아침 목표주가 [상향] 리포트 (가상 브라우저 우회 성공!)\n\n"
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
                target_price_td = cols[3]
                target_price_text = target_price_td.text.strip()
                target_html = str(target_price_td).lower()

                is_upgraded = False
                
                # 상향, BUY, 매수, 빨간 화살표 기호 모두 잡아내기
                if '상향' in report_info or 'BUY' in opinion.upper() or '매수' in opinion:
                    is_upgraded = True
                elif '▲' in target_price_text or '↑' in target_price_text:
                    is_upgraded = True
                elif 'up' in target_html or 'red' in target_html or '상향' in target_html:
                    is_upgraded = True

                if is_upgraded:
                    message += f"▪️ {report_info}\n- 목표가: {target_price_text} (의견: {opinion})\n\n"
                    count += 1
        
        if count == 0:
            if len(rows) < 3:
                message = "⚠️ 에프앤가이드가 가상 브라우저까지 차단했습니다. 보안이 매우 강력합니다."
            else:
                message += "오늘은 조건에 맞는 리포트가 없습니다."
                
        if len(message) > 4000:
            message = message[:3900] + "\n... (내용이 너무 길어 생략되었습니다)"
            
        send_message(message)
        
    except Exception as e:
        send_message(f"❌ 가상 브라우저 실행 에러: {str(e)[:500]}")

if __name__ == "__main__":
    main()
