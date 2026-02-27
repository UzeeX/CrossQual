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
        st.write("Detected columns:", portfolio.columns.tolist())
        st.stop()

    if "SYMBOL" not in qualifying.columns:
        st.error("Qualifying file must contain a SYMBOL column.")
        st.write("Detected columns:", qualifying.columns.tolist())
        st.stop()

    # ----------------------------
    # CLEAN TICKERS
    # ----------------------------
    def normalize_symbol(x):
        x = str(x).upper().strip()
        # Remove common exchange suffixes
        x = x.replace(".TO", "").replace(".US", "").replace(".O", "")
        return x

    portfolio["TICKER"] = portfolio["TICKER"].apply(normalize_symbol)
    qualifying["SYMBOL"] = qualifying["SYMBOL"].apply(normalize_symbol)

    # ----------------------------
    # DETERMINE WEIGHT SOURCE
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
    # STRATEGY COLUMN DETECTION
    # ----------------------------
    metadata_cols = {
        "SYMBOL", "EXCHANGE", "COMPANY", "COMPAGNY",
        "SECTOR", "RANK"
    }

    strategy_cols = []

    for col in qualifying.columns:
        if col not in metadata_cols:

            col_series = qualifying[col]

            # If numeric column
            if pd.api.types.is_numeric_dtype(col_series):
                strategy_cols.append(col)

            # If object column but contains YES/NO type values
            elif col_series.dropna().astype(str).str.upper().isin(
                ["YES", "NO", "Y", "N", "TRUE", "FALSE", "1", "0"]
            ).any():
                strategy_cols.append(col)

    if not strategy_cols:
        st.error("No strategy columns detected.")
        st.stop()

    # ----------------------------
    # ALIGNMENT CALCULATION
    # ----------------------------
    alignment_results = {}
    total_weight = portfolio["WEIGHT"].sum()

    for strat in strategy_cols:

        col_data = merged[strat].fillna(0)

        # Convert YES/NO formats
        col_data = col_data.replace({
            "YES": 1, "Yes": 1, "Y": 1,
            "TRUE": 1, True: 1,
            "NO": 0, "No": 0, "N": 0,
            "FALSE": 0, False: 0
        })

        col_data = pd.to_numeric(col_data, errors="coerce").fillna(0)

        strat_weight = (col_data * merged["WEIGHT"]).sum()

        if total_weight > 0:
            weight_percent = (strat_weight / total_weight) * 100
        else:
            weight_percent = 0

        alignment_results[strat] = round(weight_percent, 2)

    alignment_series = pd.Series(alignment_results).sort_values(ascending=False)

    # ----------------------------
    # DISPLAY RESULTS
    # ----------------------------
    st.divider()

    if not alignment_series.empty:
        top_strategy = alignment_series.index[0]
        top_score = alignment_series.iloc[0]

        st.metric(
            "🏆 Top Matching Strategy",
            top_strategy,
            f"{top_score:.2f}% Weight Match"
        )

    st.subheader("📈 Strategy Alignment by Weight (%)")
    st.dataframe(alignment_series)
    st.bar_chart(alignment_series)

    # ----------------------------
    # MERGE DIAGNOSTICS
    # ----------------------------
    unmatched = merged[merged[strategy_cols].isna().all(axis=1)]

    if not unmatched.empty:
        st.divider()
        st.subheader("⚠️ Stocks Not Found in Qualifying File")
        st.dataframe(unmatched[["TICKER", "WEIGHT"]])

    # ----------------------------
    # DOWNLOAD REPORT
    # ----------------------------
    st.download_button(
        "📥 Download Alignment Report",
        alignment_series.to_csv(),
        "alignment_report.csv",
        "text/csv"
    )

else:
    st.info("Upload both files to begin.")
