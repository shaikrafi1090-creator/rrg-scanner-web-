import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Set up the webpage configuration
st.set_page_config(layout="wide", page_title="Pro RRG Terminal", page_icon="📈", initial_sidebar_state="expanded")

# --- DICTIONARY OF MAJOR NSE ETFs (Expanded List) ---
NSE_INDICES = {
    # Broad Market
    'Nifty Next 50 (JUNIORBEES)': 'JUNIORBEES.NS',
    'Nifty Midcap 150 (MID150BEES)': 'MID150BEES.NS',
    'Nifty Smallcap 250 (SMA250BEES)': 'SMA250BEES.NS',
    
    # Major Sectors
    'Nifty Bank (BANKBEES)': 'BANKBEES.NS',
    'Nifty PSU Bank (PSUBNKBEES)': 'PSUBNKBEES.NS',
    'Nifty IT (ITBEES)': 'ITBEES.NS',
    'Nifty Pharma (PHARMABEES)': 'PHARMABEES.NS',
    'Nifty Healthcare (HEALTHY)': 'HEALTHY.NS',
    'Nifty FMCG (FMCGBEES)': 'FMCGBEES.NS',
    'Nifty Auto (AUTOBEES)': 'AUTOBEES.NS',
    'Nifty Metal (METALBEES)': 'METALBEES.NS',
    'Nifty Infra (INFRABEES)': 'INFRABEES.NS',
    'Nifty Consumption (CONSUMBEES)': 'CONSUMBEES.NS',
    
    # Thematic / Smart Beta
    'Nifty CPSE (CPSEETF)': 'CPSEETF.NS',
    'Nifty Div Opps (DIVOPPBEES)': 'DIVOPPBEES.NS',
    'Nifty Value 20 (NV20BEES)': 'NV20BEES.NS',
    
    # Commodities & International
    'Gold (GOLDBEES)': 'GOLDBEES.NS',
    'Silver (SILVERBEES)': 'SILVERBEES.NS',
    'Nasdaq 100 (MON100)': 'MON100.NS'
}
REVERSE_MAP = {v: k.split(" (")[0] for k, v in NSE_INDICES.items()} # Cleans name for chart

# --- SIDEBAR (WEBSITE NAVIGATION) ---
with st.sidebar:
    st.header("⚙️ Terminal Settings")
    
    # Pre-selected default ETFs
    default_selections = [
        'Nifty Bank (BANKBEES)', 'Nifty IT (ITBEES)', 'Nifty Pharma (PHARMABEES)', 
        'Nifty FMCG (FMCGBEES)', 'Nifty Auto (AUTOBEES)', 'Nifty Metal (METALBEES)',
        'Nifty PSU Bank (PSUBNKBEES)', 'Nifty Midcap 150 (MID150BEES)'
    ]
    
    selected_index_names = st.multiselect(
        "Select Sectors & ETFs:", options=list(NSE_INDICES.keys()),
        default=default_selections
    )
    
    custom_stocks_input = st.text_input("Add Individual Stocks (e.g. RELIANCE.NS):", value="")
    benchmark_input = st.text_input("Benchmark ETF:", value="NIFTYBEES.NS")
    
    with st.expander("🔧 Advanced Math Parameters"):
        jdk_period = st.slider("JdK Smoothing", 5, 30, 14)
        tail_weeks = st.slider("Tail Length", 1, 20, 6)

# --- DATA PROCESSING ---
tickers_list = [NSE_INDICES[name] for name in selected_index_names]
if custom_stocks_input.strip():
    tickers_list.extend([t.strip().upper() for t in custom_stocks_input.split(",") if t.strip()])

benchmark = benchmark_input.strip().upper()
download_list = tickers_list + [benchmark] if benchmark not in tickers_list else tickers_list

@st.cache_data(ttl=3600)
def load_data(symbols):
    df = yf.download(symbols, period='2y', interval='1d')['Close']
    
    if isinstance(df, pd.Series):
        df = df.to_frame(name=symbols[0])
        
    df = df.ffill().resample('W-FRI').last()
    df = df.dropna(axis=1, how='all').ffill().bfill()
    return df

with st.spinner("Syncing Live Market Data..."):
    df = load_data(download_list)

# Data Validation Alerts
if benchmark not in df.columns:
    st.error(f"Error: Benchmark {benchmark} not found or failed to download.")
    st.stop()

failed_tickers = [t for t in tickers_list if t not in df.columns]
if failed_tickers:
    st.warning(f"⚠️ Yahoo Finance missing data for: {', '.join(failed_tickers)}. They have been skipped.")

active_tickers = [t for t in tickers_list if t in df.columns]

if not active_tickers:
    st.error("No valid symbols to plot. Please add valid Yahoo Finance tickers.")
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

if rs_ratio_df.empty:
    st.error("Insufficient historical data for the selected timeframe.")
    st.stop()

# --- PLOTLY CHART ---
fig = go.Figure()

# Background Quadrants
fig.add_shape(type="rect", x0=100, y0=100, x1=200, y1=200, fillcolor="#008217", opacity=0.15, layer="below", line_width=0)
fig.add_shape(type="rect", x0=100, y0=0, x1=200, y1=100, fillcolor="#918000", opacity=0.15, layer="below", line_width=0)
fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100, fillcolor="#E0002B", opacity=0.15, layer="below", line_width=0)
fig.add_shape(type="rect", x0=0, y0=100, x1=100, y1=200, fillcolor="#00749D", opacity=0.15, layer="below", line_width=0)

