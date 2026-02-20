import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load_and_merge_data():
    file_id = "1cy7xHNrdkRiMqZph3zOUgC7LsXppAedk"
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    # 모든 시트를 딕셔너리로 로드
    sheets = pd.read_excel(url, sheet_name=None)
    
    df_raw = sheets['출고데이터 로우']
    # '휴젤거래처' 시트가 없으면 빈 데이터프레임 생성
    df_hugel = sheets.get('휴젤거래처', pd.DataFrame(columns=['거래처명']))
    
    # 데이터 정제
    df_raw['매출일자'] = pd.to_datetime(df_raw['매출일자'])
    df_raw['연도'] = df_raw['매출일자'].dt.year
    df_raw['월'] = df_raw['매출일자'].dt.month
    df_raw['공급가액'] = pd.to_numeric(df_raw['공급가액'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    return df_raw, df_hugel

try:
    df, df_hugel = load_and_merge_data()
    st.title("📊 2026 제휴사별 통합 전략 분석 (Error Fixed)")

    # --- [항목 1, 2, 3] 달성률 및 전년 대비 ---
    st.header("📍 1-3. 제휴사별 매출 성과 및 성장률")
    summary = df.groupby(['제휴사', '연도'])['공급가액'].sum().unstack().fillna(0)
    
    # 2025년 데이터가 없는 경우를 위한 컬럼 체크
    if 2025 not in summary.columns: summary[2025] = 0
    if 2026 not in summary.columns: summary[2026] = 0
    
    summary.columns = ['2025년 매출', '2026년 매출']
    # 0으로 나누기 방지 로직 추가
    summary['성장률(%)'] = summary.apply(lambda x: ((x['2026년 매출'] - x['2025년 매출']) / x['2025년 매출'] * 100) if x['2025년 매출'] > 0 else 0, axis=1).round(1)
    st.table(summary.reset_index())

    # --- [항목 4] 진료과별/지역별 ---
    st.header("📍 4. 26년 진료과/지역별 매출 현황")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("지역별 TOP 10")
        st.table(df[df['연도'] == 2026].groupby('지역')['공급가액'].sum().reset_index().sort_values(by='공급가액', ascending=False).head(10))
    with col2:
        st.subheader("진료과별 매출")
        st.table(df[df['연도'] == 2026].groupby('진료과')['공급가액'].sum().reset_index().sort_values(by='공급가액', ascending=False))

    # --- [항목 8] 뉴메코(메디톡스) 상세 분석 ---
    st.header("📍 8. 뉴메코(메디톡스) 심층 분석")
    nm_df = df[df['제휴사'] == '뉴메코']
    
    # 8-1. 휴젤 거래처 비교 (시트 대조)
    hugel_clients = set(df_hugel['거래처명'].unique())
    nm_clients = set(nm_df['거래처명'].unique())
    intersection = nm_clients.intersection(hugel_clients)
    
    # 8-2. 코어톡스 100개 이상 VIP 증감
    core_df = nm_df[nm_df['제품명 변환'].str.contains('코어톡스', na=False)]
    vip_25 = core_df[(core_df['연도'] == 2025) & (core_df['수량'] >= 100)]['거래처명'].nunique()
    vip_26 = core_df[(core_df['연도'] == 2026) & (core_df['수량'] >= 100)]['거래처명'].nunique()

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("📋 휴젤 거래처 내 침투율")
        st.table(pd.DataFrame({
            "항목": ["휴젤+메디톡스 병행", "메디톡스 전용", "휴젤 전용"],
            "거래처 수": [len(intersection), len(nm_clients - hugel_clients), len(hugel_clients - nm_clients)]
        }))
    with col4:
        st.subheader("📋 코어톡스 100개↑ VIP 업체 증감")
        st.table(pd.DataFrame({
            "연도": ["2025년", "2026년"],
            "VIP 업체수": [vip_25, vip_26],
            "증감": ["-", f"+{vip_26 - vip_25}"]
        }))

    # --- [항목 9, 10] SKBS 및 로파마 ---
    st.header("📍 9-10. SKBS 분석 및 로파마 스위칭")
    col5, col6 = st.columns(2)
    with col5:
        st.subheader("SKBS 상위 품목 실적")
        st.table(df[df['제휴사'] == 'SKBS'].groupby('제품명 변환')['공급가액'].sum().reset_index().sort_values(by='공급가액', ascending=False).head(5))
    with col6:
        st.subheader("로파마 아카리작스 도입 현황")
        lo_raw = df[df['제휴사'] == '로파마']
        total_lo = lo_raw['거래처명'].nunique()
        akari_lo = lo_raw[lo_raw['제품명 변환'].str.contains('아카리작스', na=False)]['거래처명'].nunique()
        
        # 0으로 나누기 방지
        switch_rate = (akari_lo / total_lo * 100) if total_lo > 0 else 0
        st.write(f"로파마 전체 {total_lo}곳 중 {akari_lo}곳 도입 완료")
        st.progress(switch_rate / 100)
        st.info(f"현재 스위칭 비율: {switch_rate:.1f}%")

except Exception as e:
    st.error(f"분석 중 오류 발생: {e}")
