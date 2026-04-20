import requests
from bs4 import BeautifulSoup
import os

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_message(text):
    if not TOKEN or not CHAT_ID:
        print("❌ 에러: 텔레그램 정보가 없습니다.")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def main():
    print("🔍 에프앤가이드 데이터 수집 시작...")
    url = 'https://comp.fnguide.com/SVO2/ASP/SVD_Report_Summary.asp'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
    }
    
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    rows = soup.find_all('tr')
    message = "📈 오늘 아침 목표주가 [상향] 리포트\n\n"
    count = 0

    for row in rows:
        # 핵심 해결 포인트: '일자' 칸이 td가 아닌 th로 숨어있어서 모두 가져오도록 변경!
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
            
            # 1. 요약 글에 '상향'이라는 단어가 직접 들어간 경우
            if '상향' in report_info:
                is_upgraded = True
            # 2. 목표주가 칸에 빨간색, 화살표, up 등의 표시가 있는 경우
            elif '▲' in target_price_text or '↑' in target_price_text:
                is_upgraded = True
            elif 'up' in target_html or 'red' in target_html:
                is_upgraded = True

            if is_upgraded:
                message += f"▪️ {report_info}\n- 목표가: {target_price_text} (의견: {opinion})\n\n"
                count += 1

    if count == 0:
        message += "오늘은 목표주가 상향 리포트가 없습니다."

    if len(message) > 4000:
        message = message[:3900] + "\n\n... (내용이 너무 길어 생략되었습니다)"

    send_message(message)

if __name__ == "__main__":
    main()
