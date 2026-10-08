"""
Employee Engagement, Satisfaction, and Burnout Diagnostic Analysis
--------------------------------------------------------------------
Steps covered: Data validation & normalization, Engagement Index,
Burnout Risk flagging, Workload & Career-Stage analysis.

HOW TO USE:
1. Put your CSV file (e.g. "Palo Alto Networks.csv") in the same folder
   as this script, and update DATA_PATH below if the name is different.
2. Install requirements once:  pip install pandas numpy matplotlib seaborn scikit-learn
3. Run:  python eda_analysis.py
4. Check the "outputs" folder for the processed CSV and chart images.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from sklearn.preprocessing import MinMaxScaler

# ---------------- CONFIG ----------------
DATA_PATH = "Palo Alto Networks.csv"   # <-- change this if your file name/path is different
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
sns.set_style("whitegrid")


# ---------------- STEP 1: LOAD & INITIAL CHECK ----------------
print("=" * 60)
print("STEP 1: Loading data")
print("=" * 60)

df = pd.read_csv(DATA_PATH)
print("Shape:", df.shape)
print("\nColumn info:")
print(df.info())
print("\nMissing values per column:")
print(df.isnull().sum())

# Drop constant/ID columns that sometimes appear in this dataset
for col in ["EmployeeCount", "EmployeeNumber", "StandardHours", "Over18"]:
    if col in df.columns:
        df.drop(columns=col, inplace=True)


# ---------------- STEP 2: DATA VALIDATION & NORMALIZATION ----------------
print("\n" + "=" * 60)
print("STEP 2: Data validation & normalization")
print("=" * 60)

ordinal_cols = ["EnvironmentSatisfaction", "JobSatisfaction", "JobInvolvement",
                "RelationshipSatisfaction", "WorkLifeBalance", "PerformanceRating"]

for col in ordinal_cols:
    if col in df.columns and df[col].isnull().sum() > 0:
        median_val = df[col].median()
        df[col] = df[col].fillna(median_val)
        print(f"Filled missing values in {col} with median ({median_val})")

# Min-max normalize the 4 core satisfaction/involvement scores (0-1 range)
norm_cols = ["JobInvolvement", "JobSatisfaction", "EnvironmentSatisfaction", "RelationshipSatisfaction"]
scaler = MinMaxScaler()
df[[c + "_norm" for c in norm_cols]] = scaler.fit_transform(df[norm_cols])


# ---------------- STEP 3: ENGAGEMENT INDEX ----------------
print("\n" + "=" * 60)
print("STEP 3: Building Engagement Index")
print("=" * 60)

df["EngagementIndex"] = df[[c + "_norm" for c in norm_cols]].mean(axis=1)
print("Engagement Index created. Sample values:")
print(df["EngagementIndex"].describe())


# ---------------- STEP 4: BURNOUT RISK ----------------
print("\n" + "=" * 60)
print("STEP 4: Flagging Burnout Risk")
print("=" * 60)

low_engagement_cutoff = df["EngagementIndex"].quantile(0.33)

def burnout_risk(row):
    score = 0
    if row["OverTime"] == "Yes":
        score += 1
    if row["WorkLifeBalance"] <= 2:
        score += 1
    if row["EngagementIndex"] < low_engagement_cutoff:
        score += 1
    if score >= 2:
        return "High"
    elif score == 1:
        return "Medium"
    return "Low"

df["BurnoutRisk"] = df.apply(burnout_risk, axis=1)
print(df["BurnoutRisk"].value_counts())


# ---------------- STEP 5: WORKLOAD & CAREER-STAGE ANALYSIS ----------------
print("\n" + "=" * 60)
print("STEP 5: Workload & Career-Stage Analysis")
print("=" * 60)

overtime_engagement = df.groupby("OverTime")["EngagementIndex"].mean()
print("\nEngagement by OverTime:\n", overtime_engagement)

travel_engagement = df.groupby("BusinessTravel")["EngagementIndex"].mean()
print("\nEngagement by BusinessTravel:\n", travel_engagement)

df["CommuteBucket"] = pd.cut(df["DistanceFromHome"], bins=[0, 5, 15, 30],
                              labels=["Short", "Medium", "Long"], include_lowest=True)
commute_engagement = df.groupby("CommuteBucket", observed=True)["EngagementIndex"].mean()
print("\nEngagement by Commute distance:\n", commute_engagement)

joblevel_engagement = df.groupby("JobLevel")["EngagementIndex"].mean()
print("\nEngagement by Job Level:\n", joblevel_engagement)

tenure_engagement = df.groupby(pd.cut(df["YearsAtCompany"], bins=[0, 2, 5, 10, 40]),
                                observed=True)["EngagementIndex"].mean()
print("\nEngagement by Tenure bucket:\n", tenure_engagement)

if "Attrition" in df.columns:
    attrition_engagement = df.groupby("Attrition")["EngagementIndex"].mean()
    print("\nEngagement by Attrition (contextual only):\n", attrition_engagement)


# ---------------- SAVE PROCESSED DATA ----------------
processed_path = os.path.join(OUTPUT_DIR, "processed_hr_data.csv")
df.to_csv(processed_path, index=False)
print(f"\nProcessed data saved to: {processed_path}")


# ---------------- CHARTS (for the research paper) ----------------
print("\nGenerating charts...")

plt.figure(figsize=(6, 4))
sns.histplot(df["EngagementIndex"], bins=20, kde=True)
plt.title("Engagement Index Distribution")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "engagement_distribution.png"))
plt.close()

plt.figure(figsize=(6, 4))
sns.countplot(x="BurnoutRisk", data=df, order=["Low", "Medium", "High"])
plt.title("Burnout Risk Levels")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "burnout_risk_counts.png"))
plt.close()

plt.figure(figsize=(7, 4))
sns.barplot(x=overtime_engagement.index, y=overtime_engagement.values)
plt.title("Engagement: OverTime vs Non-OverTime")
plt.ylabel("Avg Engagement Index")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "engagement_overtime.png"))
plt.close()

plt.figure(figsize=(8, 4))
sns.barplot(x=joblevel_engagement.index, y=joblevel_engagement.values)
plt.title("Engagement by Job Level")
plt.ylabel("Avg Engagement Index")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "engagement_joblevel.png"))
plt.close()

plt.figure(figsize=(7, 4))
sns.barplot(x=travel_engagement.index, y=travel_engagement.values)
plt.title("Engagement by Business Travel Frequency")
plt.ylabel("Avg Engagement Index")
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "engagement_travel.png"))
plt.close()

print(f"Charts saved in '{OUTPUT_DIR}/' folder.")


# ---------------- KPI SUMMARY (use these numbers in your report) ----------------
print("\n" + "=" * 60)
print("KPI SUMMARY")
print("=" * 60)
print("Org-wide Engagement Index:", round(df["EngagementIndex"].mean(), 3))
print("High Burnout Risk %:", round((df["BurnoutRisk"] == "High").mean() * 100, 1))
print("Avg Work-Life Balance Score:", round(df["WorkLifeBalance"].mean(), 2))
print("Employees on OverTime:", round((df["OverTime"] == "Yes").mean() * 100, 1), "%")
