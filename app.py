import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Portfolio Cross Qualifier", layout="wide")

st.title("📊 Portfolio Cross-Qualification Tool")

st.markdown("""
Upload your portfolio and a qualifying stock list.
The app will show which strategy your portfolio aligns with the most.
""")

# ===============================
# FILE UPLOAD
# ===============================

portfolio_file = st.file_uploader("Upload Portfolio CSV", type=["csv"])
qualifying_file = st.file_uploader("Upload Qualifying List CSV", type=["csv"])

if portfolio_file and qualifying_file:

    # ===============================
    # LOAD DATA
    # ===============================
    portfolio = pd.read_csv(portfolio_file)
    qualifying = pd.read_csv(qualifying_file)

    # Clean
    portfolio["Ticker"] = portfolio["Ticker"].str.upper().str.strip()
    qualifying["Ticker"] = qualifying["Ticker"].str.upper().str.strip()

    if "Weight" not in portfolio.columns:
        st.error("Portfolio file must include a Weight column.")
        st.stop()

    # ===============================
    # MERGE DATA
    # ===============================
    merged = portfolio.merge(qualifying, on="Ticker", how="left")

    # ===============================
    # COUNT OVERLAP
    # ===============================
    count_summary = (
        merged.groupby("Strategy")["Ticker"]
        .count()
        .sort_values(ascending=False)
    )

    weight_summary = (
        merged.groupby("Strategy")["Weight"]
        .sum()
        .sort_values(ascending=False)
    )

    total_weight = portfolio["Weight"].sum()

    weight_percent = (weight_summary / total_weight * 100).round(2)

    # ===============================
    # DISPLAY RESULTS
    # ===============================
    st.subheader("📈 Strategy Alignment by Weight (%)")

    if not weight_percent.empty:
        st.dataframe(weight_percent.reset_index().rename(columns={"Weight": "Weight %"}))

        # Pie Chart
        fig, ax = plt.subplots()
        ax.pie(
            weight_percent.values,
            labels=weight_percent.index,
            autopct="%1.1f%%",
            startangle=90,
        )
        ax.axis("equal")
        st.pyplot(fig)

    else:
        st.warning("No matching strategies found.")

    # ===============================
    # SHOW UNMAPPED
    # ===============================
    unmapped = merged[merged["Strategy"].isna()]

    if not unmapped.empty:
        st.subheader("⚠️ Unmapped Stocks")
        st.dataframe(unmapped[["Ticker", "Weight"]])
