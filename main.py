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
    
    # 🕵️ 완벽한 사람 위장을 위한 특급 보안 통과 헤더
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://comp.fnguide.com/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1'
    }
    
    try:
        # 타임아웃을 걸어 에러 방지
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        rows = soup.find_all('tr')
        message = "📈 오늘 아침 목표주가 [상향/매수] 리포트\n\n"
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
                
                # 상향, BUY, 매수, 빨간 화살표 등 모든 상승 조건을 꼼꼼히 체크
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
            # 또 차단당했는지, 아니면 진짜 리포트가 없는 건지 확인
            if len(rows) < 3:
                message = "⚠️ 에프앤가이드 보안 시스템에 접속이 차단되었습니다. (너무 강력한 보안)"
            else:
                message += "오늘은 조건에 맞는 리포트가 없습니다."

        if len(message) > 4000:
            message = message[:3900] + "\n... 생략"

        send_message(message)

    except Exception as e:
        send_message(f"❌ 실행 중 에러 발생: {e}")

if __name__ == "__main__":
    main()
