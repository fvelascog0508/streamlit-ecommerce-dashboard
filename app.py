import streamlit as st
import pandas as pd
from utils import run_query
import plotly.express as px
import numpy as np


import streamlit as st

st.write("Secrets keys:", list(st.secrets.keys()))




st.set_page_config(layout="wide")

# -------------------------
# CACHE ✅
# -------------------------
@st.cache_data(show_spinner=False)
def load_data():
    query = """
    SELECT
        s.month,
        s.year,
        s.month_num,
        s.revenue,
        s.orders,
        s.customers,
        s.avg_order_value,
        i.insight
    FROM `project-ecommerce-497614.ecommerce_de.mart_sales_monthly` s
    LEFT JOIN `project-ecommerce-497614.ecommerce_de.insights_monthly` i
    USING (year, month_num)
    ORDER BY year, month_num
    """
    return run_query(query)

df = load_data()

# -------------------------
# PREP
# -------------------------
df["month_date"] = pd.to_datetime(df["month"])
df["month_name"] = df["month_date"].dt.strftime("%b")

month_order = ["Jan","Feb","Mar","Apr","May","Jun",
               "Jul","Aug","Sep","Oct","Nov","Dec"]

df["month_name"] = pd.Categorical(
    df["month_name"],
    categories=month_order,
    ordered=True
)

df = df.sort_values(["year","month_num"])

# -------------------------
# FILTERS
# -------------------------
years = sorted(df["year"].unique(), reverse=True)
selected_year = st.sidebar.selectbox("Year", years)

months = sorted(df[df["year"]==selected_year]["month_num"])
selected_month = st.sidebar.selectbox("Month", months)

current = df[(df["year"]==selected_year)&
             (df["month_num"]==selected_month)].iloc[0]

# -------------------------
# INSIGHT ✅ (FIXED)
# -------------------------
insight = current["insight"]
if pd.notna(insight):
    # mantener bullets pero quitar espacios excesivos
    lines = insight.split("\n")
    cleaned = [l.strip() for l in lines if l.strip() != ""]
    insight = "<br>".join(cleaned)

# -------------------------
# YOY / MOM
# -------------------------
prev_year = df[(df["year"]==selected_year-1)&
               (df["month_num"]==selected_month)]

prev_month = df[df["month_date"]<current["month_date"]].tail(1)

if len(prev_year)>0:
    p = prev_year.iloc[0]
elif len(prev_month)>0:
    p = prev_month.iloc[0]
else:
    p=None

if p is not None:
    rev_change = current["revenue"]/p["revenue"]-1
    ord_change = current["orders"]/p["orders"]-1
    aov_change = current["avg_order_value"]/p["avg_order_value"]-1
else:
    rev_change = ord_change = aov_change = None

# -------------------------
# FORECAST ✅ (RECUPERADO)
# -------------------------
df_year = df[df["year"] == selected_year]

forecast_x = []
forecast_y = []

if len(df_year) >= 2:
    x = np.arange(len(df_year))
    coef = np.polyfit(x, df_year["revenue"], 1)

    last_date = df_year["month_date"].max()
    future = 12 - len(df_year)

    future_dates = pd.date_range(start=last_date,
                                periods=future+1,
                                freq="MS")

    x_future = np.arange(len(df_year)-1,
                        len(df_year)-1+len(future_dates))

    forecast = coef[0]*x_future + coef[1]

    forecast_x = future_dates
    forecast_y = forecast

# -------------------------
# FORMAT
# -------------------------
def eur(x):
    if x >= 1_000_000:
        return f"€{x/1_000_000:.2f}M"
    elif x >= 1_000:
        return f"€{x/1_000:.1f}K"
    return f"€{x:.0f}"

# -------------------------
# UI
# -------------------------
st.title("📊 Business Overview")

# Insight limpio con bullets
if insight:
    st.markdown(f"""
    <div style="background:#f5f7fa;padding:10px;border-radius:8px;font-size:14px;">
    {insight}
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -------------------------
# KPIs
# -------------------------
c1,c2,c3,c4 = st.columns(4)

c1.metric("Revenue", eur(current["revenue"]),
          f"{rev_change:.2%}" if rev_change else None)

c2.metric("Orders", f"{current['orders']:,.0f}",
          f"{ord_change:.2%}" if ord_change else None)

c3.metric("Customers", f"{current['customers']:,.0f}")

c4.metric("AOV", f"€{current['avg_order_value']:.2f}",
          f"{aov_change:.2%}" if aov_change else None)

# -------------------------
# CHARTS
# -------------------------
col1,col2 = st.columns(2)

# ---- LINE ----
with col1:
    st.markdown("### 📈 Revenue Trend + Forecast")

    fig = px.line(df, x="month_date", y="revenue")

    fig.update_traces(
        hovertemplate="%{x}<br>%{customdata}<extra></extra>",
        customdata=df["revenue"].apply(eur)
    )

    # ✅ añadir forecast
    if len(forecast_x) > 0:
        fig.add_scatter(
            x=forecast_x,
            y=forecast_y,
            mode="lines",
            name="Forecast",
            line=dict(dash="dash", color="orange")
        )

    fig.update_layout(height=260, margin=dict(l=10,r=10,t=10,b=10))

    st.plotly_chart(fig, width="stretch")

# ---- BAR ----
with col2:
    st.markdown("### 📊 Revenue by Month")

    fig_bar = px.bar(
        df,
        x="month_name",
        y="revenue",
        color=df["year"].astype(str),
        category_orders={"month_name": month_order},
        barmode="group"
    )

    fig_bar.update_traces(
        hovertemplate="%{x}<br>%{customdata}<extra></extra>",
        customdata=df["revenue"].apply(eur)
    )

    # ✅ quitar leyenda
    fig_bar.update_layout(showlegend=False)

    fig_bar.update_layout(height=260, margin=dict(l=10,r=10,t=10,b=10))

    st.plotly_chart(fig_bar, width="stretch")
