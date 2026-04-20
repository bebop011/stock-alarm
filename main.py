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
    # 타겟을 네이버 증권 리포트로 변경!
    url = 'https://finance.naver.com/research/company_list.naver'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        # 네이버 금융은 한글이 깨지지 않도록 euc-kr 인코딩을 사용합니다.
        response.encoding = 'euc-kr'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 네이버 증권 리포트 표 찾기
        table = soup.find('table', {'class': 'type_1'})
        if not table:
            send_message("⚠️ 네이버 증권에서 데이터를 불러오지 못했습니다.")
            return
            
        rows = table.find_all('tr')
        message = "📈 오늘 아침 목표주가 [매수] 리포트 (출처: 네이버 증권)\n\n"
        count = 0
        
        for row in rows:
            cols = row.find_all('td')
            
            # 네이버 표 구조: [0]종목명, [1]제목, [2]적정주가, [3]투자의견, [4]작성자, [5]제공출처, [6]등록일
            if len(cols) >= 6:
                stock_name = cols[0].text.strip()
                title = cols[1].text.strip().replace('\n', ' ').replace('\r', '')
                target_price = cols[2].text.strip()
                opinion = cols[3].text.strip()
                broker = cols[5].text.strip()
                
                # '매수' 또는 'BUY' 의견인 종목 추출
                if '매수' in opinion or 'BUY' in opinion.upper():
                    title_clean = ' '.join(title.split())
                    message += f"▪️ {stock_name} ({broker})\n- {title_clean}\n- 목표가: {target_price} (의견: {opinion})\n\n"
                    count += 1
                    
        if count == 0:
            message += "오늘은 매수 의견 리포트가 없습니다."
            
        if len(message) > 4000:
            message = message[:3900] + "\n... (내용이 너무 길어 생략되었습니다)"
            
        send_message(message)
        
    except Exception as e:
        send_message(f"❌ 실행 중 에러 발생: {e}")

if __name__ == "__main__":
    main()
