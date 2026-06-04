import streamlit as st
import pandas as pd
from utils import run_query

st.title("📈 Retention Metrics")

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
# METRIC SELECTOR
# -------------------------
metric = st.selectbox(
    "Select metric",
    ["m1", "m2", "m3", "m6", "m12"]
)

# -------------------------
# DATA PREP
# -------------------------
chart_df = df[["cohort_month", metric]].dropna()

# -------------------------
# CHART
# -------------------------
st.line_chart(chart_df.set_index("cohort_month"))
