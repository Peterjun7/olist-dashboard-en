import streamlit as st

st.set_page_config(layout="wide")

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.theme import (
    render_sidebar_footer, inject_kpi_style, kpi_card,
    SEGMENT_COLORS, SEG_ORDER, CHART_FONT, LEGEND_STYLE,
)
from utils.data_loader import load_csv, require_data, optional

render_sidebar_footer()
inject_kpi_style()
st.title("Customers")

HINT_CL = "Run the export cell at the bottom of olist_customer_clustering_4.ipynb."
HINT_FN = "Run the export cell at the bottom of olist_segment_funnel_retention.ipynb."

FEAT_EN = {
    "monetary": "Revenue/Customer", "avg_review_score": "Satisfaction", "avg_review_len": "Review Length",
    "avg_delay": "Delivery Delay", "avg_freight_ratio": "Freight Cost Ratio", "avg_item_count": "Cart Items",
}

profile = load_csv("customer/segment_profile.csv")
repeat = load_csv("customer/repeat_rate.csv")
require_data(profile, HINT_FN)
require_data(repeat, HINT_FN)

COLORS = SEGMENT_COLORS
ORDER = [s for s in SEG_ORDER if s in profile["Segment"].values]

radar = optional("customer/cluster_radar.csv")
pca = optional("customer/cluster_pca.csv")
cmap = optional("customer/cluster_map.csv")
monthly = optional("customer/monthly_revenue.csv")
monthly_share = optional("customer/monthly_share.csv")

hover_map = {}
for _, r in profile.iterrows():
    seg = r["Segment"]
    hover_map[seg] = (
        f"<b>{seg}</b><br>{int(r['customer_count']):,} customers<br>"
        f"Revenue share {r['revenue_share_pct']:.1f}%<br>Revenue/customer R$ {r['monetary']:,.0f}<br>"
        f"Avg delay {r['avg_delay']:.1f}d<extra></extra>"
    )

total_customers = int(profile["customer_count"].sum())
dis_n = int(profile.loc[profile["Segment"] == "Delivery-Disappointed", "customer_count"].sum())
top2 = profile.sort_values("revenue_share_pct", ascending=False)["revenue_share_pct"].iloc[:2].sum()
top2_names = " · ".join(profile.sort_values("revenue_share_pct", ascending=False)["Segment"].iloc[:2])

# -- KPI --
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    kpi_card("Customers Analyzed", f"{total_customers:,}")
with kpi2:
    kpi_card("Repeat Purchase Rate", f"{repeat['repeat_rate_all'].mean():.2f}%")
with kpi3:
    kpi_card("At-Risk Customers", f"{dis_n:,}",
             f"Size of the Delivery-Disappointed segment (poor delivery experience). {dis_n/total_customers*100:.1f}% of total")
with kpi4:
    kpi_card("Top-2 Segment Revenue Share", f"{top2:.1f}%",
             f"Combined revenue share of the top 2 of 5 segments ({top2_names})")

st.divider()

# -- Global segment filter (applies to all 5 charts below) --
st.markdown("**Segment Filter**")
show_only = st.pills(
    "Select segments", ORDER, default=ORDER, selection_mode="multi",
    label_visibility="collapsed",
)
if not show_only:
    st.info("Select at least one segment.")
    st.stop()



# -- Row 1: Radar | PCA --
col_r, col_p = st.columns(2)

