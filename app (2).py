import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 설정 및 데이터 로드 (모든 시트 통합 읽기)
st.set_page_config(layout="wide", page_title="핵심 7대 항목 분석")

@st.cache_data
def load_full_data():
    file_id = "1cy7xHNrdkRiMqZph3zOUgC7LsXppAedk"
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    # 모든 시트를 딕셔너리 형태로 로드
    all_sheets = pd.read_excel(url, sheet_name=None)
    return all_sheets

try:
    sheets = load_full_data()
    # 메인 로우 데이터
    df = sheets['출고데이터 로우']
    
    # 전처리
    df['매출일자'] = pd.to_datetime(df['매출일자'])
    df['연도'] = df['매출일자'].dt.year
    df['월'] = df['매출일자'].dt.month
    # 공급가액 수치화 (콤마 제거)
    if df['공급가액'].dtype == 'object':
        df['공급가액'] = df['공급가액'].str.replace(',', '').astype(float)

    st.title("📊 제휴사별 핵심 실적 분석 보고서 (항목 1~4, 8~10)")

    # --- [항목 1, 2, 3] 년/월 달성률 및 전년/시즌 대비 ---
    st.header("📍 1-3. 제휴사별 매출 및 성장률 현황")
    # 25년 동기(1~2월) vs 26년 동기(1~2월)
    df_25 = df[(df['연도'] == 2025) & (df['월'] <= 2)]
    df_26 = df[(df['연도'] == 2026) & (df['월'] <= 2)]
    
    sales_25 = df_25.groupby('제휴사')['공급가액'].sum()
    sales_26 = df_26.groupby('제휴사')['공급가액'].sum()
    
    yoy_df = pd.DataFrame({'25년 동기 실적': sales_25, '26년 동기 실적': sales_26}).fillna(0)
    yoy_df['성장률(%)'] = ((yoy_df['26년 동기 실적'] - yoy_df['25년 동기 실적']) / yoy_df['25년 동기 실적'] * 100).round(1)
    
    # 복사 가능한 표 출력
    st.subheader("제휴사별 전년 동기 대비 실적 (VAT 별도)")
    st.table(yoy_df.reset_index())

    # --- [항목 4] 진료과별 / 지역별 현황 ---
    st.header("📍 4. 진료과별 및 지역별 현황")
    col1, col2 = st.columns(2)
    with col1:
        region_sales = df[df['연도'] == 2026].groupby('지역')['공급가액'].sum().reset_index()
        st.table(region_sales.sort_values(by='공급가액', ascending=False))
    with col2:
        dept_sales = df[df['연도'] == 2026].groupby('진료과')['공급가액'].sum().reset_index()
        st.table(dept_sales.sort_values(by='공급가액', ascending=False))

    # --- [항목 8] 뉴메코(메디톡스) 집중 분석 ---
    st.header("📍 8. 뉴메코(메디톡스) 심층 분석")
    nm_df = df[df['제휴사'] == '뉴메코']
    hugel_df = df[df['제휴사'] == '휴젤']
    
    nm_cust = set(nm_df['거래처명'].unique())
    hugel_cust = set(hugel_df['거래처명'].unique())
    both = nm_cust.intersection(hugel_cust) # 중복 거래처
    
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("휴젤 거래처 비교 (중복 구매)")
        compare_data = pd.DataFrame({
            "항목": ["휴젤+메디톡스 병행", "메디톡스 전용", "휴젤 전용"],
            "거래처 수": [len(both), len(nm_cust - hugel_cust), len(hugel_cust - nm_cust)]
        })
        st.table(compare_data)
        
    with col4:
        st.subheader("코어톡스 대량 구매처 (100개↑)")
        # 단가 33,000원 기준 필터링 (데이터상 '단가' 컬럼 활용)
        vip_core = nm_df[(nm_df['제품명 변환'].str.contains('코어톡스')) & (nm_df['수량'] >= 100)]
        st.table(vip_core[['매출일자', '거래처명', '수량', '공급가액']].head(10))
        st.info(f"코어톡스 100개 이상 구매 거래처 수: {vip_core['거래처명'].nunique()}곳")

    # --- [항목 9, 10] SKBS 및 로파마 분석 ---
    st.header("📍 9-10. SKBS 품목 및 로파마 스위칭 현황")
    col5, col6 = st.columns(2)
    with col5:
        st.subheader("SKBS 품목별 매출 비교")
        sk_sales = df[df['제휴사'] == 'SKBS'].groupby('제품명 변환')['공급가액'].sum().reset_index()
        st.table(sk_sales.sort_values(by='공급가액', ascending=False).head(5))
    with col6:
        st.subheader("로파마 아카리작스 현황")
        akari_df = df[(df['제휴사'] == '로파마') & (df['제품명 변환'].str.contains('아카리작스'))]
        # 전환이 안 되는 곳(과거 로파마 구매했으나 아카리작스 없는 곳) 추정
        st.write(f"아카리작스 취급 거래처: {akari_df['거래처명'].nunique()}곳")
        st.table(akari_df[['거래처명', '공급가액']].tail(5))

except Exception as e:
    st.error(f"오류 발생: {e}. '출고데이터 로우' 시트의 컬럼명을 확인해주세요.")
