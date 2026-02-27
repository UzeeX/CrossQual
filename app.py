import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Portfolio Strategy Intelligence",
    layout="wide"
)

# -----------------------------
# STYLING (Institutional Look)
# -----------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
}
h1 {
    font-weight: 600;
}
.metric-container {
    border-radius: 12px;
    padding: 1rem;
}
</style>
""", unsafe_allow_html=True)

st.title("Portfolio Strategy Intelligence")
st.caption("Institutional Strategy Classification & Overlap Analysis")

portfolio_file = st.file_uploader("Upload Portfolio CSV", type=["csv"])
qualifying_file = st.file_uploader("Upload Cross Qualifying Matrix CSV", type=["csv"])

if portfolio_file and qualifying_file:

    # ----------------------------
    # LOAD DATA
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
        if ":" in x:
            x = x.split(":")[1]
        return x

    portfolio["TICKER"] = portfolio["TICKER"].astype(str).str.upper().str.strip()
    qualifying["SYMBOL"] = qualifying["SYMBOL"].apply(clean_symbol)

    merged = portfolio.merge(
        qualifying,
        left_on="TICKER",
        right_on="SYMBOL",
        how="left"
    )

    total_holdings = len(portfolio)
    matched = merged["SYMBOL"].notna().sum()

    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("Total Holdings", total_holdings)
    c2.metric("Matched to Strategy Universe", matched)

    if matched == 0:
        st.warning("No matches found.")
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
    # COUNT STRATEGY MEMBERSHIP
    # ----------------------------
    results = {}

    strategy_matrix = pd.DataFrame()
    strategy_matrix["TICKER"] = merged["TICKER"]

    for strat in strategy_cols:

        if strat in merged.columns:

            col_data = merged[strat].fillna(0)

            col_data = col_data.replace({
                "YES": 1, "Yes": 1, "Y": 1,
                "TRUE": 1, True: 1
            })

            col_data = pd.to_numeric(col_data, errors="coerce").fillna(0)

            qualifies = col_data > 0

            strategy_matrix[strat] = qualifies.astype(int)

            results[strat] = qualifies.sum()

    results_series = pd.Series(results).sort_values(ascending=False)
    percent_series = (results_series / total_holdings * 100).round(1)

    # ----------------------------
    # RANKING BADGES
    # ----------------------------
    ranking = results_series.reset_index()
    ranking.columns = ["Strategy", "Count"]

    ranking["Rank"] = ranking["Count"].rank(method="min", ascending=False).astype(int)

    def badge(rank):
        if rank == 1:
            return "🥇"
        elif rank == 2:
            return "🥈"
        elif rank == 3:
            return "🥉"
        else:
            return ""

    ranking["Badge"] = ranking["Rank"].apply(badge)
    ranking["% of Portfolio"] = percent_series.values

    # ----------------------------
    # DOMINANT STRATEGY
    # ----------------------------
    dominant = ranking.iloc[0]

    st.divider()
    st.subheader("Dominant Strategy")

    st.metric(
        f"{dominant['Badge']} {dominant['Strategy']}",
        f"{dominant['Count']} Holdings",
        delta=f"{dominant['% of Portfolio']}% of Portfolio"
    )

    # ----------------------------
    # STRATEGY RANKING TABLE
    # ----------------------------
    st.divider()
    st.subheader("Strategy Ranking")

    styled_table = ranking.set_index("Strategy")[[
        "Badge", "Count", "% of Portfolio"
    ]]

    st.dataframe(
        styled_table,
        use_container_width=True
    )

    st.bar_chart(percent_series)

    # ----------------------------
    # MULTI-STRATEGY OVERLAP MATRIX
    # ----------------------------
    st.divider()
    st.subheader("Multi-Strategy Overlap Matrix")

    overlap_matrix = strategy_matrix[strategy_cols]

    # Count how many strategies each stock belongs to
    strategy_matrix["Total_Strategies"] = overlap_matrix.sum(axis=1)

    overlap_summary = strategy_matrix.groupby("Total_Strategies").size()

    st.write("Distribution of strategy overlap per stock:")
    st.bar_chart(overlap_summary)

    st.write("Detailed Overlap Matrix:")
    st.dataframe(
        strategy_matrix.set_index("TICKER"),
        use_container_width=True
    )

    # ----------------------------
    # DOWNLOAD
    # ----------------------------
    st.divider()

    st.download_button(
        "Download Full Strategy Intelligence Report",
        ranking.to_csv(index=False),
        "strategy_intelligence_report.csv",
        "text/csv"
    )

else:
    st.info("Upload both files to begin.")
