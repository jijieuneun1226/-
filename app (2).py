import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. 페이지 설정
st.set_page_config(layout="wide", page_title="제휴사 핵심 전략 대시보드")

@st.cache_data
def load_data():
    # 구글 시트 ID 활용
    file_id = "1cy7xHNrdkRiMqZph3zOUgC7LsXppAedk"
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    # 메인 로우 데이터 시트 읽기
    df = pd.read_excel(url, sheet_name='출고데이터 로우')
    
    # 전처리: 날짜 및 숫자 변환
    df['매출일자'] = pd.to_datetime(df['매출일자'])
    df['연도'] = df['매출일자'].dt.year
    df['월'] = df['매출일자'].dt.month
    if df['공급가액'].dtype == 'object':
        df['공급가액'] = df['공급가액'].str.replace(',', '').astype(float)
    return df

try:
    df = load_data()
    st.title("🏥 제휴사별 핵심 영업 지표 분석 (항목 1~4, 8~10)")
    st.markdown("---")

    # --- [항목 1, 2, 3] 년/월 달성률 및 YoY ---
    st.header("📍 1-3. 제휴사별 매출 현황 및 전년 동기 대비(YoY)")
    
    # 25년 vs 26년 동기(1~2월) 비교 데이터 생성
    target_months = [1, 2]
    df_yoy = df[df['월'].isin(target_months)].groupby(['제휴사', '연도'])['공급가액'].sum().unstack().fillna(0)
    df_yoy.columns = ['25년 동기 실적', '26년 동기 실적']
    df_yoy['성장률(%)'] = ((df_yoy['26년 동기 실적'] - df_yoy['25년 동기 실적']) / df_yoy['25년 동기 실적'] * 100).round(1)
    
    # 거래처 수 추가
    cust_yoy = df[df['월'].isin(target_months)].groupby(['제휴사', '연도'])['거래처명'].nunique().unstack().fillna(0)
    cust_yoy.columns = ['25년 거래처수', '26년 거래처수']
    
    final_summary = pd.concat([df_yoy, cust_yoy], axis=1)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("📊 제휴사별 성과 요약 (VAT 별도)")
        st.table(final_summary.reset_index()) # 복사용 표
    with col2:
        fig_yoy = px.bar(df_yoy.reset_index(), x='제휴사', y='26년 동기 실적', color='성장률(%)', title="26년 제휴사별 매출 및 성장률")
        st.plotly_chart(fig_yoy, use_container_width=True)

    # --- [항목 4] 진료과별 / 지역별 현황 ---
    st.header("📍 4. 지역 및 진료과별 분석 (2026년 누계)")
    col3, col4 = st.columns(2)
    with col3:
        region_df = df[df['연도'] == 2026].groupby('지역')['공급가액'].sum().reset_index()
        fig_reg = px.pie(region_df, values='공급가액', names='지역', hole=0.4, title="지역별 매출 비중")
        st.plotly_chart(fig_reg)
        st.table(region_sales := region_df.sort_values(by='공급가액', ascending=False))
    with col4:
        dept_df = df[df['연도'] == 2026].groupby('진료과')['공급가액'].sum().reset_index()
        fig_dept = px.bar(dept_df, x='진료과', y='공급가액', title="진료과별 매출 규모")
        st.plotly_chart(fig_dept)
        st.table(dept_sales := dept_df.sort_values(by='공급가액', ascending=False))

    # --- [항목 8] 뉴메코(메디톡스) 심층 분석 ---
    st.markdown("---")
    st.header("📍 8. 뉴메코(메디톡스) 집중 분석")
    
    nm_df = df[df['제휴사'] == '뉴메코']
    hugel_cust = set(df[df['제휴사'] == '휴젤']['거래처명'].unique())
    nm_cust = set(nm_df['거래처명'].unique())
    
    intersection = nm_cust.intersection(hugel_cust)
    
    col5, col6 = st.columns(2)
    with col5:
        st.subheader("📋 휴젤 거래처 내 메디톡스 침투율")
        cross_table = pd.DataFrame({
            "구분": ["휴젤+메디톡스 병행", "메디톡스 전용", "휴젤 전용(미침투)"],
            "거래처 수": [len(intersection), len(nm_cust - hugel_cust), len(hugel_cust - nm_cust)]
        })
        st.table(cross_table)
        st.info(f"휴젤 거래처 중 메디톡스 제품 구매 비중: {(len(intersection)/len(hugel_cust)*100):.1f}%")

    with col6:
        st.subheader("📋 코어톡스 대량 구매처 (100개↑)")
        # 단가 33,000원 기준 (단가 컬럼이 있다고 가정)
        vip_df = nm_df[(nm_df['제품명 변환'].str.contains('코어톡스')) & (nm_df['수량'] >= 100)]
        st.write(f"2026년 대량 구매처 수: {vip_df['거래처명'].nunique()}곳")
        st.table(vip_df[['거래처명', '수량', '공급가액']].head(10))

    # --- [항목 9, 10] SKBS 및 로파마 ---
    st.header("📍 9-10. SKBS 및 로파마 상세 현황")
    col7, col8 = st.columns(2)
    with col7:
        st.subheader("SKBS 품목별 실적")
        sk_items = df[df['제휴사'] == 'SKBS'].groupby('제품명 변환')['공급가액'].sum().reset_index()
        st.table(sk_items.sort_values(by='공급가액', ascending=False))
    with col8:
        st.subheader("로파마 아카리작스 스위칭 현황")
        akari_df = df[(df['제휴사'] == '로파마') & (df['제품명 변환'].str.contains('아카리작스'))]
        st.write(f"아카리작스 총 매출: {akari_df['공급가액'].sum():,.0f}원")
        st.table(akari_df.groupby('거래처명')['공급가액'].sum().reset_index().head(10))

except Exception as e:
    st.error(f"데이터 분석 중 오류 발생: {e}")
