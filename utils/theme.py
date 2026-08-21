"""Shared theme - color rules, KPI cards, data cutoff caption"""
import streamlit as st

SEG_ORDER = [
    "Engaged-Premium",
    "Silent-Premium",
    "Bulk-Buyer",
    "Budget-Regular",
    "Delivery-Disappointed",
]

SEGMENT_COLORS = {
    "Engaged-Premium": "#1D9E75",
    "Silent-Premium": "#7F77DD",
    "Bulk-Buyer": "#EF9F27",
    "Budget-Regular": "#888780",
    "Delivery-Disappointed": "#E24B4A",
}

WARNING_COLOR = "#E24B4A"
GOOD_COLOR = "#1D9E75"
NEUTRAL_COLOR = "#888780"

DATA_CUTOFF_CAPTION = (
    "Data as of 2018-08-21 (collection cutoff). "
    "The period after this date shows an exponential drop in order volume (data decay), "
    "so it is excluded from every analysis."
)


def render_sidebar_footer():
    st.sidebar.markdown(
        "<p style='font-size:1.1rem; font-weight:600;'>Today 2018-08-21</p>",
        unsafe_allow_html=True,
    )

    pass

def kpi_row(items):
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        with col:
            st.metric(
                label=item["label"],
                value=item["value"],
                delta=item.get("delta"),
                help=item.get("help"),
            )


def page_header(title, problem_statement):
    st.title(title)
    st.markdown(f"**Problem statement** · {problem_statement}")
    st.divider()
def kpi_card(label, value, help_text=None):
    """Card-style KPI used instead of st.metric - hover the ⓘ next to the label to see help_text"""
    tooltip = f'<span class="kpi-tooltip" title="{help_text}"> ⓘ</span>' if help_text else ""
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}{tooltip}</div>
            <div class="kpi-value">{value}</div>
        </div>
    """, unsafe_allow_html=True)


def inject_kpi_style():
    st.markdown("""
        <style>
        .kpi-card {
            background: #F1EFE8;
            border-radius: 12px;
            padding: 18px 20px;
            border: 1px solid #D3D1C7;
            min-height: 100px;
        }
        .kpi-label { font-size: 1.1rem; color: #5F5E5A; margin-bottom: 8px; }
        .kpi-value { font-size: 2.3rem; font-weight: 600; color: #2C2C2A; }
        .kpi-tooltip { cursor: help; color: #888780; font-size: 1rem; }
        </style>
    """, unsafe_allow_html=True)

CHART_FONT = dict(size=13, color="#2C2C2A")
LEGEND_STYLE = dict(orientation="h", y=-0.22, font=dict(size=17, color="#2C2C2A"))
