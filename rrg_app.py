import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Set up the webpage configuration
st.set_page_config(layout="wide", page_title="Pro RRG Terminal", page_icon="⚡", initial_sidebar_state="expanded")

# --- EXPANDED DICTIONARY OF MAJOR NSE ETFs & THEMATICS ---
NSE_INDICES = {
    # Broad Market & Cap-Based
    'Nifty 50 (NIFTYBEES)': 'NIFTYBEES.NS',
    'Nifty Next 50 (JUNIORBEES)': 'JUNIORBEES.NS', 
    'Nifty Midcap 150 (MID150BEES)': 'MID150BEES.NS', 
    'Nifty Smallcap 250 (SMA250BEES)': 'SMA250BEES.NS',
    'Nifty LargeMidcap 250': 'HDFCNLI.NS', # Example ticker, or standard proxy
    
    # Sectoral ETFs
    'Nifty Bank (BANKBEES)': 'BANKBEES.NS', 
    'Nifty PSU Bank (PSUBNKBEES)': 'PSUBNKBEES.NS', 
    'Nifty Private Bank': 'SETFPRBK.NS',
    'Nifty IT (ITBEES)': 'ITBEES.NS',
    'Nifty Pharma (PHARMABEES)': 'PHARMABEES.NS', 
    'Nifty Healthcare (HEALTHY)': 'HEALTHY.NS', 
    'Nifty FMCG (FMCGBEES)': 'FMCGBEES.NS',
    'Nifty Auto (AUTOBEES)': 'AUTOBEES.NS', 
    'Nifty Metal (METALBEES)': 'METALBEES.NS', 
    'Nifty Infra (INFRABEES)': 'INFRABEES.NS',
    'Nifty Financial Services (FINNIFTY)': 'NIFTYFINV.NS',
    'Nifty Realty': 'REALTYSGB.NS', # Proxy/Ticker placeholder or specific ETF
    
    # Thematic & Smart Beta / Factor ETFs
    'Nifty Consumption (CONSUMBEES)': 'CONSUMBEES.NS', 
    'Nifty CPSE (CPSEETF)': 'CPSEETF.NS', 
    'Nifty Div Opps (DIVOPPBEES)': 'DIVOPPBEES.NS',
    'Nifty Value 20 (NV20BEES)': 'NV20BEES.NS', 
    'Nifty India Defence': 'DEFENCE.NS', # Check specific ticker if changing, using standard mapping
    'Nifty Manufacturing': 'MAFG.NS', 
    'Nifty Commodities': 'COMMODITIE.NS',
    'Nifty Alpha 50': 'ALPHA.NS',
    'Nifty 200 Momentum 30': 'MOM30.NS',

    # Commodities & Global
    'Gold (GOLDBEES)': 'GOLDBEES.NS', 
    'Silver (SILVERBEES)': 'SILVERBEES.NS', 
    'Nasdaq 100 (MON100)': 'MON100.NS',
    'NYSE FANG+': 'FANG.NS'
}

# Clean fallback mapping dictionary generator
REVERSE_MAP = {v: k.split(" (")[0] for k, v in NSE_INDICES.items()}

# --- SIDEBAR (WEBSITE NAVIGATION) ---
with st.sidebar:
    st.header("⚙️ Terminal Settings")
    
    timeframe = st.selectbox("⏳ Select Timeframe:", ["Daily", "Weekly", "Monthly"], index=1, help="Daily for short-term, Weekly for medium, Monthly for long-term.")
    
    default_selections = ['Nifty Bank (BANKBEES)', 'Nifty IT (ITBEES)', 'Nifty Pharma (PHARMABEES)', 'Nifty FMCG (FMCGBEES)', 'Nifty Auto (AUTOBEES)', 'Nifty Metal (METALBEES)']
    selected_index_names = st.multiselect("📊 Select Sectors & ETFs:", options=list(NSE_INDICES.keys()), default=default_selections)
    
    custom_stocks_input = st.text_input("➕ Add Stocks (e.g. RELIANCE.NS, TCS.NS):", value="")
    benchmark_input = st.text_input("🎯 Benchmark ETF:", value="NIFTYBEES.NS")
    
    with st.expander("🔧 Advanced Math Parameters"):
        jdk_period = st.slider("JdK Smoothing", 5, 30, 14)
        tail_weeks = st.slider("Tail Length (Periods)", 1, 30, 6)

# --- DATA PROCESSING ---
tickers_list = [NSE_INDICES[name] for name in selected_index_names]
if custom_stocks_input.strip():
    tickers_list.extend([t.strip().upper() for t in custom_stocks_input.split(",") if t.strip()])

