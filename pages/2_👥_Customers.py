import streamlit as st
import pandas as pd
from utils import run_query

st.title("👥 Customer Analysis")

# -------------------------
# LOAD DATA
# -------------------------
query = """
SELECT
    customer_unique_id,
    total_orders,
    total_spent,
    last_order_date
FROM `project-ecommerce-497614.ecommerce_de.mart_customers`
"""

df = run_query(query)

# -------------------------
# GLOBAL FILTER
# -------------------------
start, end = st.session_state.get("global_date_range", (None, None))

if start:
    df = df[
        (df["last_order_date"] >= pd.to_datetime(start)) &
        (df["last_order_date"] <= pd.to_datetime(end))
    ]

# -------------------------
# KPIs
# -------------------------
col1, col2, col3, col4 = st.columns(4)

total_customers = df["customer_unique_id"].nunique()
avg_value = df["total_spent"].mean()
avg_orders = df["total_orders"].mean()

top10 = df.sort_values("total_spent", ascending=False).head(10)
top10_share = top10["total_spent"].sum() / df["total_spent"].sum()

col1.metric("Customers", f"{total_customers:,}")
col2.metric("Avg Value", f"{avg_value:,.2f}")
col3.metric("Avg Orders", f"{avg_orders:.2f}")
col4.metric("Top 10 Revenue %", f"{top10_share:.2%}")

st.divider()

# -------------------------
# TOP CUSTOMERS
# -------------------------
st.subheader("🏆 Top Customers")

top = df.sort_values(
    by="total_spent",
    ascending=False
).head(20)

display = top.copy()
display["total_spent"] = display["total_spent"].apply(lambda x: f"{x:,.2f}")

st.dataframe(display, width="stretch")

# -------------------------
# SEGMENTATION ✅ (MEJOR QUE BINNING)
# -------------------------
st.subheader("📊 Customer Segments")

# segmentación simple en 3 grupos
df["segment"] = pd.qcut(
    df["total_spent"],
    q=3,
    labels=["Low", "Medium", "High"]
)

segment_counts = df["segment"].value_counts()

st.bar_chart(segment_counts)

# -------------------------
# SEGMENT VALUE
# -------------------------
st.subheader("💰 Revenue by Segment")

segment_value = df.groupby("segment")["total_spent"].sum()

st.bar_chart(segment_value)


# -------------------------
# INSIGHTS
# -------------------------
st.subheader("💡 Customer Insights")

if len(df) > 0:

    top10 = df.sort_values("total_spent", ascending=False).head(10)
    top10_share = top10["total_spent"].sum() / df["total_spent"].sum()

    high_value_ratio = (df["total_spent"] > df["total_spent"].quantile(0.8)).mean()

    if top10_share > 0.4:
        st.warning(f"⚠️ Top 10 customers generate {top10_share:.2%} of revenue (high concentration)")
    else:
        st.success(f"✅ Revenue well distributed (Top 10 = {top10_share:.2%})")

    st.info(f"👑 Top 20% customers represent {high_value_ratio:.2%} of the base")
