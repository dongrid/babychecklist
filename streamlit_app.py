import streamlit as st
from datetime import datetime, date, timedelta
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

def get_management_guidance(weight, is_first_child, delivery_method, gestational_age, days_old, has_iv_line=False, 
                           maternal_diabetes=False, maternal_thyroid_medication=False, 
                           maternal_thyroid_antibody=False, maternal_thyroid_history=False,
                           apgar_score_5min=9, delivery_stress=False, birth_date=None, birth_time=None,
                           exchange_transfusion=False, intracranial_hemorrhage=False,
                           apnea_treatment=False, gentamicin_history=False, amikacin_history=False,
                           high_oxygen=False, municipality="茅ヶ崎市", corrected_weeks=0, expanded_mass_screening=False,
                           gestational_weeks=0, gestational_days=0):
    """新生児の体重や状況に基づいて管理方針を決定"""
    guidance = {
        'category': '',
        'recommendations': [],
        'warnings': [],
        'special_management': []
    }
    
    # 体重分類（カテゴリーのみ）
    if weight < 1000:
        guidance['category'] = '極低出生体重児（ELBW）'
        guidance['warnings'].append('⚠️ 専門的なNICU管理が必要です')
    elif weight < 1500:
        guidance['category'] = '超低出生体重児（VLBW）'
        guidance['warnings'].append('⚠️ NICUでの管理が推奨されます')
    elif weight < 2500:
        guidance['category'] = '低出生体重児（LBW）'
    else:
        guidance['category'] = '正常出生体重児'
    
    # 在胎週数による考慮事項
    if gestational_age < 37:
        guidance['warnings'].append('⚠️ 早産児のため、呼吸、体温、栄養管理に特に注意が必要です')
        guidance['recommendations'].append('・早産児スクリーニング：ROP（未熟児網膜症）のスクリーニングを検討')
    
    # ケイツーシロップ12回投与法（すべての子どもに適応）
    k2_guidance = []
    
    # 1回目：日齢0（点滴あり）または日齢1（点滴なし）
    if has_iv_line:
        k2_guidance.append('・1回目：日齢0にケイツーシロップを静注（極低出生体重児の場合は半量）')
    else:
        k2_guidance.append('・1回目：日齢1にケイツーシロップ内服（極低出生体重児でも減量しない）')
    
    # 2回目：日齢4
    if has_iv_line:
        k2_guidance.append('・2回目：日齢4に消化が良ければケイツーシロップ内服、悪ければ静注（極低出生体重児の場合は静注は半量）')
    else:
        k2_guidance.append('・2回目：日齢4にケイツーシロップ内服（極低出生体重児でも減量しない）')
    
    # 3回目以降：日齢11以降に迎える水曜日から毎週水曜日に12回目まで
    if birth_date and birth_time:
        birth_datetime = datetime.combine(birth_date, birth_time)
        # 日齢11以降に迎える最初の水曜日を計算
        first_wednesday_after_day11 = None
        for i in range(11, 18):  # 日齢11から17の間で最初の水曜日を探す
            check_date = birth_date + timedelta(days=i)
            if check_date.weekday() == 2:  # 水曜日
                first_wednesday_after_day11 = check_date
                break
        
        if first_wednesday_after_day11:
            last_wednesday = first_wednesday_after_day11 + timedelta(weeks=9)  # 12回目（3回目から10週後）
            k2_guidance.append(f'・3回目〜12回目：{first_wednesday_after_day11.strftime("%Y年%m月%d日")}（水曜日）から{last_wednesday.strftime("%Y年%m月%d日")}（水曜日）まで毎週水曜日に内服')
    
    # すべての子どもに適応があるため、常に表示
    guidance['special_management'].append({
        'title': '💊 ケイツーシロップ12回投与法',
        'items': k2_guidance + [
            '・入院中の内服は処置オーダとして手続する',
            '・退院処方として12回目までのケイツーを処方する'
        ],
        'needed': True
    })
    
    # マススクリーニング（すべての子どもに適応）
    mass_screening_items = []
    if days_old == 4:
        mass_screening_items.append('・日齢4：マススクリーニングを実施')
        if expanded_mass_screening:
            mass_screening_items.append('・拡大マススクリーニングも実施（希望あり）')
    elif days_old < 4:
        mass_screening_items.append('・日齢4：マススクリーニングを実施予定')
        if expanded_mass_screening:
            mass_screening_items.append('・拡大マススクリーニングも実施予定（希望あり）')
    
    # 早産児は退院前にマススクリーニング再検
    if gestational_age < 37:
        mass_screening_items.append('・早産児のため、退院前にマススクリーニング再検を行う')
    
    # すべての子どもに適応があるため、常に表示
    guidance['special_management'].append({
        'title': '🧪 マススクリーニング',
        'items': mass_screening_items,
        'needed': True
    })
    
    # 低血糖ハイリスク児の管理
    hypoglycemia_risk = (
        gestational_age < 37 or
        weight < 2500 or
        maternal_diabetes or
        delivery_stress or
        apgar_score_5min < 7
    )
    
    if hypoglycemia_risk:
        # 適応理由を取得
        risk_reasons = []
        if gestational_age < 37:
            risk_reasons.append("在胎37週未満")
        if weight < 2500:
            risk_reasons.append("体重2500g未満")
        if maternal_diabetes:
            risk_reasons.append("糖尿病母体")
        if delivery_stress:
            risk_reasons.append("分娩ストレス")
        if apgar_score_5min < 7:
            risk_reasons.append("Apgar5分値7未満")
        
        items = [
            f'・適応理由：{"、".join(risk_reasons)}',
            '・出生3時間後に簡易血糖測定を実施',
            '・出生6時間後に簡易血糖測定を実施',
            '・出生12時間後に簡易血糖測定を実施'
        ]
        guidance['special_management'].append({
            'title': '🩸 低血糖ハイリスク児の管理',
            'items': items,
            'needed': True
        })
    else:
        # 適応がない理由を判定
        reason = []
        if gestational_age >= 37:
            reason.append("在胎37週以上")
        if weight >= 2500:
            reason.append("体重2500g以上")
        if not maternal_diabetes:
            reason.append("糖尿病母体なし")
        if not delivery_stress:
            reason.append("分娩ストレスなし")
        if apgar_score_5min >= 7:
            reason.append("Apgar5分値7以上")
        guidance['special_management'].append({
            'title': '🩸 低血糖ハイリスク児の管理',
            'items': [f'・適応なし（{"、".join(reason[:3]) if reason else "低血糖リスク因子なし"}）'],
            'needed': False
        })
    
    # 甲状腺機能検査の対象児
    thyroid_check_needed = (
        maternal_thyroid_medication or
        maternal_thyroid_antibody or
        maternal_thyroid_history
    )
    
    if thyroid_check_needed:
        # 適応理由を取得
        thyroid_reasons = []
        if maternal_thyroid_medication:
            thyroid_reasons.append("甲状腺に関する内服加療中の母体")
        if maternal_thyroid_antibody:
            thyroid_reasons.append("抗甲状腺抗体陽性の母体")
        if maternal_thyroid_history:
            thyroid_reasons.append("甲状腺疾患の既往があり、妊娠経過中の情報が不明")
        
        thyroid_items = [
            f'・適応理由：{"、".join(thyroid_reasons)}',
            '・出生前に臍帯血保存用の生化学スピッツ（茶色）を準備しておく',
            '・出生後、生化学スピッツに臍帯血を入れて保存しておく',
            '・医師は臍帯血及び日齢4の児血についてTSHとfT4をオーダする'
        ]
        
        # 日齢4が休日の場合の処理
        if days_old == 4 and birth_date:
            check_date = birth_date + timedelta(days=4)
            if check_date.weekday() >= 5:  # 土曜日(5)または日曜日(6)
                thyroid_items.append('・日齢4が休日のため、次の平日まで延期')
        
        thyroid_items.extend([
            '・TSH<0.01の時は治療を開始',
            '・fT4>3なら治療か再検を検討'
        ])
        
        guidance['special_management'].append({
            'title': '🔬 甲状腺機能検査の対象児',
            'items': thyroid_items,
            'needed': True
        })
    else:
        guidance['special_management'].append({
            'title': '🔬 甲状腺機能検査の対象児',
            'items': ['・適応なし（母体の甲状腺関連情報なし）'],
            'needed': False
        })
    
    # 頭部MRIを実施する条件
    mri_needed = (
        gestational_age < 34 or
        weight < 1500 or
        exchange_transfusion or
        intracranial_hemorrhage
    )
    
    if mri_needed:
        # 適応理由を取得
        mri_reasons = []
        if gestational_age < 34:
            mri_reasons.append("在胎34週未満")
        if weight < 1500:
            mri_reasons.append("体重1500g未満")
        if exchange_transfusion:
            mri_reasons.append("交換輸血を実施")
        if intracranial_hemorrhage:
            mri_reasons.append("頭蓋内出血")
        
        mri_items = [
            f'・適応理由：{"、".join(mri_reasons)}',
            '・退院前に頭部MRIを実施',
            '・時期：全身状態が安定した頃'
        ]
        if weight < 1000:  # 極低出生体重児
            mri_items.append('・極低出生体重児は修正37-44週で検査時体重1500g以上')
        guidance['special_management'].append({
            'title': '🧠 頭部MRI',
            'items': mri_items,
            'needed': True
        })
    else:
        # 適応がない理由を判定
        reason = []
        if gestational_age >= 34:
            reason.append("在胎34週以上")
        if weight >= 1500:
            reason.append("体重1500g以上")
        if not exchange_transfusion:
            reason.append("交換輸血なし")
        if not intracranial_hemorrhage:
            reason.append("頭蓋内出血なし")
        guidance['special_management'].append({
            'title': '🧠 頭部MRI',
            'items': [f'・適応なし（{"、".join(reason[:2]) if reason else "適応条件を満たさない"}）'],
            'needed': False
        })
    
    # AABR
    aabr_insurance = (
        gestational_age < 35 or
        weight <= 1800 or
        exchange_transfusion or  # 重症黄疸（交換輸血を実施）
        apnea_treatment or
        gentamicin_history or
        amikacin_history or
        intracranial_hemorrhage
    )
    
    if aabr_insurance:
        # 適応理由を取得
        aabr_reasons = []
        if gestational_age < 35:
            aabr_reasons.append("在胎35週未満")
        if weight <= 1800:
            aabr_reasons.append("体重1800g以下")
        if exchange_transfusion:
            aabr_reasons.append("交換輸血を実施")
        if apnea_treatment:
            aabr_reasons.append("無呼吸発作治療")
        if gentamicin_history:
            aabr_reasons.append("ゲンタシン投与歴")
        if amikacin_history:
            aabr_reasons.append("アミカシン投与歴")
        if intracranial_hemorrhage:
            aabr_reasons.append("頭蓋内出血")
        
        guidance['special_management'].append({
            'title': '👂 AABR',
            'items': [
                f'・保険適応理由：{"、".join(aabr_reasons)}',
                '・時期：全身状態が安定した頃'
            ],
            'needed': True
        })
    else:
        # 適応がない理由を判定
        reason = []
        if gestational_age >= 35:
            reason.append("在胎35週以上")
        if weight > 1800:
            reason.append("体重1800g超")
        if not exchange_transfusion:
            reason.append("交換輸血なし")
        if not apnea_treatment:
            reason.append("無呼吸発作治療なし")
        if not gentamicin_history and not amikacin_history:
            reason.append("ゲンタシン/アミカシン投与歴なし")
        if not intracranial_hemorrhage:
            reason.append("頭蓋内出血なし")
        guidance['special_management'].append({
            'title': '👂 AABR',
            'items': [f'・保険適応なし（{"、".join(reason[:2]) if reason else "適応条件を満たさない"}。ご家族の希望により自費で実施可能）'],
            'needed': False
        })
    
    # 眼底検査
    eye_exam_needed = (
        gestational_age < 34 or
        weight < 1800 or
        high_oxygen
    )
    
    if eye_exam_needed:
        # 適応理由を取得
        eye_reasons = []
        if gestational_age < 34:
            eye_reasons.append("在胎34週未満")
        if weight < 1800:
            eye_reasons.append("体重1800g未満")
        if high_oxygen:
            eye_reasons.append("高濃度酸素投与歴")
        
        eye_items = [
            f'・適応理由：{"、".join(eye_reasons)}',
            '・眼科に診察を依頼する',
            '・時期：生後2-3週毎',
            '・準備：サンドールP点眼液を事前に処方しておく',
            '・眼科宛の院内紹介状を作成し、眼科受診の指示をしておく',
            '・必要な場合には、眼科処置前後のミルク量を減らす指示を出しておく'
        ]
        guidance['special_management'].append({
            'title': '👁️ 眼底検査',
            'items': eye_items,
            'needed': True
        })
    else:
        # 適応がない理由を判定
        reason = []
        if gestational_age >= 34:
            reason.append("在胎34週以上")
        if weight >= 1800:
            reason.append("体重1800g以上")
        if not high_oxygen:
            reason.append("高濃度酸素投与歴なし")
        guidance['special_management'].append({
            'title': '👁️ 眼底検査',
            'items': [f'・適応なし（{"、".join(reason[:2]) if reason else "適応条件を満たさない"}）'],
            'needed': False
        })
    
    # 予防接種
    # 退院前に2か月齢を迎える可能性がある児
    # 条件：出生から2か月経っても修正週数が37週未満、または体重が2300g未満、またはその他の理由で入院が長引く可能性がある
    # 2か月後の修正週数を計算
    total_gestational_days_at_birth = gestational_weeks * 7 + gestational_days
    total_days_at_two_months = total_gestational_days_at_birth + 60
    corrected_weeks_at_two_months = total_days_at_two_months // 7
    
    # 2か月後の体重を予測（オーバートリアージ）
    # 体重増加率は出生体重に応じて設定（控えめに予測）
    if weight < 1500:
        daily_weight_gain = 10  # 極低出生体重児：1日10g増加
    elif weight < 2500:
        daily_weight_gain = 15  # 低出生体重児：1日15g増加
    else:
        daily_weight_gain = 20  # 正常出生体重児：1日20g増加
    
    predicted_weight_at_two_months = weight + (daily_weight_gain * 60)
    
    # 退院が長引く可能性がある条件
    long_stay_possible = (
        corrected_weeks_at_two_months < 37 or  # 2か月経っても修正37週未満
        predicted_weight_at_two_months < 2300 or  # 2か月後も2300g未満になりそう
        exchange_transfusion or  # 交換輸血を実施（重症黄疸）
        intracranial_hemorrhage or  # 頭蓋内出血
        apnea_treatment or  # 無呼吸発作治療
        high_oxygen  # 高濃度酸素投与歴
    )
    
    if long_stay_possible and days_old < 60:
        # 適応理由を取得
        vaccine_reasons = []
        if corrected_weeks_at_two_months < 37:
            vaccine_reasons.append("2か月後も修正37週未満")
        if predicted_weight_at_two_months < 2300:
            vaccine_reasons.append("2か月後も体重2300g未満になりそう")
        if exchange_transfusion:
            vaccine_reasons.append("交換輸血を実施")
        if intracranial_hemorrhage:
            vaccine_reasons.append("頭蓋内出血")
        if apnea_treatment:
            vaccine_reasons.append("無呼吸発作治療")
        if high_oxygen:
            vaccine_reasons.append("高濃度酸素投与歴")
        
        vaccine_items = [
            f'・適応理由：{"、".join(vaccine_reasons)}',
            '・退院前に2か月齢を迎える可能性があるため、予防接種を検討',
            '・注意：ロタワクチンは二次感染を考慮し、入院中は行わない（退院日も）'
        ]
        if municipality not in ["茅ヶ崎市", "寒川町"]:
            vaccine_items.append(f'・児の登録されている自治体が{municipality}の場合は当該の自治体へ連絡が必要')
        guidance['special_management'].append({
            'title': '💉 予防接種',
            'items': vaccine_items,
            'needed': True
        })
    else:
        # 適応がない理由を判定
        reason = []
        if corrected_weeks_at_two_months >= 37:
            reason.append("2か月後も修正37週以上")
        if predicted_weight_at_two_months >= 2300:
            reason.append("2か月後も体重2300g以上になりそう")
        if not exchange_transfusion and not intracranial_hemorrhage and not apnea_treatment and not high_oxygen:
            reason.append("その他の入院長期化要因なし")
        if days_old >= 60:
            reason.append("既に2か月齢を超えている")
        guidance['special_management'].append({
            'title': '💉 予防接種',
            'items': [f'・該当なし（{"、".join(reason[:2]) if reason else "退院前に2か月齢を迎える可能性が低い"}）'],
            'needed': False
        })
    
    # 特別な管理項目をrecommendationsに変換
    for special in guidance['special_management']:
        if special.get('needed', True):
            guidance['recommendations'].append(f"**{special['title']}**")
            for item in special['items']:
                guidance['recommendations'].append(item)
        else:
            guidance['recommendations'].append(f"**{special['title']}**")
            guidance['recommendations'].append(f"<span style='color: gray;'>{special['items'][0]}</span>")
    
    return guidance