benchmark = benchmark_input.strip().upper()
download_list = tickers_list + [benchmark] if benchmark not in tickers_list else tickers_list

@st.cache_data(ttl=3600)
def load_data(symbols, tf):
    period = "1y" if tf == "Daily" else ("3y" if tf == "Weekly" else "5y")
    df = yf.download(symbols, period=period, interval='1d', progress=False)['Close']
    
    if isinstance(df, pd.Series):
        df = df.to_frame(name=symbols[0])
        
    if tf == "Weekly":
        df = df.ffill().resample('W-FRI').last()
    elif tf == "Monthly":
        df = df.ffill().resample('ME').last()
    else:
        df = df.ffill()
        
    df = df.dropna(axis=1, how='all').ffill().bfill()
    return df

with st.spinner(f"Syncing {timeframe} Market Data..."):
    df = load_data(download_list, timeframe)

if benchmark not in df.columns:
    st.error(f"Error: Benchmark {benchmark} failed to download. Check ticker symbol correctness.")
    st.stop()

active_tickers = [t for t in tickers_list if t in df.columns]

if not active_tickers:
    st.error("No valid symbols to plot.")
    st.stop()

# --- MATH CALCULATIONS ---
rs_ratio_df = pd.DataFrame(index=df.index)
rs_mom_df = pd.DataFrame(index=df.index)

for ticker in active_tickers:
    rs = df[ticker] / df[benchmark]
    rs_ema = rs.ewm(span=jdk_period, adjust=False).mean()
    rs_ratio = 100 * rs_ema / rs_ema.rolling(window=jdk_period).mean()
    roc = (rs_ratio / rs_ratio.shift(10)) - 1
    rs_momentum = 100 + 100 * roc.ewm(span=jdk_period, adjust=False).mean()
    rs_ratio_df[ticker] = rs_ratio
    rs_mom_df[ticker] = rs_momentum

rs_ratio_df = rs_ratio_df.dropna().tail(tail_weeks + 1)
rs_mom_df = rs_mom_df.dropna().tail(tail_weeks + 1)
dates = rs_ratio_df.index.strftime('%Y-%m-%d').tolist()

if len(rs_ratio_df) < 2:
    st.error(f"Insufficient {timeframe} data to calculate Momentum Deltas.")
    st.stop()

# --- PLOTLY CHART & METRICS SETUP ---
fig = go.Figure()

# Background Quadrants
fig.add_shape(type="rect", x0=100, y0=100, x1=200, y1=200, fillcolor="#008217", opacity=0.12, layer="below", line_width=0)
fig.add_shape(type="rect", x0=100, y0=0, x1=200, y1=100, fillcolor="#918000", opacity=0.12, layer="below", line_width=0)
fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100, fillcolor="#E0002B", opacity=0.12, layer="below", line_width=0)
fig.add_shape(type="rect", x0=0, y0=100, x1=100, y1=200, fillcolor="#00749D", opacity=0.12, layer="below", line_width=0)

# Quadrant Labels
fig.add_annotation(x=0.98, y=0.98, xref="paper", yref="paper", text="LEADING", showarrow=False, font=dict(color="#00ff44", size=24, family="Arial Black"), xanchor="right", yanchor="top", opacity=0.3)
fig.add_annotation(x=0.98, y=0.02, xref="paper", yref="paper", text="WEAKENING", showarrow=False, font=dict(color="#ffdd00", size=24, family="Arial Black"), xanchor="right", yanchor="bottom", opacity=0.3)
fig.add_annotation(x=0.02, y=0.02, xref="paper", yref="paper", text="LAGGING", showarrow=False, font=dict(color="#ff3333", size=24, family="Arial Black"), xanchor="left", yanchor="bottom", opacity=0.3)
fig.add_annotation(x=0.02, y=0.98, xref="paper", yref="paper", text="IMPROVING", showarrow=False, font=dict(color="#33ccff", size=24, family="Arial Black"), xanchor="left", yanchor="top", opacity=0.3)

colors = px.colors.qualitative.Light24 + px.colors.qualitative.Dark24
dashboard_data = []

