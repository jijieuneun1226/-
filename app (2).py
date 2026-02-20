import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 데이터 로드 설정
st.set_page_config(layout="wide", page_title="영업 분석 대시보드")

@st.cache_data
def load_data():
    # 공유해주신 파일 ID를 활용한 export 링크
    file_id = "1cy7xHNrdkRiMqZph3zOUgC7LsXppAedk"
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    # '출고데이터 로우' 시트 읽기
    df = pd.read_excel(url, sheet_name='출고데이터 로우')
    
    # 전처리: 날짜 변환 및 부가세 제외 금액(공급가액) 확인
    df['매출일자'] = pd.to_datetime(df['매출일자'])
    df['연도'] = df['매출일자'].dt.year
    df['월'] = df['매출일자'].dt.month
    # '공급가액' 컬럼의 콤마 제거 및 숫자 변환
    if df['공급가액'].dtype == 'object':
        df['공급가액'] = df['공급가액'].str.replace(',', '').astype(float)
    return df

try:
    df = load_data()
    st.title("📊 제휴사별 영업 성과 분석 대시보드 (2025-2026)")

    # 분석 기간 설정 (26년 현재 데이터가 있다면 26년 기준, 없다면 25년 비교)
    curr_year = 2026
    prev_year = 2025
    
    # --- [1, 2, 3번] 제휴사별 달성률 및 YoY 현황 ---
    st.header("1. 제휴사별 매출 및 전년 동기 대비(YoY) 현황")
    
    # 전년 동기(1~2월) vs 올해 동기(1~2월) 매출 합산
    mask_25 = (df['연도'] == prev_year) & (df['월'] <= 2)
    mask_26 = (df['연도'] == curr_year) & (df['월'] <= 2)
    
    sales_yoy = df[mask_25 | mask_26].groupby(['연도', '제휴사'])['공급가액'].sum().unstack(level=0).fillna(0)
    sales_yoy.columns = ['25년 동기 실적', '26년 동기 실적']
    sales_yoy['성장률(%)'] = ((sales_yoy['26년 동기 실적'] - sales_yoy['25년 동기 실적']) / sales_yoy['25년 동기 실적'] * 100).round(1)
    
    # 거래처 수 현황 추가
    cust_yoy = df[mask_25 | mask_26].groupby(['연도', '제휴사'])['거래처명'].nunique().unstack(level=0).fillna(0)
    cust_yoy.columns = ['25년 거래처수', '26년 거래처수']
    
    summary_table = pd.concat([sales_yoy, cust_yoy], axis=1)
    st.table(summary_table.reset_index()) # 복사 가능한 표

    # --- [4번] 진료과별 / 지역별 현황 ---
    st.header("2. 지역 및 진료과별 매출 분포")
    col1, col2 = st.columns(2)
    with col1:
        region_df = df[df['연도'] == curr_year].groupby('지역')['공급가액'].sum().reset_index()
        fig_reg = px.pie(region_df, values='공급가액', names='지역', title="지역별 매출 비중")
        st.plotly_chart(fig_reg)
    with col2:
        dept_df = df[df['연도'] == curr_year].groupby('진료과')['공급가액'].sum().reset_index()
        fig_dept = px.bar(dept_df, x='진료과', y='공급가액', title="진료과별 매출 현황")
        st.plotly_chart(fig_dept)

    # --- [8번] 뉴메코(메디톡스) 집중 분석 ---
    st.header("3. 뉴메코(메디톡스) 전략 분석")
    nm_df = df[df['제휴사'] == '뉴메코']
    hugel_clients = set(df[df['제휴사'] == '휴젤']['거래처명'].unique())
    nm_clients = set(nm_df['거래처명'].unique())
    
    # 휴젤 거래처 중 메디톡스 구매 여부
    intersection = nm_clients.intersection(hugel_clients)
    
    st.subheader("📍 휴젤 거래처 침투 및 코어톡스 현황")
    col3, col4 = st.columns(2)
    with col3:
        cross_data = {
            "구분": ["휴젤+메디톡스 병행", "메디톡스 전용", "휴젤 전용(미침투)"],
            "거래처 수": [len(intersection), len(nm_clients - hugel_clients), len(hugel_clients - nm_clients)]
        }
        st.table(pd.DataFrame(cross_data))
    with col4:
        # 코어톡스 100개 이상 구매처 (판가 33,000원 기준)
        core_vip = nm_df[(nm_df['제품명 변환'].str.contains('코어톡스')) & (nm_df['수량'] >= 100)]
        st.write("코어톡스 대량 구매처(100개↑) 리스트")
        st.dataframe(core_vip[['거래처명', '수량', '공급가액']].drop_duplicates())

    # --- [9, 10번] SKBS 및 로파마 분석 ---
    st.header("4. SKBS 및 로파마 상세 현황")
    col5, col6 = st.columns(2)
    with col5:
        st.subheader("SKBS 품목별 매출 비중")
        sk_items = df[df['제휴사'] == 'SKBS'].groupby('제품명 변환')['공급가액'].sum().reset_index()
        st.table(sk_items.sort_values(by='공급가액', ascending=False).head(10))
    with col6:
        st.subheader("로파마 아카리작스 분석")
        lo_df = df[(df['제휴사'] == '로파마') & (df['제품명 변환'].str.contains('아카리작스'))]
        st.write(f"아카리작스 총 매출: {lo_df['공급가액'].sum():,.0f}원")
        st.info("인사이트: 기존 거래처의 스위칭 정체 원인 파악 필요 (강남권 피부과 중심)")

except Exception as e:
    st.error(f"데이터 처리 중 오류 발생: {e}")
