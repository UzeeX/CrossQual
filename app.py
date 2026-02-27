import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Portfolio Strategy Analyzer",
    layout="wide"
)

st.title("📊 Portfolio Strategy Analyzer")
st.caption("Match portfolio holdings against cross-qualifying strategy lists")

portfolio_file = st.file_uploader("Upload Portfolio CSV", type=["csv"])
qualifying_file = st.file_uploader("Upload Cross Qualifying Matrix CSV", type=["csv"])

if portfolio_file and qualifying_file:

    # ----------------------------
    # LOAD + CLEAN
    # ----------------------------
    portfolio = pd.read_csv(portfolio_file)
    qualifying = pd.read_csv(qualifying_file)

    portfolio.columns = portfolio.columns.str.strip().str.upper()
    qualifying.columns = qualifying.columns.str.strip().str.upper()

    if "TICKER" not in portfolio.columns:
        st.error("Portfolio must contain a TICKER column.")
        st.stop()

    if "SYMBOL" not in qualifying.columns:
        st.error("Qualifying file must contain a SYMBOL column.")
        st.stop()

    # Clean symbols
    def clean_symbol(x):
        x = str(x).upper().strip()
        if ":" in x:  # remove XTSE:
            x = x.split(":")[1]
        return x

    portfolio["TICKER"] = portfolio["TICKER"].astype(str).str.upper().str.strip()
    qualifying["SYMBOL"] = qualifying["SYMBOL"].apply(clean_symbol)

    # ----------------------------
    # MERGE
    # ----------------------------
    merged = portfolio.merge(
        qualifying,
        left_on="TICKER",
        right_on="SYMBOL",
        how="left"
    )

    total_holdings = len(portfolio)
    matched = merged["SYMBOL"].notna().sum()

    st.divider()
    col_a, col_b = st.columns(2)
    col_a.metric("Total Holdings", total_holdings)
    col_b.metric("Matched to Strategy Universe", matched)

    if matched == 0:
        st.warning("No symbol matches found. Check formatting.")
        st.stop()

    # ----------------------------
    # IDENTIFY STRATEGY COLUMNS
    # ----------------------------
    metadata_cols = {
        "SYMBOL", "EXCHANGE", "COMPANY", "COMPAGNY",
        "SECTOR", "RANK"
    }

    strategy_cols = [
        col for col in qualifying.columns
        if col not in metadata_cols
    ]

    # ----------------------------
    # COUNT QUALIFICATIONS
    # ----------------------------
    results = {}

    for strat in strategy_cols:

        if strat in merged.columns:

            col_data = merged[strat].fillna(0)

            col_data = col_data.replace({
                "YES": 1, "Yes": 1, "Y": 1,
                "TRUE": 1, True: 1
            })

            col_data = pd.to_numeric(col_data, errors="coerce").fillna(0)

            count = (col_data > 0).sum()

            results[strat] = count

    results_series = pd.Series(results).sort_values(ascending=False)

    percent_series = (results_series / total_holdings * 100).round(1)

    # ----------------------------
    # DOMINANT STRATEGY
    # ----------------------------
    dominant_strategy = results_series.idxmax()
    dominant_count = results_series.max()
    dominant_percent = percent_series.loc[dominant_strategy]

    st.divider()
    st.subheader("🏆 Dominant Strategy")

    st.metric(
        label=dominant_strategy,
        value=f"{dominant_count} Holdings",
        delta=f"{dominant_percent}% of Portfolio"
    )

    # ----------------------------
    # STRATEGY BREAKDOWN
    # ----------------------------
    st.divider()
    st.subheader("📊 Strategy Breakdown")

    breakdown_df = pd.DataFrame({
        "Qualified Holdings": results_series,
        "% of Portfolio": percent_series
    })

    st.dataframe(
        breakdown_df,
        use_container_width=True
    )

    st.bar_chart(percent_series)

    # ----------------------------
    # VIEW STOCKS PER STRATEGY
    # ----------------------------
    st.divider()
    st.subheader("🔎 View Stocks by Strategy")

    selected_strategy = st.selectbox("Select Strategy", strategy_cols)

    if selected_strategy:

        col_data = pd.to_numeric(
            merged[selected_strategy],
            errors="coerce"
        ).fillna(0)

        qualifying_stocks = merged.loc[col_data > 0, "TICKER"]

        st.write(
            f"{len(qualifying_stocks)} holdings qualify under **{selected_strategy}**"
        )

        st.dataframe(
            qualifying_stocks.reset_index(drop=True),
            use_container_width=True
        )

    # ----------------------------
    # DOWNLOAD REPORT
    # ----------------------------
    st.divider()

    st.download_button(
        "📥 Download Strategy Report",
        breakdown_df.to_csv(),
        "strategy_analysis_report.csv",
        "text/csv"
    )

else:
    st.info("Upload both files to begin.")
