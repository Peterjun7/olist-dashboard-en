"""CSV loader - cached via @st.cache_data, returns None if missing"""
import os
import streamlit as st
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


@st.cache_data
def load_csv(relative_path):
    full_path = os.path.join(DATA_DIR, relative_path)
    if not os.path.exists(full_path):
        return None
    return pd.read_csv(full_path)


def optional(relative_path):
    """Supplementary data that shouldn't break the page if missing"""
    return load_csv(relative_path)


def require_data(df, export_hint):
    if df is None:
        st.warning(f"Data not available yet. {export_hint}")
        st.stop()
    return True
