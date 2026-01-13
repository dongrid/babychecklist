import streamlit as st
from datetime import datetime, date
import plotly.graph_objects as go

st.set_page_config(
    page_title="新生児管理チェックリスト",
    page_icon="👶",
    layout="wide"
)

st.title("👶 新生児管理チェックリスト")
st.markdown("---")

# 全ての基準値を定義（グローバル変数として定義）
ALL_PHOTOTHERAPY_THRESHOLDS = {
    "≥ 2,500g": {
        0: 11.0, 1: 12.0, 2: 15.0, 3: 17.0,
        4: 18.0, 5: 19.0, 6: 19.5, 7: 20.0
    },
    "2,000 ~ 2,499g": {
        0: 9.5, 1: 10.0, 2: 12.0, 3: 14.0,
        4: 16.0, 5: 17.0, 6: 18.0, 7: 18.0
    },
    "1,500 ~ 1,999g": {
        0: 7.5, 1: 8.0, 2: 10.0, 3: 12.0,
        4: 14.0, 5: 15.0, 6: 16.0, 7: 16.0
    },
    "1,000 ~ 1,499g": {
        0: 6.5, 1: 7.0, 2: 7.0, 3: 8.0,
        4: 9.0, 5: 10.0, 6: 11.0, 7: 12.0
    },
    "≤ 999g": {
        0: 4.5, 1: 5.0, 2: 5.0, 3: 6.0,
        4: 7.0, 5: 8.0, 6: 9.0, 7: 10.0
    }
}

def get_phototherapy_threshold(weight, days_old, has_kernicterus_risk=False):
    """村田基準に基づいて光線療法基準値を取得"""
    
    # 出生体重カテゴリーの決定
    if weight >= 2500:
        category = "≥ 2,500g"
    elif weight >= 2000:
        category = "2,000 ~ 2,499g"
    elif weight >= 1500:
        category = "1,500 ~ 1,999g"
    elif weight >= 1000:
        category = "1,000 ~ 1,499g"
    else:  # weight < 1000
        category = "≤ 999g"
    
    original_category = category
    
    # 核黄疸危険因子がある場合は1段階低い基準を使用
    if has_kernicterus_risk:
        if category == "≥ 2,500g":
            category = "2,000 ~ 2,499g"
        elif category == "2,000 ~ 2,499g":
            category = "1,500 ~ 1,999g"
        elif category == "1,500 ~ 1,999g":
            category = "1,000 ~ 1,499g"
        elif category == "1,000 ~ 1,499g":
            category = "≤ 999g"
        # ≤ 999g の場合はこれ以上低い基準がないので、そのまま使用
    
    thresholds = ALL_PHOTOTHERAPY_THRESHOLDS[category]
    
    # 日齢に応じた基準値を取得
    # 0日目の場合は1日目の基準値を使用（0日目は厳密には定義されていないため）
    if days_old == 0:
        day = 1
        threshold = thresholds.get(1, thresholds[7])
        is_day0 = True
    else:
        day = min(days_old, 7)
        threshold = thresholds.get(day, thresholds[7])
        is_day0 = False
    
    # 0日目の参考基準値も取得
    day0_threshold = thresholds.get(0, None)
    
    # 核黄疸危険因子により基準を変更した場合の情報も返す
    adjusted = has_kernicterus_risk and original_category != category
    
    return category, threshold, adjusted, original_category, is_day0, day0_threshold

def get_management_guidance(weight, is_first_child, delivery_method, gestational_age):
    """新生児の体重や状況に基づいて管理方針を決定"""
    guidance = {
        'category': '',
        'recommendations': [],
        'warnings': []
    }
    
    # 体重分類
    if weight < 1000:
        guidance['category'] = '極低出生体重児（ELBW）'
        guidance['warnings'].append('⚠️ 専門的なNICU管理が必要です')
        guidance['recommendations'].extend([
            '・体温管理：インキュベーターでの厳密な体温管理が必要',
            '・呼吸管理：人工呼吸器やCPAPの適応を検討',
            '・栄養管理：早期から経静脈栄養を開始',
            '・感染対策：厳格な無菌操作と感染予防',
            '・神経学的モニタリング：頭部エコーでのIVHスクリーニング'
        ])
    elif weight < 1500:
        guidance['category'] = '超低出生体重児（VLBW）'
        guidance['warnings'].append('⚠️ NICUでの管理が推奨されます')
        guidance['recommendations'].extend([
            '・体温管理：インキュベーターまたは開放型ベッドでの保温',
            '・呼吸管理：呼吸状態の慎重な観察',
            '・栄養管理：可能な限り早期からの経口栄養を検討',
            '・黄疸管理：早期からの光線療法を検討',
            '・感染予防：手洗いと清潔な環境の維持'
        ])
    elif weight < 2500:
        guidance['category'] = '低出生体重児（LBW）'
        guidance['recommendations'].extend([
            '・体温管理：適切な保温（帽子、靴下の使用）',
            '・栄養管理：3時間ごとの授乳、必要に応じて補足',
            '・体重増加：毎日の体重測定',
            '・黄疸スクリーニング：生後24-48時間で測定',
            '・低血糖スクリーニング：必要に応じて血糖測定'
        ])
    else:
        guidance['category'] = '正常出生体重児'
        guidance['recommendations'].extend([
            '・授乳：3-4時間ごとの授乳（1日8-12回）',
            '・体重変化：生後3-4日で生理的体重減少（出生体重の5-10%）',
            '・排泄：生後24時間以内に第1回の排便、48時間以内に第1回の排尿',
            '・黄疸：生後2-3日で生理的黄疸のピーク',
            '・ビタミンK：生後24時間以内にビタミンK2シロップを投与'
        ])
    
    # 初産/経産によるアドバイス
    if is_first_child:
        guidance['recommendations'].append('・初産の場合：母親の育児指導を丁寧に実施（授乳姿勢、おむつ交換など）')
    else:
        guidance['recommendations'].append('・経産の場合：以前の経験を活かしつつ、今回の赤ちゃんの個別性にも注意')
    
    # 在胎週数による考慮事項
    if gestational_age < 37:
        guidance['warnings'].append('⚠️ 早産児のため、呼吸、体温、栄養管理に特に注意が必要です')
        guidance['recommendations'].append('・早産児スクリーニング：ROP（未熟児網膜症）のスクリーニングを検討')
    
    return guidance

