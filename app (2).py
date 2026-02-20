import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 데이터 로드 및 시트 통합
@st.cache_data
def load_and_merge_data():
    file_id = "1cy7xHNrdkRiMqZph3zOUgC7LsXppAedk"
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    sheets = pd.read_excel(url, sheet_name=None)
    
    # 각 시트 가져오기
    df_raw = sheets['출고데이터 로우']
    df_hugel = sheets.get('휴젤거래처', pd.DataFrame(columns=['거래처명']))
    
    # 전처리
    df_raw['매출일자'] = pd.to_datetime(df_raw['매출일자'])
    df_raw['연도'] = df_raw['매출일자'].dt.year
    df_raw['월'] = df_raw['매출일자'].dt.month
    df_raw['공급가액'] = pd.to_numeric(df_raw['공급가액'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    return df_raw, df_hugel

try:
    df, df_hugel = load_and_merge_data()
    st.title("📊 2026 제휴사별 통합 전략 분석 보고서")

    # --- [1, 2, 3번] 달성률 및 전년/시즌 대비 ---
    st.header("📍 1-3. 제휴사별 매출 성과 및 성장률 (YoY)")
    # 25년(전체) vs 26년(현재)
    summary = df.groupby(['제휴사', '연도'])['공급가액'].sum().unstack().fillna(0)
    summary.columns = ['2025년 매출', '2026년 매출']
    summary['성장률(%)'] = ((summary['2026년 매출'] - summary['2025년 매출']) / summary['2025년 매출'] * 100).round(1)
    st.table(summary.reset_index())

    # --- [4번] 진료과별/지역별 현황 ---
    st.header("📍 4. 진료과별 및 지역별 현황 (26년 누계)")
    col1, col2 = st.columns(2)
    with col1:
        reg_df = df[df['연도'] == 2026].groupby('지역')['공급가액'].sum().reset_index()
        st.table(reg_df.sort_values(by='공급가액', ascending=False))
    with col2:
        dept_df = df[df['연도'] == 2026].groupby('진료과')['공급가액'].sum().reset_index()
        st.table(dept_df.sort_values(by='공급가액', ascending=False))

    # --- [8번] 뉴메코(메디톡스) 심층 분석 ---
    st.header("📍 8. 뉴메코(메디톡스) 상세 분석")
    nm_df = df[df['제휴사'] == '뉴메코']
    
    # 8-1. 휴젤 거래처 비교
    hugel_clients = set(df_hugel['거래처명'].unique())
    nm_clients = set(nm_df['거래처명'].unique())
    intersection = nm_clients.intersection(hugel_clients)
    
    # 8-2. 코어톡스 100개 이상 구매처 (판매가 33,000원 필터링)
    # 실제 데이터의 '단가' 컬럼 혹은 공급가액/수량으로 계산
    core_df = nm_df[nm_df['제품명 변환'].str.contains('코어톡스', na=False)]
    vip_25 = core_df[(core_df['연도'] == 2025) & (core_df['수량'] >= 100)]['거래처명'].nunique()
    vip_26 = core_df[(core_df['연도'] == 2026) & (core_df['수량'] >= 100)]['거래처명'].nunique()

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("📋 휴젤 거래처 내 침투 현황")
        st.table(pd.DataFrame({
            "항목": ["휴젤+메디톡스 병행", "메디톡스 전용", "휴젤 전용(잠재적 타겟)"],
            "거래처 수": [len(intersection), len(nm_clients - hugel_clients), len(hugel_clients - nm_clients)]
        }))
    with col4:
        st.subheader("📋 코어톡스 100개↑ VIP 업체 증감")
        st.table(pd.DataFrame({
            "연도": ["2025년", "2026년 (현재)"],
            "100개 이상 구매처": [vip_25, vip_26],
            "증감": ["-", f"+{vip_26 - vip_25}"]
        }))

    # --- [9, 10번] SKBS 및 로파마 ---
    st.header("📍 9-10. SKBS 품목 분석 및 로파마 스위칭 현황")
    col5, col6 = st.columns(2)
    with col5:
        st.subheader("SKBS 주요 품목별 비중")
        sk_items = df[df['제휴사'] == 'SKBS'].groupby('제품명 변환')['공급가액'].sum().reset_index()
        st.table(sk_items.sort_values(by='공급가액', ascending=False).head(5))
    with col6:
        st.subheader("로파마 아카리작스 도입 현황")
        lo_raw = df[df['제휴사'] == '로파마']
        akari_clients = lo_raw[lo_raw['제품명 변환'].str.contains('아카리작스', na=False)]['거래처명'].nunique()
        total_lo_clients = lo_raw['거래처명'].nunique()
        st.write(f"전체 거래처 {total_lo_clients}곳 중 {akari_clients}곳 도입")
        st.progress(akari_clients / total_lo_clients)

except Exception as e:
    st.error(f"분석 중 오류 발생: {e}")
