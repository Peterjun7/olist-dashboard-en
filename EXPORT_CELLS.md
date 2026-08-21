# Per-notebook export cells

For each notebook, add a **new cell at the very bottom**, paste the code in, and run it.
Just adjust the `DASH` path to match your own environment.

---

## 1. olist_customer_clustering_4.ipynb

```python
# ===== Dashboard export (Customers screen) =====
DASH = r'C:\Users\Peter\Desktop\olist_dashboard\data\customer'
import os; os.makedirs(DASH, exist_ok=True)

# Cluster number -> segment name (same rule as the funnel notebook)
_p = cust_clean.groupby('Cluster')[features].mean()
_names, _rem = {}, list(_p.index)
def _take(col, how):
    global _rem
    idx = _p.loc[_rem, col].idxmin() if how == 'min' else _p.loc[_rem, col].idxmax()
    _rem = [r for r in _rem if r != idx]
    return idx
_names[_take('avg_review_score', 'min')] = 'Delivery-Disappointed'
_names[_take('avg_item_count',   'max')] = 'Bulk-Buyer'
_names[_take('monetary',         'min')] = 'Budget-Regular'
_names[_take('avg_review_len',   'min')] = 'Silent-Premium'
_names[_rem[0]]                          = 'Engaged-Premium'
cust_clean['Segment'] = cust_clean['Cluster'].map(_names)

# (1) Radar chart
_radar = radar_mm.copy()
_radar.index = [_names[i] for i in _radar.index]
_radar.reset_index().rename(columns={'index': 'Segment'}).to_csv(
    f'{DASH}/cluster_radar.csv', index=False, encoding='utf-8-sig')

# (2) PCA scatter (sampled)
_pca = pca_df.copy()
_pca['Segment'] = _pca['Cluster'].map(_names) if _pca['Cluster'].dtype != object \
                  else _pca['Cluster'].astype(int).map(_names)
_pca.sample(min(6000, len(_pca)), random_state=42)[['PC1', 'PC2', 'Segment']].to_csv(
    f'{DASH}/cluster_pca.csv', index=False, encoding='utf-8-sig')

# (3) Map
_map = cust_geo_sample.copy()
_map['Cluster'] = _map['Cluster'].astype(int)
_map['Segment'] = _map['Cluster'].map(_names)
_map[['lat', 'lng', 'Segment']].to_csv(
    f'{DASH}/cluster_map.csv', index=False, encoding='utf-8-sig')

# (4) Within Delivery-Disappointed: average delay by repeat-purchase group
_dis = [k for k, v in _names.items() if v == 'Delivery-Disappointed'][0]
_c1 = cust_clean[cust_clean['Cluster'] == _dis]
_c1.groupby('repeat_group').agg(
    mean_delay=('avg_delay', 'mean'),
    median_delay=('avg_delay', 'median'),
    n=('avg_delay', 'size'),
).reset_index().to_csv(f'{DASH}/cluster1_delay.csv', index=False, encoding='utf-8-sig')

# (5) Voucher effect (computed directly from raw payments)
from scipy.stats import chi2_contingency
_pay = payments.copy()
_pay['is_v'] = (_pay['payment_type'] == 'voucher')
_o = _pay.groupby('order_id').apply(
    lambda g: pd.Series({
        'v_amt': g.loc[g['is_v'], 'payment_value'].sum(),
        'tot':   g['payment_value'].sum(),
    }), include_groups=False).reset_index()
_o['v_share'] = np.where(_o['tot'] > 0, _o['v_amt'] / _o['tot'] * 100, 0)
_cv = df[['order_id', 'customer_unique_id']].merge(_o, on='order_id', how='left')
_cv = _cv.groupby('customer_unique_id').agg(
    v_share=('v_share', 'mean'), used=('v_amt', lambda s: (s > 0).any())).reset_index()
_m = cust_clean[['customer_unique_id', 'Segment', 'repeat_group']].merge(
    _cv, on='customer_unique_id', how='left')
_m['used'] = _m['used'].fillna(False)

_rows = []
for seg, g in _m.groupby('Segment'):
    ct = pd.crosstab(g['used'], g['repeat_group'])
    try:
        _, pval, _, _ = chi2_contingency(ct)
    except Exception:
        pval = np.nan
    rr = g.groupby('used')['repeat_group'].apply(lambda s: (s != '1 purchase').mean() * 100)
    _rows.append({
        'Segment': seg,
        'repeat_rate_voucher':   rr.get(True, np.nan),
        'repeat_rate_no_voucher': rr.get(False, np.nan),
        'chi2_p': pval,
        'voucher_share_of_payment_pct': g.loc[g['used'], 'v_share'].mean(),
    })
pd.DataFrame(_rows).to_csv(f'{DASH}/voucher_effect.csv', index=False, encoding='utf-8-sig')

print('Customers screen export done:', os.listdir(DASH))
```

---

## 2. olist_segment_funnel_retention.ipynb

