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
        # 💡 야후 파이낸스 오류 방지를 위해 종목을 하나씩 안전하게 가져옵니다.
        for t in tickers:
            ticker_obj = yf.Ticker(t)
            # history()를 사용하면 수정종가(배당 등 반영)가 기본 'Close'로 깔끔하게 나옵니다.
            df = ticker_obj.history(period='2y')
            
            if df.empty:
                raise Exception(f"'{t}' 종목의 데이터를 불러오지 못했습니다.")
                
            data[t] = df['Close']
            
        # 빈 날짜(휴장일 차이 등) 제거해서 계산 오류 방지
        data = data.dropna()
        
    except Exception as e:
        send_message(f"❌ 야후 파이낸스 데이터 수집 에러: {e}")
        return
        
    # 데이터가 252일(약 1년 거래일)보다 적으면 계산 불가
    if len(data) < 252:
        send_message("❌ 에러: 12개월(252일) 치의 충분한 가격 데이터가 모이지 않았습니다.")
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
