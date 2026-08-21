import streamlit as st

st.set_page_config(layout="wide")

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.theme import (
    render_sidebar_footer, inject_kpi_style, kpi_card,
    SEGMENT_COLORS, SEG_ORDER, CHART_FONT, LEGEND_STYLE, WARNING_COLOR,
)
from utils.data_loader import load_csv, require_data, optional

render_sidebar_footer()
inject_kpi_style()
st.title("Delivery Delay Root-Cause Dashboard")

HINT = "Run the export cell at the bottom of olist_segment_funnel_retention.ipynb."
STAGE_LABELS = ["Purchased", "Approved", "Shipped", "Delivered"]

COLORS = SEGMENT_COLORS
ORDER = SEG_ORDER

sla = load_csv("delivery/sla_table_by_state.csv")
require_data(sla, HINT)
sla = sla.rename(columns={
    "violation_rate_pct": "exceed_rate_pct",
    "p80_days": "time_to_80pct_delivered",
})

seg_reach = optional("delivery/seg_funnel_reach.csv")
seg_days = optional("delivery/seg_stage_days.csv")
cat_reach = optional("delivery/category_funnel_reach.csv")
cat_days = optional("delivery/category_cum_days.csv")
vol_reach = optional("delivery/volume_funnel_reach.csv")
vol_days = optional("delivery/volume_cum_days.csv")
state_reach = optional("delivery/state_funnel_reach.csv")
state_days = optional("delivery/state_cum_days.csv")
weight_delay = optional("delivery/weight_seller_delay.csv")

DAYS_COLS = ["days_purchased", "days_approved", "days_shipped", "days_delivered"]

# -- KPI --
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    kpi_card("Overall Delivery Completion Rate", "97.02%", "96,478 of 99,441 orders delivered")
with kpi2:
    kpi_card("Average Delivery Time", "12.56 days", "Median 10.22 days / Time by which 80% of orders are delivered: 17.44 days")
with kpi3:
    kpi_card("Max Regional Delivery-Time Gap", "3.0x", "SP 8.76 days ↔ AM 26.43 days")
with kpi4:
    kpi_card("Estimated-Delivery-Date Miss Rate", "8.11%",
             "Share of orders that arrived later than the promised delivery date")

st.divider()

# -- Dimension selector (applies to both reach and days panels) --
st.markdown("**Where does delivery delay get worse?**")
dimension = st.radio(
    "Dimension", ["By Segment", "By Category", "By Product Volume", "By Customer Region"],
    horizontal=True, label_visibility="collapsed",
)

seg_filter = ORDER
if dimension == "By Segment":
    seg_filter = st.pills(
        "Select segments", ORDER, default=ORDER, selection_mode="multi",
        label_visibility="collapsed",
    )
    if not seg_filter:
        st.info("Select at least one segment.")
        st.stop()

cat_highlight = None
if dimension == "By Category" and cat_reach is not None:
    cat_highlight = st.multiselect(
        "Categories to show", cat_reach["category"].tolist(),
        default=cat_reach["category"].tolist(),
    )

vol_filter = None
if dimension == "By Product Volume" and vol_reach is not None:
    vol_options = vol_reach["volume_bin"].tolist()
    vol_filter = st.pills(
        "Select volume bins", vol_options, default=vol_options, selection_mode="multi",
        label_visibility="collapsed",
    )
    if not vol_filter:
        st.info("Select at least one volume bin.")
        st.stop()

region_highlight = None
if dimension == "By Customer Region" and state_reach is not None:
    region_highlight = st.multiselect(
        "Regions to highlight", state_reach["customer_state"].tolist(),
        default=[s for s in ["SP", "RJ", "AM"] if s in state_reach["customer_state"].values],
    )




def draw_reach_chart(df, key_col, cols, label_map=None, color_map=None, highlight=None, dim_others=True):
    fig = go.Figure()
    y_min = 100
    for _, row in df.iterrows():
        name = row[key_col]
        label = label_map.get(name, name) if label_map else name
        is_hl = highlight is None or label in highlight or name in (highlight or [])
        vals = [row[c] for c in cols]
        y_min = min(y_min, vals[-1])
        line_kwargs = dict(width=3 if (highlight is None or is_hl) else 1)
        if color_map and is_hl:
            line_kwargs["color"] = color_map.get(label)
        elif highlight is not None and not is_hl and dim_others:
            line_kwargs["color"] = "rgba(150,150,150,0.3)"
        fig.add_trace(go.Scatter(
            x=STAGE_LABELS, y=vals, mode="lines+markers", name=label,
            showlegend=(highlight is None) or is_hl,
            line=line_kwargs,
            hovertemplate=f"<b>{label}</b><br>%{{x}}: %{{y:.2f}}%<extra></extra>",
        ))
    fig.update_layout(
        template="plotly_white", font=CHART_FONT, height=440,
        yaxis_title="Reach Rate (%)", yaxis_range=[y_min - (100 - y_min) * 0.3, 100.5],
        legend=dict(**{**LEGEND_STYLE, "font": dict(size=11)}),
        margin=dict(l=10, r=10, t=10, b=100),
        hoverlabel=dict(font=dict(size=15)),
    )
    return fig