# 入力フィールド
st.header("📝 赤ちゃんの情報を入力してください")

# 基本情報
st.subheader("👶 基本情報")
col1, col2, col3 = st.columns(3)
with col1:
    birth_date = st.date_input(
        "出生日",
        value=date.today(),
        max_value=date.today()
    )
with col2:
    birth_time = st.time_input("出生時刻", value=datetime.now().time())
with col3:
    gender = st.selectbox(
        "性別",
        ["男児", "女児"]
    )

col1, col2 = st.columns(2)
with col1:
    birth_weight = st.number_input(
        "出生体重 (g)",
        min_value=500,
        max_value=6000,
        value=3000,
        step=10
    )
with col2:
    is_first_child = st.radio(
        "初産/経産",
        ["初産", "経産"],
        horizontal=True
    )

# 分娩情報
st.subheader("🤱 分娩情報")
col1, col2 = st.columns(2)
with col1:
    delivery_method = st.selectbox(
        "分娩形式",
        ["経腟分娩", "計画帝王切開", "緊急帝王切開", "吸引・鉗子分娩", "その他"]
    )
with col2:
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

# Apgarスコア
st.subheader("📊 Apgarスコア")
col1, col2 = st.columns(2)
with col1:
    apgar_score_1min = st.number_input(
        "Apgarスコア（1分）",
        min_value=0,
        max_value=10,
        value=9,
        step=1
    )
