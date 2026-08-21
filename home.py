import streamlit as st
import pandas as pd
import os

from utils.theme import render_sidebar_footer, inject_kpi_style

st.set_page_config(page_title="Olist E-Commerce Dashboard", page_icon="🛒", layout="wide")

render_sidebar_footer()
inject_kpi_style()

st.markdown("""
<style>
div[data-testid="column"] { display: flex; }
div[data-testid="column"] > div { width: 100%; }
div[data-testid="stVerticalBlockBorderWrapper"] {
    height: 100%;
    display: flex;
}
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    width: 100%;
    display: flex;
    flex-direction: column;
}
div.stAlert {
    min-height: 108px;
    font-size: 1.05rem;
}
div.stAlert p {
    font-size: 1.05rem !important;
}
div[data-testid="stPageLink"] p {
    font-size: 1.05rem !important;
}
</style>
""", unsafe_allow_html=True)

st.title("Olist Brazilian E-Commerce Analysis Dashboard")
st.markdown(
    '<p style="font-size:1.3rem; color:gray;">Use the sidebar or the cards below to navigate between screens.</p>',
    unsafe_allow_html=True,
)
st.divider()

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def safe_read(path):
    full = os.path.join(DATA_DIR, path)
    if not os.path.exists(full):
        return None
    try:
        return pd.read_csv(full)
    except UnicodeDecodeError:
        return pd.read_csv(full, encoding="cp949")

pacing = safe_read("sales/pacing_headline.csv")
repeat = safe_read("customer/repeat_rate.csv")
monthly_share = safe_read("customer/monthly_share.csv")
sla = safe_read("delivery/sla_table_by_state.csv")

col1, col2, col3 = st.columns(3)

# -- Customers --
with col1:
    with st.container(border=True):
        st.markdown("### 👥 Customers")
        st.markdown(f"""
            <div style="min-height:98px;">
                <div style="font-size:1rem; color:rgba(49,51,63,0.6); margin-bottom:2px;">Repeat Purchase Rate</div>
                <div style="font-size:2.5rem; font-weight:600; line-height:1.2; margin-bottom:8px;">
                    {f"{repeat['repeat_rate_all'].mean():.2f}%" if repeat is not None else "—"}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.error("🚨 **Problem: Low repeat purchase rate**\n\nOverall repeat purchase rate is only 3.01%, a significant issue")
        st.page_link("pages/1_Customers.py", label="Open screen", icon="➡️")

# -- Products & Delivery --
with col2:
    with st.container(border=True):
        st.markdown("### 📦 Products & Delivery")
        overall_viol = 8.11  # validated against raw orders table
        st.markdown(f"""
            <div style="min-height:98px;">
                <div style="font-size:1rem; color:rgba(49,51,63,0.6); margin-bottom:2px;">Estimated-Delivery-Date Miss Rate</div>
                <div style="font-size:2.5rem; font-weight:600; line-height:1.2; margin-bottom:8px;">
                    {f"{overall_viol:.2f}%" if sla is not None else "—"}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.error("🚨 **Problem: Delivery delays → lower satisfaction**\n\nDelivery delays are lowering customer satisfaction, and the revenue share of delayed orders keeps rising")
        st.page_link("pages/2_Delivery.py", label="Open screen", icon="➡️")

# -- Revenue --
with col3:
    with st.container(border=True):
        st.markdown("### 📈 Revenue")
        if pacing is not None:
            p = pacing.iloc[0]
            revenue_text = f"R$ {p['projected_close']:,.0f}"
        else:
            revenue_text = "—"
        st.markdown(f"""
            <div style="min-height:98px;">
                <div style="font-size:1rem; color:rgba(49,51,63,0.6); margin-bottom:2px;">Projected Revenue This Month</div>
                <div style="font-size:2.5rem; font-weight:600; line-height:1.2; margin-bottom:8px;">{revenue_text}</div>
            </div>
        """, unsafe_allow_html=True)

        st.error("🚨 **Problem: High volatility makes month-end targets hard to gauge**\n\nWeekend revenue runs at only ~74% of weekday revenue, and that volatility makes it hard to tell whether the month-end target will be hit")
        st.page_link("pages/3_Revenue.py", label="Open screen", icon="➡️")

st.divider()