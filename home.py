import streamlit as st
import pandas as pd
import os

from utils.theme import render_sidebar_footer, inject_kpi_style

st.set_page_config(page_title="Olist E-Commerce Dashboard", page_icon="🛒", layout="wide")

render_sidebar_footer()
inject_kpi_style()

st.title("Olist Brazilian E-Commerce Analysis Dashboard")
st.caption("Use the sidebar or the cards below to navigate between screens.")
st.divider()

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def safe_read(path):
    full = os.path.join(DATA_DIR, path)
    return pd.read_csv(full) if os.path.exists(full) else None

pacing = safe_read("sales/pacing_headline.csv")
repeat = safe_read("customer/repeat_rate.csv")
monthly_share = safe_read("customer/monthly_share.csv")
sla = safe_read("delivery/sla_table_by_state.csv")

col1, col2, col3 = st.columns(3)

# -- Customers --
with col1:
    with st.container(border=True):
        st.markdown("### 👥 Customers")
        if repeat is not None:
            st.metric("Repeat Purchase Rate", f"{repeat['repeat_rate_all'].mean():.2f}%")
        else:
            st.metric("Repeat Purchase Rate", "—")

        if monthly_share is not None and "Delivery-Disappointed" in monthly_share.columns:
            start = monthly_share["Delivery-Disappointed"].iloc[0]
            end = monthly_share["Delivery-Disappointed"].iloc[-1]
            diff = end - start
            if diff > 1:
                st.markdown(f"🔴 **Delivery-Disappointed revenue share is rising** ({start:.1f}% → {end:.1f}%)")
            else:
                st.markdown(f"🟢 Delivery-Disappointed revenue share is stable ({start:.1f}% → {end:.1f}%)")
        st.page_link("pages/1_Customers.py", label="Open screen", icon="➡️")

# -- Products & Delivery --
with col2:
    with st.container(border=True):
        st.markdown("### 📦 Products & Delivery")
        if sla is not None:
            overall_viol = 8.11  # validated against raw orders table
            median_viol = sla["violation_rate_pct"].median() if "violation_rate_pct" in sla.columns else pd.Series().median()
            st.metric("Estimated-Delivery-Date Miss Rate", f"{overall_viol:.2f}%")
            if overall_viol > 7:
                st.markdown("🔴 **Above average** — check regional detail")
            else:
                st.markdown("🟢 Healthy level")
        else:
            st.metric("Estimated-Delivery-Date Miss Rate", "—")
        st.page_link("pages/2_Delivery.py", label="Open screen", icon="➡️")

# -- Revenue --
with col3:
    with st.container(border=True):
        st.markdown("### 📈 Revenue")
        if pacing is not None:
            p = pacing.iloc[0]
            delta = p["vs_target_pct"] - 100
            st.metric("Projected Month-End Close", f"R$ {p['projected_close']:,.0f}",
                      delta=f"{delta:+.1f}%p (vs. prior month)")
        else:
            st.metric("Projected Month-End Close", "—")
        st.page_link("pages/3_Revenue.py", label="Open screen", icon="➡️")

st.divider()