with col_r:
    st.markdown("**Segment Profile**")
    if radar is not None:
        radar_f = radar[radar["Segment"].isin(show_only)]
        radar_f["Segment"] = pd.Categorical(radar_f["Segment"], categories=ORDER, ordered=True)
        radar_f = radar_f.sort_values("Segment")
        feats = [c for c in radar.columns if c != "Segment"]
        feats_en = [FEAT_EN.get(f, f) for f in feats]

        fig_radar = go.Figure()
        for _, row in radar_f.iterrows():
            seg = row["Segment"]
            vals = [row[f] for f in feats]
            feat_lines = []
            for fk, f, v in zip(feats_en, feats, vals):
                if f == "monetary":
                    feat_lines.append(f"{fk}: R$ {v:.2f}")
                else:
                    feat_lines.append(f"{fk}: {v:.2f}")
            hover_text = f"<b>{seg}</b><br>" + "<br>".join(feat_lines) + "<extra></extra>"
            fig_radar.add_trace(go.Scatterpolar(
                r=vals + [vals[0]], theta=feats_en + [feats_en[0]],
                name=seg, fill="toself", opacity=0.55,
                line=dict(color=COLORS.get(seg, "#888"), width=2.5),
                hovertemplate=hover_text,
            ))
        fig_radar.update_layout(
            template="plotly_white", font=CHART_FONT,
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            height=400, margin=dict(l=30, r=30, t=10, b=70),
            legend=dict(**LEGEND_STYLE, itemsizing="constant", itemwidth=40),
            hoverlabel=dict(font=dict(size=20)),
        )
        st.plotly_chart(fig_radar, width='stretch')
    else:
        st.info(f"No data. {HINT_CL}")

with col_p:
    st.markdown("**PCA Distribution**")
    if pca is not None:
        pca["hover"] = pca["Segment"].map(hover_map)
        pca_f = pca[pca["Segment"].isin(show_only)]
        fig_pca = px.scatter(
            pca_f, x="PC1", y="PC2", color="Segment",
            color_discrete_map=COLORS,
            category_orders={"Segment": ORDER},
            custom_data=["hover"],
        )
        fig_pca.update_traces(marker=dict(size=5, opacity=0.8,
                               line=dict(width=0.4, color="white")),
                               hovertemplate="%{customdata[0]}")
        fig_pca.update_layout(
            template="plotly_white", font=CHART_FONT, height=400,
            margin=dict(l=30, r=20, t=10, b=70),
            legend=dict(**LEGEND_STYLE, itemsizing="constant", itemwidth=40),
            hoverlabel=dict(font=dict(size=20)),
        )
        st.plotly_chart(fig_pca, width='stretch')
    else:
        st.info(f"No data. {HINT_CL}")



# -- Row 2: Map (+ top cities) | Revenue trend by segment (combined) --
col_m, col_gap, col_t = st.columns([1.2, 0.06, 1.2])

with col_m:
    st.markdown("**Segment Map**")
    if cmap is not None:
        plot_df = cmap[cmap["Segment"].isin(show_only)]

        fig_map = px.scatter_geo(
            plot_df, lat="lat", lon="lng", color="Segment",
            color_discrete_map=COLORS,
            scope="south america", category_orders={"Segment": ORDER},
            hover_name="customer_city",
        )
        fig_map.update_traces(marker=dict(size=4, opacity=0.85))
        fig_map.update_geos(fitbounds="locations", showcountries=True)
        fig_map.update_layout(template="plotly_white", font=CHART_FONT, height=430,
                              margin=dict(l=0, r=0, t=10, b=0), showlegend=False,
                              hoverlabel=dict(font=dict(size=15)))
        st.plotly_chart(fig_map, width='stretch')

        st.caption("Top cities by customer count (segment mix)")
        city_seg = (
            plot_df.groupby(["customer_city", "Segment"]).size()
            .reset_index(name="customer_count")
        )
        top_city_order = (
            city_seg.groupby("customer_city")["customer_count"].sum()
            .sort_values(ascending=False).head(15).index.tolist()
        )
        city_seg = city_seg[city_seg["customer_city"].isin(top_city_order)]

        fig_city = px.bar(
            city_seg, x="customer_count", y="customer_city", color="Segment",
            orientation="h", color_discrete_map=COLORS,
            category_orders={"customer_city": top_city_order[::-1], "Segment": ORDER},
        )
        fig_city.update_traces(
            hovertemplate="<b>%{y}</b><br>%{fullData.name}: %{x:,.0f}<extra></extra>"
        )
        fig_city.update_layout(
            template="plotly_white", font=CHART_FONT, height=300,
            yaxis_title="", xaxis_title="Customers",
            legend=dict(**LEGEND_STYLE, itemsizing="constant", itemwidth=40),
            margin=dict(l=10, r=10, t=10, b=70),
            hoverlabel=dict(font=dict(size=15)),
        )
        st.plotly_chart(fig_city, width='stretch')
    else:
        st.info(f"No data. {HINT_CL}")

