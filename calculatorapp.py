pip install streamlit pandas plotly numpy

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import List, Dict, Tuple

# Define the pricing tiers
TIERS = [
    {"lower": 0, "upper": 125_000, "rate": 0.0330},
    {"lower": 125_001, "upper": 250_000, "rate": 0.0315},
    {"lower": 250_001, "upper": 416_667, "rate": 0.0297},
    {"lower": 416_668, "upper": 833_333, "rate": 0.0264},
    {"lower": 833_334, "upper": 1_666_667, "rate": 0.0231},
    {"lower": 1_666_668, "upper": 2_500_000, "rate": 0.0215},
    {"lower": 2_500_001, "upper": 3_333_333, "rate": 0.0198},
    {"lower": 3_333_334, "upper": 4_166_667, "rate": 0.0182},
    {"lower": 4_166_668, "upper": 6_250_000, "rate": 0.0165},
    {"lower": 6_250_001, "upper": 8_333_333, "rate": 0.0132},
    {"lower": 8_333_334, "upper": 12_500_000, "rate": 0.0116},
    {"lower": 12_500_001, "upper": 16_666_667, "rate": 0.0107},
    {"lower": 16_666_668, "upper": 20_833_333, "rate": 0.0100},
    {"lower": 20_833_334, "upper": 25_000_000, "rate": 0.0095},
    {"lower": 25_000_001, "upper": 29_166_667, "rate": 0.0091},
    {"lower": 29_166_668, "upper": 33_333_333, "rate": 0.0088},
    {"lower": 33_333_334, "upper": 41_666_667, "rate": 0.0084},
    {"lower": 41_666_668, "upper": 62_500_000, "rate": 0.0069},
    {"lower": 62_500_001, "upper": 83_333_333, "rate": 0.0062},
    {"lower": 83_333_334, "upper": 104_166_667, "rate": 0.0054},
    {"lower": 104_166_668, "upper": 125_000_000, "rate": 0.0050},
    {"lower": 125_000_001, "upper": 145_833_333, "rate": 0.0046},
    {"lower": 145_833_334, "upper": 166_666_667, "rate": 0.0043},
    {"lower": 166_666_668, "upper": 187_500_000, "rate": 0.0040},
    {"lower": 187_500_001, "upper": 208_333_333, "rate": 0.0038},
    {"lower": 208_333_334, "upper": 250_000_000, "rate": 0.0034}
]

