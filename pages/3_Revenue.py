import streamlit as st

st.set_page_config(layout="wide")

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.theme import (
    render_sidebar_footer, inject_kpi_style, kpi_card,
    CHART_FONT, LEGEND_STYLE, WARNING_COLOR,
)
from utils.data_loader import load_csv, require_data, optional

render_sidebar_footer()
inject_kpi_style()
st.title("Revenue Forecast Dashboard")

HINT_V2 = "Run the export cell at the bottom of olist_forecast_v2.ipynb."
HINT_DS = "Run the export cell at the bottom of olist_daily_sales_forecasting.ipynb."

pacing = load_csv("sales/pacing_headline.csv")
forecast7 = load_csv("sales/forecast_7d.csv")
daily = load_csv("sales/daily_actual.csv")
require_data(pacing, HINT_V2)
require_data(forecast7, HINT_V2)
require_data(daily, HINT_V2)

cat_rev = optional("sales/category_revenue.csv")
seller_decile = optional("sales/seller_decile.csv")
seller_top10 = optional("sales/seller_top10_share.csv")
region_rev = optional("sales/region_revenue.csv")
calendar_effect = optional("sales/calendar_effect.csv")
bf_effect = optional("sales/black_friday_effect.csv")
reg_pacing = optional("sales/regional_pacing.csv")
reg_7d = optional("sales/regional_7d.csv")

p = pacing.iloc[0]

# -- KPI --
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    kpi_card("Projected Revenue This Month", f"R$ {p['projected_close']:,.0f}", f"Range {p['lower_bound']:,.0f} - {p['upper_bound']:,.0f}")
with kpi2:
    kpi_card("MTD Confirmed Actuals", f"R$ {p['mtd_actual']:,.0f}", f"{int(p['days_elapsed'])} days elapsed / {int(p['days_remaining'])} days remaining")
with kpi3:
    kpi_card("Revenue Growth vs. Prior Month", f"{p['vs_target_pct']:.1f}%", "Target is a placeholder based on the prior month's actuals")
with kpi4:
    kpi_card("Next-7-Day Forecast Total", f"R$ {forecast7['forecast'].sum():,.0f}")

st.divider()

# -- Dimension selector --
st.markdown("**Choose a Dimension**")
dimension = st.radio(
    "Dimension", ["Monthly (Pacing)", "7-Day Forecast", "Regional 7-Day Forecast"],
    horizontal=True, label_visibility="collapsed",
)

if dimension == "Monthly (Pacing)":
    col_a, col_b = st.columns([2, 3])
    with col_a:
        st.markdown("**Monthly Revenue Trend**")
        daily["order_date"] = pd.to_datetime(daily["order_date"])
        monthly_rev = (
            daily.set_index("order_date")["daily_revenue"]
            .resample("MS").sum().reset_index()
        )
        monthly_rev["month_label"] = monthly_rev["order_date"].dt.strftime("%Y-%m")
        fig_month = go.Figure()
        fig_month.add_trace(go.Scatter(
            x=monthly_rev["month_label"], y=monthly_rev["daily_revenue"],
            mode="lines+markers", line=dict(color="#2C2C2A", width=2.5),
            marker=dict(size=6, color="#2C2C2A"),
            hovertemplate="%{x}<br>Revenue: R$ %{y:,.0f}<extra></extra>",
        ))
        fig_month.update_layout(template="plotly_white", font=CHART_FONT, height=340,
                                 yaxis_title="Monthly Revenue (R$)", xaxis_title="",
                                 margin=dict(l=10, r=10, t=10, b=10),
                                 hoverlabel=dict(font=dict(size=13)))
        st.plotly_chart(fig_month, width='stretch')
    with col_b:
        st.markdown("**Projected Revenue This Month**")
        remain = p["projected_close"] - p["mtd_actual"]
        delta = p["vs_target_pct"] - 100
        direction = "up" if delta >= 0 else "down"
        fig_donut = go.Figure(go.Pie(
            labels=["MTD Confirmed Actuals", "Remaining-Days Forecast"],
            values=[p["mtd_actual"], remain],
            hole=0.68,
            marker=dict(colors=["#444441", WARNING_COLOR], line=dict(color="white", width=2)),
            textinfo="percent",
            textposition="outside",
            textfont=dict(size=13),
            hovertemplate="%{label}<br>R$ %{value:,.0f} (%{percent})<extra></extra>",
        ))
        fig_donut.update_layout(
            template="plotly_white", font=CHART_FONT, height=360,
            annotations=[
                dict(text="Projected revenue this month", x=0.5, y=0.60,
                     font=dict(size=12, color="#5F5E5A"), showarrow=False),
                dict(text=f"R$ {p['projected_close']:,.0f}", x=0.5, y=0.48,
                     font=dict(size=19, color="#2C2C2A"), showarrow=False),
                dict(text=f"{abs(delta):.1f}% {direction} vs. prior month", x=0.5, y=0.38,
                     font=dict(size=11, color=("#1D9E75" if delta >= 0 else WARNING_COLOR)),
                     showarrow=False),
            ],
            showlegend=True, legend=dict(orientation="h", y=-0.15, font=CHART_FONT),
            margin=dict(l=40, r=40, t=30, b=30),
            hoverlabel=dict(font=dict(size=15)),
        )
        st.plotly_chart(fig_donut, width='stretch')

        delta = p["vs_target_pct"] - 100
        direction = "up" if delta >= 0 else "down"



