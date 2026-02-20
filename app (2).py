import streamlit as st
import pandas as pd

@st.cache_data
def load_and_analyze():
    file_id = "1cy7xHNrdkRiMqZph3zOUgC7LsXppAedk"
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    sheets = pd.read_excel(url, sheet_name=None)
    
    # 1. 시트 로드
    df_raw = sheets['출고데이터 로우']
    df_hugel = sheets.get('휴젤거래처', pd.DataFrame(columns=['거래처명']))
    
    # 2. 전처리 (부가세/날짜/숫자)
    df_raw['매출일자'] = pd.to_datetime(df_raw['매출일자'])
    df_raw['연도'] = df_raw['매출일자'].dt.year
    df_raw['월'] = df_raw['매출일자'].dt.month
    df_raw['공급가액'] = pd.to_numeric(df_raw['공급가액'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    return df_raw, df_hugel

try:
    df, df_hugel = load_and_analyze()
    st.title("🚀 제휴사별 정밀 영업 전략 분석")

    # --- 1~4. 제휴사별 통합 분석 ---
    st.header("📍 1-4. 제휴사별 성과 (년/월/과/지역)")
    for partner in df['제휴사'].unique():
        with st.expander(f"🏢 {partner} 상세 분석"):
            p_df = df[df['제휴사'] == partner]
            # 년/월 매출
            perf = p_df.groupby(['연도', '월'])['공급가액'].sum().unstack(level=0).fillna(0)
            st.subheader(f"{partner} 전년대비/시즌 매출 현황")
            st.table(perf)
            
            # 진료과/지역별
            c1, c2 = st.columns(2)
            c1.write("Top 지역")
            c1.table(p_df.groupby('지역')['공급가액'].sum().nlargest(5))
            c2.write("Top 진료과")
            c2.table(p_df.groupby('진료과')['공급가액'].sum().nlargest(5))

    # --- 8. 뉴메코(메디톡스) 집중 분석 ---
    st.header("📍 8. 뉴메코(메디톡스) 전략 분석")
    nm_df = df[df['제휴사'] == '뉴메코']
    
    # (1) 휴젤 직거래처 구매 전환 분석
    hugel_list = set(df_hugel['거래처명'].unique())
    nm_buy_hugel = nm_df[nm_df['거래처명'].isin(hugel_list)]
    
    # (2) 코어톡스 수익성 분석 (매입가 31,500 -> 30,000 변동 반영)
    # 매입가는 부가세 포함이므로 / 1.1 해서 공급가 기준으로 계산
    core_df = nm_df[nm_df['제품명 변환'].str.contains('코어톡스', na=False)].copy()
    
    def calc_profit(row):
        # 2월 2일 기준 매입가 변동 (부가세 제외로 환산)
        cost_pre = 31500 / 1.1
        cost_post = 30000 / 1.1
        current_cost = cost_post if row['매출일자'] >= pd.Timestamp('2026-02-02') else cost_pre
        return (row['단가'] - current_cost) * row['수량']

    core_df['수익'] = core_df.apply(calc_profit, axis=1)
    profit_increase = core_df[core_df['매출일자'] >= pd.Timestamp('2026-02-02')]['수익'].sum()

    # (3) 코어톡스 33,000원 100개 이상 업체 증감
    vip_25 = core_df[(core_df['연도'] == 2025) & (core_df['수량'] >= 100)]['거래처명'].nunique()
    vip_26 = core_df[(core_df['연도'] == 2026) & (core_df['수량'] >= 100)]['거래처명'].nunique()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📋 휴젤 직거래처 -> 뉴메코 전환")
        st.write(f"휴젤 직거래처 중 뉴메코 구매 업체: **{nm_buy_hugel['거래처명'].nunique()}곳**")
        st.write(f"해당 업체 총 매출액: {nm_buy_hugel['공급가액'].sum():,.0f}원")
    with col2:
        st.subheader("📋 코어톡스 단가/수익 분석")
        st.write(f"2/2 매입가 인하 후 발생 수익: **{profit_increase:,.0f}원**")
        st.write(f"100개↑ VIP 업체: 25년({vip_25}곳) → 26년({vip_26}곳)")

    # --- 9. SKBS & 10. 로파마 ---
    st.header("📍 9-10. SKBS & 로파마 스위칭 분석")
    
    # 로파마 스위칭 (아카리작스 -> 라이스정)
    lo_df = df[df['제휴사'] == '로파마']
    akari_buyers = set(lo_df[lo_df['제품명 변환'].str.contains('아카리작스', na=False)]['거래처명'].unique())
    rice_buyers = set(lo_df[lo_df['제품명 변환'].str.contains('라이스정', na=False)]['거래처명'].unique())
    switched = akari_buyers.intersection(rice_buyers)

    st.subheader("로파마 아카리작스 -> 라이스정 전환 현황")
    st.write(f"아카리작스 구매처: {len(akari_buyers)}곳")
    st.write(f"라이스정으로 전환(병행)된 곳: {len(switched)}곳")
    st.write(f"미전환 업체 수: {len(akari_buyers - rice_buyers)}곳")

except Exception as e:
    st.error(f"데이터 연산 오류: {e}")
