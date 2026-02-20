import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(layout="wide", page_title="영업 분석 보고서")

@st.cache_data
def load_data():
    # 구글 시트 ID 직접 참조
    file_id = "1cy7xHNrdkRiMqZph3zOUgC7LsXppAedk"
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    # '출고데이터 로우' 시트 읽기
    df = pd.read_excel(url, sheet_name='출고데이터 로우')
    
    # 데이터 정제: 날짜 변환 및 금액 수치화
    df['매출일자'] = pd.to_datetime(df['매출일자'])
    df['연도'] = df['매출일자'].dt.year
    df['월'] = df['매출일자'].dt.month
    # 공급가액(VAT별도) 수치화
    if df['공급가액'].dtype == 'object':
        df['공급가액'] = pd.to_numeric(df['공급가액'].str.replace(',', ''), errors='coerce')
    return df

try:
    df = load_data()
    st.title("🏥 제휴사별 핵심 영업 지표 분석 (항목 1~4, 8~10)")
    st.info("💡 모든 금액은 부가세(VAT) 제외 기준입니다.")

    # --- [항목 1, 2, 3] 년/월 달성률 및 YoY ---
    st.header("📍 1-3. 제휴사별 매출 및 전년 동기 대비(YoY)")
    # 25년 vs 26년 동기(1~2월) 비교
    df_yoy = df[df['월'] <= 2].groupby(['제휴사', '연도'])['공급가액'].sum().unstack().fillna(0)
    df_yoy.columns = ['25년 동기 실적', '26년 동기 실적']
    df_yoy['성장률(%)'] = ((df_yoy['26년 동기 실적'] - df_yoy['25년 동기 실적']) / df_yoy['25년 동기 실적'] * 100).round(1)
    st.subheader("📊 제휴사별 성과 요약")
    st.table(df_yoy.reset_index())

    # --- [항목 4] 진료과별 / 지역별 현황 ---
    st.header("📍 4. 지역 및 진료과별 현황 (26년 누계)")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("지역별 매출 순위")
        region_sales = df[df['연도'] == 2026].groupby('지역')['공급가액'].sum().reset_index()
        st.table(region_sales.sort_values(by='공급가액', ascending=False))
    with col2:
        st.subheader("진료과별 매출 순위")
        dept_sales = df[df['연도'] == 2026].groupby('진료과')['공급가액'].sum().reset_index()
        st.table(dept_sales.sort_values(by='공급가액', ascending=False))

    # --- [항목 8] 뉴메코(메디톡스) 집중 분석 ---
    st.markdown("---")
    st.header("📍 8. 뉴메코(메디톡스) 상세 분석")
    nm_df = df[df['제휴사'] == '뉴메코']
    hugel_cust = set(df[df['제휴사'] == '휴젤']['거래처명'].unique())
    nm_cust = set(nm_df['거래처명'].unique())
    intersection = nm_cust.intersection(hugel_cust)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("📋 휴젤 거래처 내 메디톡스 구매 현황")
        cross_table = pd.DataFrame({
            "구분": ["휴젤+메디톡스 병행", "메디톡스 전용", "휴젤 전용(미침투)"],
            "거래처 수": [len(intersection), len(nm_cust - hugel_cust), len(hugel_cust - nm_cust)]
        })
        st.table(cross_table)
    with col4:
        st.subheader("📋 코어톡스 대량 구매처 (100개↑)")
        vip_df = nm_df[(nm_df['제품명 변환'].str.contains('코어톡스', na=False)) & (nm_df['수량'] >= 100)]
        st.table(vip_df[['거래처명', '수량', '공급가액']].head(10))

    # --- [항목 9, 10] SKBS 및 로파마 ---
    st.header("📍 9-10. SKBS 및 로파마 현황")
    col5, col6 = st.columns(2)
    with col5:
        st.subheader("SKBS 상위 품목 실적")
        sk_items = df[df['제휴사'] == 'SKBS'].groupby('제품명 변환')['공급가액'].sum().reset_index()
        st.table(sk_items.sort_values(by='공급가액', ascending=False).head(5))
    with col6:
        st.subheader("로파마 아카리작스 실적")
        akari_df = df[(df['제휴사'] == '로파마') & (df['제품명 변환'].str.contains('아카리작스', na=False))]
        st.table(akari_df.groupby('거래처명')['공급가액'].sum().reset_index().head(5))

except Exception as e:
    st.error(f"데이터 로드 오류: {e}")
