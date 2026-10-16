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

    # Sectoral ETFs & Indices
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
REVERSE_MAP.update({
    "^CNXMETAL": "Nifty Metal",
    "^CNXFMCG": "Nifty FMCG",
    "^CNXCMDT": "Nifty Commodities",
    "NIFTYBEES.NS": "Nifty 50",
    "MON100.NS": "Nasdaq 100"
})

# --- SIDEBAR (TERMINAL CONTROLS) ---
with st.sidebar:
    st.header("⚙️ Institutional Settings")

    timeframe = st.selectbox(
        "⏳ Base Timeframe:",
        ["Daily", "Weekly", "Monthly"],
        index=1,
        help="Primary timeframe for RRG calculations."
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
        "📊 Select Sectors & Assets:",
        options=list(NSE_INDICES.keys()),
        default=default_selections
    )

    custom_stocks_input = st.text_input("➕ Add Custom Tickers:", value="")
    benchmark_input = st.text_input("🎯 Benchmark Asset:", value="NIFTYBEES.NS")

    st.markdown("---")
    st.subheader("⏪ Time-Machine & Filters")
    replay_offset = st.slider("Scrub Back (Periods Ago):", 0, 30, 0)

    quadrant_filter = st.multiselect(
        "🔍 Filter Quadrants:",
        options=["Leading 🟢", "Weakening 🟡", "Lagging 🔴", "Improving 🔵"],
        default=["Leading 🟢", "Weakening 🟡", "Lagging 🔴", "Improving 🔵"]
    )

    with st.expander("🔧 Advanced Parameters"):
        jdk_period = st.slider("JdK Smoothing Period", 5, 52, 14)
        tail_weeks = st.slider("Tail Length", 1, 30, 6)
        spline_smooth = st.checkbox("Curved Spline Tails", value=True)
        show_labels = st.checkbox("Show Labels on Chart", value=True)


# --- CORE FUNCTIONS ---
@st.cache_data(ttl=3600)
def load_multi_tf_data(symbols):
    """Downloads daily data and generates resampled weekly and monthly frames for MTF alignment."""
    raw = yf.download(symbols, period="5y", interval="1d", progress=False, auto_adjust=True)
    if raw.empty:
        return {}, {}, {}

    df_daily = (raw["Close"] if "Close" in raw else raw).ffill(limit=5)
    if isinstance(df_daily, pd.Series):
        df_daily = df_daily.to_frame(name=symbols[0])

    df_weekly = df_daily.resample("W-FRI").last().dropna(axis=1, how="all")
    df_monthly = df_daily.resample("ME").last().dropna(axis=1, how="all")
    if df_monthly.empty:
        df_monthly = df_daily.resample("M").last().dropna(axis=1, how="all")

    return df_daily.dropna(axis=1, how="all"), df_weekly, df_monthly


def classify_quadrant(r, m):
    if r >= 100 and m >= 100:
        return "Leading 🟢"
    elif r >= 100 and m < 100:
        return "Weakening 🟡"
    elif r < 100 and m < 100:
        return "Lagging 🔴"
    return "Improving 🔵"