class PricingCalculator:
    def __init__(self, tiers: List[Dict]):
        self.tiers = tiers
        self.df_tiers = pd.DataFrame(tiers)
    
    def calculate_flex_price(self, monthly_spend: float) -> float:
        """Calculate the flex pricing based on monthly spend."""
        total = 0
        remaining = monthly_spend
        
        for tier in self.tiers:
            if remaining <= 0:
                break
                
            tier_spend = min(remaining, tier["upper"] - tier["lower"])
            total += tier_spend * tier["rate"]
            remaining -= tier_spend
        
        # Enforce $2,500 minimum for spends under $125,000
        if monthly_spend <= 125_000:
            return max(total, 2500)
        
        return total
    
    def calculate_commit_price(self, monthly_spend: float, commit_amount: float) -> float:
        """Calculate the commit pricing based on monthly spend and commitment."""
        if commit_amount == 0:
            return self.calculate_flex_price(monthly_spend)
        
        # Find the appropriate tier rate for the commitment
        commit_tier = next(
            (tier for tier in self.tiers if tier["upper"] >= commit_amount),
            self.tiers[-1]
        )
        commit_rate = commit_tier["rate"]
        
        # Calculate committed spend
        committed_amount = min(monthly_spend, commit_amount) * commit_rate
        
        # Calculate any overflow at flex rates
        overflow_amount = (
            self.calculate_flex_price(monthly_spend - commit_amount)
            if monthly_spend > commit_amount
            else 0
        )
        
        return committed_amount + overflow_amount
    
    def recommend_commit_tier(self, monthly_spend: float) -> float:
        """Recommend an optimal commitment tier based on monthly spend."""
        current_tier = next(
            (tier for tier in self.tiers if 
             monthly_spend >= tier["lower"] and monthly_spend <= tier["upper"]),
            self.tiers[-1]
        )
        
        # Find the next tier for comparison
        tier_index = self.tiers.index(current_tier)
        next_tier = self.tiers[tier_index + 1] if tier_index < len(self.tiers) - 1 else None
        
        # If we're near the top of current tier, recommend next tier
        if next_tier and monthly_spend > current_tier["upper"] * 0.8:
            return next_tier["upper"]
        
        return current_tier["upper"]
    
    def generate_comparison_chart(self, monthly_spend: float, commit_amount: float) -> go.Figure:
        """Generate a visual comparison of flex vs commit pricing."""
        flex_price = self.calculate_flex_price(monthly_spend)
        commit_price = self.calculate_commit_price(monthly_spend, commit_amount)
        
        fig = go.Figure()
        
        # Add bars for flex and commit pricing
        fig.add_trace(go.Bar(
            x=['Flex Pricing', 'Commit Pricing'],
            y=[flex_price, commit_price],
            marker_color=['rgb(55, 83, 109)', 'rgb(26, 118, 255)']
        ))
        
        # Update layout
        fig.update_layout(
            title='Pricing Comparison',
            yaxis_title='Monthly Cost ($)',
            showlegend=False,
            height=400
        )
        
        return fig

def main():
    st.set_page_config(page_title="CloudBolt Pricing Calculator", layout="wide")
    
    st.title("CloudBolt Pricing Calculator")
    
    # Initialize calculator
    calculator = PricingCalculator(TIERS)
    
    # Create columns for inputs
    col1, col2 = st.columns(2)
    
    with col1:
        monthly_spend = st.slider(
            "Monthly Cloud Spend ($)",
            min_value=50_000,
            max_value=250_000_000,
            value=500_000,
            step=10_000,
            format="$%d"
        )
    
    recommended_tier = calculator.recommend_commit_tier(monthly_spend)
    
    with col2:
        commit_amount = st.slider(
            "Monthly Commitment Level ($)",
            min_value=0,
            max_value=int(max(monthly_spend, recommended_tier)),
            value=0,
            step=10_000,
            format="$%d"
        )
    
    # Calculate prices
    flex_price = calculator.calculate_flex_price(monthly_spend)
    commit_price = calculator.calculate_commit_price(monthly_spend, commit_amount)
    savings = flex_price - commit_price
    
    # Display pricing comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Flex Pricing", f"${flex_price:,.2f}")
    
    with col2:
        st.metric("Commit Pricing", f"${commit_price:,.2f}")
    
    # Display recommendations
    st.subheader("Pricing Recommendations")
    
    if savings > 0:
        st.success(f"Potential Monthly Savings: ${savings:,.2f}")
    
    st.info(
        f"Recommended Commitment Tier: ${recommended_tier:,.2f}\n\n"
        f"Based on your current monthly spend of ${monthly_spend:,.2f}"
    )
    
    # Display comparison chart
    st.plotly_chart(calculator.generate_comparison_chart(monthly_spend, commit_amount))
    
    # Display tier table
    st.subheader("Pricing Tiers")
    
    # Convert tiers to DataFrame for display
    df_display = pd.DataFrame(TIERS)
    df_display['Rate'] = df_display['rate'].apply(lambda x: f"{x:.2%}")
    df_display['Spend Range'] = df_display.apply(
        lambda x: f"${x['lower']:,.0f} - ${x['upper']:,.0f}", 
        axis=1
    )
    
    st.dataframe(
        df_display[['Spend Range', 'Rate']],
        hide_index=True,
        use_container_width=True
    )

if __name__ == "__main__":
    main()
