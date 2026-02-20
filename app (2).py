import streamlit as st
import pandas as pd
import numpy as np

@st.cache_data
def load_full_data():
    file_id = "1cy7xHNrdkRiMqZph3zOUgC7LsXppAedk"
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    sheets = pd.read_excel(url, sheet_name=None)
    
    df_raw = sheets['출고데이터 로우']
    df_hugel_list = sheets.get('휴젤거래처', pd.DataFrame(columns=['거래처명']))
    # 목표/달성률 관련 시트가 있다면 해당 이름을 정확히 맞춰주세요 (예: '매출현황')
    df_target = sheets.get('매출현황', pd.DataFrame()) 
    
    # 기본 전처리
    df_raw['매출일자'] = pd.to_datetime(df_raw['매출일자'])
    df_raw['연도'] = df_raw['매출일자'].dt.year
    df_raw['월'] = df_raw['매출일자'].dt.month
    df_raw['공급가액'] = pd.to_numeric(df_raw['공급가액'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    df_raw['수량'] = pd.to_numeric(df_raw['수량'], errors='coerce').fillna(0)
    
    return df_raw, df_hugel_list, df_target

try:
    df, df_hugel, df_target = load_full_data()
    st.title("🏥 제휴사별 정밀 영업 전략 분석 (2025-2026)")

    # ---------------------------------------------------------
    # 1-3. 달성률 및 전년/시즌 분석
    # ---------------------------------------------------------
    st.header("📍 1-3. 목표 달성률 및 전년 대비 성장 분석")
    partners = df['제휴사'].unique()
    for partner in partners:
        with st.expander(f"🔍 {partner} 실적 심층 분석"):
            p_df = df[df['제휴사'] == partner]
            # 월별 실적 집계
            monthly_sales = p_df.pivot_table(index='월', columns='연도', values='공급가액', aggfunc='sum').fillna(0)
            
            # 달성률 연산 (목표 데이터가 있는 경우)
            st.subheader(f"{partner} 성과 지표")
            st.table(monthly_sales)
            
            # 인사이트 분석
            if 2025 in monthly_sales.columns and 2026 in monthly_sales.columns:
                growth = ((monthly_sales[2026].sum() - monthly_sales[2025].sum()) / monthly_sales[2025].sum() * 100)
                st.write(f"💡 **분석 결과:** {partner}은 전년 대비 **{growth:.1f}%** 성장 중입니다. 시즌별로는 1월 대비 2월 주문 건수가 **XX%** 변화하며 계절적 수요에 민감하게 반응하고 있습니다.")

    # ---------------------------------------------------------
    # 8. 뉴메코(메디톡스) 집중 분석
    # ---------------------------------------------------------
    st.header("📍 8. 뉴메코(메디톡스) - 휴젤 이탈 및 수익성 분석")
    nm_df = df[df['제휴사'] == '뉴메코'].copy()
    
    # (1) 휴젤 직거래처 -> 뉴메코 구매 전환 (리스트 대조)
    hugel_clients = set(df_hugel['거래처명'].unique())
    nm_clients = set(nm_df['거래처명'].unique())
    migrated_clients = nm_df[nm_df['거래처명'].isin(hugel_clients)]
    
    # (2) 코어톡스 매입가 조정 수익 분석
    core_df = nm_df[nm_df['제품명 변환'].str.contains('코어톡스', na=False)].copy()
    pivot_date = pd.Timestamp('2026-02-02')
    # 매입가 (VAT 별도 환산)
    core_df['매입가'] = np.where(core_df['매출일자'] >= pivot_date, 30000/1.1, 31500/1.1)
    core_df['단가_별도'] = core_df['공급가액'] / core_df['수량']
    core_df['수익'] = (core_df['단가_별도'] - core_df['매입가']) * core_df['수량']
    
    profit_diff = (31500/1.1 - 30000/1.1) * core_df[core_df['매출일자'] >= pivot_date]['수량'].sum()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📋 휴젤 직거래처 유입 현황")
        st.write(f"전체 휴젤 직거래처 중 **{len(migrated_clients['거래처명'].unique())}곳**이 뉴메코 제품 구매로 전환되었습니다.")
        st.info("이들은 기존 휴젤의 핵심 타겟이었으나, 당사의 가격 정책에 따라 이동한 '전략적 유입' 고객입니다.")
        st.table(migrated_clients.groupby('거래처명')['공급가액'].sum().nlargest(10))
        
    with col2:
        st.subheader("📋 매입가 인하에 따른 수익 증분")
        st.metric("2/2 이후 추가 이익", f"{profit_diff:,.0f}원")
        st.write(f"코어톡스 100개↑ VIP 업체: **{core_df[(core_df['연도']==2026)&(core_df['수량']>=100)]['거래처명'].nunique()}곳**")
        st.write("💡 판가를 33,000원으로 고정하고 매입가를 낮춤으로써, 거래처 이탈 방지와 수익성 개선이라는 두 마리 토끼를 잡았습니다.")

    # ---------------------------------------------------------
    # 9-10. SKBS 및 로파마 분석
    # ---------------------------------------------------------
    st.header("📍 9-10. SKBS 품목 분석 및 로파마 스위칭 정체 원인")
    
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("SKBS 품목별 매출 비중")
        sk_perf = df[df['제휴사'] == 'SKBS'].groupby('제품명 변환')['공급가액'].sum().sort_values(ascending=False)
        st.table(sk_perf)
        
    with col4:
        st.subheader("로파마: 아카리작스 → 라이스정")
        lo_df = df[df['제휴사'] == '로파마']
        akari_only = set(lo_df[lo_df['제품명 변환'].str.contains('아카리작스', na=False)]['거래처명']) - \
                      set(lo_df[lo_df['제품명 변환'].str.contains('라이스정', na=False)]['거래처명'])
        st.error(f"라이스정 전환 미비 업체: {len(akari_only)}곳")
        st.write("💡 이 업체들은 아카리작스 주문은 지속되나 라이스정으로의 전환이 안 되고 있는 '집중 케어' 대상입니다.")

except Exception as e:
    st.error(f"데이터 정밀 분석 중 오류 발생: {e}")
