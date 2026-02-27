def generate_internal_analysis(results_series, percent_series, strategy_matrix):
    
    dominant_strategy = results_series.idxmax()
    dominant_percent = percent_series.loc[dominant_strategy]
    
    top_two = percent_series.iloc[:2].sum()
    
    avg_overlap = strategy_matrix["Total_Strategies"].mean()
    
    # Concentration logic
    if dominant_percent > 50:
        concentration = "High single-factor concentration"
    elif dominant_percent > 35:
        concentration = "Moderate factor concentration"
    else:
        concentration = "Diversified factor exposure"
    
    # Overlap logic
    if avg_overlap < 1.5:
        overlap_comment = "Low multi-factor overlap"
    elif avg_overlap < 2.5:
        overlap_comment = "Moderate multi-factor overlap"
    else:
        overlap_comment = "High multi-factor clustering"
    
    summary = f"""
    Dominant Style: {dominant_strategy} ({dominant_percent}% of holdings).

    Top two strategies represent {round(top_two,1)}% of the portfolio,
    indicating {concentration.lower()}.

    Average strategies per stock: {round(avg_overlap,2)}.
    {overlap_comment}.
    """
    
    return summary
