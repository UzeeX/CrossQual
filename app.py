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

    # ----------------------------
    # VALIDATE REQUIRED COLUMNS
    # ----------------------------
    if "TICKER" not in portfolio.columns:
        st.error("Portfolio must contain a TICKER column.")
        st.stop()

    if "SYMBOL" not in qualifying.columns:
        st.error("Qualifying file must contain a SYMBOL column.")
        st.stop()

    # ----------------------------
    # NORMALIZE SYMBOLS
    # ----------------------------
    def clean_portfolio_symbol(x):
        return str(x).upper().strip()

    def clean_qualifying_symbol(x):
        x = str(x).upper().strip()

        # Remove exchange prefix like XTSE:
        if ":" in x:
            x = x.split(":")[1]

        return x

    portfolio["TICKER"] = portfolio["TICKER"].apply(clean_portfolio_symbol)
    qualifying["SYMBOL"] = qualifying["SYMBOL"].apply(clean_qualifying_symbol)

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

    matches = merged["SYMBOL"].notna().sum()
    st.write(f"Matched {matches} out of {len(portfolio)} holdings")

    # ----------------------------
    # STRATEGY COLUMNS
    # ----------------------------
    metadata_cols = {
        "SYMBOL", "EXCHANGE", "COMPAGNY", "COMPANY",
        "SECTOR", "RANK"
    }

    strategy_cols = [
        col for col in qualifying.columns
        if col not in metadata_cols
    ]

    # ----------------------------
    # ALIGNMENT CALCULATION (RANK-BASED)
    # ----------------------------
    alignment_results = {}
    total_weight = portfolio["WEIGHT"].sum()

    for strat in strategy_cols:

        if strat in merged.columns:

            col_data = pd.to_numeric(
                merged[strat],
                errors="coerce"
            ).fillna(0)

            # Weighted average score
            strat_score = (col_data * merged["WEIGHT"]).sum()

            if total_weight > 0:
                score_percent = strat_score / total_weight
            else:
                score_percent = 0

            alignment_results[strat] = round(score_percent, 2)

    alignment_series = pd.Series(alignment_results).sort_values(ascending=False)

    # ----------------------------
    # DISPLAY
    # ----------------------------
    st.divider()

    if not alignment_series.empty:
        top_strategy = alignment_series.index[0]
        top_score = alignment_series.iloc[0]

        st.metric(
            "🏆 Top Matching Strategy",
            top_strategy,
            f"Avg Score: {top_score}"
        )

    st.subheader("📈 Strategy Alignment (Weighted Average Score)")
    st.dataframe(alignment_series)
    st.bar_chart(alignment_series)

    # ----------------------------
    # UNMATCHED STOCKS
    # ----------------------------
    unmatched = merged[merged["SYMBOL"].isna()]

    if not unmatched.empty:
        st.divider()
        st.subheader("⚠️ Stocks Not Found in Qualifying File")
        st.dataframe(unmatched[["TICKER", "WEIGHT"]])

    # ----------------------------
    # DOWNLOAD
    # ----------------------------
    st.download_button(
        "📥 Download Alignment Report",
        alignment_series.to_csv(),
        "alignment_report.csv",
        "text/csv"
    )

else:
    st.info("Upload both files to begin.")
