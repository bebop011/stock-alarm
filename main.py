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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find('table')
    if not table:
        send_message("⚠️ 에프앤가이드에서 데이터를 불러오지 못했습니다. (차단 가능성)")
        return

    # 표의 데이터 행(tr)을 모두 가져옵니다.
    rows = table.find('tbody').find_all('tr')
    message = "📈 오늘 아침 목표주가 [상향/매수] 리포트\n\n"
    count = 0

    for row in rows:
        cols = row.find_all('td')
        
        # 에프앤가이드 표 구조: [0]일자, [1]종목명/요약, [2]투자의견, [3]목표주가, [4]전일종가, [5]제공처
        if len(cols) >= 4:
            # 1. 종목명과 리포트 요약 내용 깔끔하게 정리 (줄바꿈 없애기)
            raw_info = cols[1].text.strip().replace('\n', ' ').replace('\r', '')
            report_info = ' '.join(raw_info.split()) 
            
            # 2. 투자의견 (BUY, 매수 등)
            opinion = cols[2].text.strip()
            
            # 3. 목표주가
            target_price = cols[3].text.strip()

            # --- 조건 검사 ---
            is_target = False
            
            # 조건 A: 투자의견이 'BUY' 거나 '매수'인 경우
            if 'BUY' in opinion.upper() or '매수' in opinion:
                is_target = True
                
            # 조건 B: 목표주가에 '상향(빨간 화살표)' 이미지 아이콘이 있는 경우
            up_icon = cols[3].find('img')
            if up_icon and 'up' in up_icon.get('src', '').lower():
                is_target = True

            # 두 조건 중 하나라도 만족하면 텔레그램 메시지에 추가
            if is_target:
                message += f"▪️ {report_info}\n- 목표가: {target_price} / 의견: {opinion}\n\n"
                count += 1

    if count == 0:
        message += "오늘은 목표주가 상향 리포트가 없습니다."

    # 메시지가 너무 길면 텔레그램에서 오류가 날 수 있으므로 안전장치 추가
    if len(message) > 4000:
        message = message[:3900] + "\n\n... (내용이 너무 길어 생략되었습니다)"

    send_message(message)

if __name__ == "__main__":
    main()
