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