elif dimension == "7-Day Forecast":
    daily["order_date"] = pd.to_datetime(daily["order_date"])
    forecast7["target_date"] = pd.to_datetime(forecast7["target_date"])
    recent = daily[daily["order_date"] >= forecast7["target_date"].min() - pd.Timedelta(days=40)]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=list(forecast7["target_date"]) + list(forecast7["target_date"][::-1]),
        y=list(forecast7["upper_bound"]) + list(forecast7["lower_bound"][::-1]),
        fill="toself", fillcolor="rgba(226,75,74,0.15)", line=dict(width=0),
        name="80% Prediction Interval", hoverinfo="skip",
    ))

    fig.add_trace(go.Scatter(x=recent["order_date"], y=recent["daily_revenue"],
                              mode="lines", name="Actual", line=dict(color="#444441", width=1.8),
                              hovertemplate="%{x|%Y-%m-%d}<br>Actual: R$ %{y:,.0f}<extra></extra>"))

    if not recent.empty and not forecast7.empty:
        last_actual_date = recent["order_date"].iloc[-1]
        last_actual_value = recent["daily_revenue"].iloc[-1]
        first_pred_date = forecast7["target_date"].iloc[0]
        first_pred_value = forecast7["forecast"].iloc[0]
        fig.add_trace(go.Scatter(
            x=[last_actual_date, first_pred_date],
            y=[last_actual_value, first_pred_value],
            mode="lines", line=dict(color=WARNING_COLOR, width=2.5),
            showlegend=False, hoverinfo="skip",
        ))

    fig.add_trace(go.Scatter(x=forecast7["target_date"], y=forecast7["forecast"],
                              mode="lines+markers", name="Forecast", line=dict(color=WARNING_COLOR, width=2.5),
                              hovertemplate="%{x|%Y-%m-%d}<br>Forecast: R$ %{y:,.0f}<extra></extra>"))

    fig.update_layout(template="plotly_white", font=CHART_FONT, height=460,
                       yaxis_title="Daily Revenue (R$)",
                       legend=dict(**LEGEND_STYLE),
                       margin=dict(l=10, r=10, t=10, b=70),
                       hoverlabel=dict(font=dict(size=15)))
    st.plotly_chart(fig, width='stretch')

