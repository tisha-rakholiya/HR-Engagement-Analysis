"""
Employee Engagement, Satisfaction & Burnout Diagnostic Dashboard
--------------------------------------------------------------------
HOW TO USE:
1. First run eda_analysis.py — it creates outputs/processed_hr_data.csv
   which this dashboard reads.
2. Install requirements once: pip install streamlit pandas matplotlib seaborn
3. Run:  streamlit run streamlit_app.py
"""

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Employee Engagement Dashboard", layout="wide")


@st.cache_data
def load_data():
    return pd.read_csv("outputs/processed_hr_data.csv")

df = load_data()

st.title("🧭 Employee Engagement, Satisfaction & Burnout Diagnostic Dashboard")
st.caption("Palo Alto Networks — HR Analytics Project")

# ---------------- SIDEBAR FILTERS ----------------
st.sidebar.header("Filters")

departments = st.sidebar.multiselect(
    "Department", options=sorted(df["Department"].unique()),
    default=sorted(df["Department"].unique())
)
roles = st.sidebar.multiselect(
    "Job Role", options=sorted(df["JobRole"].unique()),
    default=sorted(df["JobRole"].unique())
)
overtime_filter = st.sidebar.selectbox("OverTime", options=["All", "Yes", "No"])
engagement_threshold = st.sidebar.slider("Min Engagement Index", 0.0, 1.0, 0.0, 0.05)
tenure_range = st.sidebar.slider(
    "Years at Company", 0, int(df["YearsAtCompany"].max()),
    (0, int(df["YearsAtCompany"].max()))
)

filtered = df[
    (df["Department"].isin(departments)) &
    (df["JobRole"].isin(roles)) &
    (df["EngagementIndex"] >= engagement_threshold) &
    (df["YearsAtCompany"].between(tenure_range[0], tenure_range[1]))
].copy()

if overtime_filter != "All":
    filtered = filtered[filtered["OverTime"] == overtime_filter]

st.sidebar.markdown(f"**{len(filtered)}** employees match current filters")

# ---------------- TABS ----------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Engagement Overview", "🔥 Burnout Risk Dashboard",
    "🧑‍💼 Role & Career Stage", "🚨 Manager Action Panel"
])

# ===== TAB 1: ENGAGEMENT OVERVIEW =====
with tab1:
    col1, col2, col3 = st.columns(3)
    col1.metric("Org-wide Engagement Index", round(filtered["EngagementIndex"].mean(), 3) if len(filtered) else "N/A")
    col2.metric("Employees in view", len(filtered))
    col3.metric("Avg Work-Life Balance", round(filtered["WorkLifeBalance"].mean(), 2) if len(filtered) else "N/A")

    c1, c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots()
        sns.histplot(filtered["EngagementIndex"], bins=20, kde=True, ax=ax)
        ax.set_title("Engagement Index Distribution")
        st.pyplot(fig)
    with c2:
        fig2, ax2 = plt.subplots()
        sns.boxplot(x="Department", y="EngagementIndex", data=filtered, ax=ax2)
        plt.setp(ax2.get_xticklabels(), rotation=30, ha="right")
        ax2.set_title("Engagement by Department")
        st.pyplot(fig2)

# ===== TAB 2: BURNOUT RISK =====
with tab2:
    high_risk_pct = round((filtered["BurnoutRisk"] == "High").mean() * 100, 1) if len(filtered) else 0
    st.metric("High Burnout Risk %", f"{high_risk_pct}%")

    c1, c2 = st.columns(2)
    with c1:
        fig3, ax3 = plt.subplots()
        sns.countplot(x="BurnoutRisk", data=filtered, order=["Low", "Medium", "High"], ax=ax3)
        ax3.set_title("Burnout Risk Levels")
        st.pyplot(fig3)
    with c2:
        fig4, ax4 = plt.subplots()
        sns.barplot(x="OverTime", y="EngagementIndex", data=filtered, ax=ax4)
        ax4.set_title("Engagement: OverTime vs Non-OverTime")
        st.pyplot(fig4)

    st.subheader("High-Risk Employees")
    st.dataframe(
        filtered[filtered["BurnoutRisk"] == "High"][
            ["Department", "JobRole", "OverTime", "WorkLifeBalance", "EngagementIndex"]
        ]
    )

# ===== TAB 3: ROLE & CAREER STAGE =====
with tab3:
    c1, c2 = st.columns(2)
    with c1:
        fig5, ax5 = plt.subplots()
        sns.barplot(x="JobLevel", y="EngagementIndex", data=filtered, ax=ax5)
        ax5.set_title("Engagement by Job Level")
        st.pyplot(fig5)
    with c2:
        fig6, ax6 = plt.subplots()
        sns.scatterplot(x="YearsInCurrentRole", y="EngagementIndex", data=filtered, ax=ax6)
        ax6.set_title("Years in Current Role vs Engagement")
        st.pyplot(fig6)

    fig7, ax7 = plt.subplots(figsize=(10, 4))
    sns.barplot(x="YearsAtCompany", y="EngagementIndex", data=filtered, ax=ax7, errorbar=None)
    ax7.set_title("Engagement Trend by Years at Company")
    st.pyplot(fig7)

# ===== TAB 4: MANAGER ACTION PANEL =====
with tab4:
    st.subheader("Low-Engagement Alerts")
    if len(filtered):
        cutoff = filtered["EngagementIndex"].quantile(0.25)
        low_engagement = filtered[filtered["EngagementIndex"] < cutoff]
        st.dataframe(
            low_engagement[
                ["Department", "JobRole", "EngagementIndex", "BurnoutRisk", "WorkLifeBalance", "OverTime"]
            ]
        )
        st.warning(f"⚠️ {len(low_engagement)} employees flagged as priority intervention areas.")
    else:
        st.info("No employees match the current filters.")