with col2:
    apgar_score_5min = st.number_input(
        "Apgarスコア（5分）",
        min_value=0,
        max_value=10,
        value=9,
        step=1
    )


# 追加情報
st.subheader("ℹ️ 追加情報")
col1, col2 = st.columns(2)
with col1:
    has_iv_line = st.checkbox("点滴ラインあり")
    maternal_diabetes = st.checkbox("糖尿病母体より出生")
    maternal_thyroid_medication = st.checkbox("甲状腺に関する内服加療中の母体より出生")
with col2:
    maternal_thyroid_antibody = st.checkbox("抗甲状腺抗体(TRAbまたはTSAb)陽性の母体より出生")
    maternal_thyroid_history = st.checkbox("甲状腺疾患の既往があり、妊娠経過中の情報が不明")
    expanded_mass_screening = st.checkbox("拡大マススクリーニング希望")

# 検査・治療歴
st.subheader("🏥 検査・治療歴")
col1, col2 = st.columns(2)
with col1:
    exchange_transfusion = st.checkbox("重症黄疸（交換輸血を実施）")
    intracranial_hemorrhage = st.checkbox("頭蓋内出血")
    apnea_treatment = st.checkbox("無呼吸発作治療")
    respiratory_distress = st.checkbox("呼吸窮迫（PaO2≦40が2時間以上持続）")
    acidosis = st.checkbox("アシドーシス（pH≦7.15）")