```python
# ===== Dashboard export (Customers + Delivery screens) =====
DASH_C = r'C:\Users\Peter\Desktop\olist_dashboard\data\customer'
DASH_D = r'C:\Users\Peter\Desktop\olist_dashboard\data\delivery'
import os
os.makedirs(DASH_C, exist_ok=True); os.makedirs(DASH_D, exist_ok=True)

# --- Customers ---
_prof = cust_clean.groupby('Segment')[features].mean()
_prof['customer_count'] = cust_clean['Segment'].value_counts()
_prof['total_revenue'] = _prof['monetary'] * _prof['customer_count']
_prof['revenue_share_pct'] = (_prof['total_revenue'] / _prof['total_revenue'].sum() * 100).round(1)
_prof.reset_index().to_csv(f'{DASH_C}/segment_profile.csv', index=False, encoding='utf-8-sig')

tbl.reset_index().to_csv(f'{DASH_C}/repeat_rate.csv', index=False, encoding='utf-8-sig')

# --- Delivery ---
funnel_pct.reset_index().to_csv(f'{DASH_D}/seg_funnel_reach.csv', index=False, encoding='utf-8-sig')

_gap = pd.DataFrame({
    'purchase->approved': stage_days['days_approved'],
    'approved->shipped':  stage_days['days_shipped'] - stage_days['days_approved'],
    'shipped->delivered': stage_days['days_delivered'] - stage_days['days_shipped'],
})
_gap.reset_index().to_csv(f'{DASH_D}/seg_stage_days.csv', index=False, encoding='utf-8-sig')

cum_days_by_state.reset_index().to_csv(
    f'{DASH_D}/state_cum_days.csv', index=False, encoding='utf-8-sig')
cum_days_by_cat.reset_index().to_csv(
    f'{DASH_D}/category_cum_days.csv', index=False, encoding='utf-8-sig')
group_summary.reset_index().to_csv(
    f'{DASH_D}/weight_seller_delay.csv', index=False, encoding='utf-8-sig')

print('Funnel notebook export done')
print(' customer:', os.listdir(DASH_C))
print(' delivery:', os.listdir(DASH_D))
```

---

## 3. olist_forecast_v2.ipynb

```python
# ===== Dashboard export (Revenue screen, main) =====
DASH = r'C:\Users\Peter\Desktop\olist_dashboard\data\sales'
import os; os.makedirs(DASH, exist_ok=True)

LAST_DATE = b["order_date"].max()
_target = base.loc[base["order_date"].dt.to_period("M")
                   == (LAST_DATE.to_period("M") - 1), "daily_revenue"].sum()
pd.DataFrame([month_pacing_beyond_data(LAST_DATE, target=_target)]).to_csv(
    f'{DASH}/pacing_headline.csv', index=False, encoding='utf-8-sig')

f7_oos.to_csv(f'{DASH}/forecast_7d.csv', index=False, encoding='utf-8-sig')
base[['order_date', 'daily_revenue']].to_csv(
    f'{DASH}/daily_actual.csv', index=False, encoding='utf-8-sig')
conv.to_csv(f'{DASH}/pacing_convergence.csv', index=False, encoding='utf-8-sig')
summary.reset_index().rename(columns={'index': 'model'}).to_csv(
    f'{DASH}/model_summary.csv', index=False, encoding='utf-8-sig')
byh.reset_index().to_csv(f'{DASH}/horizon_wmape.csv', index=False, encoding='utf-8-sig')

print('Revenue main export done:', os.listdir(DASH))
```

---

## 4. olist_daily_sales_forecasting.ipynb

```python
# ===== Dashboard export (feature importance + predicted vs. actual) =====
DASH = r'C:\Users\Peter\Desktop\olist_dashboard\data\sales'
import os; os.makedirs(DASH, exist_ok=True)

importance_v7.to_csv(f'{DASH}/feature_importance.csv', index=False, encoding='utf-8-sig')

pd.DataFrame({
    'order_date': model_df_v7['order_date'].iloc[split7:].values,
    'actual': y7_test.values,
    'forecast': pred_v7,
}).to_csv(f'{DASH}/pred_vs_actual.csv', index=False, encoding='utf-8-sig')

print('Daily model export done')
```

---

## 5. olist_regional_forecast.ipynb

```python
# ===== Dashboard export (regional) =====
DASH = r'C:\Users\Peter\Desktop\olist_dashboard\data\sales'
import os; os.makedirs(DASH, exist_ok=True)

regions = [sp]
if 'mg' in dir():
    regions.append(mg)

_pac, _f7 = [], []
for reg in regions:
    AS_OF = reg['origins'][-2]   # [-1] (8/1) falls in the late-August data-decay window, so it's excluded
    r = reg['month_pacing'](AS_OF); r['region'] = reg['state_name']
    _pac.append(r)
    f = reg['forecast'](AS_OF, 7).copy(); f['region'] = reg['state_name']
    _f7.append(f)

pd.DataFrame(_pac).to_csv(f'{DASH}/regional_pacing.csv', index=False, encoding='utf-8-sig')
pd.concat(_f7).to_csv(f'{DASH}/regional_7d.csv', index=False, encoding='utf-8-sig')
print('Regional export done')
```
