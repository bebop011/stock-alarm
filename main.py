import requests
from bs4 import BeautifulSoup
import os

# 깃허브 금고에서 텔레그램 정보 가져오기
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def main():
    url = 'https://comp.fnguide.com/SVO2/ASP/SVD_Report_Summary.asp'
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find('table')
    if not table:
        send_message("데이터를 불러오지 못했습니다.")
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
