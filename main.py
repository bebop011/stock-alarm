import requests
from bs4 import BeautifulSoup
import os

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_message(text):
    if not TOKEN or not CHAT_ID:
        print("❌ 에러: 텔레그램 토큰이나 CHAT_ID가 없습니다.")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    res = requests.post(url, data={"chat_id": CHAT_ID, "text": text})
    if res.status_code != 200:
        print(f"❌ 텔레그램 전송 실패: {res.text}")
    else:
        print("✅ 텔레그램 메시지 전송 완료")

def main():
    print("🔍 에프앤가이드 데이터 수집 시작...")
    url = 'https://comp.fnguide.com/SVO2/ASP/SVD_Report_Summary.asp'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
    }
    
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    # 웹페이지에 있는 '모든' 표의 줄(tr)을 다 가져옵니다. (검색창 무시용)
    rows = soup.find_all('tr')
    
    message = "📈 오늘 아침 목표주가 [상향] 리포트\n\n"
    count = 0

    for row in rows:
        cols = row.find_all('td')
        
        # 진짜 데이터 표는 반드시 6개의 칸(td)으로 이루어져 있습니다.
        if len(cols) >= 6:
            date_text = cols[0].text.strip()
            
            # 날짜 칸에 '/' 기호가 없다면 진짜 데이터가 아니므로 건너뜁니다.
            if '/' not in date_text:
                continue

            # 종목명과 요약 내용 가져오기 (지저분한 줄바꿈 제거)
            raw_info = cols[1].text.strip().replace('\n', ' ').replace('\r', '')
            report_info = ' '.join(raw_info.split()) 
            
            opinion = cols[2].text.strip()
            
            # 4번째 칸: 목표주가
            target_price_td = cols[3]
            target_price_text = target_price_td.text.strip()
            target_html = str(target_price_td).lower() # 화살표 그림을 찾기 위해 HTML 전체를 읽음

            is_upgraded = False
            
            # 목표주가 칸에 '상향(Up)'을 의미하는 텍스트나 화살표 그림 코드가 있는지 철저하게 검사
            if '▲' in target_price_text or '↑' in target_price_text:
                is_upgraded = True
            elif 'up' in target_html or 'red' in target_html or '상향' in target_html:
                is_upgraded = True

            # 목표주가가 상향된 종목만 메시지에 추가!
            if is_upgraded:
                message += f"▪️ {report_info}\n- 목표가: {target_price_text} (의견: {opinion})\n\n"
                count += 1

    if count == 0:
        message += "오늘은 목표주가 상향 리포트가 없습니다."

    # 텔레그램 글자 수 제한 방지
    if len(message) > 4000:
        message = message[:3900] + "\n\n... (내용이 너무 길어 생략되었습니다)"

    send_message(message)

if __name__ == "__main__":
    main()
