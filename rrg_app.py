import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# Set up the webpage configuration
st.set_page_config(
    layout="wide",
    page_title="Pro RRG Institutional Terminal",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# --- EXPANDED DICTIONARY OF MAJOR NSE ETFs & INDICES ---
NSE_INDICES = {
    # Broad Market & Cap-Based
    "Nifty 50 (NIFTYBEES)": "NIFTYBEES.NS",
    "Nifty Next 50 (JUNIORBEES)": "JUNIORBEES.NS",
    "Nifty Midcap 150 (MID150BEES)": "MID150BEES.NS",
    "Nifty Smallcap 250 (HDFCSML250)": "HDFCSML250.NS",
    "Nifty LargeMidcap 250 (TOP100CASE)": "TOP100CASE.NS",

    # Sectoral ETFs & Indices (Using stable index proxies & ETFs)
    "Nifty Bank (BANKBEES)": "BANKBEES.NS",
    "Nifty PSU Bank (PSUBNKBEES)": "PSUBNKBEES.NS",
    "Nifty Private Bank (SBIETFPB)": "SBIETFPB.NS",
    "Nifty IT (ITBEES)": "ITBEES.NS",
    "Nifty Pharma (PHARMABEES)": "PHARMABEES.NS",
    "Nifty Healthcare (HEALTHY)": "HEALTHY.NS",
    "Nifty FMCG (^CNXFMCG)": "^CNXFMCG",
    "Nifty Auto (AUTOBEES)": "AUTOBEES.NS",
    "Nifty Metal (^CNXMETAL)": "^CNXMETAL",
    "Nifty Infra (INFRABEES)": "INFRABEES.NS",
    "Nifty Financial Services (BFSI)": "BFSI.NS",
    "Nifty Realty (MOREALTY)": "MOREALTY.NS",

    # Thematic & Smart Beta / Factor ETFs
    "Nifty Consumption (CONSUMBEES)": "CONSUMBEES.NS",
    "Nifty CPSE (CPSEETF)": "CPSEETF.NS",
    "Nifty Div Opps (DIVOPPBEES)": "DIVOPPBEES.NS",
    "Nifty Value 20 (NV20BEES)": "NV20BEES.NS",
    "Nifty India Defence (MODEFENCE)": "MODEFENCE.NS",
    "Nifty Manufacturing (MAKEINDIA)": "MAKEINDIA.NS",
    "Nifty Commodities (^CNXCMDT)": "^CNXCMDT",
    "Nifty Alpha 50 (ALPHA)": "ALPHA.NS",
    "Nifty 200 Momentum 30 (MOM30IETF)": "MOM30IETF.NS",

    # Commodities & Global
    "Gold (GOLDBEES)": "GOLDBEES.NS",
    "Silver (SILVERBEES)": "SILVERBEES.NS",
    "Nasdaq 100 (MON100)": "MON100.NS",
    "NYSE FANG+ (MAFANG)": "MAFANG.NS"
}

# Sector Constituents for Drill-Down RRG
SECTOR_CONSTITUENTS = {
    "Nifty IT (ITBEES)": {
        "benchmark": "ITBEES.NS",
        "stocks": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS", "LTIM.NS", "PERSISTENT.NS", "COFORGE.NS"]
    },
    "Nifty Bank (BANKBEES)": {
        "benchmark": "BANKBEES.NS",
        "stocks": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS", "INDUSINDBK.NS", "BANKBARODA.NS", "PNB.NS"]
    },
    "Nifty Auto (AUTOBEES)": {
        "benchmark": "AUTOBEES.NS",
        "stocks": ["M&M.NS", "MARUTI.NS", "TATAMOTORS.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "TVSMOTOR.NS", "ASHOKLEY.NS"]
    },
    "Nifty Pharma (PHARMABEES)": {
        "benchmark": "PHARMABEES.NS",
        "stocks": ["SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "LUPIN.NS", "AUROPHARMA.NS", "TORNTPHARM.NS", "ZYDUSLIFE.NS"]
    },
    "Nifty Metal (^CNXMETAL)": {
        "benchmark": "^CNXMETAL",
        "stocks": ["TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "VEDL.NS", "JINDALSTEL.NS", "COALINDIA.NS", "NMDC.NS", "NATIONALUM.NS"]
    },
    "Nifty FMCG (^CNXFMCG)": {
        "benchmark": "^CNXFMCG",
        "stocks": ["ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS", "TATACONSUM.NS", "GODREJCP.NS", "DABUR.NS", "MARICO.NS"]
    },
    "Nifty Infra (INFRABEES)": {
        "benchmark": "INFRABEES.NS",
        "stocks": ["LT.NS", "RELIANCE.NS", "BHARTIARTL.NS", "NTPC.NS", "POWERGRID.NS", "ULTRACEMCO.NS", "ADANIPORTS.NS", "ONGC.NS"]
    }
}

REVERSE_MAP = {v: k.split(" (")[0] for k, v in NSE_INDICES.items()}
# Add clean mappings for index proxies too
REVERSE_MAP.update({
    "^CNXMETAL": "Nifty Metal",
    "^CNXFMCG": "Nifty FMCG",
    "^CNXCMDT": "Nifty Commodities"
})

# --- SIDEBAR (TERMINAL CONTROLS) ---
with st.sidebar:
    st.header("⚙️ Terminal Settings")

    timeframe = st.selectbox(
        "⏳ Select Timeframe:",
        ["Daily", "Weekly", "Monthly"],
        index=1,
        help="Daily for short-term swing, Weekly for medium-term positional, Monthly for macro trends."
    )

    default_selections = [
        "Nifty IT (ITBEES)",
        "Nifty Bank (BANKBEES)",
        "Nifty Pharma (PHARMABEES)",
        "Nifty Auto (AUTOBEES)",
        "Nifty Metal (^CNXMETAL)",
        "Nifty FMCG (^CNXFMCG)",
        "Nifty Infra (INFRABEES)",
        "Nifty Realty (MOREALTY)"
    ]

    selected_index_names = st.multiselect(
        "📊 Select Sectors & ETFs:",
        options=list(NSE_INDICES.keys()),
        default=default_selections
    )

    custom_stocks_input = st.text_input("➕ Add Custom Tickers (comma-separated):", value="")
    benchmark_input = st.text_input("🎯 Primary Benchmark:", value="NIFTYBEES.NS")

    st.markdown("---")
    st.subheader("⏪ Historical Time-Machine")
    replay_offset = st.slider(
        "Scrub Back in Time (Periods Ago):",
        min_value=0,
        max_value=30,
        value=0,
        help="0 = Latest live data. Increase to rewind the RRG chart and inspect historical rotations."
    )

    quadrant_filter = st.multiselect(
        "🔍 Filter Quadrants:",
        options=["Leading 🟢", "Weakening 🟡", "Lagging 🔴", "Improving 🔵"],
        default=["Leading 🟢", "Weakening 🟡", "Lagging 🔴", "Improving 🔵"]
    )

    if st.button("🔄 Refresh Market Data", use_container_width=True):
        st.cache_data.clear()

    with st.expander("🔧 Advanced RRG & Visual Settings"):
        jdk_period = st.slider("JdK Smoothing Period", 5, 52, 14)
        roc_period = st.slider("RS-Momentum Lookback", 3, 30, 10,
                               help="Bars used to calculate the change in RS-Ratio before smoothing.")
        tail_weeks = st.slider("Tail Length (Periods)", 1, 30, 6)
        spline_smooth = st.checkbox("Curved Spline Tails", value=True)
        show_labels = st.checkbox("Show Ticker Labels on Chart", value=True)


# --- HELPER FUNCTIONS ---
@st.cache_data(ttl=3600, show_spinner=False)
def load_data(symbols, tf):
    """Download adjusted close data and normalize yfinance's column formats."""
    symbols = list(dict.fromkeys(symbols))
    if not symbols:
        return pd.DataFrame()

    period = "2y" if tf == "Daily" else ("5y" if tf == "Weekly" else "10y")
    try:
        raw = yf.download(
            tickers=symbols,
            period=period,
            interval="1d",
            progress=False,
            auto_adjust=True,
            group_by="column",
            threads=True,
        )
    except Exception as exc:
        st.error(f"Market data download failed: {exc}")
        return pd.DataFrame()

    if raw is None or raw.empty:
        return pd.DataFrame()

    # yfinance may return either (field, ticker) or (ticker, field) MultiIndex columns.
    if isinstance(raw.columns, pd.MultiIndex):
        level0 = raw.columns.get_level_values(0)
        level1 = raw.columns.get_level_values(1)
        if "Close" in level0:
            df = raw.xs("Close", axis=1, level=0, drop_level=True)
        elif "Close" in level1:
            df = raw.xs("Close", axis=1, level=1, drop_level=True)
        else:
            return pd.DataFrame()
    elif "Close" in raw.columns:
        if len(symbols) == 1:
            df = raw[["Close"]].rename(columns={"Close": symbols[0]})
        else:
            df = raw[["Close"]]
            df.columns = [symbols[0]]
    else:
        return pd.DataFrame()

    if isinstance(df, pd.Series):
        df = df.to_frame(name=symbols[0])

    # Normalize output column names to ticker strings and safely handle absent tickers.
    df.columns = [str(col) for col in df.columns]
    df = df.sort_index().replace([np.inf, -np.inf], np.nan)
    df = df.ffill(limit=5)

    if tf == "Weekly":
        df = df.resample("W-FRI").last()
    elif tf == "Monthly":
        try:
            df = df.resample("ME").last()
        except ValueError:
            # Compatibility with pandas releases that use the legacy month-end alias.
            df = df.resample("M").last()

    return df.dropna(axis=1, how="all").dropna(how="all")


def classify_quadrant(r, m):
    if r >= 100 and m >= 100:
        return "Leading 🟢"
    elif r >= 100 and m < 100:
        return "Weakening 🟡"
    elif r < 100 and m < 100:
        return "Lagging 🔴"
    return "Improving 🔵"


def generate_rotational_signal(r_prev, m_prev, r_curr, m_curr, heading_deg):
    prev_q = classify_quadrant(r_prev, m_prev)
    curr_q = classify_quadrant(r_curr, m_curr)

    if prev_q != curr_q:
        if curr_q == "Leading 🟢":
            return "🚀 Fresh Breakout -> Leading"
        if curr_q == "Improving 🔵":
            return "🌱 Fresh Turn -> Improving"
        if curr_q == "Weakening 🟡":
            return "⚠️ Loss of Mom -> Weakening"
        if curr_q == "Lagging 🔴":
            return "🩸 Breakdown -> Lagging"

    if 0 <= heading_deg <= 90:
        if curr_q == "Leading 🟢":
            return "🔥 Northeast Power Trend"
        if curr_q == "Improving 🔵":
            return "📈 Accelerating Toward Leading"
        if curr_q == "Lagging 🔴":
            return "🔄 Bullish Hook in Lagging"
    if 180 <= heading_deg <= 270 and curr_q in ["Leading 🟢", "Weakening 🟡"]:
        return "📉 Rolling Over (SW Trajectory)"

    return "➡️ Steady Rotation"


def compute_rrg_metrics(price_df, tickers, bench_col, jdk_len, tail_len, offset, roc_period=10):
    full_series = {}
    tails = {}
    metrics_rows = []
    skipped = []
    as_of_date = None
    relative_lookbacks = (10, 20, 60)

    for ticker in tickers:
        if ticker not in price_df.columns or ticker == bench_col:
            continue

        pair = price_df[[ticker, bench_col]].dropna()
        if offset > 0:
            pair = pair.iloc[:-offset] if offset < len(pair) else pair.iloc[0:0]

        if len(pair) < (jdk_len * 2 + roc_period + 3):
            skipped.append(ticker)
            continue

        rs = pair[ticker] / pair[bench_col].replace(0, np.nan)
        rs_ema = rs.ewm(span=jdk_len, adjust=False).mean()
        rs_ratio = 100 * rs_ema / rs_ema.rolling(window=jdk_len, min_periods=jdk_len).mean()
        roc = (rs_ratio / rs_ratio.shift(roc_period)) - 1
        rs_momentum = 100 + 100 * roc.ewm(span=jdk_len, adjust=False).mean()

        complete_df = pd.DataFrame({
            "Price": pair[ticker],
            "Benchmark": pair[bench_col],
            "RS": rs,
            "RS_Ratio": rs_ratio,
            "RS_Mom": rs_momentum
        }).replace([np.inf, -np.inf], np.nan).dropna()

        if len(complete_df) < 2:
            skipped.append(ticker)
            continue

        full_series[ticker] = complete_df
        valid_tail = complete_df.tail(tail_len + 1)
        tails[ticker] = valid_tail
        as_of_date = valid_tail.index[-1].strftime("%Y-%m-%d")

        x_vals = valid_tail["RS_Ratio"].values
        y_vals = valid_tail["RS_Mom"].values
        r_curr, m_curr = float(x_vals[-1]), float(y_vals[-1])
        r_prev, m_prev = float(x_vals[-2]), float(y_vals[-2])
        dx, dy = r_curr - r_prev, m_curr - m_prev
        r_dist = float(np.hypot(r_curr - 100.0, m_curr - 100.0))
        velocity = float(np.hypot(dx, dy))
        heading_deg = float((np.degrees(np.arctan2(dy, dx)) + 360.0) % 360.0)

        clean_name = REVERSE_MAP.get(ticker, ticker.replace(".NS", ""))
        quad = classify_quadrant(r_curr, m_curr)
        signal = generate_rotational_signal(r_prev, m_prev, r_curr, m_curr, heading_deg)

        row = {
            "Ticker": ticker,
            "Symbol": clean_name,
            "Quadrant": quad,
            "Signal": signal,
            "Strength (RS-Ratio)": round(r_curr, 2),
            "Str Chg": round(dx, 2),
            "Momentum (RS-Mom)": round(m_curr, 2),
            "Mom Chg": round(dy, 2),
            "RRG Distance": round(r_dist, 2),
            "Velocity": round(velocity, 2),
            "Heading (°)": round(heading_deg, 1),
        }

        # Returns use the same replay cut-off as the RRG metrics, so historical replay stays aligned.
        for lookback in relative_lookbacks:
            if len(pair) > lookback:
                asset_return = (pair[ticker].iloc[-1] / pair[ticker].iloc[-lookback - 1] - 1) * 100
                bench_return = (pair[bench_col].iloc[-1] / pair[bench_col].iloc[-lookback - 1] - 1) * 100
                row[f"Asset Return ({lookback} bars) %"] = round(float(asset_return), 2)
                row[f"Benchmark Return ({lookback} bars) %"] = round(float(bench_return), 2)
                row[f"Excess Return ({lookback} bars) %"] = round(float(asset_return - bench_return), 2)
            else:
                row[f"Asset Return ({lookback} bars) %"] = np.nan
                row[f"Benchmark Return ({lookback} bars) %"] = np.nan
                row[f"Excess Return ({lookback} bars) %"] = np.nan
        metrics_rows.append(row)

    metrics_df = pd.DataFrame(metrics_rows)
    if not metrics_df.empty:
        # Cross-sectional score, not a probability or guaranteed trading signal.
        metrics_df["RS Rank"] = metrics_df["Strength (RS-Ratio)"].rank(pct=True) * 100
        metrics_df["Momentum Rank"] = metrics_df["Momentum (RS-Mom)"].rank(pct=True) * 100
        metrics_df["Velocity Rank"] = metrics_df["Velocity"].rank(pct=True) * 100
        trend_score = np.select(
            [
                (metrics_df["Str Chg"] > 0) & (metrics_df["Mom Chg"] > 0),
                (metrics_df["Str Chg"] > 0) | (metrics_df["Mom Chg"] > 0),
            ],
            [100, 60],
            default=20,
        )
        metrics_df["Rotation Score"] = (
            0.40 * metrics_df["RS Rank"]
            + 0.35 * metrics_df["Momentum Rank"]
            + 0.15 * metrics_df["Velocity Rank"]
            + 0.10 * trend_score
        ).round(1)
        metrics_df[["RS Rank", "Momentum Rank", "Velocity Rank"]] = metrics_df[["RS Rank", "Momentum Rank", "Velocity Rank"]].round(1)
        metrics_df = metrics_df.sort_values(by="Strength (RS-Ratio)", ascending=False)

    return tails, full_series, metrics_df, skipped, as_of_date


def build_rrg_figure(tails_dict, metrics_df, allowed_quadrants, use_spline=True, display_labels=True):
    fig = go.Figure()
    colors = px.colors.qualitative.Light24 + px.colors.qualitative.Dark24
    all_x, all_y = [], []

    filtered_tickers = set(
        metrics_df[metrics_df["Quadrant"].isin(allowed_quadrants)]["Ticker"].tolist()
    ) if not metrics_df.empty else set()

    for i, (ticker, tail_df) in enumerate(tails_dict.items()):
        if ticker not in filtered_tickers:
            continue

        x_data = tail_df["RS_Ratio"].values
        y_data = tail_df["RS_Mom"].values
        dates = tail_df.index.strftime("%Y-%m-%d").tolist()

        all_x.extend(x_data)
        all_y.extend(y_data)

        color = colors[i % len(colors)]
        clean_name = REVERSE_MAP.get(ticker, ticker.replace(".NS", ""))
        n_pts = len(x_data)
        node_sizes = np.linspace(4, 9, n_pts).tolist()

        fig.add_trace(go.Scatter(
            x=x_data,
            y=y_data,
            mode="lines+markers",
            marker=dict(size=node_sizes, color=color, opacity=0.75),
            line=dict(
                width=2.8,
                color=color,
                shape="spline" if use_spline else "linear",
                smoothing=1.1 if use_spline else 0
            ),
            name=clean_name,
            text=dates,
            hovertemplate=(
                f"<b>{clean_name}</b><br>"
                "Date: %{text}<br>"
                "RS-Ratio: %{x:.2f}<br>"
                "RS-Mom: %{y:.2f}<extra></extra>"
            )
        ))

        fig.add_trace(go.Scatter(
            x=[x_data[-2], x_data[-1]],
            y=[y_data[-2], y_data[-1]],
            mode="markers+text" if display_labels else "markers",
            marker=dict(
                symbol=["circle", "arrow"],
                size=[0, 16],
                angleref="previous",
                color=color,
                line=dict(width=1.5, color="white")
            ),
            text=["", clean_name] if display_labels else None,
            textposition="top center",
            textfont=dict(size=12, color="#ffffff"),
            showlegend=False,
            hoverinfo="skip"
        ))

    if not all_x:
        all_x, all_y = [98, 102], [98, 102]

    all_x_arr = np.array(all_x)
    all_y_arr = np.array(all_y)
    max_dev = max(np.abs(all_x_arr - 100).max(), np.abs(all_y_arr - 100).max(), 2.0)
    center_spread = max_dev * 1.18
    low_bound, high_bound = 100 - center_spread, 100 + center_spread

    fig.add_shape(type="rect", x0=100, y0=100, x1=high_bound, y1=high_bound, fillcolor="#008217", opacity=0.12, layer="below", line_width=0)
    fig.add_shape(type="rect", x0=100, y0=low_bound, x1=high_bound, y1=100, fillcolor="#918000", opacity=0.12, layer="below", line_width=0)
    fig.add_shape(type="rect", x0=low_bound, y0=low_bound, x1=100, y1=100, fillcolor="#E0002B", opacity=0.12, layer="below", line_width=0)
    fig.add_shape(type="rect", x0=low_bound, y0=100, x1=100, y1=high_bound, fillcolor="#00749D", opacity=0.12, layer="below", line_width=0)

    fig.add_vline(x=100, line_width=1.5, line_color="#666")
    fig.add_hline(y=100, line_width=1.5, line_color="#666")

    fig.add_annotation(x=0.98, y=0.98, xref="paper", yref="paper", text="LEADING", showarrow=False, font=dict(color="#00ff44", size=22, family="Arial Black"), xanchor="right", yanchor="top", opacity=0.28)
    fig.add_annotation(x=0.98, y=0.02, xref="paper", yref="paper", text="WEAKENING", showarrow=False, font=dict(color="#ffdd00", size=22, family="Arial Black"), xanchor="right", yanchor="bottom", opacity=0.28)
    fig.add_annotation(x=0.02, y=0.02, xref="paper", yref="paper", text="LAGGING", showarrow=False, font=dict(color="#ff3333", size=22, family="Arial Black"), xanchor="left", yanchor="bottom", opacity=0.28)
    fig.add_annotation(x=0.02, y=0.98, xref="paper", yref="paper", text="IMPROVING", showarrow=False, font=dict(color="#33ccff", size=22, family="Arial Black"), xanchor="left", yanchor="top", opacity=0.28)

    fig.update_layout(
        xaxis_title="Relative Strength (JdK RS-Ratio) ➔",
        yaxis_title="Relative Momentum (JdK RS-Momentum) ➔",
        xaxis=dict(range=[low_bound, high_bound], zeroline=False, showgrid=True, gridcolor="#222"),
        yaxis=dict(range=[low_bound, high_bound], zeroline=False, showgrid=True, gridcolor="#222"),
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font=dict(color="#e0e0e0"),
        height=720,
        margin=dict(l=40, r=40, t=30, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0)
    )
    return fig


# --- DATA DOWNLOAD & PRIMARY COMPUTATION ---
raw_tickers = [NSE_INDICES[name] for name in selected_index_names]
if custom_stocks_input.strip():
    raw_tickers.extend([t.strip().upper() for t in custom_stocks_input.split(",") if t.strip()])

tickers_list = list(dict.fromkeys(raw_tickers))
benchmark = benchmark_input.strip().upper()

if not benchmark:
    st.error("Please enter a valid Benchmark ticker in the sidebar.")
    st.stop()

download_list = list(dict.fromkeys(tickers_list + [benchmark]))

with st.spinner(f"Syncing {timeframe} Market Data..."):
    df = load_data(download_list, timeframe)

if df.empty or benchmark not in df.columns:
    st.error(f"Error: Benchmark '{benchmark}' failed to download. Check ticker symbol correctness.")
    st.stop()

missing_tickers = [t for t in tickers_list if t not in df.columns]
if missing_tickers:
    st.sidebar.warning(f"⚠️ Unavailable tickers skipped: {', '.join(missing_tickers)}")

# Filter active tickers to only those successfully downloaded
tickers_list = [t for t in tickers_list if t in df.columns]

ticker_tails, full_rrg_series, dash_df, skipped_short, as_of_date = compute_rrg_metrics(
    df, tickers_list, benchmark, jdk_period, tail_weeks, replay_offset, roc_period
)

if skipped_short:
    st.sidebar.info(f"ℹ️ Skipped (short history): {', '.join(skipped_short)}")

if dash_df.empty:
    st.error(f"Insufficient {timeframe} data across selected symbols. Try lowering JdK Smoothing or Replay Offset.")
    st.stop()

# --- TOP HEADER & KPI METRICS ---
st.title("⚡ Pro RRG Institutional Terminal")
st.caption(f"RRG calculations use {timeframe.lower()} bars, adjusted-close price history, and benchmark-relative strength. Returns shown as bars depend on the selected timeframe.")

leaders_df = dash_df[dash_df["Quadrant"] == "Leading 🟢"]
laggers_df = dash_df[dash_df["Quadrant"] == "Lagging 🔴"]
top_leader = leaders_df.sort_values("Strength (RS-Ratio)", ascending=False).iloc[0] if not leaders_df.empty else dash_df.sort_values("Rotation Score", ascending=False).iloc[0]
top_lagger = laggers_df.sort_values("Strength (RS-Ratio)", ascending=True).iloc[0] if not laggers_df.empty else dash_df.sort_values("Rotation Score", ascending=True).iloc[0]
fastest_mover = dash_df.sort_values(by="Velocity", ascending=False).iloc[0]

mode_badge = f"⏪ REPLAY MODE ({replay_offset} bars ago • {as_of_date})" if replay_offset > 0 else f"🟢 LIVE SNAPSHOT ({as_of_date})"
st.info(
    f"**{mode_badge}** | **{top_leader['Symbol']}** leads relative strength ({top_leader['Signal']}), "
    f"while **{fastest_mover['Symbol']}** exhibits the highest rotational velocity ({fastest_mover['Velocity']:.2f}/bar)."
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🌟 Top Leader", top_leader["Symbol"], f"{top_leader['Str Chg']:+.2f} Str | {top_leader['Heading (°)']}°")
with col2:
    st.metric("🚀 Highest Velocity", fastest_mover["Symbol"], f"{fastest_mover['Velocity']:.2f} / period")
with col3:
    st.metric("⚠️ Deepest Lagger", top_lagger["Symbol"], f"{top_lagger['Str Chg']:+.2f} Strength")
with col4:
    st.metric("📊 Active Universe", f"{len(dash_df)} Assets", f"vs {benchmark.replace('.NS', '')} ({timeframe})")

st.markdown("---")

# --- NAVIGATION TABS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🎯 Macro Rotation Chart",
    "🔬 Sector Constituent Drill-Down",
    "📈 RS & Price Inspector",
    "📋 Pro Data Matrix & Signals",
    "⭐ Rotation Watchlist & Alerts",
    "📊 Performance & Risk"
])

# TAB 1: MACRO ROTATION CHART
with tab1:
    macro_fig = build_rrg_figure(
        ticker_tails,
        dash_df,
        allowed_quadrants=quadrant_filter,
        use_spline=spline_smooth,
        display_labels=show_labels
    )
    st.plotly_chart(macro_fig, use_container_width=True)

# TAB 2: SECTOR CONSTITUENT DRILL-DOWN
with tab2:
    st.markdown("### 🔬 Intra-Sector Stock Rotation")
    d_col1, d_col2 = st.columns([2, 2])
    with d_col1:
        chosen_sector = st.selectbox("Select Sector Universe:", options=list(SECTOR_CONSTITUENTS.keys()))
    with d_col2:
        sector_bench_Default = SECTOR_CONSTITUENTS[chosen_sector]["benchmark"]
        bench_mode = st.radio(
            "Compare Constituents Against:",
            options=[f"Sector Index/ETF ({sector_bench_Default})", f"Primary Benchmark ({benchmark})"],
            horizontal=True
        )

    drill_bench = sector_bench_Default if "Sector Index/ETF" in bench_mode else benchmark
    drill_stocks = SECTOR_CONSTITUENTS[chosen_sector]["stocks"]
    drill_download = list(dict.fromkeys(drill_stocks + [drill_bench]))

    with st.spinner(f"Loading {chosen_sector} constituents..."):
        drill_df = load_data(drill_download, timeframe)

    if not drill_df.empty and drill_bench in drill_df.columns:
        d_tails, _, d_metrics, _, _ = compute_rrg_metrics(
            drill_df, drill_stocks, drill_bench, jdk_period, tail_weeks, replay_offset, roc_period
        )
        if not d_metrics.empty:
            drill_fig = build_rrg_figure(
                d_tails,
                d_metrics,
                allowed_quadrants=["Leading 🟢", "Weakening 🟡", "Lagging 🔴", "Improving 🔵"],
                use_spline=spline_smooth,
                display_labels=show_labels
            )
            st.plotly_chart(drill_fig, use_container_width=True)
            st.dataframe(d_metrics.drop(columns=["Ticker"]), use_container_width=True, hide_index=True)
        else:
            st.warning("Insufficient historical bars for selected sector parameters.")
    else:
        st.error(f"Could not load benchmark {drill_bench} for sector drill-down.")

# TAB 3: RS & PRICE TIME-SERIES INSPECTOR
with tab3:
    st.markdown("### 📈 Historical Relative Strength & Oscillator Breakdown")
    symbol_map = {row["Symbol"]: row["Ticker"] for _, row in dash_df.iterrows()}
    selected_sym_label = st.selectbox("Select Asset to Inspect:", options=list(symbol_map.keys()))
    inspected_ticker = symbol_map[selected_sym_label]
    ts_df = full_rrg_series[inspected_ticker].tail(120)

    sub_fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
        row_heights=[0.5, 0.5],
        subplot_titles=(
            f"{selected_sym_label} vs {benchmark.replace('.NS', '')} (Normalized to 100)",
            "JdK RS-Ratio & RS-Momentum Oscillators"
        )
    )

    norm_asset = 100 * ts_df["Price"] / ts_df["Price"].iloc[0]
    norm_bench = 100 * ts_df["Benchmark"] / ts_df["Benchmark"].iloc[0]

    sub_fig.add_trace(go.Scatter(x=ts_df.index, y=norm_asset, name=selected_sym_label, line=dict(color="#00ff88", width=2.5)), row=1, col=1)
    sub_fig.add_trace(go.Scatter(x=ts_df.index, y=norm_bench, name=benchmark.replace(".NS", ""), line=dict(color="#888888", width=2, dash="dot")), row=1, col=1)

    sub_fig.add_trace(go.Scatter(x=ts_df.index, y=ts_df["RS_Ratio"], name="JdK RS-Ratio (Strength)", line=dict(color="#33ccff", width=2.5)), row=2, col=1)
    sub_fig.add_trace(go.Scatter(x=ts_df.index, y=ts_df["RS_Mom"], name="JdK RS-Momentum", line=dict(color="#ffaa00", width=2)), row=2, col=1)
    sub_fig.add_hline(y=100, line_dash="dash", line_color="#666", row=2, col=1)

    sub_fig.update_layout(
        height=650,
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font=dict(color="#e0e0e0"),
        hovermode="x unified",
        margin=dict(l=40, r=40, t=50, b=40)
    )
    sub_fig.update_xaxes(showgrid=True, gridcolor="#222")
    sub_fig.update_yaxes(showgrid=True, gridcolor="#222")
    st.plotly_chart(sub_fig, use_container_width=True)

# TAB 4: PRO DATA MATRIX & SIGNALS
with tab4:
    st.markdown(f"### 📋 {timeframe} Rotational Rankings & Trajectory Signals ({as_of_date})")

    display_df = dash_df[dash_df["Quadrant"].isin(quadrant_filter)].drop(columns=["Ticker"])
    sort_metric = st.selectbox(
        "Sort rankings by:",
        ["Rotation Score", "Strength (RS-Ratio)", "Momentum (RS-Mom)", "Excess Return (20 bars) %", "Velocity"],
        index=0,
        key="matrix_sort_metric",
    )
    display_df = display_df.sort_values(sort_metric, ascending=False, na_position="last")
    bar_min = float(min(85.0, dash_df["Strength (RS-Ratio)"].min(), dash_df["Momentum (RS-Mom)"].min()))
    bar_max = float(max(115.0, dash_df["Strength (RS-Ratio)"].max(), dash_df["Momentum (RS-Mom)"].max()))

    st.dataframe(
        display_df,
        column_config={
            "Str Chg": st.column_config.NumberColumn("1-Bar Str Δ", format="%+.2f"),
            "Mom Chg": st.column_config.NumberColumn("1-Bar Mom Δ", format="%+.2f"),
            "Strength (RS-Ratio)": st.column_config.ProgressColumn("Strength (RS-Ratio)", format="%.2f", min_value=bar_min, max_value=bar_max),
            "Momentum (RS-Mom)": st.column_config.ProgressColumn("Momentum (RS-Mom)", format="%.2f", min_value=bar_min, max_value=bar_max),
            "RRG Distance": st.column_config.NumberColumn("Radius (Dist)", format="%.2f", help="Distance from the (100, 100) center benchmark."),
            "Velocity": st.column_config.NumberColumn("Tail Velocity", format="%.2f", help="Speed of movement over the most recent bar."),
            "Heading (°)": st.column_config.NumberColumn("Heading", format="%.1f°", help="0°-90° = Northeast (strengthening & accelerating)."),
            "Rotation Score": st.column_config.ProgressColumn("Rotation Score", format="%.1f", min_value=0, max_value=100,
                                                               help="Cross-sectional heuristic score based on RS rank, momentum rank, velocity rank, and direction."),
            "RS Rank": st.column_config.NumberColumn("RS Rank", format="%.1f"),
            "Momentum Rank": st.column_config.NumberColumn("Momentum Rank", format="%.1f"),
            "Velocity Rank": st.column_config.NumberColumn("Velocity Rank", format="%.1f"),
        },
        use_container_width=True,
        hide_index=True
    )

    csv_bytes = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export RRG Matrix to CSV",
        data=csv_bytes,
        file_name=f"rrg_matrix_{timeframe.lower()}_{as_of_date}.csv",
        mime="text/csv"
    )

# TAB 5: ROTATION WATCHLIST & ALERTS
with tab5:
    st.markdown("### ⭐ Rotation Watchlist & Signal Filters")
    st.caption("These are rule-based research flags, not automated orders or guaranteed buy/sell signals.")

    w1, w2, w3 = st.columns(3)
    with w1:
        min_rotation_score = st.slider("Minimum Rotation Score", 0, 100, 60, 5)
    with w2:
        signal_mode = st.selectbox(
            "Setup filter",
            ["All setups", "Bullish quadrants", "Fresh quadrant transitions", "Improving only", "Leading only"],
        )
    with w3:
        min_excess_return = st.slider("Minimum 20-bar excess return (%)", -30, 30, -5, 1)

    watch_df = dash_df.copy()
    watch_df = watch_df[watch_df["Rotation Score"] >= min_rotation_score]
    watch_df = watch_df[watch_df["Excess Return (20 bars) %"].isna() | (watch_df["Excess Return (20 bars) %"] >= min_excess_return)]

    if signal_mode == "Bullish quadrants":
        watch_df = watch_df[watch_df["Quadrant"].isin(["Leading 🟢", "Improving 🔵"])]
    elif signal_mode == "Fresh quadrant transitions":
        watch_df = watch_df[watch_df["Signal"].str.contains("Fresh|Breakout|Breakdown|Loss of Mom", case=False, na=False)]
    elif signal_mode == "Improving only":
        watch_df = watch_df[watch_df["Quadrant"] == "Improving 🔵"]
    elif signal_mode == "Leading only":
        watch_df = watch_df[watch_df["Quadrant"] == "Leading 🟢"]

    watch_df = watch_df.sort_values(["Rotation Score", "Strength (RS-Ratio)"], ascending=False)
    wc1, wc2, wc3 = st.columns(3)
    wc1.metric("Matching Setups", len(watch_df))
    wc2.metric("Leading / Improving", int(watch_df["Quadrant"].isin(["Leading 🟢", "Improving 🔵"]).sum()))
    fresh_count = int(watch_df["Signal"].str.contains("Fresh|Breakout", case=False, na=False).sum())
    wc3.metric("Fresh Bullish Transitions", fresh_count)

    if watch_df.empty:
        st.info("No assets match these filters. Lower the score or relax the excess-return threshold.")
    else:
        watch_display = watch_df.drop(columns=["Ticker"])
        st.dataframe(watch_display, use_container_width=True, hide_index=True)
        st.download_button(
            "📥 Download Watchlist CSV",
            data=watch_display.to_csv(index=False).encode("utf-8"),
            file_name=f"rrg_watchlist_{timeframe.lower()}_{as_of_date}.csv",
            mime="text/csv",
        )

    with st.expander("How Rotation Score is calculated"):
        st.markdown(
            "Rotation Score is a **cross-sectional ranking heuristic** calculated from the currently selected universe: "
            "40% RS-Ratio percentile rank, 35% RS-Momentum percentile rank, 15% velocity percentile rank, "
            "and 10% direction score. The direction score is higher when both RS-Ratio and RS-Momentum are rising. "
            "The score is not a probability, a forecast, or a substitute for risk management."
        )

# TAB 6: PERFORMANCE & RISK
with tab6:
    st.markdown("### 📊 Relative Performance, Correlation & Drawdown")
    valid_lookbacks = [lb for lb in (10, 20, 60) if f"Excess Return ({lb} bars) %" in dash_df.columns]
    perf_lookback = st.selectbox("Relative-performance lookback (bars)", valid_lookbacks, index=1 if 20 in valid_lookbacks else 0)
    excess_col = f"Excess Return ({perf_lookback} bars) %"
    perf_df = dash_df[["Symbol", "Quadrant", "Asset Return (" + str(perf_lookback) + " bars) %", "Benchmark Return (" + str(perf_lookback) + " bars) %", excess_col]].dropna(subset=[excess_col]).sort_values(excess_col)

    if perf_df.empty:
        st.info("Not enough historical bars for this relative-performance lookback. Try a shorter lookback or another timeframe.")
    else:
        perf_fig = go.Figure()
        perf_colors = ["#00c853" if v >= 0 else "#ff5252" for v in perf_df[excess_col]]
        perf_fig.add_trace(go.Bar(
            x=perf_df[excess_col], y=perf_df["Symbol"], orientation="h",
            marker_color=perf_colors,
            text=[f"{v:+.2f}%" for v in perf_df[excess_col]], textposition="outside",
            hovertemplate="%{y}<br>Excess return: %{x:.2f}%<extra></extra>",
            name="Excess Return",
        ))
        perf_fig.add_vline(x=0, line_color="#888", line_dash="dash")
        perf_fig.update_layout(
            title=f"Excess Return vs {benchmark.replace('.NS', '')} over {perf_lookback} bars",
            height=max(380, 28 * len(perf_df)),
            plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font=dict(color="#e0e0e0"),
            margin=dict(l=35, r=45, t=55, b=35), xaxis_title="Asset return minus benchmark return (%)",
            yaxis_title="", showlegend=False,
        )
        st.plotly_chart(perf_fig, use_container_width=True)
        st.dataframe(perf_df.sort_values(excess_col, ascending=False), use_container_width=True, hide_index=True)

    st.markdown("#### Return Correlation Matrix")
    correlation_symbols = [t for t in tickers_list if t in df.columns]
    if benchmark in df.columns and benchmark not in correlation_symbols:
        correlation_symbols.append(benchmark)
    if len(correlation_symbols) >= 2:
        return_data = df[correlation_symbols].pct_change().replace([np.inf, -np.inf], np.nan).dropna(how="all")
        corr = return_data.corr(min_periods=10)
        corr.index = [REVERSE_MAP.get(x, x.replace(".NS", "")) for x in corr.index]
        corr.columns = [REVERSE_MAP.get(x, x.replace(".NS", "")) for x in corr.columns]
        heatmap = go.Figure(data=go.Heatmap(
            z=corr.values, x=corr.columns, y=corr.index,
            zmin=-1, zmax=1, colorscale="RdBu", reversescale=True,
            colorbar=dict(title="Correlation"),
            hovertemplate="%{y} vs %{x}<br>Correlation: %{z:.2f}<extra></extra>",
        ))
        heatmap.update_layout(
            height=max(420, 30 * len(corr)),
            plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font=dict(color="#e0e0e0"),
            margin=dict(l=25, r=25, t=25, b=100), xaxis_tickangle=-45,
        )
        st.plotly_chart(heatmap, use_container_width=True)
        st.caption("Correlation is calculated from periodic returns, not price levels. It can change across market regimes.")
    else:
        st.info("Select at least two successfully downloaded assets to calculate return correlation.")

    st.markdown("#### Drawdown Inspector")
    drawdown_symbol_map = {row["Symbol"]: row["Ticker"] for _, row in dash_df.iterrows() if row["Ticker"] in full_rrg_series}
    if drawdown_symbol_map:
        drawdown_label = st.selectbox("Asset for drawdown comparison", list(drawdown_symbol_map.keys()), key="drawdown_asset")
        drawdown_ticker = drawdown_symbol_map[drawdown_label]
        dd_df = full_rrg_series[drawdown_ticker].tail(120).copy()
        asset_dd = (dd_df["Price"] / dd_df["Price"].cummax() - 1) * 100
        bench_dd = (dd_df["Benchmark"] / dd_df["Benchmark"].cummax() - 1) * 100
        dd_fig = go.Figure()
        dd_fig.add_trace(go.Scatter(x=dd_df.index, y=asset_dd, name=drawdown_label, fill="tozeroy", line=dict(width=2)))
        dd_fig.add_trace(go.Scatter(x=dd_df.index, y=bench_dd, name=benchmark.replace(".NS", "") + " benchmark", line=dict(width=2, dash="dot")))
        dd_fig.update_layout(
            title="Rolling-peak drawdown (last 120 bars)", yaxis_title="Drawdown (%)",
            height=420, hovermode="x unified", plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
            font=dict(color="#e0e0e0"), margin=dict(l=35, r=25, t=55, b=35),
        )
        dd_fig.update_yaxes(showgrid=True, gridcolor="#222")
        dd_fig.update_xaxes(showgrid=True, gridcolor="#222")
        st.plotly_chart(dd_fig, use_container_width=True)

