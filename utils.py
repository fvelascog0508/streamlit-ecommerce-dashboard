import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

@st.cache_resource
def get_client():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return bigquery.Client(credentials=credentials)

client = get_client()

@st.cache_data(ttl=600)
def run_query(query):
    return client.query(query).to_dataframe()

# import streamlit as st
# from google.cloud import bigquery

# @st.cache_resource
# def get_client():
#     return bigquery.Client()

# client = get_client()

# @st.cache_data(ttl=600)
# def run_query(query):
#     return client.query(query).to_dataframe()