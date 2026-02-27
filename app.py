import streamlit as st
import pandas as pd

st.set_page_config(page_title="Portfolio Cross Qualifier", layout="wide")

st.title("📊 Portfolio Cross-Qualification Engine")
st.markdown("Upload a portfolio and a qualifying strategy list to see alignment.")

# ============================
# FILE UPLOAD
# ============================

portfolio_file = st.file_uploader("Upload Portfolio CSV", type=["csv"])
qualifying_file = st.file_uploader("Upload Qualifying List CSV", type=["csv"])

# ============================
# MAIN LOGIC
# ============================

if portfolio_file and qualifying_file:

    try:
        portfolio = pd.read_csv(portfolio_file)
        qualifying = pd.read_csv(qualifying_file)
    except Exception as e:
        st.error("Error reading CSV files.")
        st.stop()

    # ----------------------------
    # CLEAN COLUMN NAMES
    # ----------------------------
    portfolio.columns = portfolio.columns.str.strip().str.upper()
    qualifying.columns = qualifying.columns.str.strip().str.upper()

    # ----------------------------
    # VALIDATE REQUIRED COLUMNS
    # ----------------------------
    required_portfolio_cols = {"TICKER", "WEIGHT"}
    required_qualifying_cols = {"TICKER", "STRATEGY"}

    if not required_portfolio_cols.issubset(portfolio.columns):
        st.error("Portfolio file must contain columns: Ticker, Weight")
        st.write("Detected columns:", portfolio.columns.tolist())
        st.stop()

    if not required_qualifying_cols.issubset(qualifying.columns):
        st.error("Qualifying file must contain columns: Ticker, Strategy")
        st.write("Detected columns:", qualifying.columns.tolist())
        st.stop()

    # ----------------------------
    # CLEAN DATA
    # ----------------------------
    portfolio["TICKER"] = portfolio["TICKER"].astype(str).str.upper().str.strip()
    qualifying["TICKER"] = qualifying["TICKER"].astype(str).str.upper().str.strip()
    portfolio["WEIGHT"] = pd.to_numeric(portfolio["WEIGHT"], errors="coerce").fillna(0)

    # ----------------------------
    # MERGE
    # ----------------------------
    merged = portfolio.merge(qualifying, on="TICKER", how="left")

    # ----------------------------
    # COUNT-BASED ALIGNMENT
    # ----------------------------
    count_summary = (
        merged.groupby("STRATEGY")["TICKER"]
        .count()
        .sort_values(ascending=False)
    )

    # ----------------------------
    # WEIGHT-BASED ALIGNMENT
    # ----------------------------
    weight_summary = (
        merged.groupby("STRATEGY")["WEIGHT"]
        .sum()
        .sort_values(ascending=False)
    )

    total_weight = portfolio["WEIGHT"].sum()
    weight_percent = (weight_summary / total_weight * 100).round(2)

    # ----------------------------
    # ALIGNMENT SCORE (Weighted + Count)
    # ----------------------------
    count_percent = (count_summary / len(portfolio) * 100).round(2)

    alignment_score = (
        (weight_percent * 0.7) +
        (count_percent * 0.3)
    ).sort_values(ascending=False)

    # ============================
    # DISPLAY RESULTS
    # ============================

    st.divider()
    st.subheader("🏆 Best Strategy Match")

    if not alignment_score.empty:
        best_strategy = alignment_score.index[0]
        best_score = alignment_score.iloc[0]

        st.metric(
            label="Top Matching Strategy",
            value=best_strategy,
            delta=f"{best_score:.2f} Alignment Score"
        )
    else:
        st.warning("No strategy matches found.")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Alignment by Weight (%)")
        st.dataframe(weight_percent)
        st.bar_chart(weight_percent)

    with col2:
        st.subheader("📊 Alignment by Stock Count (%)")
        st.dataframe(count_percent)
        st.bar_chart(count_percent)

    # ----------------------------
    # UNMAPPED STOCKS
    # ----------------------------
    unmapped = merged[merged["STRATEGY"].isna()]

    if not unmapped.empty:
        st.divider()
        st.subheader("⚠️ Unmapped Stocks")
        st.dataframe(unmapped[["TICKER", "WEIGHT"]])

    # ----------------------------
    # DOWNLOAD REPORT
    # ----------------------------
    summary_df = pd.DataFrame({
        "Weight %": weight_percent,
        "Count %": count_percent,
        "Alignment Score": alignment_score
    }).fillna(0).sort_values("Alignment Score", ascending=False)

    st.download_button(
        label="📥 Download Alignment Report",
        data=summary_df.to_csv(index=True),
        file_name="alignment_report.csv",
        mime="text/csv"
    )

else:
    st.info("Please upload both files to begin.")