for i, ticker in enumerate(active_tickers):
    x_data = rs_ratio_df[ticker].values
    y_data = rs_mom_df[ticker].values
    color = colors[i % len(colors)]
    clean_name = REVERSE_MAP.get(ticker, ticker)
    
    r_chg = x_data[-1] - x_data[-2]
    m_chg = y_data[-1] - y_data[-2]
    
    fig.add_trace(go.Scatter(x=x_data, y=y_data, mode='lines+markers', marker=dict(size=7, color=color), line=dict(width=3, color=color), name=clean_name, text=dates, hovertemplate=f"<b>{clean_name}</b><br>Date: %{{text}}<br>Strength: %{{x:.2f}}<br>Momentum: %{{y:.2f}}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[x_data[-1]], y=[y_data[-1]], mode='markers+text', marker=dict(size=14, color=color, line=dict(width=2, color='white')), text=[clean_name], textposition="top center", showlegend=False, hoverinfo='skip'))
    
    r, m = x_data[-1], y_data[-1]
    if r > 100 and m > 100: quad = "Leading 🟢"
    elif r > 100 and m < 100: quad = "Weakening 🟡"
    elif r < 100 and m < 100: quad = "Lagging 🔴"
    else: quad = "Improving 🔵"
    
    dashboard_data.append({
        "Symbol": clean_name, 
        "Strength (RS-Ratio)": round(r, 2), "Str Chg": round(r_chg, 2), 
        "Momentum (RS-Mom)": round(m, 2), "Mom Chg": round(m_chg, 2), 
        "Quadrant": quad
    })

dash_df = pd.DataFrame(dashboard_data).sort_values(by="Strength (RS-Ratio)", ascending=False)

# Auto-Insights Logic
leaders_df = dash_df[dash_df["Quadrant"] == "Leading 🟢"]
laggers_df = dash_df[dash_df["Quadrant"] == "Lagging 🔴"]
top_leader = leaders_df.iloc[0] if not leaders_df.empty else dash_df.iloc[0]
top_lagger = laggers_df.iloc[-1] if not laggers_df.empty else dash_df.iloc[-1]

all_x = rs_ratio_df.values.flatten()
all_y = rs_mom_df.values.flatten()
x_min, x_max = max(80, all_x.min() - 1), min(120, all_x.max() + 1)
y_min, y_max = max(80, all_y.min() - 1), min(120, all_y.max() + 1)
center_spread = max(abs(x_max - 100), abs(100 - x_min), abs(y_max - 100), abs(100 - y_min)) + 0.5

fig.update_layout(
    xaxis_title="Relative Strength (JdK RS-Ratio) ➔", yaxis_title="Relative Momentum (JdK RS-Momentum) ➔", 
    xaxis=dict(range=[100 - center_spread, 100 + center_spread], zeroline=False, showgrid=True, gridcolor='#222'), 
    yaxis=dict(range=[100 - center_spread, 100 + center_spread], zeroline=False, showgrid=True, gridcolor='#222'), 
    plot_bgcolor='#0e1117', paper_bgcolor='#0e1117', font=dict(color='#e0e0e0'), height=750, margin=dict(l=40, r=40, t=40, b=40), 
    shapes=[dict(type="line", x0=100, x1=100, y0=0, y1=200, line=dict(color="#666", width=1.5)), dict(type="line", x0=0, x1=200, y0=100, y1=100, line=dict(color="#666", width=1.5))],
    showlegend=False
)

# --- WEBSITE UI LAYOUT ---
st.title("⚡ Pro RRG Trading Terminal")

st.info(f"💡 **Market Insight ({timeframe}):** **{top_leader['Symbol']}** is currently dominating the market with strong momentum, while **{top_lagger['Symbol']}** is showing the deepest weakness.")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🌟 Top Leader", top_leader['Symbol'], f"{top_leader['Str Chg']:+.2f} Strength")
with col2:
    st.metric("⚠️ Deepest Lagger", top_lagger['Symbol'], f"{top_lagger['Str Chg']:+.2f} Strength")
with col3:
    st.metric("⏱️ Timeframe", f"{timeframe} Chart", "Active")
with col4:
    st.metric("📊 Assets Tracked", len(active_tickers), f"vs {benchmark_input.replace('.NS', '')}")

st.markdown("---")

tab1, tab2 = st.tabs(["🎯 Interactive Rotation Chart", "📋 Pro Data Matrix"])

with tab1:
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown(f"### {timeframe} Sector Rankings & Momentum Changes")
    st.dataframe(
        dash_df,
        column_config={
            "Str Chg": st.column_config.NumberColumn("1-Period Str Chg", format="%+.2f"),
            "Mom Chg": st.column_config.NumberColumn("1-Period Mom Chg", format="%+.2f"),
            "Strength (RS-Ratio)": st.column_config.ProgressColumn("Strength", format="%.2f", min_value=85, max_value=115),
            "Momentum (RS-Mom)": st.column_config.ProgressColumn("Momentum", format="%.2f", min_value=85, max_value=115),
        },
        use_container_width=True, hide_index=True
    )
