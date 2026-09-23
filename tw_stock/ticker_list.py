import pandas as pd
import requests
import yfinance as yf

def get_taiwan_stock_tickers():
    """
    抓取台灣上市 (TWSE) 與上櫃 (TPEX) 的股票代號與名稱
    並轉成 yfinance 格式 (.TW / .TWO)
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    # 1. 定義證交所資料來源：strMode=2 為上市，strMode=4 為上櫃
    targets = [
        {"market": "上市", "suffix": ".TW", "url": "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"},
        {"market": "上櫃", "suffix": ".TWO", "url": "https://isin.twse.com.tw/isin/C_public.jsp?strMode=4"}
    ]

    all_stocks = []

    for target in targets:
        print(f"抓取 {target['market']} 股票資料...")
        resp = requests.get(target["url"], headers=headers)
        resp.encoding = 'big5'  # 證交所網頁編碼通常為 Big5
        print(f" 狀態碼：{resp.status_code}")
        # 使用 pandas 解析 HTML 表格
        tables = pd.read_html(resp.text)
        df = tables[0]

        # 第一列通常為欄位名稱
        df.columns = df.iloc[0]
        df = df.iloc[1:]

        # 篩選「股票」區段（排除 ETF、認購售權證、特別股等）
        # 證交所表格中，「有價證券代號及名稱」欄位包含「代號 名稱」
        col_name = df.columns[0]

        for val in df[col_name]:
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            parts = val.strip().split('\u3000')  # 全形空白分隔
            if len(parts) < 2:
                parts = val.strip().split()  # 一般空白分隔備用

            if len(parts) == 2:
                code, name = parts[0].strip(), parts[1].strip()
                # 台灣普通股多為 4 碼純數字（排除權證與特別股等）
                if len(code) == 4 and code.isdigit():
                    all_stocks.append({
                        "代號": code,
                        "名稱": name,
                        "市場": target["market"],
                        "yf_symbol": f"{code}{target['suffix']}"
                    })

    result_df = pd.DataFrame(all_stocks)
    return result_df


# --- 執行抓取與測試 ---
if __name__ == "__main__":
    df_stocks = get_taiwan_stock_tickers()
    
    print(f"成功抓取共 {len(df_stocks)} 檔股票（上市 + 上櫃）\n")
    #print(df_stocks.head(10))

    # 匯出成 CSV 檔案備用
    df_stocks.to_csv("taiwan_stocks_yf.csv", index=False, encoding="utf-8-sig")
    print("\n已儲存為 taiwan_stocks_yf.csv")

    # 示範：使用 yfinance 驗證下載其中一檔股票（如台積電 2330.TW）的歷史資料
    sample_ticker = df_stocks.loc[df_stocks['代號'] == '2330', 'yf_symbol'].values[0]
    #print(f"\n測試使用 yfinance 下載 {sample_ticker} 最近 5 日報價：")
    #stock_data = yf.download(sample_ticker, period="5d")
    #print(stock_data[['Open', 'High', 'Low', 'Close', 'Volume']])