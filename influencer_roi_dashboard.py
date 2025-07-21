# influencer_dashboard_final.py

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Influencer ROI Dashboard", layout="wide")
st.title("📈 Influencer Campaign ROI Dashboard")

# Sidebar File Uploads
st.sidebar.header("📂 Upload CSV Files")
influencers_file = st.sidebar.file_uploader("Influencers CSV", type="csv")
posts_file = st.sidebar.file_uploader("Posts CSV", type="csv")
tracking_file = st.sidebar.file_uploader("Tracking Data CSV", type="csv")
payouts_file = st.sidebar.file_uploader("Payouts CSV", type="csv")

# Proceed only if all files are uploaded
if all([influencers_file, posts_file, tracking_file, payouts_file]):
    try:
        # Load files
        influencers_df = pd.read_csv(influencers_file)
        posts_df = pd.read_csv(posts_file)
        tracking_df = pd.read_csv(tracking_file)
        payouts_df = pd.read_csv(payouts_file)

        # Validate required columns
        for df, name, cols in [
            (influencers_df, "influencers", ["id", "name", "category", "gender", "follower_count", "platform"]),
            (posts_df, "posts", ["influencer_id", "platform", "date", "URL", "caption", "reach", "likes", "comments"]),
            (tracking_df, "tracking_data", ["source", "campaign", "influencer_id", "user_id", "product", "date", "revenue"]),
            (payouts_df, "payouts", ["influencer_id", "basis", "rate", "total_payout"])
        ]:
            missing_cols = [col for col in cols if col not in df.columns]
            if missing_cols:
                st.error(f"Missing columns in {name}.csv: {missing_cols}")
                st.stop()

        # Merge tracking and payouts
        merged_df = tracking_df.merge(payouts_df, on="influencer_id", how="left")
        merged_df["revenue"] = merged_df["revenue"].fillna(0)
        merged_df["total_payout"] = merged_df["total_payout"].fillna(0)
        merged_df["ROAS"] = merged_df.apply(lambda row: row["revenue"] / row["total_payout"] if row["total_payout"] > 0 else 0, axis=1)

        # Filter Influencers
        st.sidebar.header("🔍 Filters")
        selected_platform = st.sidebar.multiselect("Platform", influencers_df["platform"].unique(), default=list(influencers_df["platform"].unique()))
        selected_category = st.sidebar.multiselect("Category", influencers_df["category"].unique(), default=list(influencers_df["category"].unique()))

        filtered_influencers = influencers_df[
            influencers_df["platform"].isin(selected_platform) &
            influencers_df["category"].isin(selected_category)
        ]

        # Campaign Summary
        st.subheader("📊 Campaign Performance Summary")
        campaign_summary = tracking_df.groupby("campaign").agg({"sum", "revenue": "sum"}).reset_index()
        st.dataframe(campaign_summary)

        # ROAS Summary
        st.subheader("📈 ROAS by Influencer")
        roas_df = merged_df.groupby("influencer_id").agg({
            "revenue": "sum",
            "total_payout": "sum",
            "ROAS": "mean"
        }).reset_index()

        roas_df = roas_df.merge(filtered_influencers, left_on="influencer_id", right_on="id", how="left")

        fig = px.bar(roas_df, x="name", y="ROAS", color="platform", title="Return on Ad Spend (ROAS) by Influencer")
        st.plotly_chart(fig, use_container_width=True)

        # Top Performers
        st.subheader("🏆 Top Influencers by Revenue")
        st.dataframe(roas_df.sort_values(by="revenue", ascending=False)[["name", "revenue", "ROAS"]].head(5))

        # Underperformers
        st.subheader("⚠️ Influencers with Low ROAS")
        st.dataframe(roas_df[roas_df["ROAS"] < 1][["name", "revenue", "total_payout", "ROAS"]].sort_values(by="ROAS").head(5))

        # Export
        st.subheader("📤 Download ROAS Report")
        st.download_button("Download CSV", roas_df.to_csv(index=False), file_name="roas_report.csv")

    except Exception as e:
        st.error(f"Unexpected error occurred: {e}")

else:
    st.info("Please upload all required CSV files to begin.")