def compute_rrg_metrics(price_df, tickers, bench_col, jdk_len, tail_len, offset):
    full_series = {}
    tails = {}
    metrics_rows = []
    skipped = []
    as_of_date = None

    for ticker in tickers:
        if ticker not in price_df.columns or ticker == bench_col:
            continue

        pair = price_df[[ticker, bench_col]].dropna()
        if offset > 0:
            pair = pair.iloc[:-offset]

        if len(pair) < (jdk_len * 2 + 12):
            skipped.append(ticker)
            continue

        rs = pair[ticker] / pair[bench_col]
        rs_ema = rs.ewm(span=jdk_len, adjust=False).mean()
        rs_ratio = 100 * rs_ema / rs_ema.rolling(window=jdk_len).mean()
        roc = (rs_ratio / rs_ratio.shift(10)) - 1
        rs_momentum = 100 + 100 * roc.ewm(span=jdk_len, adjust=False).mean()

        complete_df = pd.DataFrame({
            "Price": pair[ticker],
            "Benchmark": pair[bench_col],
            "RS": rs,
            "RS_Ratio": rs_ratio,
            "RS_Mom": rs_momentum
        }).dropna()

        if len(complete_df) < 3:
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
        dx = r_curr - r_prev
        dy = m_curr - m_prev

        r_dist = float(np.hypot(r_curr - 100.0, m_curr - 100.0))
        velocity = float(np.hypot(dx, dy))
        heading_deg = float((np.degrees(np.arctan2(dy, dx)) + 360.0) % 360.0)

        clean_name = REVERSE_MAP.get(ticker, ticker.replace(".NS", ""))
        quad = classify_quadrant(r_curr, m_curr)
        prev_quad = classify_quadrant(r_prev, m_prev)

        # Crossover Detection
        if quad != prev_quad:
            crossover_signal = f"⚡ Cross: {prev_quad.split()[0]} ➔ {quad.split()[0]}"
        else:
            crossover_signal = "Holding Quadrant"

        metrics_rows.append({
            "Ticker": ticker,
            "Symbol": clean_name,
            "Quadrant": quad,
            "Crossover": crossover_signal,
            "Strength (RS-Ratio)": round(r_curr, 2),
            "Str Chg": round(dx, 2),
            "Momentum (RS-Mom)": round(m_curr, 2),
            "Mom Chg": round(dy, 2),
            "RRG Distance": round(r_dist, 2),
            "Velocity": round(velocity, 2),
            "Heading (°)": round(heading_deg, 1)
        })

    metrics_df = pd.DataFrame(metrics_rows)
    if not metrics_df.empty:
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
            x=x_data, y=y_data,
            mode="lines+markers",
            marker=dict(size=node_sizes, color=color, opacity=0.75),
            line=dict(width=2.8, color=color, shape="spline" if use_spline else "linear", smoothing=1.1 if use_spline else 0),
            name=clean_name, text=dates,
            hovertemplate=f"<b>{clean_name}</b><br>Date: %{{text}}<br>RS-Ratio: %{{x:.2f}}<br>RS-Mom: %{{y:.2f}}<extra></extra>"
        ))

        fig.add_trace(go.Scatter(
            x=[x_data[-2], x_data[-1]], y=[y_data[-2], y_data[-1]],
            mode="markers+text" if display_labels else "markers",
            marker=dict(symbol=["circle", "arrow"], size=[0, 16], angleref="previous", color=color, line=dict(width=1.5, color="white")),
            text=["", clean_name] if display_labels else None,
            textposition="top center", textfont=dict(size=12, color="#ffffff"),
            showlegend=False, hoverinfo="skip"
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
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font=dict(color="#e0e0e0"),
        height=720, margin=dict(l=40, r=40, t=30, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0)
    )
    return fig


# --- LOAD DATA ---
raw_tickers = [NSE_INDICES[name] for name in selected_index_names]
if custom_stocks_input.strip():
    raw_tickers.extend([t.strip().upper() for t in custom_stocks_input.split(",") if t.strip()])

tickers_list = list(dict.fromkeys(raw_tickers))
benchmark = benchmark_input.strip().upper()

if not benchmark:
    st.error("Please enter a valid Benchmark ticker.")
    st.stop()

download_list = list(dict.fromkeys(tickers_list + [benchmark]))

with st.spinner("Syncing Institutional Multi-Timeframe Data..."):
    df_d, df_w, df_m = load_multi_tf_data(download_list)

if df_d.empty or benchmark not in df_d.columns:
    st.error(f"Benchmark '{benchmark}' failed to download.")
    st.stop()

# Select active timeframe dataframe
active_df = df_d if timeframe == "Daily" else (df_w if timeframe == "Weekly" else df_m)
active_tickers = [t for t in tickers_list if t in active_df.columns]

ticker_tails, full_rrg_series, dash_df, skipped_short, as_of_date = compute_rrg_metrics(
    active_df, active_tickers, benchmark, jdk_period, tail_weeks, replay_offset
)

if dash_df.empty:
    st.error("Insufficient history for computed parameters. Adjust sliders.")
    st.stop()

# --- TOP HEADER & KPI METRICS ---
st.title("⚡ Pro RRG Institutional Terminal")

leaders_df = dash_df[dash_df["Quadrant"] == "Leading 🟢"]
top_leader = leaders_df.iloc[0] if not leaders_df.empty else dash_df.iloc[0]
fastest_mover = dash_df.sort_values(by="Velocity", ascending=False).iloc[0]
crossovers = dash_df[dash_df["Crossover"].str.contains("⚡")]

st.info(
    f"🟢 **{timeframe} Snapshot ({as_of_date})** | **{top_leader['Symbol']}** leads strength, "
    f"while **{len(crossovers)}** assets triggered quadrant crossovers this period."
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🌟 Top Leader", top_leader["Symbol"], f"{top_leader['Str Chg']:+.2f} Str")
with col2:
    st.metric("🚀 Highest Velocity", fastest_mover["Symbol"], f"{fastest_mover['Velocity']:.2f} / bar")
with col3:
    st.metric("⚡ Crossovers Today", len(crossovers), "Quadrant Shifts")
with col4:
    st.metric("📊 Active Universe", f"{len(dash_df)} Assets", f"vs {benchmark.replace('.NS', '')}")

st.markdown("---")

# --- TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 Macro Rotation Chart",
    "🌐 Multi-Timeframe Matrix",
    "🔬 Sector Drill-Down",
    "📈 RS & Price Inspector",
    "📋 Pro Data Matrix"
])

