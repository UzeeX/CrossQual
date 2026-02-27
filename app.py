import streamlit as st
import pandas as pd

st.set_page_config(page_title="Portfolio Cross Qualifier", layout="wide")

st.title("📊 Portfolio Cross-Qualification Engine")

portfolio_file = st.file_uploader("Upload Portfolio CSV", type=["csv"])
qualifying_file = st.file_uploader("Upload Qualifying List CSV", type=["csv"])

if portfolio_file and qualifying_file:

    portfolio = pd.read_csv(portfolio_file)
    qualifying = pd.read_csv(qualifying_file)

    # Clean column names
    portfolio.columns = portfolio.columns.str.strip().str.upper()
    qualifying.columns = qualifying.columns.str.strip().str.upper()

    # Validate Ticker
    if "TICKER" not in portfolio.columns:
        st.error("Portfolio must contain a TICKER column.")
        st.write("Detected columns:", portfolio.columns.tolist())
        st.stop()

    if "TICKER" not in qualifying.columns or "STRATEGY" not in qualifying.columns:
        st.error("Qualifying file must contain TICKER and STRATEGY columns.")
        st.write("Detected columns:", qualifying.columns.tolist())
        st.stop()

    # Clean tickers
    portfolio["TICKER"] = portfolio["TICKER"].astype(str).str.upper().str.strip()
    qualifying["TICKER"] = qualifying["TICKER"].astype(str).str.upper().str.strip()

    # ----------------------------
    # DETERMINE WEIGHT COLUMN
    # ----------------------------
    if "WEIGHT" in portfolio.columns:
        portfolio["WEIGHT"] = pd.to_numeric(portfolio["WEIGHT"], errors="coerce").fillna(0)
        weight_source = "WEIGHT column"

    elif "SHARES" in portfolio.columns:
        portfolio["WEIGHT"] = pd.to_numeric(portfolio["SHARES"], errors="coerce").fillna(0)
        weight_source = "SHARES column (used as proxy weight)"

    else:
        # Equal weight fallback
        portfolio["WEIGHT"] = 1
        weight_source = "Equal weight (no WEIGHT or SHARES column found)"

    st.info(f"Using: {weight_source}")

    # ----------------------------
    # MERGE
    # ----------------------------
    merged = portfolio.merge(qualifying, on="TICKER", how="left")

    # ----------------------------
    # CALCULATIONS
    # ----------------------------
    total_weight = portfolio["WEIGHT"].sum()

    weight_summary = (
        merged.groupby("STRATEGY")["WEIGHT"]
        .sum()
        .sort_values(ascending=False)
    )

    weight_percent = (weight_summary / total_weight * 100).round(2)

    count_summary = (
        merged.groupby("STRATEGY")["TICKER"]
        .count()
        .sort_values(ascending=False)
    )

    count_percent = (count_summary / len(portfolio) * 100).round(2)

    alignment_score = (
        weight_percent * 0.7 +
        count_percent * 0.3
    ).sort_values(ascending=False)

    # ----------------------------
    # DISPLAY
    # ----------------------------
    st.divider()

    if not alignment_score.empty:
        best_strategy = alignment_score.index[0]
        best_score = alignment_score.iloc[0]

        st.metric(
            "Top Matching Strategy",
            best_strategy,
            f"{best_score:.2f} Score"
        )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Alignment by Weight (%)")
        st.dataframe(weight_percent)
        st.bar_chart(weight_percent)

    with col2:
        st.subheader("Alignment by Count (%)")
        st.dataframe(count_percent)
        st.bar_chart(count_percent)

    # Unmapped
    unmapped = merged[merged["STRATEGY"].isna()]

    if not unmapped.empty:
        st.divider()
        st.subheader("Unmapped Stocks")
        st.dataframe(unmapped[["TICKER", "WEIGHT"]])

    # Download
    summary_df = pd.DataFrame({
        "Weight %": weight_percent,
        "Count %": count_percent,
        "Alignment Score": alignment_score
    }).fillna(0).sort_values("Alignment Score", ascending=False)

    st.download_button(
        "Download Alignment Report",
        summary_df.to_csv(),
        "alignment_report.csv",
        "text/csv"
    )

else:
    st.info("Upload both files to begin.")