# 入力フィールド
st.header("📝 赤ちゃんの情報を入力してください")

col1, col2 = st.columns(2)

with col1:
    birth_date = st.date_input(
        "出生日",
        value=date.today(),
        max_value=date.today()
    )
    birth_time = st.time_input("出生時刻", value=datetime.now().time())
    birth_weight = st.number_input(
        "出生体重 (g)",
        min_value=500,
        max_value=6000,
        value=3000,
        step=10
    )
    gender = st.selectbox(
        "性別",
        ["男の子", "女の子", "その他"]
    )

with col2:
    is_first_child = st.radio(
        "初産/経産",
        ["初産", "経産"],
        horizontal=True
    )
    delivery_method = st.selectbox(
        "分娩形式",
        ["経腟分娩", "計画帝王切開", "緊急帝王切開", "吸引・鉗子分娩", "その他"]
    )
    col_weeks, col_days = st.columns(2)
    with col_weeks:
        gestational_weeks = st.number_input(
            "在胎週数（週）",
            min_value=20,
            max_value=42,
            value=39,
            step=1
        )
    with col_days:
        gestational_days = st.number_input(
            "在胎日数（日）",
            min_value=0,
            max_value=6,
            value=0,
            step=1
        )
    gestational_age = gestational_weeks + gestational_days / 7.0
    col_apgar1, col_apgar5 = st.columns(2)
    with col_apgar1:
        apgar_score_1min = st.number_input(
            "Apgarスコア（1分）",
            min_value=0,
            max_value=10,
            value=9,
            step=1
        )
    with col_apgar5:
        apgar_score_5min = st.number_input(
            "Apgarスコア（5分）",
            min_value=0,
            max_value=10,
            value=9,
            step=1
        )
    kernicterus_risk = st.checkbox(
        "核黄疸危険因子あり（周産期仮死、呼吸窮迫、アシデミア、低体温、低タンパク血症、低血糖・溶血、敗血症など）"
    )
    bilirubin_value = st.number_input(
        "血清総ビリルビン値 (mg/dL) - オプション",
        min_value=0.0,
        max_value=30.0,
        value=None,
        step=0.1,
        help="測定値がある場合は入力してください。0日目でも異常に高い値の場合は警告を表示します。"
    )

# 日齢の計算
today = date.today()
days_old = (today - birth_date).days

# 修正週数・日数の計算
total_gestational_days = gestational_weeks * 7 + gestational_days
corrected_total_days = total_gestational_days + days_old
corrected_weeks = corrected_total_days // 7
corrected_days = corrected_total_days % 7

# 核黄疸危険因子の自動判定（Apgarスコア5分値<3の場合は自動的に適用）
has_kernicterus_risk = kernicterus_risk or (apgar_score_5min < 3)

# 光線療法基準の計算
phototherapy_category, phototherapy_threshold, adjusted, original_category, is_day0, day0_threshold = get_phototherapy_threshold(
    birth_weight,
    days_old,
    has_kernicterus_risk
)

# 0日目でビリルビン値が異常に高い場合の警告
if is_day0 and bilirubin_value is not None:
    # 0日目の参考基準値と比較
    if day0_threshold and bilirubin_value > day0_threshold:
        st.warning(f"⚠️ 0日目でビリルビン値が参考基準値（{day0_threshold} mg/dL）を超えています。測定値: {bilirubin_value} mg/dL。1日目の基準値（{phototherapy_threshold} mg/dL）と比較して慎重に判断してください。")
    # 1日目の基準値と比較（より厳格なチェック）
    if bilirubin_value > phototherapy_threshold:
        st.error(f"🚨 0日目でビリルビン値が1日目の基準値（{phototherapy_threshold} mg/dL）を超えています。測定値: {bilirubin_value} mg/dL。早急な対応を検討してください。")

