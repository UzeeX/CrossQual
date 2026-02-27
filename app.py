import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Portfolio Strategy Intelligence",
    layout="wide"
)

# -----------------------------
# Institutional Styling
# -----------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
}
h1, h2, h3 {
    font-weight: 600;
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

    # ----------------------------
    # CLEAN SYMBOLS
    # ----------------------------
    def clean_symbol(x):
        x = str(x).upper().strip()
        if ":" in x:  # remove XTSE: prefix
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
    col1, col2 = st.columns(2)
    col1.metric("Total Holdings", total_holdings)
    col2.metric("Matched to Strategy Universe", matched)

    if matched == 0:
        st.warning("No symbol matches found.")
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
    # BUILD STRATEGY MATRIX
    # ----------------------------
    strategy_matrix = pd.DataFrame()
    strategy_matrix["TICKER"] = merged["TICKER"]

    results = {}

    for strat in strategy_cols:

        col_data = merged[strat].fillna(0)

        col_data = col_data.replace({
            "YES": 1, "Yes": 1, "Y": 1,
            "TRUE": 1, True: 1
        })

        col_data = pd.to_numeric(col_data, errors="coerce").fillna(0)

        qualifies = (col_data > 0).astype(int)

        strategy_matrix[strat] = qualifies
        results[strat] = qualifies.sum()

    results_series = pd.Series(results).sort_values(ascending=False)
    percent_series = (results_series / total_holdings * 100).round(1)

    # ----------------------------
    # RANKING + BADGES
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

    display_table = ranking.set_index("Strategy")[[
        "Badge", "Count", "% of Portfolio"
    ]]

    st.dataframe(display_table, use_container_width=True)
    st.bar_chart(percent_series)

    # ----------------------------
    # OVERLAP DISTRIBUTION
    # ----------------------------
    st.divider()
    st.subheader("Strategy Overlap Distribution")

    strategy_matrix["Total_Strategies"] = strategy_matrix[strategy_cols].sum(axis=1)
    overlap_distribution = strategy_matrix.groupby("Total_Strategies").size()

    st.bar_chart(overlap_distribution)

    # ----------------------------
    # STYLED OVERLAP MATRIX
    # ----------------------------
    st.divider()
    st.subheader("Detailed Overlap Matrix")

    display_matrix = strategy_matrix.set_index("TICKER")

    # Replace 1 with check mark and 0 with blank
    display_matrix = display_matrix.replace({1: "✓", 0: ""})

    def style_cells(val):
        if val == "✓":
            return "background-color: #1f7a1f; color: white; text-align: center;"
        else:
            return "background-color: #0e1117; color: #0e1117; text-align: center;"

    styled_matrix = display_matrix.style.applymap(style_cells)

    st.dataframe(styled_matrix, use_container_width=True)

    # ----------------------------
    # DOWNLOAD REPORT
    # ----------------------------
    st.divider()

    st.download_button(
        "Download Strategy Intelligence Report",
        ranking.to_csv(index=False),
        "strategy_intelligence_report.csv",
        "text/csv"
    )

else:
    st.info("Upload both files to begin.")