else:  # Regional 7-Day Forecast
    reg_daily = optional("sales/regional_daily_actual.csv")

    if reg_7d is not None:
        reg_7d["target_date"] = pd.to_datetime(reg_7d["target_date"])
        regions = reg_7d["region"].unique().tolist()
        pick = st.pills("Select region", regions, default=regions[0], selection_mode="single")
        r = reg_7d[reg_7d["region"] == pick]

        figr = go.Figure()

        figr.add_trace(go.Scatter(
            x=list(r["target_date"]) + list(r["target_date"][::-1]),
            y=list(r["upper_bound"]) + list(r["lower_bound"][::-1]),
            fill="toself", fillcolor="rgba(226,75,74,0.15)", line=dict(width=0),
            name="80% Prediction Interval", hoverinfo="skip"))

        if reg_daily is not None:
            rd = reg_daily[reg_daily["region"] == pick].copy()
            rd["order_date"] = pd.to_datetime(rd["order_date"])
            recent_rd = rd[rd["order_date"] >= r["target_date"].min() - pd.Timedelta(days=40)]

            figr.add_trace(go.Scatter(
                x=recent_rd["order_date"], y=recent_rd["daily_revenue"],
                mode="lines", name="Actual", line=dict(color="#444441", width=1.8),
                hovertemplate="%{x|%Y-%m-%d}<br>Actual: R$ %{y:,.0f}<extra></extra>"))

            if not recent_rd.empty:
                figr.add_trace(go.Scatter(
                    x=[recent_rd["order_date"].iloc[-1], r["target_date"].iloc[0]],
                    y=[recent_rd["daily_revenue"].iloc[-1], r["forecast"].iloc[0]],
                    mode="lines", line=dict(color=WARNING_COLOR, width=2.5),
                    showlegend=False, hoverinfo="skip"))
        else:
            figr.add_trace(go.Scatter(x=r["target_date"], y=r["actual"], name="Actual",
                                       line=dict(color="#444441", width=2)))

        figr.add_trace(go.Scatter(x=r["target_date"], y=r["forecast"], name="Forecast",
                                   line=dict(color=WARNING_COLOR, width=2.5, dash="dot")))
        figr.update_layout(template="plotly_white", font=CHART_FONT, height=420,
                            yaxis_title="Daily Revenue (R$)",
                            legend=dict(**LEGEND_STYLE),
                            margin=dict(l=10, r=10, t=10, b=70),
                            hoverlabel=dict(font=dict(size=15)))
        st.plotly_chart(figr, width='stretch')
    else:
        st.info(f"No data. {HINT_V2}")



st.divider()

# -- Revenue mix --
st.markdown("**Revenue Mix**")
col_c, col_s, col_r = st.columns(3)

with col_c:
    st.caption("Revenue by category (top 10 + other)")
    if cat_rev is not None:
        total_rev = cat_rev["revenue"].sum()
        cat_rev["share_pct"] = (cat_rev["revenue"] / total_rev * 100).round(1)
        fig_cat = go.Figure()
        fig_cat.add_trace(go.Bar(
            x=cat_rev["category"], y=cat_rev["revenue"],
            marker_color="#378ADD",
            customdata=cat_rev["share_pct"],
            hovertemplate="<b>%{x}</b><br>Revenue: R$ %{y:,.0f}<br>Share: %{customdata:.1f}%<extra></extra>",
        ))
        fig_cat.update_layout(template="plotly_white", font=CHART_FONT, height=380,
                               yaxis_title="Revenue (R$)", xaxis_title="",
                               margin=dict(l=10, r=10, t=10, b=100),
                               hoverlabel=dict(font=dict(size=13)))
        st.plotly_chart(fig_cat, width='stretch')
    else:
        st.info(f"No data. {HINT_V2}")

with col_s:
    st.caption("How Much Revenue Do the Top Sellers Account For?")
    if seller_decile is not None:
        fig_sel = go.Figure()
        fig_sel.add_trace(go.Bar(
            x=seller_decile["tier"], y=seller_decile["revenue_share_pct"],
            marker_color="#378ADD",
            hovertemplate="Top %{x} sellers<br>Revenue share: %{y:.1f}%<extra></extra>",
        ))
        fig_sel.update_layout(template="plotly_white", font=CHART_FONT, height=380,
                               xaxis_title="Seller Group (Top 10% Deciles by Revenue)", yaxis_title="Revenue Share (%)",
                               margin=dict(l=10, r=10, t=10, b=70),
                               hoverlabel=dict(font=dict(size=13)))
        st.plotly_chart(fig_sel, width='stretch')
    else:
        st.info(f"No data. {HINT_V2}")

