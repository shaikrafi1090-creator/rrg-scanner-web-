import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# Set up the webpage configuration
st.set_page_config(
    layout="wide",
    page_title="Pro RRG Terminal",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# --- EXPANDED DICTIONARY OF MAJOR NSE ETFs & INDICES ---
NSE_INDICES = {
    # Broad Market & Cap-Based
    'Nifty 50 (NIFTYBEES)': 'NIFTYBEES.NS',
    'Nifty Next 50 (JUNIORBEES)': 'JUNIORBEES.NS',
    'Nifty Midcap 150 (MID150BEES)': 'MID150BEES.NS',
    'Nifty Smallcap 250 (HDFCSML250)': 'HDFCSML250.NS',
    'Nifty LargeMidcap 250 (ZERODHA)': 'TOP100CASE.NS',

    # Sectoral ETFs & Indices
    'Nifty Bank (BANKBEES)': 'BANKBEES.NS',
    'Nifty PSU Bank (PSUBNKBEES)': 'PSUBNKBEES.NS',
    'Nifty Private Bank (SBIETFPB)': 'SBIETFPB.NS',
    'Nifty IT (ITBEES)': 'ITBEES.NS',
    'Nifty Pharma (PHARMABEES)': 'PHARMABEES.NS',
    'Nifty Healthcare (HEALTHY)': 'HEALTHY.NS',
    'Nifty FMCG (FMCGBEES)': 'FMCGBEES.NS',
    'Nifty Auto (AUTOBEES)': 'AUTOBEES.NS',
    'Nifty Metal (METALBEES)': 'METALBEES.NS',
    'Nifty Infra (INFRABEES)': 'INFRABEES.NS',
    'Nifty Financial Services (BFSI)': 'BFSI.NS',
    'Nifty Realty (MOREALTY)': 'MOREALTY.NS',

    # Thematic & Smart Beta / Factor ETFs
    'Nifty Consumption (CONSUMBEES)': 'CONSUMBEES.NS',
    'Nifty CPSE (CPSEETF)': 'CPSEETF.NS',
    'Nifty Div Opps (DIVOPPBEES)': 'DIVOPPBEES.NS',
    'Nifty Value 20 (NV20BEES)': 'NV20BEES.NS',
    'Nifty India Defence (MODEFENCE)': 'MODEFENCE.NS',
    'Nifty Manufacturing (MAFG)': 'MAKEINDIA.NS',
    'Nifty Commodities (^CNXCMDT)': '^CNXCMDT',
    'Nifty Alpha 50 (ALPHA)': 'ALPHA.NS',
    'Nifty 200 Momentum 30 (MOM30IETF)': 'MOM30IETF.NS',

    # Commodities & Global
    'Gold (GOLDBEES)': 'GOLDBEES.NS',
    'Silver (SILVERBEES)': 'SILVERBEES.NS',
    'Nasdaq 100 (MON100)': 'MON100.NS',
    'NYSE FANG+ (MAFANG)': 'MAFANG.NS'
}

# Clean fallback mapping dictionary generator
REVERSE_MAP = {v: k.split(" (")[0] for k, v in NSE_INDICES.items()}

# --- SIDEBAR (WEBSITE NAVIGATION) ---
with st.sidebar:
    st.header("⚙️ Terminal Settings")

    timeframe = st.selectbox(
        "⏳ Select Timeframe:",
        ["Daily", "Weekly", "Monthly"],
        index=1,
        help="Daily for short-term, Weekly for medium, Monthly for long-term."
    )

    default_selections = [
        'Nifty IT (ITBEES)',
        'Nifty Pharma (PHARMABEES)',
        'Nifty Healthcare (HEALTHY)',
        'Nifty Auto (AUTOBEES)',
        'Nifty Metal (METALBEES)',
        'Nifty Infra (INFRABEES)',
        'Nifty Realty (MOREALTY)'
    ]

    selected_index_names = st.multiselect(
        "📊 Select Sectors & ETFs:",
        options=list(NSE_INDICES.keys()),
        default=default_selections
    )

    custom_stocks_input = st.text_input("➕ Add Stocks (e.g. RELIANCE.NS, TCS.NS):", value="")
    benchmark_input = st.text_input("🎯 Benchmark ETF:", value="NIFTYBEES.NS")

    with st.expander("🔧 Advanced Math Parameters"):
        jdk_period = st.slider("JdK Smoothing", 5, 52, 14)
        tail_weeks = st.slider("Tail Length (Periods)", 1, 52, 6)

# --- DATA PROCESSING ---
raw_tickers = [NSE_INDICES[name] for name in selected_index_names]
if custom_stocks_input.strip():
    raw_tickers.extend([t.strip().upper() for t in custom_stocks_input.split(",") if t.strip()])

# Deduplicate while preserving order
tickers_list = list(dict.fromkeys(raw_tickers))
benchmark = benchmark_input.strip().upper()

if not benchmark:
    st.error("Please provide a valid Benchmark ticker.")
    st.stop()

download_list = list(dict.fromkeys(tickers_list + [benchmark]))


@st.cache_data(ttl=3600)
def load_data(symbols, tf):
    # Longer periods ensure Monthly/Weekly charts have enough warmup bars for large JdK sliders
    period = "2y" if tf == "Daily" else ("5y" if tf == "Weekly" else "10y")
    raw = yf.download(symbols, period=period, interval="1d", progress=False, auto_adjust=True)

    if raw.empty:
        return pd.DataFrame()

    df = raw["Close"] if "Close" in raw else raw

    if isinstance(df, pd.Series):
        df = df.to_frame(name=symbols[0])

    # Forward-fill minor holiday gaps (up to 5 days) without backfilling pre-IPO dates
    df = df.ffill(limit=5)

    if tf == "Weekly":
        df = df.resample("W-FRI").last()
    elif tf == "Monthly":
        try:
            df = df.resample("ME").last()
        except ValueError:
            df = df.resample("M").last()

    df = df.dropna(axis=1, how="all")
    return df


with st.spinner(f"Syncing {timeframe} Market Data..."):
    df = load_data(download_list, timeframe)

if df.empty or benchmark not in df.columns:
    st.error(f"Error: Benchmark '{benchmark}' failed to download. Check ticker symbol correctness.")
    st.stop()

active_tickers = [t for t in tickers_list if t in df.columns and t != benchmark]
missing_tickers = [t for t in tickers_list if t not in df.columns]

if missing_tickers:
    st.sidebar.warning(f"⚠️ Failed to load: {', '.join(missing_tickers)}")

if not active_tickers:
    st.error("No valid symbols to plot. Select at least one symbol distinct from the benchmark.")
    st.stop()

# --- MATH CALCULATIONS (PER TICKER TO PREVENT NaN CONTAGION) ---
ticker_tails = {}
skipped_short_history = []

for ticker in active_tickers:
    pair = df[[ticker, benchmark]].dropna()
    if len(pair) < (jdk_period * 2 + 12):
        skipped_short_history.append(ticker)
        continue

    rs = pair[ticker] / pair[benchmark]
    rs_ema = rs.ewm(span=jdk_period, adjust=False).mean()
    rs_ratio = 100 * rs_ema / rs_ema.rolling(window=jdk_period).mean()
    roc = (rs_ratio / rs_ratio.shift(10)) - 1
    rs_momentum = 100 + 100 * roc.ewm(span=jdk_period, adjust=False).mean()

    valid_tail = pd.DataFrame({
        "ratio": rs_ratio,
        "mom": rs_momentum
    }).dropna().tail(tail_weeks + 1)

    if len(valid_tail) >= 2:
        ticker_tails[ticker] = valid_tail
    else:
        skipped_short_history.append(ticker)

if skipped_short_history:
    st.sidebar.info(f"ℹ️ Skipped (insufficient {timeframe} history): {', '.join(skipped_short_history)}")

if not ticker_tails:
    st.error(f"Insufficient {timeframe} data across selected symbols to calculate Momentum Deltas. Try lowering JdK Smoothing.")
    st.stop()

# --- PLOTLY CHART & METRICS SETUP ---
fig = go.Figure()

colors = px.colors.qualitative.Light24 + px.colors.qualitative.Dark24
dashboard_data = []
all_x, all_y = [], []

for i, (ticker, tail_df) in enumerate(ticker_tails.items()):
    x_data = tail_df["ratio"].values
    y_data = tail_df["mom"].values
    dates = tail_df.index.strftime("%Y-%m-%d").tolist()

    all_x.extend(x_data)
    all_y.extend(y_data)

    color = colors[i % len(colors)]
    clean_name = REVERSE_MAP.get(ticker, ticker)

    r_chg = float(x_data[-1] - x_data[-2])
    m_chg = float(y_data[-1] - y_data[-2])
    r, m = float(x_data[-1]), float(y_data[-1])

    fig.add_trace(go.Scatter(
        x=x_data,
        y=y_data,
        mode="lines+markers",
        marker=dict(size=7, color=color),
        line=dict(width=3, color=color),
        name=clean_name,
        text=dates,
        hovertemplate=f"<b>{clean_name}</b><br>Date: %{{text}}<br>Strength: %{{x:.2f}}<br>Momentum: %{{y:.2f}}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=[x_data[-1]],
        y=[y_data[-1]],
        mode="markers+text",
        marker=dict(size=14, color=color, line=dict(width=2, color="white")),
        text=[clean_name],
        textposition="top center",
        showlegend=False,
        hoverinfo="skip"
    ))

    if r >= 100 and m >= 100:
        quad = "Leading 🟢"
    elif r >= 100 and m < 100:
        quad = "Weakening 🟡"
    elif r < 100 and m < 100:
        quad = "Lagging 🔴"
    else:
        quad = "Improving 🔵"

    dashboard_data.append({
        "Symbol": clean_name,
        "Strength (RS-Ratio)": round(r, 2),
        "Str Chg": round(r_chg, 2),
        "Momentum (RS-Mom)": round(m, 2),
        "Mom Chg": round(m_chg, 2),
        "Quadrant": quad
    })

dash_df = pd.DataFrame(dashboard_data).sort_values(by="Strength (RS-Ratio)", ascending=False)

# Auto-Insights Logic
leaders_df = dash_df[dash_df["Quadrant"] == "Leading 🟢"]
laggers_df = dash_df[dash_df["Quadrant"] == "Lagging 🔴"]
top_leader = leaders_df.iloc[0] if not leaders_df.empty else dash_df.iloc[0]
top_lagger = laggers_df.iloc[-1] if not laggers_df.empty else dash_df.iloc[-1]

# Dynamic Symmetric Axis Bounds Around 100
all_x_arr = np.array(all_x)
all_y_arr = np.array(all_y)
max_dev = max(
    np.abs(all_x_arr - 100).max(),
    np.abs(all_y_arr - 100).max(),
    2.0
)
center_spread = max_dev * 1.15
low_bound, high_bound = 100 - center_spread, 100 + center_spread

# Background Quadrants (using add_shape without overwriting in update_layout)
fig.add_shape(type="rect", x0=100, y0=100, x1=high_bound, y1=high_bound, fillcolor="#008217", opacity=0.12, layer="below", line_width=0)
fig.add_shape(type="rect", x0=100, y0=low_bound, x1=high_bound, y1=100, fillcolor="#918000", opacity=0.12, layer="below", line_width=0)
fig.add_shape(type="rect", x0=low_bound, y0=low_bound, x1=100, y1=100, fillcolor="#E0002B", opacity=0.12, layer="below", line_width=0)
fig.add_shape(type="rect", x0=low_bound, y0=100, x1=100, y1=high_bound, fillcolor="#00749D", opacity=0.12, layer="below", line_width=0)

# Crosshair Lines at 100
fig.add_vline(x=100, line_width=1.5, line_color="#666")
fig.add_hline(y=100, line_width=1.5, line_color="#666")

# Quadrant Labels
fig.add_annotation(x=0.98, y=0.98, xref="paper", yref="paper", text="LEADING", showarrow=False, font=dict(color="#00ff44", size=24, family="Arial Black"), xanchor="right", yanchor="top", opacity=0.3)
fig.add_annotation(x=0.98, y=0.02, xref="paper", yref="paper", text="WEAKENING", showarrow=False, font=dict(color="#ffdd00", size=24, family="Arial Black"), xanchor="right", yanchor="bottom", opacity=0.3)
fig.add_annotation(x=0.02, y=0.02, xref="paper", yref="paper", text="LAGGING", showarrow=False, font=dict(color="#ff3333", size=24, family="Arial Black"), xanchor="left", yanchor="bottom", opacity=0.3)
fig.add_annotation(x=0.02, y=0.98, xref="paper", yref="paper", text="IMPROVING", showarrow=False, font=dict(color="#33ccff", size=24, family="Arial Black"), xanchor="left", yanchor="top", opacity=0.3)

fig.update_layout(
    xaxis_title="Relative Strength (JdK RS-Ratio) ➔",
    yaxis_title="Relative Momentum (JdK RS-Momentum) ➔",
    xaxis=dict(range=[low_bound, high_bound], zeroline=False, showgrid=True, gridcolor="#222"),
    yaxis=dict(range=[low_bound, high_bound], zeroline=False, showgrid=True, gridcolor="#222"),
    plot_bgcolor="#0e1117",
    paper_bgcolor="#0e1117",
    font=dict(color="#e0e0e0"),
    height=750,
    margin=dict(l=40, r=40, t=40, b=40),
    showlegend=False
)

# --- WEBSITE UI LAYOUT ---
st.title("⚡ Pro RRG Trading Terminal")

st.info(
    f"💡 **Market Insight ({timeframe}):** **{top_leader['Symbol']}** is currently dominating the market "
    f"with strong relative strength, while **{top_lagger['Symbol']}** is showing the deepest weakness."
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🌟 Top Leader", top_leader["Symbol"], f"{top_leader['Str Chg']:+.2f} Strength")
with col2:
    st.metric("⚠️ Deepest Lagger", top_lagger["Symbol"], f"{top_lagger['Str Chg']:+.2f} Strength")
with col3:
    st.metric("⏱️ Timeframe", f"{timeframe} Chart", "Active")
with col4:
    st.metric("📊 Assets Tracked", len(ticker_tails), f"vs {benchmark.replace('.NS', '')}")

st.markdown("---")

tab1, tab2 = st.tabs(["🎯 Interactive Rotation Chart", "📋 Pro Data Matrix"])

with tab1:
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown(f"### {timeframe} Sector Rankings & Momentum Changes")
    bar_min = float(min(85.0, dash_df["Strength (RS-Ratio)"].min(), dash_df["Momentum (RS-Mom)"].min()))
    bar_max = float(max(115.0, dash_df["Strength (RS-Ratio)"].max(), dash_df["Momentum (RS-Mom)"].max()))

    st.dataframe(
        dash_df,
        column_config={
            "Str Chg": st.column_config.NumberColumn("1-Period Str Chg", format="%+.2f"),
            "Mom Chg": st.column_config.NumberColumn("1-Period Mom Chg", format="%+.2f"),
            "Strength (RS-Ratio)": st.column_config.ProgressColumn("Strength", format="%.2f", min_value=bar_min, max_value=bar_max),
            "Momentum (RS-Mom)": st.column_config.ProgressColumn("Momentum", format="%.2f", min_value=bar_min, max_value=bar_max),
        },
        use_container_width=True,
        hide_index=True
    )
