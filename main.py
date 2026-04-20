import requests
from bs4 import BeautifulSoup
import os

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_message(text):
    if not TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def main():
    url = 'https://comp.fnguide.com/SVO2/ASP/SVD_Report_Summary.asp'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
    }
    
    response = requests.get(url, headers=headers)
    # 한글 깨짐 방지를 위해 텍스트 원본(content)을 통째로 넘겨 자동 해석하게 함
    soup = BeautifulSoup(response.content, 'html.parser')

    rows = soup.find_all('tr')
    message = "📈 오늘 아침 [BUY/매수] 리포트\n\n"
    count = 0
    debug_info = ""

    for row in rows:
        cols = row.find_all(['th', 'td'])
        
        if len(cols) >= 6:
            date_text = cols[0].text.strip()
            if '/' not in date_text:
                continue

            # 비서가 읽은 첫 번째 줄의 데이터를 원인 분석(디버그)용으로 저장해 둠
            if not debug_info:
                debug_info = f"- 원본날짜: {date_text}\n- 투자의견: {cols[2].text.strip()}\n- 목표가구조: {str(cols[3])[:100]}"

            raw_info = cols[1].text.strip().replace('\n', ' ').replace('\r', '')
            report_info = ' '.join(raw_info.split()) 
            opinion = cols[2].text.strip()
            target_price = cols[3].text.strip()

            # 일단 '상향' 기호 찾는 건 포기! 'BUY'나 '매수'면 전부 가져오기
            if 'BUY' in opinion.upper() or '매수' in opinion:
                message += f"▪️ {report_info}\n- 목표가: {target_price} (의견: {opinion})\n\n"
                count += 1

    # 만약 하나도 못 찾았다면, 비서가 본 화면을 그대로 보고하도록 함
    if count == 0:
        message = "⚠️ 조건에 맞는 리포트가 없습니다.\n\n"
        message += "🛠️ [비서의 눈에 보이는 화면] 🛠️\n"
        message += f"- 웹사이트에서 찾아낸 표의 줄 수: {len(rows)}줄\n"
        message += f"- 비서가 읽은 첫 번째 종목 텍스트:\n{debug_info if debug_info else '데이터가 텅 비어있음 (사이트에서 로봇을 완벽히 차단함)'}"
    else:
        message += f"💡 (원인 파악을 위해 당분간 상향/하향 상관없이 BUY 리포트를 모두 가져옵니다.)"

    if len(message) > 4000:
        message = message[:3900] + "\n... (내용이 너무 길어 생략되었습니다)"

    send_message(message)

if __name__ == "__main__":
    main()
