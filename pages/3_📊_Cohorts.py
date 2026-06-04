import streamlit as st
import pandas as pd
from utils import run_query

st.title("📊 Cohort Analysis")

# -------------------------
# LOAD DATA
# -------------------------
query = """
SELECT *
FROM `project-ecommerce-497614.ecommerce_de.mart_customer_cohorts_pivot`
ORDER BY cohort_month
"""

df = run_query(query)

# -------------------------
# KPIs
# -------------------------
col1, col2, col3 = st.columns(3)

col1.metric("Cohorts", df.shape[0])
col2.metric("Avg M1", f"{df['m1'].mean():.2%}")
col3.metric("Avg M3", f"{df['m3'].mean():.2%}")

st.divider()

# -------------------------
# FILTER
# -------------------------
min_c = df["cohort_month"].min()
max_c = df["cohort_month"].max()

cohort_range = st.slider(
    "Select cohort range",
    min_value=min_c,
    max_value=max_c,
    value=(min_c, max_c)
)

filtered_df = df[
    (df["cohort_month"] >= pd.to_datetime(cohort_range[0])) &
    (df["cohort_month"] <= pd.to_datetime(cohort_range[1]))
]

# -------------------------
# FORMAT
# -------------------------
percent_cols = [col for col in df.columns if col.startswith("m")]

display_df = filtered_df.copy()

for col in percent_cols:
    display_df[col] = display_df[col].apply(
        lambda x: f"{x:.2%}" if pd.notnull(x) else ""
    )

# -------------------------
# TABLE (lighter → faster)
# -------------------------
st.dataframe(display_df.head(200), width="stretch")