with col_r:
    st.caption("How Much Revenue Do the Top Cities Generate?")
    if region_rev is not None:
        top_region = region_rev.head(10)
        fig_reg = px.bar(top_region, x="customer_state", y="revenue",
                          color_discrete_sequence=["#378ADD"],
                          custom_data=["share_pct"])
        fig_reg.update_traces(
            hovertemplate="<b>%{x}</b><br>Revenue: R$ %{y:,.0f}<br>Share: %{customdata[0]:.1f}%<extra></extra>"
        )
        fig_reg.update_layout(template="plotly_white", font=CHART_FONT, height=380,
                               xaxis_title="", yaxis_title="Revenue (R$)",
                               margin=dict(l=10, r=10, t=10, b=10),
                               hoverlabel=dict(font=dict(size=13)))
        st.plotly_chart(fig_reg, width='stretch')
    else:
        st.info(f"No data. {HINT_V2}")

st.divider()

# -- Calendar effects --
st.markdown("**How Much Does Revenue Vary by Date?**")
if calendar_effect is not None:
    col_w, col_h, col_bf = st.columns(3)

    with col_w:
        st.caption("Weekday vs. Weekend Revenue")
        sub = calendar_effect[calendar_effect["group"] == "Day of week"]
        fig_w = go.Figure()
        fig_w.add_trace(go.Bar(
            x=sub["label"], y=sub["revenue"],
            marker_color=["#378ADD", "#B4B2A9"],
            hovertemplate="%{x}<br>Avg. revenue: R$ %{y:,.0f}<extra></extra>",
        ))
        fig_w.update_layout(template="plotly_white", font=CHART_FONT, height=340,
                             yaxis_title="Avg. Daily Revenue (R$)",
                             margin=dict(l=10, r=10, t=10, b=10),
                             hoverlabel=dict(font=dict(size=15)))
        st.plotly_chart(fig_w, width='stretch')

    with col_h:
        st.caption("Regular Days vs. Holiday Revenue")
        sub = calendar_effect[calendar_effect["group"] == "Holiday"]
        fig_h = go.Figure()
        fig_h.add_trace(go.Bar(
            x=sub["label"], y=sub["revenue"],
            marker_color=["#378ADD", "#B4B2A9"],
            hovertemplate="%{x}<br>Avg. revenue: R$ %{y:,.0f}<extra></extra>",
        ))
        fig_h.update_layout(template="plotly_white", font=CHART_FONT, height=340,
                             yaxis_title="Avg. Daily Revenue (R$)",
                             margin=dict(l=10, r=10, t=10, b=10),
                             hoverlabel=dict(font=dict(size=15)))
        st.plotly_chart(fig_h, width='stretch')

    with col_bf:
        st.caption("Regular Days vs. Black Friday Revenue")
        if bf_effect is not None:
            b = bf_effect.iloc[0]
            fig_bf = go.Figure()
            fig_bf.add_trace(go.Bar(
                x=["Normal (overall)", "Black Friday"],
                y=[b["normal_revenue"], b["black_friday_revenue"]],
                marker_color=["#B4B2A9", WARNING_COLOR],
                hovertemplate="%{x}<br>Avg. revenue: R$ %{y:,.0f}<extra></extra>",
            ))
            fig_bf.update_layout(template="plotly_white", font=CHART_FONT, height=340,
                                  yaxis_title="Avg. Daily Revenue (R$)",
                                  margin=dict(l=10, r=10, t=10, b=10),
                                  hoverlabel=dict(font=dict(size=15)))
            st.plotly_chart(fig_bf, width='stretch')
else:
    st.info(f"No data. {HINT_DS}")