st.markdown("---")
st.header("📋 新生児管理の推奨事項")

# 日齢と修正週数・日数の表示
col1, col2 = st.columns(2)
with col1:
    st.metric("日齢（今日）", f"{days_old} 日")
with col2:
    st.metric("修正週数・日数（今日）", f"{corrected_weeks}週{corrected_days}日")

# 光線療法基準の表示
st.subheader("💡 光線療法基準（村田基準）")

# グラフの作成
fig = go.Figure()

# カテゴリーの順序
category_order = ["≥ 2,500g", "2,000 ~ 2,499g", "1,500 ~ 1,999g", "1,000 ~ 1,499g", "≤ 999g"]
colors = {
    "≥ 2,500g": "#1f77b4",  # 青
    "2,000 ~ 2,499g": "#ff7f0e",  # オレンジ
    "1,500 ~ 1,999g": "#2ca02c",  # 緑
    "1,000 ~ 1,499g": "#d62728",  # 赤
    "≤ 999g": "#9467bd"  # 紫
}

# 各カテゴリーのラインを描画
for cat in category_order:
    thresholds = ALL_PHOTOTHERAPY_THRESHOLDS[cat]
    days = list(range(8))  # 0-7日
    values = [thresholds[d] for d in days]
    
    # 本児が該当するラインかどうか
    is_highlighted = (cat == phototherapy_category)
    
    fig.add_trace(go.Scatter(
        x=days,
        y=values,
        mode='lines+markers',
        name=cat,
        line=dict(
            width=4 if is_highlighted else 2,
            color=colors[cat],
            dash='solid' if is_highlighted else 'dot'
        ),
        marker=dict(
            size=8 if is_highlighted else 6,
            color=colors[cat]
        ),
        hovertemplate=f'<b>{cat}</b><br>日齢: %{{x}}日<br>基準値: %{{y}} mg/dL<extra></extra>'
    ))

# 現在の日齢の位置を示す縦線
fig.add_vline(
    x=min(days_old, 7),
    line_dash="dash",
    line_color="gray",
    annotation_text=f"今日（日齢{days_old}日）",
    annotation_position="top"
)

# 現在の基準値を示す横線（該当カテゴリーのみ）
fig.add_hline(
    y=phototherapy_threshold,
    line_dash="dash",
    line_color=colors[phototherapy_category],
    annotation_text=f"基準値: {phototherapy_threshold} mg/dL",
    annotation_position="right"
)

fig.update_layout(
    title="光線療法基準（村田基準）",
    xaxis_title="生後日齢（日）",
    yaxis_title="血清総ビリルビン値（mg/dL）",
    hovermode='x unified',
    height=500,
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    )
)

st.plotly_chart(fig, use_container_width=True)

# 情報メッセージ
st.metric("適用基準ライン", phototherapy_category)
if is_day0:
    threshold_message = f"💡 今日は0日目です。0日目は厳密には基準値が定義されていないため、**1日目の基準値（{phototherapy_threshold} mg/dL）**を参考にしてください。"
    if day0_threshold:
        threshold_message += f"\n\n📌 0日目の参考値: {day0_threshold} mg/dL（参考値としてのみ使用）"
else:
    threshold_message = f"💡 今日（日齢{days_old}日）の光線療法基準値: **{phototherapy_threshold} mg/dL**（血清総ビリルビン値）"

if adjusted:
    threshold_message += f"\n\n⚠️ 核黄疸危険因子により、基準を1段階低く調整しました（元の基準: {original_category} → 適用基準: {phototherapy_category}）"
elif has_kernicterus_risk:
    threshold_message += f"\n\n⚠️ 核黄疸危険因子が確認されていますが、既に最低基準（{phototherapy_category}）を適用しています。"

st.info(threshold_message)

# 管理方針の取得
is_first_child_bool = is_first_child == "初産"
guidance = get_management_guidance(
    birth_weight,
    is_first_child_bool,
    delivery_method,
    gestational_age
)

# 分類の表示
st.subheader(f"分類: {guidance['category']}")

# 警告の表示
if guidance['warnings']:
    for warning in guidance['warnings']:
        st.warning(warning)

# 推奨事項の表示
st.subheader("✅ 管理のポイント")
for rec in guidance['recommendations']:
    st.markdown(rec)

st.markdown("---")
st.header("📝 基本的なチェックリスト")

checklist_items = [
    "体温測定（1日2-4回）",
    "体重測定（毎日）",
    "授乳記録（回数と量）",
    "排泄記録（回数と性状）",
    "黄疸の観察",
    "臍帯の観察（感染徴候の有無）",
    "皮膚の状態の確認",
    "呼吸状態の観察",
    "哺乳力の確認"
]

cols = st.columns(3)
for i, item in enumerate(checklist_items):
    with cols[i % 3]:
        st.checkbox(item, key=f"checklist_{i}")
