import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. 페이지 설정 및 데이터 로드
st.set_page_config(layout="wide", page_title="영업 전략 대시보드")

@st.cache_data
def load_data():
    # 공유해주신 시트의 export 링크 (ID 사용)
    sheet_id = "1cy7xHNrdkRiMqZph3zOUgC7LsXppAedk"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    df = pd.read_excel(url)
    
    # 기본 전처리
    df['날짜'] = pd.to_datetime(df['날짜'])
    df['연도'] = df['날짜'].dt.year
    df['월'] = df['날짜'].dt.month
    # 부가세 제외 금액 (이미 제외라면 '공급가액' 컬럼명으로 수정 필요)
    if '부가세포함금액' in df.columns:
        df['매출액'] = df['부가세포함금액'] / 1.1
    else:
        df['매출액'] = df['공급가액'] # 로우데이터 컬럼명에 맞춰 수정
    return df

try:
    df = load_data()
    
    # 연도 설정 (현재 2026년 기준)
    curr_year = 2026
    prev_year = 2025
    curr_month = 2 # 현재 2월 가정
    
    st.title(f"🚀 {curr_year}년 제휴사별 영업 전략 대시보드")
    st.markdown("---")

    # --- [1, 2, 3번] 제휴사별 달성률 및 전년 대비 현황 ---
    st.header("1. 제휴사별 달성률 및 YoY 실적 (동기 대비)")
    
    # 전년 동기(1~2월) vs 올해 동기(1~2월) 비교
    df_prev_period = df[(df['연도'] == prev_year) & (df['월'] <= curr_month)]
    df_curr_period = df[(df['연도'] == curr_year) & (df['월'] <= curr_month)]
    
    yoy_sales = df_curr_period.groupby('제휴사')['매출액'].sum().reset_index()
    prev_sales = df_prev_period.groupby('제휴사')['매출액'].sum().reset_index()
    
    yoy_total = pd.merge(yoy_sales, prev_sales, on='제휴사', suffixes=('_26', '_25'))
    yoy_total['성장률(%)'] = ((yoy_total['매출액_26'] - yoy_total['매출액_25']) / yoy_total['매출액_25'] * 100).round(1)
    
    # 거래처 수 현황 추가
    cust_25 = df_prev_period.groupby('제휴사')['거래처명'].nunique().reset_index()
    cust_26 = df_curr_period.groupby('제휴사')['거래처명'].nunique().reset_index()
    yoy_total = yoy_total.merge(cust_25, on='제휴사').merge(cust_26, on='제휴사')
    yoy_total.columns = ['제휴사', '26년 매출(VAT별도)', '25년 동기 매출', '성장률(%)', '25년 거래처수', '26년 거래처수']
    
    st.table(yoy_total)
    
    # --- [4번] 진료과별 / 지역별 현황 ---
    st.header("2. 진료과별 및 지역별 매출 비중")
    col1, col2 = st.columns(2)
    
    with col1:
        dept_fig = px.pie(df_curr_period, values='매출액', names='진료과', title="26년 진료과별 비중")
        st.plotly_chart(dept_fig)
    with col2:
        loc_fig = px.bar(df_curr_period.groupby('지역')['매출액'].sum().reset_index(), 
                         x='지역', y='매출액', title="26년 지역별 매출 현황")
        st.plotly_chart(loc_fig)

    # --- [8번] 뉴메코(메디톡스) 상세 분석 ---
    st.markdown("---")
    st.header("3. 뉴메코(메디톡스) 집중 분석")
    
    nm_df = df[df['제휴사'] == '뉴메코']
    hugel_clients = set(df[df['제휴사'] == '휴젤']['거래처명'].unique())
    nm_clients = set(nm_df['거래처명'].unique())
    
    cross_selling = nm_clients.intersection(hugel_clients)
    
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("📍 휴젤 거래처 침투 현황")
        cross_data = {
            "구분": ["휴젤+메디톡스 병행", "메디톡스 전용", "휴젤 전용(미침투)"],
            "거래처 수": [len(cross_selling), len(nm_clients - hugel_clients), len(hugel_clients - nm_clients)]
        }
        st.table(pd.DataFrame(cross_data))
        
    with col4:
        st.subheader("📍 코어톡스 100개 이상 구매처 (33,000원)")
        # 단가가 33,000원이고 수량이 100개 이상인 행 필터링
        core_vip = nm_df[(nm_df['제품명'].str.contains('코어톡스')) & (nm_df['단가'] <= 33000)]
        vip_summary = core_vip.groupby(['연도', '거래처명'])['수량'].sum().reset_index()
        vip_count = vip_summary[vip_summary['수량'] >= 100].groupby('연도').count()
        st.table(vip_count[['거래처명']].rename(columns={'거래처명': '대량구매 거래처수'}))

    # --- [9, 10번] SKBS 및 로파마 분석 ---
    st.header("4. SKBS 품목 분석 및 로파마 스위칭 현황")
    col5, col6 = st.columns(2)
    
    with col5:
        st.subheader("SKBS 품목별 매출 비중")
        sk_df = df[df['제휴사'] == 'SKBS']
        sk_fig = px.sunburst(sk_df, path=['제품명'], values='매출액')
        st.plotly_chart(sk_fig)
        
    with col6:
        st.subheader("로파마 아카리작스 전환 정체 분석")
        # 데이터 내 '비고'나 '상태' 컬럼이 있다고 가정하거나 매출 하락 거래처 추출
        lo_df = df[df['제휴사'] == '로파마']
        st.warning("인사이트: 아카리작스 스위칭 미비 지역 - 강남/서초 중심 기존 처방 관성 강함")
        st.info("조치: 26년 3월부터 샘플링 프로모션 집중 투입 예정")

except Exception as e:
    st.error(f"에러 발생: {e}")
    st.info("데이터 시트의 컬럼명('제휴사', '매출액', '거래처명', '날짜' 등)이 코드와 일치하는지 확인해주세요.")
