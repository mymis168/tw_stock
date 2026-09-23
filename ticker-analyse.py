"""台股個股分析 Streamlit 頁面（獨立執行版）。

輸入股票代號後，從 yfinance 下載股價資料，分析獲利、指數趨勢發展，
並給出最近的投資建議。

執行方式:
    streamlit run ticker-analyse.py
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

# ---------------------------------------------------------------------------
# 常數與選項
# ---------------------------------------------------------------------------

# 加權指數代號（yfinance 格式）
TAIEX = "^TWII"

# UI 期間選項 → yfinance period / interval
PERIOD_OPTIONS: dict[str, dict[str, str]] = {
    "日線 (近 3 個月)": {"period": "3mo", "interval": "1d"},
    "日線 (近 6 個月)": {"period": "6mo", "interval": "1d"},
    "日線 (近 1 年)": {"period": "1y", "interval": "1d"},
    "日線 (近 2 年)": {"period": "2y", "interval": "1d"},
    "週線 (近 3 年)": {"period": "3y", "interval": "1wk"},
    "週線 (近 5 年)": {"period": "5y", "interval": "1wk"},
    "月線 (近 5 年)": {"period": "5y", "interval": "1mo"},
    "月線 (近 10 年)": {"period": "10y", "interval": "1mo"},
    "月線 (全部)": {"period": "max", "interval": "1mo"},
}

# 常見台股代號（代號, 名稱）
STOCKS: list[tuple[str, str]]=[
    ("2330", "台積電"),
    ("2317", "鴻海"),
    ("2454", "聯發科"),
    ("2383", "聯強"),
    ("2407", "國巨"),
    ("2455", "日月光"),
    ("2409", "大立光"),
    ("2402", "光學"),
    ("2408", "大立光"),
    ("2403", "光學"),
    ("2404", "光學"),
    ("2405", "光學"),
    ("2406", "光學"),
    ("2407", "國巨"),
    ("2408", "大立光"),
    ("2409", "大立光"),
    ("2410", "光學"),
    ("2411", "光學"),
    ("2412", "光學"),
    ("2413", "光學"),
    ("2414", "光學"),
    ("2415", "光學"),
    ("2416", "光學"),
    ("2417", "光學"),
    ("2418", "光學"),
    ("2419", "光學"),
    ("2420", "光學"),
    ("2421", "光學"),
    ("2422", "光學"),
    ("2423", "光學"),
    ("2424", "光學"),
    ("2425", "光學"),
    ("2426", "光學"),
    ("2427", "光學"),
    ("2428", "光學"),
    ("2429", "光學"),
    ("2430", "光學"),
    ("2431", "光學"),
    ("2432", "光學"),
    ("2433", "光學"),
    ("2434", "光學"),
    ("2435", "光學"),
    ("2436", "光學"),
    ("2437", "光學"),
    ("2438", "光學"),
    ("2439", "光學"),
    ("2440", "光學"),
    ("2441", "光學"),
    ("2442", "光學"),
    ("2443", "光學"),
    ("2444", "光學"),
    ("2445", "光學"),
    ("2446", "光學"),
    ("2447", "光學"),
    ("2448", "光學"),
    ("2449", "光學"),
    ("2450", "光學"),
    ("2451", "光學"),
    ("2452", "光學"),
    ("2453", "光學"),
    ("2454", "聯發科"),
    ("2455", "日月光"),
    ("2456", "光學"),
    ("2457", "光學"),
    ("2458", "光學"),
    ("2459", "光學"),
    ("2460", "光學"),
    ("2461", "光學"),
    ("2462", "光學"),
    ("2463", "光學"),
    ("2464", "光學"),
    ("2465", "光學"),
    ("2466", "光學"),
    ("2467", "光學"),
    ("2468", "光學"),
    ("2469", "光學"),
    ("2470", "光學"),
    ("2471", "光學"),
    ("2472", "光學"),
    ("2473", "光學"),
    ("2474", "光學"),
    ("2475", "光學"),
    ("2476", "光學"),
    ("2477", "光學"),
    ("2478", "光學"),
    ("2479", "光學"),
    ("2480", "光學"),
    ("2481", "光學"),
    ("2482", "光學"),
    ("2483", "光學"),
    ("2484", "光學"),
    ("2485", "光學"),
    ("2486", "光學"),
    ("2487", "光學"),
    ("2488", "光學"),
    ("2489", "光學"),
    ("2490", "光學"),
    ("2491", "光學"),
    ("2492", "光學"),
    ("2493", "光學"),
    ("2494", "光學"),
    ("2495", "光學"),
    ("2496", "光學"),
    ("2497", "光學"),
    ("2498", "光學"),
    ("2499", "光學"),
    ("2500", "光學"),
]

# ---------------------------------------------------------------------------
# 資料下載與技術指標
# ---------------------------------------------------------------------------

def normalize_ticker(ticker: str) -> str:
    """確保代號帶有 .TW 或 .TWO 後綴。"""
    ticker = ticker.strip().upper()
    if not ticker:
        return ticker
    if ticker.endswith(".TW") or ticker.endswith(".TWO"):
        return ticker
    return f"{ticker}.TW"


def download_history(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """下載單一股票的 OHLCV 歷史資料。"""
    ticker = normalize_ticker(ticker)
    tk = yf.Ticker(ticker)
    df = tk.history(period=period, interval=interval, auto_adjust=False)
    if df is None or df.empty:
        return pd.DataFrame()
    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df = df.dropna(subset=["Close"])
    return df


def get_info(ticker: str) -> dict:
    """取得股票基本資料（從容處理失敗）。"""
    ticker = normalize_ticker(ticker)
    try:
        info = yf.Ticker(ticker).info
    except Exception:
        return {}
    if not isinstance(info, dict):
        return {}
    keys =[
        "shortName",
        "longName",
        "sector",
        "industry",
        "marketCap",
        "trailingPE",
        "forwardPE",
        "trailingEps",
        "forwardEps",
        "dividendYield",
        "beta",
        "returnOnEquity",
        "profitMargins",
        "fiftyTwoWeekHigh",
        "fiftyTwoWeekLow",
   ]
    return {k: info.get(k) for k in keys}


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """計算技術指標並回傳 df 的副本。

    新增:
      * 移動平均線: MA5, MA10, MA20, MA60
      * 布林通道: BOLL_MID, BOLL_UP, BOLL_LOW
      * MACD: MACD, MACD_SIGNAL, MACD_HIST
      * RSI(14)
    """
    if df is None or df.empty:
        return df

    out = df.copy()
    close = out["Close"]

    # 移動平均線
    for n in (5, 10, 20, 60):
        out[f"MA{n}"] = close.rolling(window=n, min_periods=1).mean()

    # 布林通道 (20, 2 std)
    window = 20
    mid = close.rolling(window=window, min_periods=1).mean()
    std = close.rolling(window=window, min_periods=1).std()
    out["BOLL_MID"] = mid
    out["BOLL_UP"] = mid + 2 * std
    out["BOLL_LOW"] = mid - 2 * std

    # MACD (12, 26, 9)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    out["MACD"] = ema12 - ema26
    out["MACD_SIGNAL"] = out["MACD"].ewm(span=9, adjust=False).mean()
    out["MACD_HIST"] = out["MACD"] - out["MACD_SIGNAL"]

    # RSI (14)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    out["RSI"] = 100 - (100 / (1 + rs))

    return out


def load_with_indicators(ticker: str, period_key: str) -> pd.DataFrame:
    """下載指定期間的歷史資料並附加技術指標。"""
    cfg = PERIOD_OPTIONS.get(period_key, {"period": "1y", "interval": "1d"})
    df = download_history(ticker, period=cfg["period"], interval=cfg["interval"])
    if df.empty:
        return df
    return add_indicators(df)


# ---------------------------------------------------------------------------
# 資料載入（快取，避免每次互動都重新下載）
# ---------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def load_stock(ticker: str, period_key: str) -> pd.DataFrame:
    """下載個股歷史資料並附加技術指標。"""
    return load_with_indicators(ticker, period_key)


@st.cache_data(ttl=3600)
def load_index(period_key: str) -> pd.DataFrame:
    """下載加權指數歷史資料並附加技術指標。"""
    cfg = PERIOD_OPTIONS.get(period_key, {"period": "1y", "interval": "1d"})
    tk = yf.Ticker(TAIEX)
    df = tk.history(period=cfg["period"], interval=cfg["interval"], auto_adjust=False)
    if df is None or df.empty:
        return pd.DataFrame()
    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df = df.dropna(subset=["Close"])
    return add_indicators(df)


# ---------------------------------------------------------------------------
# 分析邏輯
# ---------------------------------------------------------------------------
def compute_profit_metrics(df: pd.DataFrame) -> dict:
    """由 OHLCV 計算獲利相關指標。"""
    if df is None or df.empty:
        return {}
    close = df["Close"]
    last = float(close.iloc[-1])
    first = float(close.iloc[0])
    return {
        "last_close": last,
        "period_return": (last / first - 1) * 100 if first else 0.0,
        "high": float(close.max()),
        "low": float(close.min()),
        "volatility": float(close.pct_change().std() * 100),
        "last_date": str(df.index[-1].date()),
    }


def compute_advice(df: pd.DataFrame) -> dict:
    """由技術指標給出投資建議。

    回傳 dict:
        score: -100 ~ 100 的綜合評分
        signal: 強烈看多 / 看多 / 中性 / 看空 / 強烈看空
        reasons: 各指標說明
    """
    if df is None or df.empty or len(df)<2:
        return {"score": 0, "signal": "資料不足", "reasons":["資料不足，無法分析"]}

    reasons: list[str] =[]
    score = 0

    last = df.iloc[-1]
    close = float(last["Close"])

    # 均線多空
    ma20 = last.get("MA20")
    ma60 = last.get("MA60")
    if pd.notna(ma20):
        if close > ma20:
            score += 20
            reasons.append(f"收盤價高於 MA20 ({ma20:.2f})，短線偏多")
        else:
            score -= 20
            reasons.append(f"收盤價低於 MA20 ({ma20:.2f})，短線偏空")
    if pd.notna(ma60):
        if close > ma60:
            score += 15
            reasons.append(f"收盤價高於 MA60 ({ma60:.2f})，中線偏多")
        else:
            score -= 15
            reasons.append(f"收盤價低於 MA60 ({ma60:.2f})，中線偏空")

    # MACD
    hist = last.get("MACD_HIST")
    if pd.notna(hist):
        if hist > 0:
            score += 15
            reasons.append(f"MACD 柱狀為正（{hist:.3f}），動能偏多")
        else:
            score -= 15
            reasons.append(f"MACD 柱狀為負（{hist:.3f}），動能偏空")

    # RSI
    rsi = last.get("RSI")
    if pd.notna(rsi):
        if rsi >= 70:
            score -= 10
            reasons.append(f"RSI={rsi:.1f} 超買，注意回調風險")
        elif rsi<= 30:
            score += 10
            reasons.append(f"RSI={rsi:.1f} 超賣，可能反彈")
        else:
            reasons.append(f"RSI={rsi:.1f} 中性區間")

    # 布林通道位置
    boll_up = last.get("BOLL_UP")
    boll_low = last.get("BOLL_LOW")
    if pd.notna(boll_up) and pd.notna(boll_low) and boll_up > boll_low:
        pos = (close - boll_low) / (boll_up - boll_low)
        if pos >= 1:
            score -= 10
            reasons.append("收盤價觸及布林上軌，短期偏熱")
        elif pos<= 0:
            score += 10
            reasons.append("收盤價觸及布林下軌，短期偏冷")

    score = max(-100, min(100, score))
    if score >= 40:
        signal = "強烈看多"
    elif score >= 15:
        signal = "看多"
    elif score > -15:
        signal = "中性"
    elif score > -40:
        signal = "看空"
    else:
        signal = "強烈看空"

    return {"score": score, "signal": signal, "reasons": reasons}


def trend_summary(df: pd.DataFrame) -> str:
    """由均線排列給出趨勢描述。"""
    if df is None or df.empty or len(df)<60:
        return "資料不足，無法判斷趨勢"
    last = df.iloc[-1]
    ma5, ma10, ma20, ma60 = (last.get(k) for k in ("MA5", "MA10", "MA20", "MA60"))
    if any(pd.isna(x) for x in (ma5, ma10, ma20, ma60)):
        return "資料不足，無法判斷趨勢"
    if ma5 > ma10 > ma20 > ma60:
        return "多頭排列 (MA5 > MA10 > MA20 > MA60)，趨勢偏強"
    if ma5< ma10< ma20< ma60:
        return "空頭排列 (MA5< MA10< MA20< MA60)，趨勢偏弱"
    return "均線交織，趨勢不明確，建議觀察"


# ---------------------------------------------------------------------------
# 圖表
# ---------------------------------------------------------------------------
def price_figure(df: pd.DataFrame, title: str) -> go.Figure:
    """股價 + 均線 + 布林通道圖。"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], name="收盤價", line=dict(color="#1f77b4")))
    for col, color in (("MA5", "#ff7f0e"), ("MA10", "#2ca02c"), ("MA20", "#d62728"), ("MA60", "#9467bd")):
        if col in df:
            fig.add_trace(go.Scatter(x=df.index, y=df[col], name=col, line=dict(color=color, width=1)))
    if "BOLL_UP" in df:
        fig.add_trace(go.Scatter(x=df.index, y=df["BOLL_UP"], name="布林上軌", line=dict(color="gray", width=1, dash="dot")))
        fig.add_trace(go.Scatter(x=df.index, y=df["BOLL_LOW"], name="布林下軌", line=dict(color="gray", width=1, dash="dot"), showlegend=False))
    fig.update_layout(title=title, xaxis_title="日期", yaxis_title="價格", height=480, template="plotly_white")
    return fig


