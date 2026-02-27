import streamlit as st
import pandas as pd

st.set_page_config(page_title="Portfolio Cross Qualifier", layout="wide")
st.title("📊 Portfolio Cross-Qualification Engine")

portfolio_file = st.file_uploader("Upload Portfolio CSV", type=["csv"])
qualifying_file = st.file_uploader("Upload Qualifying Matrix CSV", type=["csv"])

if portfolio_file and qualifying_file:

    portfolio = pd.read_csv(portfolio_file)
    qualifying = pd.read_csv(qualifying_file)

    # ----------------------------
    # CLEAN COLUMN NAMES
    # ----------------------------
    portfolio.columns = portfolio.columns.str.strip().str.upper()
    qualifying.columns = qualifying.columns.str.strip().str.upper()

    # Validate ticker column in portfolio
    if "TICKER" not in portfolio.columns:
        st.error("Portfolio must contain a TICKER column.")
        st.write("Detected:", portfolio.columns.tolist())
        st.stop()

    # Validate SYMBOL in qualifying
    if "SYMBOL" not in qualifying.columns:
        st.error("Qualifying file must contain a SYMBOL column.")
        st.write("Detected:", qualifying.columns.tolist())
        st.stop()

    # Clean tickers
    portfolio["TICKER"] = portfolio["TICKER"].astype(str).str.upper().str.strip()
    qualifying["SYMBOL"] = qualifying["SYMBOL"].astype(str).str.upper().str.strip()

    # ----------------------------
    # DETERMINE WEIGHT
    # ----------------------------
    if "WEIGHT" in portfolio.columns:
        portfolio["WEIGHT"] = pd.to_numeric(portfolio["WEIGHT"], errors="coerce").fillna(0)
        weight_source = "WEIGHT column"
    elif "SHARES" in portfolio.columns:
        portfolio["WEIGHT"] = pd.to_numeric(portfolio["SHARES"], errors="coerce").fillna(0)
        weight_source = "SHARES column"
    else:
        portfolio["WEIGHT"] = 1
        weight_source = "Equal weight"

    st.info(f"Using: {weight_source}")

    # ----------------------------
    # MERGE
    # ----------------------------
    merged = portfolio.merge(
        qualifying,
        left_on="TICKER",
        right_on="SYMBOL",
        how="left"
    )

    # ----------------------------
    # IDENTIFY STRATEGY COLUMNS
    # ----------------------------
    ignore_cols = {
        "SYMBOL", "EXCHANGE", "COMPANY", "SECTOR",
        "RANK"
    }

    strategy_cols = [
        col for col in qualifying.columns
        if col not in ignore_cols
    ]

    if not strategy_cols:
        st.error("No strategy columns detected.")
        st.stop()

    # ----------------------------
    # CALCULATE ALIGNMENT
    # ----------------------------
    alignment_results = {}

    total_weight = portfolio["WEIGHT"].sum()

    for strat in strategy_cols:

        if strat in merged.columns:
            # If strategy column contains numeric flags (1/0)
            strat_weight = (
                merged[strat].fillna(0) *
                merged["WEIGHT"]
            ).sum()

            weight_percent = (strat_weight / total_weight) * 100

            alignment_results[strat] = round(weight_percent, 2)

    alignment_series = pd.Series(alignment_results).sort_values(ascending=False)

    # ----------------------------
    # DISPLAY
    # ----------------------------
    st.divider()

    if not alignment_series.empty:
        top_strategy = alignment_series.index[0]
        top_score = alignment_series.iloc[0]

        st.metric("Top Matching Strategy", top_strategy, f"{top_score:.2f}% Weight Match")

    st.subheader("📈 Strategy Alignment by Weight (%)")
    st.dataframe(alignment_series)
    st.bar_chart(alignment_series)

    # ----------------------------
    # UNMAPPED STOCKS
    # ----------------------------
    unmapped = merged[merged[strategy_cols].isna().all(axis=1)]

    if not unmapped.empty:
        st.divider()
        st.subheader("⚠️ Unmapped Stocks")
        st.dataframe(unmapped[["TICKER", "WEIGHT"]])

    # ----------------------------
    # DOWNLOAD
    # ----------------------------
    st.download_button(
        "Download Alignment Report",
        alignment_series.to_csv(),
        "alignment_report.csv",
        "text/csv"
    )

else:
    st.info("Upload both files to begin.")
