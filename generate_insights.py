import os
from google.cloud import bigquery
from google import genai
from datetime import datetime, timezone
import pandas as pd
import time

# ----------------------------------
# CONFIG
# ----------------------------------
bq_client = bigquery.Client(project="project-ecommerce-497614")
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

TABLE_ID = "project-ecommerce-497614.ecommerce_de.insights_monthly"

# ----------------------------------
# 1. LOAD MONTHLY DATA
# ----------------------------------
query = """
SELECT
    month,
    year,
    month_num,
    revenue,
    orders,
    customers,
    avg_order_value
FROM `project-ecommerce-497614.ecommerce_de.mart_sales_monthly`
ORDER BY year, month_num
"""

df = bq_client.query(query).to_dataframe()

# ----------------------------------
# 2. GET MAX PROCESSED MONTH
# ----------------------------------
try:
    max_query = f"""
    SELECT MAX(DATE(year, month_num, 1)) AS max_month
    FROM `{TABLE_ID}`
    """
    max_df = bq_client.query(max_query).to_dataframe()
    max_processed = max_df.iloc[0]["max_month"]

except:
    max_processed = None

# ----------------------------------
# 3. LIMIT TO NEW + RECENT MONTHS
# ----------------------------------
df["month_date"] = pd.to_datetime(df["month"])

# ✅ recalcular últimos 3 meses SIEMPRE
cutoff_recent = df["month_date"].max() - pd.DateOffset(months=3)

rows_to_process = []

for i in range(len(df)):

    current = df.iloc[i]
    current_date = current["month_date"]

    if i == 0:
        continue

    prev = df.iloc[i - 1]

    # ✅ lógica híbrida
    if max_processed:
        if current_date <= max_processed and current_date < cutoff_recent:
            continue  # skip meses antiguos

    rows_to_process.append((current, prev))

print(f"Processing {len(rows_to_process)} months...")

# ----------------------------------
# DRIVER FUNCTION
# ----------------------------------
def detect_driver(revenue_change, orders_change, aov_change):

    if revenue_change > 0:
        if orders_change > 0 and aov_change > 0:
            return "Growth driven by both demand and basket size."
        elif orders_change > 0:
            return "Growth driven by demand (volume)."
        elif aov_change > 0:
            return "Growth driven by pricing / basket value."
        else:
            return "Growth despite weak drivers."
    else:
        if orders_change < 0 and aov_change < 0:
            return "Decline driven by both demand and basket size."
        elif orders_change < 0:
            return "Decline driven by demand."
        elif aov_change < 0:
            return "Decline driven by basket value."
        else:
            return "Decline despite stable drivers."


# ----------------------------------
# 4. GENERATE INSIGHTS (INCREMENTAL)
# ----------------------------------
for current, prev in rows_to_process:

    print(f"Processing {current['year']}-{current['month_num']}")

    # --------------------------
    # CALCULATION
    # --------------------------
    revenue_change = current["revenue"] / prev["revenue"] - 1
    orders_change = current["orders"] / prev["orders"] - 1
    aov_change = current["avg_order_value"] / prev["avg_order_value"] - 1

    driver = detect_driver(revenue_change, orders_change, aov_change)

    # --------------------------
    # PROMPT
    # --------------------------
    prompt = f"""
You are a senior e-commerce analyst.

Monthly performance:

Revenue change: {revenue_change:.2%}
Orders change: {orders_change:.2%}
AOV change: {aov_change:.2%}

Driver:
{driver}

Explain the business situation.

IMPORTANT:
- Monthly context only (no weekly references)

Format:
- 1 main sentence
- 2 bullets

Rules:
- max 3 lines
- do not repeat numbers
- concise
"""

    # --------------------------
    # GEMINI CALL
    # --------------------------
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            insight_text = response.text.replace("\n", "\n\n")
            break

        except Exception as e:
            print(f"Error Gemini intento {attempt+1}: {e}")

            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                insight_text = f"""
Fallback insight:

Revenue: {revenue_change:.1%}
Orders: {orders_change:.1%}
AOV: {aov_change:.1%}
""".strip()

    # --------------------------
    # SAVE (APPEND ✅)
    # --------------------------
    row = pd.DataFrame([{
        "year": int(current["year"]),
        "month_num": int(current["month_num"]),
        "month": current["month"],
        "driver": driver,
        "created_at": datetime.now(timezone.utc),
        "insight": insight_text
    }])

    bq_client.load_table_from_dataframe(
        row,
        TABLE_ID,
        job_config=bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND"
        )
    ).result()

    # ✅ rate limit
    time.sleep(1.5)

print("\n✅ Incremental insights updated")