# Labels
fig.add_annotation(x=0.98, y=0.98, xref="paper", yref="paper", text="LEADING", showarrow=False, font=dict(color="#00ff44", size=22, family="Arial Black"), xanchor="right", yanchor="top", opacity=0.4)
fig.add_annotation(x=0.98, y=0.02, xref="paper", yref="paper", text="WEAKENING", showarrow=False, font=dict(color="#ffdd00", size=22, family="Arial Black"), xanchor="right", yanchor="bottom", opacity=0.4)
fig.add_annotation(x=0.02, y=0.02, xref="paper", yref="paper", text="LAGGING", showarrow=False, font=dict(color="#ff3333", size=22, family="Arial Black"), xanchor="left", yanchor="bottom", opacity=0.4)
fig.add_annotation(x=0.02, y=0.98, xref="paper", yref="paper", text="IMPROVING", showarrow=False, font=dict(color="#33ccff", size=22, family="Arial Black"), xanchor="left", yanchor="top", opacity=0.4)

colors = px.colors.qualitative.Light24 + px.colors.qualitative.Dark24
dashboard_data = []

# Plot lines and dots
for i, ticker in enumerate(active_tickers):
    x_data = rs_ratio_df[ticker].values
    y_data = rs_mom_df[ticker].values
    color = colors[i % len(colors)]
    clean_name = REVERSE_MAP.get(ticker, ticker)
    
    # Tail
    fig.add_trace(go.Scatter(x=x_data, y=y_data, mode='lines+markers', marker=dict(size=7, color=color), line=dict(width=2.5, color=color), name=clean_name, text=dates, hovertemplate=f"<b>{clean_name}</b><br>Date: %{{text}}<br>RS-Ratio: %{{x:.2f}}<br>RS-Momentum: %{{y:.2f}}<extra></extra>"))
    # Head
    fig.add_trace(go.Scatter(x=[x_data[-1]], y=[y_data[-1]], mode='markers+text', marker=dict(size=14, color=color, line=dict(width=2, color='white')), text=[clean_name], textposition="top center", showlegend=False, hoverinfo='skip'))
    
    r, m = x_data[-1], y_data[-1]
    if r > 100 and m > 100: quad = "Leading 🟢"
    elif r > 100 and m < 100: quad = "Weakening 🟡"
    elif r < 100 and m < 100: quad = "Lagging 🔴"
    else: quad = "Improving 🔵"
    
    dashboard_data.append({"Symbol": clean_name, "RS-Ratio (Strength)": round(r, 2), "RS-Momentum": round(m, 2), "Quadrant": quad})

# Dynamic sizing
all_x = rs_ratio_df.values.flatten()
all_y = rs_mom_df.values.flatten()
x_min, x_max = max(80, all_x.min() - 1), min(120, all_x.max() + 1)
y_min, y_max = max(80, all_y.min() - 1), min(120, all_y.max() + 1)
center_spread = max(abs(x_max - 100), abs(100 - x_min), abs(y_max - 100), abs(100 - y_min)) + 0.5

fig.update_layout(
    xaxis_title="JdK RS-Ratio (Relative Strength) ➔", 
    yaxis_title="JdK RS-Momentum ➔", 
    xaxis=dict(range=[100 - center_spread, 100 + center_spread], zeroline=False, showgrid=True, gridcolor='#333'), 
    yaxis=dict(range=[100 - center_spread, 100 + center_spread], zeroline=False, showgrid=True, gridcolor='#333'), 
    plot_bgcolor='#0e1117', paper_bgcolor='#0e1117', font=dict(color='#e0e0e0'), height=700, margin=dict(l=40, r=40, t=40, b=40), 
    shapes=[dict(type="line", x0=100, x1=100, y0=0, y1=200, line=dict(color="#555", width=1.5)), dict(type="line", x0=0, x1=200, y0=100, y1=100, line=dict(color="#555", width=1.5))]
)

# --- WEBSITE UI LAYOUT ---
st.title("📈 Institutional RRG Terminal (ETF Based)")
st.markdown("Monitor accurate sector rotation and momentum shifts using Nifty ETFs.")

# Top Metric Cards
dash_df = pd.DataFrame(dashboard_data).sort_values(by="RS-Ratio (Strength)", ascending=False)
leaders = dash_df[dash_df["Quadrant"] == "Leading 🟢"]["Symbol"].tolist()
laggers = dash_df[dash_df["Quadrant"] == "Lagging 🔴"]["Symbol"].tolist()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Top Leader", leaders[0] if leaders else "None", "Strong Momentum")
with col2:
    st.metric("Deepest Lagger", laggers[-1] if laggers else "None", "-Weak Momentum")
with col3:
    st.metric("Assets Tracked", len(active_tickers), f"vs NIFTYBEES")

st.markdown("---")

# Tabs for Website feel
tab1, tab2 = st.tabs(["🎯 Interactive Rotation Chart", "📋 Data & Rankings"])

with tab1:
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("### Current Sector Rankings")
    st.dataframe(dash_df, use_container_width=True, hide_index=True)
