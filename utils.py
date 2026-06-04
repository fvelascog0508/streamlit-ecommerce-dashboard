import streamlit as st
from google.cloud import bigquery

@st.cache_resource
def get_client():
    return bigquery.Client()

client = get_client()

@st.cache_data(ttl=600)
def run_query(query):
    return client.query(query).to_dataframe()