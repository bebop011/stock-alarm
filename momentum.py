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
    tickers = ['SPYM', 'EFA', 'AGG', 'BIL']
    data = pd.DataFrame()
    
    try:
        for t in tickers:
            ticker_obj = yf.Ticker(t)
            df = ticker_obj.history(period='2y')
            if df.empty:
                raise Exception(f"'{t}' 종목 데이터를 못 불렀습니다.")
            data[t] = df['Close']
        data = data.dropna()
    except Exception as e:
        send_message(f"❌ 야후 파이낸스 데이터 수집 에러: {e}")
        return
        
    if len(data) < 252:
        send_message("❌ 에러: 데이터가 부족합니다.")
        return

    # 1. 오리지널 듀얼모멘텀
    odm_ret = (data.iloc[-1] / data.iloc[-252]) - 1
    spym_12m, efa_12m, bil_12m = odm_ret['SPYM'], odm_ret['EFA'], odm_ret['BIL']
    
    odm_winner = 'SPYM' if spym_12m > efa_12m else 'EFA'
    odm_final = "AGG(채권)" if odm_ret[odm_winner] < bil_12m else f"{odm_winner}(주식)"

    # 2. 가속 듀얼모멘텀
    m1 = (data.iloc[-1] / data.iloc[-21]) - 1
    m3 = (data.iloc[-1] / data.iloc[-63]) - 1
    m6 = (data.iloc[-1] / data.iloc[-126]) - 1
    adm_score = (m1 + m3 + m6) / 3
    
    adm_winner = adm_score[['SPYM', 'EFA', 'BIL']].idxmax()
    adm_final = "AGG(채권)" if adm_winner == 'BIL' else f"{adm_winner}(주식)"

    # 텔레그램 메시지 작성 (헷갈리는 수익률 계산 과정 삭제)
    msg = f"📅 *{datetime.now().strftime('%Y년 %m월')} 듀얼모멘텀 리포트*\n\n"
    msg += f"✅ *오리지널(ODM):* **{odm_final}**\n\n"
    msg += f"🚀 *가속(ADM):* **{adm_final}**\n\n"
    msg += "🚩 매월 1일 기준 리밸런싱 신호입니다."

    send_message(msg)

if __name__ == "__main__":
    main()