with col_t:
    st.markdown("**Revenue Trend by Segment**")
    if monthly is not None and monthly_share is not None:
        monthly["month"] = pd.to_datetime(monthly["month"])
        monthly_share["month"] = pd.to_datetime(monthly_share["month"])

        fig_combo = go.Figure()
        for seg in SEG_ORDER:
            if seg not in monthly.columns or seg not in show_only:
                continue
            share_vals = monthly_share[seg] if seg in monthly_share.columns else pd.Series([None] * len(monthly))
            fig_combo.add_trace(go.Scatter(
                x=monthly["month"], y=monthly[seg], name=seg,
                stackgroup="one", mode="lines",
                line=dict(width=0.5, color=COLORS[seg]),
                fillcolor=COLORS[seg],
                customdata=share_vals,
                hovertemplate=f"<b>{seg}</b><br>Revenue: R$ %{{y:,.0f}}<br>Share: %{{customdata:.1f}}%<extra></extra>",
            ))
        if "Delivery-Disappointed" in show_only:
            fig_combo.add_trace(go.Scatter(
                x=monthly_share["month"], y=monthly_share["Delivery-Disappointed"],
                name="Delivery-Disappointed share (%)", yaxis="y2", mode="lines+markers",
                line=dict(color="#791F1F", width=2.5, dash="dot"),
                hovertemplate="Delivery-Disappointed share: %{y:.1f}%<extra></extra>",
            ))
        fig_combo.update_layout(
            template="plotly_white", font=CHART_FONT, height=800,
            yaxis=dict(title="Revenue (R$)"),
            yaxis2=dict(title="Delivery-Disappointed share (%)", overlaying="y", side="right", range=[0, 30]),
            legend=dict(**LEGEND_STYLE, itemsizing="constant", itemwidth=40),
            margin=dict(l=10, r=10, t=10, b=70),
            hoverlabel=dict(font=dict(size=15)),
        )
        st.plotly_chart(fig_combo, width='stretch')
    else:
        st.info("No data. Run the olist_segment_funnel_retention.ipynb export cell.")

st.divider()

# -- Row 3: New customers | Satisfaction --
st.markdown("**New Customer Growth · Satisfaction Trend**")

new_cust = optional("customer/new_customers_monthly.csv")
satisfaction = optional("customer/satisfaction_monthly.csv")

col_n, col_s = st.columns(2)

with col_n:
    st.caption("New customers per month")
    if new_cust is not None:
        new_cust["month"] = pd.to_datetime(new_cust["month"])
        fig_n = go.Figure()
        fig_n.add_trace(go.Bar(
            x=new_cust["month"], y=new_cust["new_customers"],
            marker_color="#378ADD",
            hovertemplate="%{x|%b %Y}<br>New customers: %{y:,.0f}<extra></extra>",
        ))
        fig_n.update_layout(template="plotly_white", font=CHART_FONT, height=340,
                             yaxis_title="New Customers",
                             margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_n, width='stretch')
    else:
        st.info(f"No data. {HINT_CL}")

with col_s:
    st.caption("Average satisfaction (mean review score) per month")
    if satisfaction is not None:
        satisfaction["month"] = pd.to_datetime(satisfaction["month"])
        fig_s = go.Figure()
        fig_s.add_trace(go.Scatter(x=satisfaction["month"], y=satisfaction["avg_satisfaction"],
                                    name="Overall", mode="lines+markers",
                                    line=dict(color="#444441", width=2.5),
                                    hovertemplate="Overall: %{y:.2f}<extra></extra>"))
        fig_s.add_trace(go.Scatter(x=satisfaction["month"], y=satisfaction["disappointed_avg_satisfaction"],
                                    name="Delivery-Disappointed", mode="lines+markers",
                                    line=dict(color="#E24B4A", width=2, dash="dot"),
                                    hovertemplate="Delivery-Disappointed: %{y:.2f}<extra></extra>"))
        fig_s.update_layout(template="plotly_white", font=CHART_FONT, height=340,
                             yaxis_title="Average review score (1-5)", yaxis_range=[1, 5],
                             legend=dict(orientation="h", y=1.15, font=CHART_FONT),
                             margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_s, width='stretch')
    else:
        st.info(f"No data. {HINT_CL}")