def draw_days_chart(df, key_col, cols, label_map=None, color_map=None, highlight=None, dim_others=True):
    fig = go.Figure()
    for _, row in df.iterrows():
        name = row[key_col]
        label = label_map.get(name, name) if label_map else name
        is_hl = highlight is None or label in highlight or name in (highlight or [])
        vals = [row[c] for c in cols]
        line_kwargs = dict(width=3 if (highlight is None or is_hl) else 1)
        if color_map and is_hl:
            line_kwargs["color"] = color_map.get(label)
        elif highlight is not None and not is_hl and dim_others:
            line_kwargs["color"] = "rgba(150,150,150,0.3)"
        fig.add_trace(go.Scatter(
            x=STAGE_LABELS, y=vals, mode="lines+markers", name=label,
            showlegend=(highlight is None) or is_hl,
            line=line_kwargs,
            hovertemplate=f"<b>{label}</b><br>%{{x}}: %{{y:.2f}} days<extra></extra>",
        ))
    fig.update_layout(
        template="plotly_white", font=CHART_FONT, height=440,
        yaxis_title="Days Since Purchase",
        legend=dict(**{**LEGEND_STYLE, "font": dict(size=11)}),
        margin=dict(l=10, r=10, t=10, b=100),
        hoverlabel=dict(font=dict(size=15)),
    )
    return fig


col_reach, col_days = st.columns(2)

with col_reach:
    st.markdown(f"**Reach Funnel ({dimension})**")
    if dimension == "By Segment":
        if seg_reach is not None:
            df = seg_reach[seg_reach["Segment"].isin(seg_filter)]
            fig = draw_reach_chart(df, "Segment", ["s1_purchased", "s2_approved", "s3_shipped", "s4_delivered"],
                                    color_map=COLORS)
            st.plotly_chart(fig, width='stretch')
        else:
            st.info(f"No data. {HINT}")
    elif dimension == "By Category":
        if cat_reach is not None:
            if not cat_highlight:
                st.info("Select at least one category.")
            else:
                df = cat_reach[cat_reach["category"].isin(cat_highlight)].sort_values("delivered")
                fig = draw_reach_chart(df, "category", ["purchased", "approved", "shipped", "delivered"])
                st.plotly_chart(fig, width='stretch')
        else:
            st.info(f"No data. {HINT}")
    elif dimension == "By Product Volume":
        if vol_reach is not None:
            df = vol_reach[vol_reach["volume_bin"].isin(vol_filter)]
            fig = draw_reach_chart(df, "volume_bin", ["purchased", "approved", "shipped", "delivered"])
            st.plotly_chart(fig, width='stretch')
        else:
            st.info(f"No data. {HINT}")
    else:
        if state_reach is not None:
            fig = draw_reach_chart(state_reach, "customer_state",
                                    ["purchased", "approved", "shipped", "delivered"],
                                    highlight=region_highlight)
            st.plotly_chart(fig, width='stretch')
        else:
            st.info(f"No data. {HINT}")

with col_days:
    st.markdown(f"**Average Days per Stage ({dimension})**")
    if dimension == "By Segment":
        if seg_days is not None:
            df = seg_days[seg_days["Segment"].isin(seg_filter)]
            fig = draw_days_chart(df, "Segment",
                                   ["days_purchased", "days_approved", "days_shipped", "days_delivered"],
                                   color_map=COLORS)
            st.plotly_chart(fig, width='stretch')
        else:
            st.info(f"No data. {HINT}")
    elif dimension == "By Category":
        if cat_days is not None:
            if not cat_highlight:
                st.info("Select at least one category.")
            else:
                df = cat_days[cat_days["category"].isin(cat_highlight)]
                fig = draw_days_chart(df, "category", DAYS_COLS)
                st.plotly_chart(fig, width='stretch')
        else:
            st.info(f"No data. {HINT}")
    elif dimension == "By Product Volume":
        if vol_days is not None:
            df = vol_days[vol_days["volume_bin"].isin(vol_filter)]
            fig = draw_days_chart(df, "volume_bin", DAYS_COLS)
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No data. Run export cell (6), days-by-volume.")
    else:
        if state_days is not None:
            fig = draw_days_chart(state_days, "customer_state", DAYS_COLS, highlight=region_highlight)
            st.plotly_chart(fig, width='stretch')
        else:
            st.info(f"No data. {HINT}")