with tab1:
    macro_fig = build_rrg_figure(ticker_tails, dash_df, quadrant_filter, spline_smooth, show_labels)
    st.plotly_chart(macro_fig, use_container_width=True)

with tab2:
    st.markdown("### 🌐 Multi-Timeframe Consensus Alignment (Daily vs Weekly vs Monthly)")
    mtf_rows = []
    for t in active_tickers:
        if t == benchmark: continue
        # Compute latest quadrant across D, W, M
        _, _, d_m, _, _ = compute_rrg_metrics(df_d, [t], benchmark, jdk_period, 1, 0)
        _, _, w_m, _, _ = compute_rrg_metrics(df_w, [t], benchmark, jdk_period, 1, 0)
        _, _, m_m, _, _ = compute_rrg_metrics(df_m, [t], benchmark, jdk_period, 1, 0)

        mtf_rows.append({
            "Symbol": REVERSE_MAP.get(t, t.replace(".NS", "")),
            "Daily Quadrant": d_m["Quadrant"].values[0] if not d_m.empty else "N/A",
            "Weekly Quadrant": w_m["Quadrant"].values[0] if not w_m.empty else "N/A",
            "Monthly Quadrant": m_m["Quadrant"].values[0] if not m_m.empty else "N/A"
        })
    st.dataframe(pd.DataFrame(mtf_rows), use_container_width=True, hide_index=True)

with tab3:
    st.markdown("### 🔬 Intra-Sector Stock Rotation")
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        chosen_sector = st.selectbox("Select Sector:", options=list(SECTOR_CONSTITUENTS.keys()))
    with d_col2:
        sec_bench = SECTOR_CONSTITUENTS[chosen_sector]["benchmark"]
        drill_bench = st.selectbox("Benchmark:", options=[sec_bench, benchmark])

    drill_stocks = SECTOR_CONSTITUENTS[chosen_sector]["stocks"]
    d_tails, _, d_metrics, _, _ = compute_rrg_metrics(active_df, drill_stocks, drill_bench, jdk_period, tail_weeks, replay_offset)
    if not d_metrics.empty:
        drill_fig = build_rrg_figure(d_tails, d_metrics, ["Leading 🟢", "Weakening 🟡", "Lagging 🔴", "Improving 🔵"], spline_smooth, show_labels)
        st.plotly_chart(drill_fig, use_container_width=True)
        st.dataframe(d_metrics.drop(columns=["Ticker"]), use_container_width=True, hide_index=True)

with tab4:
    st.markdown("### 📈 Relative Strength & Price Breakdown")
    symbol_map = {row["Symbol"]: row["Ticker"] for _, row in dash_df.iterrows()}
    sel_sym = st.selectbox("Select Asset:", options=list(symbol_map.keys()))
    ts_df = full_rrg_series[symbol_map[sel_sym]].tail(120)

    sub_fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.5, 0.5])
    sub_fig.add_trace(go.Scatter(x=ts_df.index, y=100*ts_df["Price"]/ts_df["Price"].iloc[0], name=sel_sym, line=dict(color="#00ff88", width=2.5)), row=1, col=1)
    sub_fig.add_trace(go.Scatter(x=ts_df.index, y=100*ts_df["Benchmark"]/ts_df["Benchmark"].iloc[0], name="Benchmark", line=dict(color="#88", dash="dot")), row=1, col=1)
    sub_fig.add_trace(go.Scatter(x=ts_df.index, y=ts_df["RS_Ratio"], name="RS-Ratio", line=dict(color="#33ccff", width=2)), row=2, col=1)
    sub_fig.add_trace(go.Scatter(x=ts_df.index, y=ts_df["RS_Mom"], name="RS-Mom", line=dict(color="#ffaa00", width=2)), row=2, col=1)
    sub_fig.add_hline(y=100, line_dash="dash", line_color="#666", row=2, col=1)
    sub_fig.update_layout(height=600, plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font=dict(color="#e0e0e0"), margin=dict(l=40, r=40, t=30, b=40))
    st.plotly_chart(sub_fig, use_container_width=True)

with tab5:
    st.markdown(f"### 📋 Rotational Matrix & Crossover Signals")
    display_df = dash_df[dash_df["Quadrant"].isin(quadrant_filter)].drop(columns=["Ticker"])
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    st.download_button("📥 Export CSV", display_df.to_csv(index=False).encode("utf-8"), file_name="rrg_matrix.csv", mime="text/csv")
