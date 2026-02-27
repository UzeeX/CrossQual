import streamlit as st
import pandas as pd

st.set_page_config(page_title="Portfolio Cross Qualifier", layout="wide")
st.title("📊 Portfolio Strategy Membership Counter")

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
    def clean_qual_symbol(x):
        x = str(x).upper().strip()
        if ":" in x:  # Remove XTSE: prefix
            x = x.split(":")[1]
        return x

    portfolio["TICKER"] = portfolio["TICKER"].astype(str).str.upper().str.strip()
    qualifying["SYMBOL"] = qualifying["SYMBOL"].apply(clean_qual_symbol)

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
    st.info(f"Matched {matches} out of {len(portfolio)} portfolio stocks")

    if matches == 0:
        st.warning("No symbol matches found. Check formatting.")
        st.stop()

    # ----------------------------
    # DETECT STRATEGY COLUMNS
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
    # COUNT MEMBERSHIP
    # ----------------------------
    membership_counts = {}

    for strat in strategy_cols:

        if strat in merged.columns:

            col_data = merged[strat].fillna(0)

            # Convert possible YES/TRUE formats to 1
            col_data = col_data.replace({
                "YES": 1, "Yes": 1, "Y": 1,
                "TRUE": 1, True: 1
            })

            col_data = pd.to_numeric(col_data, errors="coerce").fillna(0)

            # Count only positive values (qualified stocks)
            count = (col_data > 0).sum()

            membership_counts[strat] = int(count)

    membership_series = pd.Series(membership_counts).sort_values(ascending=False)

    # ----------------------------
    # DISPLAY RESULTS
    # ----------------------------
    st.divider()

    st.subheader("📊 Number of Portfolio Stocks Qualifying Per Strategy")
    st.dataframe(membership_series)
    st.bar_chart(membership_series)

    # ----------------------------
    # OPTIONAL: SHOW WHICH STOCKS QUALIFY PER STRATEGY
    # ----------------------------
    st.divider()
    st.subheader("🔎 See Stocks Per Strategy")

    selected_strategy = st.selectbox("Select a strategy", strategy_cols)

    if selected_strategy:
        col_data = pd.to_numeric(
            merged[selected_strategy],
            errors="coerce"
        ).fillna(0)

        qualified_stocks = merged.loc[col_data > 0, "TICKER"]

        st.write(f"{len(qualified_stocks)} stocks qualify under {selected_strategy}")
        st.dataframe(qualified_stocks.reset_index(drop=True))

else:
    st.info("Upload both files to begin.")
