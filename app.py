import streamlit as st
import pandas as pd

st.set_page_config(page_title="Portfolio Cross Qualifier", layout="wide")
st.title("📊 Portfolio Cross-Qualification Engine")

portfolio_file = st.file_uploader("Upload Portfolio CSV", type=["csv"])
qualifying_file = st.file_uploader("Upload Cross Qualifying Matrix CSV", type=["csv"])

if portfolio_file and qualifying_file:

    # ----------------------------
    # LOAD FILES
    # ----------------------------
    portfolio = pd.read_csv(portfolio_file)
    qualifying = pd.read_csv(qualifying_file)

    portfolio.columns = portfolio.columns.str.strip().str.upper()
    qualifying.columns = qualifying.columns.str.strip().str.upper()

    # ----------------------------
    # VALIDATE COLUMNS
    # ----------------------------
    if "TICKER" not in portfolio.columns:
        st.error("Portfolio must contain a TICKER column.")
        st.stop()

    if "SYMBOL" not in qualifying.columns:
        st.error("Qualifying file must contain a SYMBOL column.")
        st.stop()

    # ----------------------------
    # CLEAN SYMBOLS
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
    # MERGE
    # ----------------------------
    merged = portfolio.merge(
        qualifying,
        left_on="TICKER",
        right_on="SYMBOL",
        how="left"
    )

    matches = merged["SYMBOL"].notna().sum()
    st.info(f"Matched {matches} out of {len(portfolio)} holdings")

    if matches == 0:
        st.warning("No matches found. Check symbol formatting.")
        st.stop()

    # ----------------------------
    # DETECT STRATEGY COLUMNS
    # ----------------------------
    metadata_cols = {
        "SYMBOL", "EXCHANGE", "COMPAGNY", "COMPANY",
        "SECTOR", "RANK"
    }

    strategy_cols = [
        col for col in qualifying.columns
        if col not in metadata_cols
        and pd.api.types.is_numeric_dtype(qualifying[col])
    ]

    if not strategy_cols:
        st.error("No numeric strategy columns detected.")
        st.stop()

    # ----------------------------
    # THRESHOLD SETTING
    # ----------------------------
    st.subheader("Strategy Qualification Settings")

    threshold = st.slider(
        "Minimum score required to qualify",
        min_value=0,
        max_value=100,
        value=80
    )

    # ----------------------------
    # COUNT MEMBERSHIP
    # ----------------------------
    membership_results = {}

    for strat in strategy_cols:

        col_data = pd.to_numeric(
            merged[strat],
            errors="coerce"
        ).fillna(0)

        qualifies = col_data >= threshold
        count = qualifies.sum()

        membership_results[strat] = int(count)

    membership_series = pd.Series(membership_results).sort_values(ascending=False)

    # ----------------------------
    # DISPLAY RESULTS
    # ----------------------------
    st.divider()

    if not membership_series.empty:
        top_strategy = membership_series.index[0]
        top_count = membership_series.iloc[0]

        st.metric(
            "🏆 Most Represented Strategy",
            top_strategy,
            f"{top_count} Stocks Qualify"
        )

    st.subheader("📊 Strategy Membership Count")
    st.dataframe(membership_series)
    st.bar_chart(membership_series)

    # ----------------------------
    # PERCENTAGE OF PORTFOLIO
    # ----------------------------
    membership_percent = (
        membership_series / len(portfolio) * 100
    ).round(1)

    st.subheader("📈 % of Portfolio Qualifying")
    st.dataframe(membership_percent)

    # ----------------------------
    # UNMATCHED STOCKS
    # ----------------------------
    unmatched = merged[merged["SYMBOL"].isna()]

    if not unmatched.empty:
        st.divider()
        st.subheader("⚠️ Stocks Not Found in Qualifying File")
        st.dataframe(unmatched[["TICKER"]])

    # ----------------------------
    # DOWNLOAD REPORT
    # ----------------------------
    report_df = pd.DataFrame({
        "Stock Count": membership_series,
        "Portfolio %": membership_percent
    })

    st.download_button(
        "📥 Download Strategy Count Report",
        report_df.to_csv(),
        "strategy_membership_report.csv",
        "text/csv"
    )

else:
    st.info("Upload both files to begin.")