def macd_figure(df: pd.DataFrame, title: str) -> go.Figure:
    """MACD 圖。"""
    fig = go.Figure()
    colors =["#2ca02c" if v >= 0 else "#d62728" for v in df["MACD_HIST"].fillna(0)]
    fig.add_trace(go.Bar(x=df.index, y=df["MACD_HIST"], name="MACD 柱", marker_color=colors))
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD", line=dict(color="#1f77b4")))
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD_SIGNAL"], name="Signal", line=dict(color="#ff7f0e")))
    fig.update_layout(title=title, xaxis_title="日期", height=300, template="plotly_white")
    return fig


def rsi_figure(df: pd.DataFrame, title: str) -> go.Figure:
    """RSI 圖。"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI(14)", line=dict(color="#9467bd")))
    fig.add_hline(y=70, line=dict(color="#d62728", width=1, dash="dash"))
    fig.add_hline(y=30, line=dict(color="#2ca02c", width=1, dash="dash"))
    fig.update_layout(title=title, xaxis_title="日期", yaxis_title="RSI", yaxis=dict(range=[0, 100]), height=300, template="plotly_white")
    return fig


# ---------------------------------------------------------------------------
# 頁面
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title="台股個股分析", page_icon="📈", layout="wide")
    st.title("📈 台股個股分析")
    st.caption("輸入股票代號，從 yfinance 下載資料，分析獲利、指數趨勢與投資建議。")

    # 側邊欄：輸入
    with st.sidebar:
        st.header("輸入股票")
        options = {f"{t} - {n}": t for t, n in STOCKS}
        selected = st.selectbox("選擇股票（或下方手動輸入）", list(options.keys()))
        manual = st.text_input("或手動輸入代號（如 2330 / 2330.TW）", "")
        ticker = manual.strip() if manual.strip() else options[selected]

        period_key = st.selectbox("分析期間", list(PERIOD_OPTIONS.keys()), index=2)
        st.divider()
        st.write("### 說明")
        st.markdown(
            "- 資料來源：yfinance（Yahoo Finance）\n"
            "- 上市股票代號加 `.TW`，上櫃加 `.TWO`\n"
            "- 投資建議僅供參考，不構成投資建議"
        )

    if not ticker:
        st.info("請在側邊欄輸入股票代號。")
        return

    ticker = normalize_ticker(ticker)

    with st.spinner(f"下載 {ticker} 資料中..."):
        df = load_stock(ticker, period_key)
        idx_df = load_index(period_key)

    if df is None or df.empty:
        st.error(f"無法取得 {ticker} 的歷史資料，請確認代號是否正確。")
        return

    info = get_info(ticker)
    metrics = compute_profit_metrics(df)
    advice = compute_advice(df)
    trend = trend_summary(df)

    # 標題與基本資訊
    name = info.get("shortName") or info.get("longName") or ticker
    st.subheader(f"{name} ({ticker})")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("最新收盤", f"{metrics['last_close']:.2f}")
    c2.metric("期間報酬", f"{metrics['period_return']:+.2f}%")
    c3.metric("期間最高 / 最低", f"{metrics['high']:.2f} / {metrics['low']:.2f}")
    c4.metric("波動率（日）", f"{metrics['volatility']:.2f}%")

    # 基本面
    if info:
        with st.expander("基本面資料", expanded=False):
            f1, f2, f3, f4 = st.columns(4)
            f1.metric("產業", info.get("sector") or "N/A")
            f2.metric("產業別", info.get("industry") or "N/A")
            f3.metric("本益比 (TTM)", f"{info['trailingPE']:.2f}" if info.get("trailingPE") else "N/A")
            f4.metric("殖利率", f"{info['dividendYield']:.2f}%" if info.get("dividendYield") else "N/A")
            f5, f6, f7, f8 = st.columns(4)
            f5.metric("市值", f"{(info.get('marketCap') or 0) / 1e8:,.0f} 億" if info.get("marketCap") else "N/A")
            f6.metric("Beta", f"{info['beta']:.2f}" if info.get("beta") else "N/A")
            f7.metric("ROE", f"{(info.get('returnOnEquity') or 0) * 100:.2f}%" if info.get("returnOnEquity") else "N/A")
            f8.metric("52 週高 / 低", f"{info['fiftyTwoWeekHigh']:.2f} / {info['fiftyTwoWeekLow']:.2f}" if info.get("fiftyTwoWeekHigh") else "N/A")

    # 投資建議
    st.subheader("🎯 投資建議")
    sig_color = {
        "強烈看多": "🟢", "看多": "🟢", "中性": "🟡", "看空": "🔴", "強烈看空": "🔴", "資料不足": "⚪",
    }
    st.markdown(f"**{sig_color.get(advice['signal'], '⚪')} 綜合評分：{advice['score']:+d}　→　{advice['signal']}**")
    st.markdown(f"**趨勢判斷：** {trend}")
    for r in advice["reasons"]:
        st.markdown(f"- {r}")
    st.caption("※ 以上分析僅供參考，不構成投資建議。")

    # 圖表
    st.subheader("📊 股價與技術指標")
    st.plotly_chart(price_figure(df, f"{name} 股價（{period_key}）"), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(macd_figure(df, "MACD"), use_container_width=True)
    with c2:
        st.plotly_chart(rsi_figure(df, "RSI(14)"), use_container_width=True)

    # 加權指數趨勢
    if not idx_df.empty:
        st.subheader("📉 加權指數趨勢")
        st.plotly_chart(price_figure(idx_df, f"加權指數（{period_key}）"), use_container_width=True)
        idx_metrics = compute_profit_metrics(idx_df)
        st.markdown(
            f"加權指數最新 **{idx_metrics['last_close']:.2f}**，期間報酬 **{idx_metrics['period_return']:+.2f}%**，"
            f"趨勢：{trend_summary(idx_df)}"
        )


if __name__ == "__main__":
    main()