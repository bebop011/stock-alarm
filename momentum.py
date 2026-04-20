import yfinance as yf
import pandas as pd
import os
import requests
from datetime import datetime

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_message(text):
    if not TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

def main():
    # 데이터 수집 (SPYM:미국, EFA:선진국, AGG:채권, BIL:현금)
    tickers = ['SPYM', 'EFA', 'AGG', 'BIL']
    try:
        data = yf.download(tickers, period='2y')['Adj Close']
    except Exception as e:
        send_message(f"❌ 야후 파이낸스 데이터 수집 에러: {e}")
        return
    
    # 1. 오리지널 듀얼모멘텀 (12개월 수익률)
    odm_ret = (data.iloc[-1] / data.iloc[-252]) - 1
    spym_12m, efa_12m, bil_12m = odm_ret['SPYM'], odm_ret['EFA'], odm_ret['BIL']
    
    # 상대 모멘텀: SPYM과 EFA 중 승자 선택
    odm_winner = 'SPYM' if spym_12m > efa_12m else 'EFA'
    # 절대 모멘텀: 승자가 현금(BIL)보다 수익률이 낮으면 채권(AGG)으로 대피
    odm_final = "AGG(채권)" if odm_ret[odm_winner] < bil_12m else f"{odm_winner}(주식)"

    # 2. 가속 듀얼모멘텀 (1, 3, 6개월 평균)
    m1 = (data.iloc[-1] / data.iloc[-21]) - 1
    m3 = (data.iloc[-1] / data.iloc[-63]) - 1
    m6 = (data.iloc[-1] / data.iloc[-126]) - 1
    adm_score = (m1 + m3 + m6) / 3
    
    # SPYM, EFA, BIL 중 가장 모멘텀 점수가 높은 자산 선택
    adm_winner = adm_score[['SPYM', 'EFA', 'BIL']].idxmax()
    adm_final = "AGG(채권)" if adm_winner == 'BIL' else f"{adm_winner}(주식)"

    # 텔레그램 메시지 작성
    msg = f"📅 *{datetime.now().strftime('%Y년 %m월')} 듀얼모멘텀 리포트*\n\n"
    msg += f"✅ *오리지널(ODM):* **{odm_final}**\n"
    msg += f"- (SPYM: {spym_12m:.1%}, EFA: {efa_12m:.1%})\n\n"
    msg += f"🚀 *가속(ADM):* **{adm_final}**\n\n"
    msg += "🚩 매월 1일 기준 리밸런싱 신호입니다."

    send_message(msg)

if __name__ == "__main__":
    main()