if dimension == "By Segment":
    st.caption("The shipped → delivered stage shows the widest gap between segments.")
elif dimension == "By Category":
    st.caption("Differences in reach rate and days between categories are minor compared to regional differences.")
elif dimension == "By Product Volume":
    st.caption("Larger products tend to have a lower reach rate and take longer to deliver.")
else:
    st.caption("The northeast belt (SE, CE, MA, AL, PI, BA, PE, etc.) dominates the bottom of the reach-rate ranking. "
               "The regional delivery-time gap explodes in the delivered stage. "
               "RJ, a large city near SP, is a notable outlier in the bottom tier.")

st.divider()

# -- Weight/volume by seller-delay-share group --
st.markdown("**Heavier, bulkier products shift more of the delivery time onto the seller rather than the carrier**")
if weight_delay is not None:
    fig_h = go.Figure()
    fig_h.add_trace(go.Bar(x=weight_delay["ratio_group"], y=weight_delay["avg_weight_g"],
                            name="Avg. Weight (g)", marker_color="#378ADD"))
    fig_h.add_trace(go.Scatter(x=weight_delay["ratio_group"], y=weight_delay["avg_volume_cm3"],
                                name="Avg. Volume (cm³)", yaxis="y2",
                                line=dict(color=WARNING_COLOR, width=2.5), mode="lines+markers"))
    fig_h.update_layout(
        template="plotly_white", font=CHART_FONT, height=420,
        xaxis=dict(title="Seller-Delay-Share Group (1=highest share -> 10=lowest)",
                   tickmode="linear", dtick=1),
        yaxis=dict(title="Avg. Weight (g)"),
        yaxis2=dict(title="Avg. Volume (cm³)", overlaying="y", side="right"),
        legend=dict(**LEGEND_STYLE, itemsizing="constant", itemwidth=40),
        margin=dict(l=10, r=10, t=10, b=70),
        hoverlabel=dict(font=dict(size=15)),
    )
    fig_h.add_vline(x=3.5, line_dash="dash", line_color="gray")
    st.plotly_chart(fig_h, width='stretch')
else:
    st.info(f"No data. {HINT}")

st.divider()

# -- Reference table: estimated-delivery-date miss rate by region --
st.markdown("**Estimated-Delivery-Date Miss Rate by Region**")

med_days = sla["avg_days"].median()
med_viol = sla["exceed_rate_pct"].median()

def classify(row):
    slow = row["avg_days"] > med_days
    high = row["exceed_rate_pct"] > med_viol
    if slow and not high:
        return "Slow delivery · Good ETA reliability"
    if not slow and high:
        return "Fast delivery · Poor ETA reliability"
    if slow and high:
        return "Slow delivery · Poor ETA reliability"
    return "Fast delivery · Good ETA reliability"

sla["type"] = sla.apply(classify, axis=1)
type_colors = {
    "Slow delivery · Good ETA reliability": "#5DCAA5",
    "Fast delivery · Poor ETA reliability": "#EF9F27",
    "Slow delivery · Poor ETA reliability": WARNING_COLOR,
    "Fast delivery · Good ETA reliability": "#B4B2A9",
}

fig_i = px.scatter(sla, x="avg_days", y="exceed_rate_pct", size="order_count",
                    color="type", color_discrete_map=type_colors,
                    text="customer_state", hover_data=["time_to_80pct_delivered", "order_count"],
                    size_max=70)
fig_i.update_traces(marker=dict(sizemin=10, line=dict(width=0.5, color="white")),
                     textfont=dict(size=13))
fig_i.add_vline(x=med_days, line_dash="dash", line_color="gray", opacity=0.4)
fig_i.add_hline(y=med_viol, line_dash="dash", line_color="gray", opacity=0.4)
fig_i.update_traces(textposition="top center")
fig_i.update_layout(template="plotly_white", font=CHART_FONT, height=520,
                     legend=dict(**LEGEND_STYLE, itemsizing="constant", itemwidth=40),
                     margin=dict(l=10, r=10, t=10, b=70),
                     hoverlabel=dict(font=dict(size=15)))
st.plotly_chart(fig_i, width='stretch')

tf = st.multiselect("Filter by type", sla["type"].unique().tolist(),
                     default=sla["type"].unique().tolist())
disp = sla[sla["type"].isin(tf)].sort_values("exceed_rate_pct", ascending=False)
st.dataframe(disp[["customer_state", "avg_days", "time_to_80pct_delivered", "exceed_rate_pct", "order_count", "type"]],
             width='stretch', hide_index=True)
st.download_button("Download CSV", disp.to_csv(index=False).encode("utf-8-sig"),
                    "sla_table.csv", "text/csv")