with col2:
    gentamicin_history = st.checkbox("ゲンタシン投与歴")
    amikacin_history = st.checkbox("アミカシン投与歴")
    high_oxygen = st.checkbox("高濃度酸素投与歴")
    hypothermia = st.checkbox("低体温（直腸温<35℃が2時間以上持続）")
    hypoproteinemia = st.checkbox("低蛋白血症（血清蛋白≦4.0またはAlb≦2.5）")
    hypoglycemia = st.checkbox("低血糖")
    hemolysis = st.checkbox("溶血")
    cns_abnormality = st.checkbox("敗血症を含む中枢神経系の異常徴候")

# その他
st.subheader("📍 その他")
municipality = st.selectbox(
    "登録自治体",
    ["茅ヶ崎市", "寒川町", "その他"],
    help="予防接種の連絡先を決定するため"
)

# 日齢の計算
today = date.today()
days_old = (today - birth_date).days

# 修正週数・日数の計算
total_gestational_days = gestational_weeks * 7 + gestational_days
corrected_total_days = total_gestational_days + days_old
corrected_weeks = corrected_total_days // 7
corrected_days = corrected_total_days % 7

# 核黄疸危険因子の自動判定（Apgarスコア5分値≦3、またはその他の危険因子がある場合）
has_kernicterus_risk = (
    apgar_score_5min <= 3 or
    respiratory_distress or
    acidosis or
    hypothermia or
    hypoproteinemia or
    hypoglycemia or
    hemolysis or
    cns_abnormality
)

