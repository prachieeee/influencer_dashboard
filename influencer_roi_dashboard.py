# influencer_dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Influencer Campaign ROI Dashboard", layout="wide")
st.title("📊 Influencer Campaign ROI Dashboard")

st.sidebar.header("🔍 Filter Data")

# Upload CSVs
st.sidebar.subheader("Upload CSV Files")
influencers_file = st.sidebar.file_uploader("Upload influencers.csv", type="csv")
posts_file = st.sidebar.file_uploader("Upload posts.csv", type="csv")
tracking_file = st.sidebar.file_uploader("Upload tracking_data.csv", type="csv")
payouts_file = st.sidebar.file_uploader("Upload payouts.csv", type="csv")

if all([influencers_file, posts_file, tracking_file, payouts_file]):
    try:
        # Read CSVs
        influencers_df = pd.read_csv(influencers_file)
        posts_df = pd.read_csv(posts_file)
        tracking_df = pd.read_csv(tracking_file)
        payouts_df = pd.read_csv(payouts_file)

        # Ensure required columns exist in tracking and payouts
        default_tracking_cols = {"influencer_id": 0, "revenue": 0, "orders": 0, "campaign": "Unknown"}
        default_payouts_cols = {"influencer_id": 0, "total_payout": 0}

        for col, default in default_tracking_cols.items():
            if col not in tracking_df.columns:
                tracking_df[col] = default
        for col, default in default_payouts_cols.items():
            if col not in payouts_df.columns:
                payouts_df[col] = default

        # Merge tracking and payouts for ROAS
        merged_df = tracking_df.merge(payouts_df, on="influencer_id", how="left")

        # Safely calculate ROAS
        merged_df["revenue"] = merged_df["revenue"].fillna(0)
        merged_df["total_payout"] = merged_df["total_payout"].fillna(0)
        merged_df["ROAS"] = merged_df.apply(lambda row: row["revenue"] / row["total_payout"] if row["total_payout"] > 0 else 0, axis=1)

        # Filters
        selected_platform = st.sidebar.multiselect(
            "Platform", influencers_df["platform"].unique(), default=list(influencers_df["platform"].unique())
        )
        selected_category = st.sidebar.multiselect(
            "Category", influencers_df["category"].unique(), default=list(influencers_df["category"].unique())
        )

        influencers_df = influencers_df[
            influencers_df["platform"].isin(selected_platform)
            & influencers_df["category"].isin(selected_category)
        ]

        # Performance Summary
        st.subheader("Campaign Performance Summary")
        campaign_summary = tracking_df.groupby("campaign").agg({
            "orders": "sum",
            "revenue": "sum"
        }).reset_index()
        st.dataframe(campaign_summary)

        # ROAS Visualization
        st.subheader("ROAS by Influencer")
        roas_df = merged_df.groupby("influencer_id").agg({
            "orders": "sum",
            "revenue": "sum",
            "total_payout": "sum",
            "ROAS": "mean"
        }).reset_index()
        roas_df = roas_df.merge(influencers_df, left_on="influencer_id", right_on="id", how="left")

        fig = px.bar(
            roas_df,
            x="name",
            y="ROAS",
            color="platform",
            title="Return on Ad Spend (ROAS) by Influencer"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Top Influencers
        st.subheader("Top Influencers by Revenue")
        top_influencers = roas_df.sort_values(by="revenue", ascending=False)[["name", "revenue", "ROAS"]]
        st.dataframe(top_influencers.head(5))

        # Poor ROI influencers
        st.subheader("Low Performing Influencers")
        low_performers = roas_df[roas_df["ROAS"] < 1].sort_values(by="ROAS")
        st.dataframe(low_performers[["name", "revenue", "total_payout", "ROAS"]].head(5))

        # Export
        st.subheader("Download Insights")
        csv_data = roas_df.to_csv(index=False)
        st.download_button("Download ROAS Report", csv_data, file_name="roas_report.csv", mime="text/csv")

    except Exception as e:
        st.error(f"An error occurred while processing the data: {e}")

else:
    st.info("Please upload all required CSV files from the sidebar to begin.")
