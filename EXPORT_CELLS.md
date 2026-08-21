# 노트북별 export 셀 모음

각 노트북 **맨 아래에 새 셀**을 만들어 붙여넣고 실행하세요.
`DASH` 경로만 본인 환경에 맞게 수정하면 됩니다.

---

## 1. olist_customer_clustering_4.ipynb

```python
# ===== 대시보드 export (고객 화면) =====
DASH = r'C:\Users\Peter\Desktop\olist_dashboard\data\customer'
import os; os.makedirs(DASH, exist_ok=True)

# 군집 번호 -> 세그먼트 이름 (퍼널 노트북과 동일한 규칙)
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

# (1) 레이더 차트
_radar = radar_mm.copy()
_radar.index = [_names[i] for i in _radar.index]
_radar.reset_index().rename(columns={'index': 'Segment'}).to_csv(
    f'{DASH}/cluster_radar.csv', index=False, encoding='utf-8-sig')

# (2) PCA 산점도 (샘플링)
_pca = pca_df.copy()
_pca['Segment'] = _pca['Cluster'].map(_names) if _pca['Cluster'].dtype != object \
                  else _pca['Cluster'].astype(int).map(_names)
_pca.sample(min(6000, len(_pca)), random_state=42)[['PC1', 'PC2', 'Segment']].to_csv(
    f'{DASH}/cluster_pca.csv', index=False, encoding='utf-8-sig')

# (3) 지도
_map = cust_geo_sample.copy()
_map['Cluster'] = _map['Cluster'].astype(int)
_map['Segment'] = _map['Cluster'].map(_names)
_map[['lat', 'lng', 'Segment']].to_csv(
    f'{DASH}/cluster_map.csv', index=False, encoding='utf-8-sig')

# (4) 배송실망군 내부: 재구매 여부별 평균 지연일
_dis = [k for k, v in _names.items() if v == 'Delivery-Disappointed'][0]
_c1 = cust_clean[cust_clean['Cluster'] == _dis]
_c1.groupby('repeat_group').agg(
    mean_delay=('avg_delay', 'mean'),
    median_delay=('avg_delay', 'median'),
    n=('avg_delay', 'size'),
).reset_index().to_csv(f'{DASH}/cluster1_delay.csv', index=False, encoding='utf-8-sig')

# (5) 바우처 효과 (원본 payments에서 직접 계산)
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
    rr = g.groupby('used')['repeat_group'].apply(lambda s: (s != '1회 구매').mean() * 100)
    _rows.append({
        'Segment': seg,
        '재구매율_바우처사용':   rr.get(True, np.nan),
        '재구매율_바우처미사용': rr.get(False, np.nan),
        '카이제곱_p': pval,
        '결제액대비_바우처비중(%)': g.loc[g['used'], 'v_share'].mean(),
    })
pd.DataFrame(_rows).to_csv(f'{DASH}/voucher_effect.csv', index=False, encoding='utf-8-sig')

print('고객 화면 export 완료:', os.listdir(DASH))
```

---

## 2. olist_segment_funnel_retention.ipynb

```python
# ===== 대시보드 export (고객 + 배송 화면) =====
DASH_C = r'C:\Users\Peter\Desktop\olist_dashboard\data\customer'
DASH_D = r'C:\Users\Peter\Desktop\olist_dashboard\data\delivery'
import os
os.makedirs(DASH_C, exist_ok=True); os.makedirs(DASH_D, exist_ok=True)

# --- 고객 ---
_prof = cust_clean.groupby('Segment')[features].mean()
_prof['고객수'] = cust_clean['Segment'].value_counts()
_prof['총매출'] = _prof['monetary'] * _prof['고객수']
_prof['매출기여도(%)'] = (_prof['총매출'] / _prof['총매출'].sum() * 100).round(1)
_prof.reset_index().to_csv(f'{DASH_C}/segment_profile.csv', index=False, encoding='utf-8-sig')

tbl.reset_index().to_csv(f'{DASH_C}/repeat_rate.csv', index=False, encoding='utf-8-sig')

# --- 배송 ---
funnel_pct.reset_index().to_csv(f'{DASH_D}/seg_funnel_reach.csv', index=False, encoding='utf-8-sig')

_gap = pd.DataFrame({
    'purchase→approved': stage_days['days_approved'],
    'approved→shipped':  stage_days['days_shipped'] - stage_days['days_approved'],
    'shipped→delivered': stage_days['days_delivered'] - stage_days['days_shipped'],
})
_gap.reset_index().to_csv(f'{DASH_D}/seg_stage_days.csv', index=False, encoding='utf-8-sig')

cum_days_by_state.reset_index().to_csv(
    f'{DASH_D}/state_cum_days.csv', index=False, encoding='utf-8-sig')
cum_days_by_cat.reset_index().to_csv(
    f'{DASH_D}/category_cum_days.csv', index=False, encoding='utf-8-sig')
group_summary.reset_index().to_csv(
    f'{DASH_D}/weight_seller_delay.csv', index=False, encoding='utf-8-sig')

print('퍼널 노트북 export 완료')
print(' customer:', os.listdir(DASH_C))
print(' delivery:', os.listdir(DASH_D))
```

---

## 3. olist_forecast_v2.ipynb

```python
# ===== 대시보드 export (매출 화면 메인) =====
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
summary.reset_index().rename(columns={'index': '모델'}).to_csv(
    f'{DASH}/model_summary.csv', index=False, encoding='utf-8-sig')
byh.reset_index().to_csv(f'{DASH}/horizon_wmape.csv', index=False, encoding='utf-8-sig')

print('매출 메인 export 완료:', os.listdir(DASH))
```

---

## 4. olist_daily_sales_forecasting.ipynb

```python
# ===== 대시보드 export (피처중요도 + 예측vs실제) =====
DASH = r'C:\Users\Peter\Desktop\olist_dashboard\data\sales'
import os; os.makedirs(DASH, exist_ok=True)

importance_v7.to_csv(f'{DASH}/feature_importance.csv', index=False, encoding='utf-8-sig')

pd.DataFrame({
    'order_date': model_df_v7['order_date'].iloc[split7:].values,
    '실제': y7_test.values,
    '예측': pred_v7,
}).to_csv(f'{DASH}/pred_vs_actual.csv', index=False, encoding='utf-8-sig')

print('일별모델 export 완료')
```

---

## 5. olist_regional_forecast.ipynb

```python
# ===== 대시보드 export (지역별) =====
DASH = r'C:\Users\Peter\Desktop\olist_dashboard\data\sales'
import os; os.makedirs(DASH, exist_ok=True)

regions = [sp]
if 'mg' in dir():
    regions.append(mg)

_pac, _f7 = [], []
for reg in regions:
    AS_OF = reg['origins'][-2]   # [-1](8/1)은 8월 후반 데이터 붕괴 구간이 걸려 제외
    r = reg['month_pacing'](AS_OF); r['지역'] = reg['state_name']
    _pac.append(r)
    f = reg['forecast'](AS_OF, 7).copy(); f['지역'] = reg['state_name']
    _f7.append(f)

pd.DataFrame(_pac).to_csv(f'{DASH}/regional_pacing.csv', index=False, encoding='utf-8-sig')
pd.concat(_f7).to_csv(f'{DASH}/regional_7d.csv', index=False, encoding='utf-8-sig')
print('지역별 export 완료')
```