# 光線療法基準の計算
phototherapy_category, phototherapy_threshold, adjusted, original_category, is_day0, day0_threshold = get_phototherapy_threshold(
    birth_weight,
    days_old,
    has_kernicterus_risk
)

st.markdown("---")
st.header("📋 新生児管理の推奨事項")

# 日齢と修正週数・日数の表示
col1, col2 = st.columns(2)
with col1:
    st.metric("日齢（今日）", f"{days_old} 日")
with col2:
    st.metric("修正週数・日数（今日）", f"{corrected_weeks}週{corrected_days}日")

# 分娩ストレスの判定
delivery_stress = (
    delivery_method in ["吸引・鉗子分娩", "緊急帝王切開"] or
    apgar_score_5min < 7
)

# 管理方針の取得
is_first_child_bool = is_first_child == "初産"
guidance = get_management_guidance(
    birth_weight,
    is_first_child_bool,
    delivery_method,
    gestational_age,
    days_old,
    has_iv_line,
    maternal_diabetes,
    maternal_thyroid_medication,
    maternal_thyroid_antibody,
    maternal_thyroid_history,
    apgar_score_5min,
    delivery_stress,
    birth_date,
    birth_time,
    exchange_transfusion,
    intracranial_hemorrhage,
    apnea_treatment,
    gentamicin_history,
    amikacin_history,
    high_oxygen,
    municipality,
    corrected_weeks,
    expanded_mass_screening,
    gestational_weeks,
    gestational_days
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
    if rec.startswith('<span'):
        st.markdown(rec, unsafe_allow_html=True)
    else:
        st.markdown(rec)

# 光線療法基準の表示（管理のポイントの中）
st.markdown("---")
st.markdown("### 💡 光線療法基準（村田基準）")

# 情報メッセージ（グラフの上に表示）
st.metric("適用基準ライン", phototherapy_category)
if is_day0:
    threshold_message = f"💡 今日は0日目です。0日目は厳密には基準値が定義されていないため、**1日目の基準値（{phototherapy_threshold} mg/dL）**を参考にしてください。"
    if day0_threshold:
        threshold_message += f"\n\n📌 0日目の参考値: {day0_threshold} mg/dL（参考値としてのみ使用）"
else:
    threshold_message = f"💡 今日（日齢{days_old}日）の光線療法基準値: **{phototherapy_threshold} mg/dL**（血清総ビリルビン値）"

# 核黄疸危険因子の詳細を取得
risk_factors = []
if apgar_score_5min <= 3:
    risk_factors.append("5分Apgar≦3")
if respiratory_distress:
    risk_factors.append("呼吸窮迫（PaO2≦40が2時間以上持続）")
if acidosis:
    risk_factors.append("アシドーシス（pH≦7.15）")
if hypothermia:
    risk_factors.append("低体温（直腸温<35℃が2時間以上持続）")
if hypoproteinemia:
    risk_factors.append("低蛋白血症（血清蛋白≦4.0またはAlb≦2.5）")
if hypoglycemia:
    risk_factors.append("低血糖")
if hemolysis:
    risk_factors.append("溶血")
if cns_abnormality:
    risk_factors.append("敗血症を含む中枢神経系の異常徴候")

if adjusted:
    risk_factors_str = "、".join(risk_factors)
    threshold_message += f"\n\n⚠️ 核黄疸危険因子（{risk_factors_str}）により、基準を1段階低く調整しました（元の基準: {original_category} → 適用基準: {phototherapy_category}）"
elif has_kernicterus_risk:
    risk_factors_str = "、".join(risk_factors)
    threshold_message += f"\n\n⚠️ 核黄疸危険因子（{risk_factors_str}）が確認されていますが、既に最低基準（{phototherapy_category}）を適用しています。"
else:
    threshold_message += f"\n\n✅ 核黄疸危険因子は該当しません。"

st.info(threshold_message)

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

