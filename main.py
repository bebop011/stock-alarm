import requests
from bs4 import BeautifulSoup
import os

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_message(text):
    if not TOKEN or not CHAT_ID:
        print("❌ 에러: 텔레그램 토큰이나 CHAT_ID가 없습니다. alarm.yml 설정을 확인하세요.")
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
    
    # 봇 차단 방지를 위해 일반 브라우저(크롬)인 척 위장
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

    rows = table.find('tbody').find_all('tr')
    message = "📈 오늘 아침 목표주가 [상향/매수] 리포트\n\n"
    count = 0

    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 5:
            stock_name = cols[0].text.strip()
            title = cols[1].text.strip()
            target_price = cols[2].text.strip()
            opinion = cols[3].text.strip()

            if '상향' in opinion or 'Buy' in opinion or '매수' in opinion:
                message += f"▪️ {stock_name}\n- {title}\n- 목표가: {target_price} / 의견: {opinion}\n\n"
                count += 1

    if count == 0:
        message += "오늘은 목표주가 상향 리포트가 없습니다."

    send_message(message)

if __name__ == "__main__":
    main()
