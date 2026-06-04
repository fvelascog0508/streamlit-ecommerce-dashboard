import streamlit as st
import pandas as pd
from utils import run_query

st.title("📊 Sales Overview")

sales_query = """
SELECT
    date,
    revenue,
    orders,
    customers,
    avg_order_value
FROM `project-ecommerce-497614.ecommerce_de.mart_sales_daily`
ORDER BY date
"""

sales_df = run_query(sales_query)

start, end = st.session_state.get("global_date_range", (None, None))

if start:
    sales_df = sales_df[
        (sales_df["date"] >= pd.to_datetime(start)) &
        (sales_df["date"] <= pd.to_datetime(end))
    ]

# KPIs
col1, col2, col3, col4 = st.columns(4)

col1.metric("Revenue", f"{sales_df['revenue'].sum():,.0f}")
col2.metric("Orders", f"{sales_df['orders'].sum():,.0f}")
col3.metric("Customers", f"{sales_df['customers'].sum():,.0f}")
col4.metric("AOV", f"{sales_df['avg_order_value'].mean():,.2f}")

# Charts
st.line_chart(sales_df.set_index("date")[["revenue"]])

# Table (limit rows)
st.dataframe(sales_df.head(200), width="stretch")