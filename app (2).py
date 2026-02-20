import streamlit as st
import pandas as pd
import numpy as np

@st.cache_data
def load_data():
    file_id = "1cy7xHNrdkRiMqZph3zOUgC7LsXppAedk"
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    sheets = pd.read_excel(url, sheet_name=None)
    
    df_raw = sheets['출고데이터 로우']
    df_hugel_list = sheets.get('휴젤거래처', pd.DataFrame(columns=['거래처명']))
    
    # 기본 전처리
    df_raw['매출일자'] = pd.to_datetime(df_raw['매출일자'])
    df_raw['연도'] = df_raw['매출일자'].dt.year
    df_raw['월'] = df_raw['매출일자'].dt.month
    df_raw['공급가액'] = pd.to_numeric(df_raw['공급가액'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    df_raw['수량'] = pd.to_numeric(df_raw['수량'], errors='coerce').fillna(0)
    
    # 단가 계산 (공급가액 / 수량)
    df_raw['단가_VAT별도'] = np.where(df_raw['수량'] > 0, df_raw['공급가액'] / df_raw['수량'], 0)
    
    return df_raw, df_hugel_list

try:
    df, df_hugel = load_data()
    st.title("📊 제휴사 정밀 분석 보고서 (1-4, 8-10번)")

    # --- 1-4. 제휴사별 통합 분석 (구분 분석) ---
    st.header("📍 1-4. 제휴사별 실적 및 지역/과별 분석")
    partners = df['제휴사'].unique()
    for partner in partners:
        with st.expander(f"🏢 {partner} 분석 결과 확인"):
            p_df = df[df['제휴사'] == partner]
            
            # 년/월 매출 현황
            perf = p_df.pivot_table(index='월', columns='연도', values='공급가액', aggfunc='sum').fillna(0)
            st.subheader(f"{partner} 년/월 매출 및 YoY")
            st.table(perf)
            
            # 지역 및 진료과 (4번 항목)
            c1, c2 = st.columns(2)
            with c1:
                st.write("**지역별 순위**")
                st.table(p_df.groupby('지역')['공급가액'].sum().sort_values(ascending=False).head(5))
            with c2:
                st.write("**진료과별 순위**")
                st.table(p_df.groupby('진료과')['공급가액'].sum().sort_values(ascending=False).head(5))

    # --- 8. 뉴메코(메디톡스) 상세 분석 ---
    st.header("📍 8. 뉴메코(메디톡스) 집중 분석")
    nm_df = df[df['제휴사'] == '뉴메코'].copy()
    
    # (1) 휴젤 직거래처 리스트 대조 (휴젤 리스트 병원이 뉴메코를 샀는가)
    hugel_clients = set(df_hugel['거래처명'].unique())
    nm_clients = set(nm_df['거래처명'].unique())
    hugel_to_nm = nm_df[nm_df['거래처명'].isin(hugel_clients)]
    
    # (2) 코어톡스 수익 분석 (매입가 변동 반영: 31,500 -> 30,000 / VAT 포함 주의)
    core_df = nm_df[nm_df['제품명 변환'].str.contains('코어톡스', na=False)].copy()
    
    # 매입가 VAT 별도 환산 (31,500/1.1=28,636, 30,000/1.1=27,273)
    pivot_date = pd.Timestamp('2026-02-02')
    core_df['매입단가_별도'] = np.where(core_df['매출일자'] >= pivot_date, 30000/1.1, 31500/1.1)
    core_df['수익'] = (core_df['단가_VAT별도'] - core_df['매입단가_별도']) * core_df['수량']
    
    # (3) 코어톡스 100개 이상 구매처 (판매가 33,000원)
    vip_25 = core_df[(core_df['연도'] == 2025) & (core_df['수량'] >= 100)]['거래처명'].nunique()
    vip_26 = core_df[(core_df['연도'] == 2026) & (core_df['수량'] >= 100)]['거래처명'].nunique()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📋 타사(휴젤) 고객 침투")
        st.metric("휴젤 리스트 중 뉴메코 구매처", f"{hugel_to_nm['거래처명'].nunique()}곳")
        st.write("침투 거래처 총 매출:", f"{hugel_to_nm['공급가액'].sum():,.0f}원")
    with col2:
        st.subheader("📋 코어톡스 수익 및 VIP")
        st.write(f"2/2 매입가 인하 후 총 수익: **{core_df[core_df['매출일자'] >= pivot_date]['수익'].sum():,.0f}원**")
        st.write(f"100개↑ VIP 업체: 25년({vip_25}곳) → 26년({vip_26}곳)")

    # --- 9. SKBS & 10. 로파마 ---
    st.header("📍 9-10. SKBS 분석 및 로파마 스위칭")
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("SKBS 품목별 매출 및 특성")
        sk_perf = df[df['제휴사'] == 'SKBS'].groupby('제품명 변환')['공급가액'].sum().reset_index()
        st.table(sk_perf.sort_values(by='공급가액', ascending=False))
        
    with col4:
        st.subheader("로파마 아카리작스 -> 라이스정 전환")
        lo_df = df[df['제휴사'] == '로파마']
        akari_users = set(lo_df[lo_df['제품명 변환'].str.contains('아카리작스', na=False)]['거래처명'].unique())
        rice_users = set(lo_df[lo_df['제품명 변환'].str.contains('라이스정', na=False)]['거래처명'].unique())
        
        switched = akari_users.intersection(rice_users)
        st.write(f"아카리작스 구매처: {len(akari_users)}곳")
        st.write(f"라이스정 병행/전환처: {len(switched)}곳")
        st.error(f"미전환(라이스정 미구매) 업체: {len(akari_users - rice_users)}곳")

except Exception as e:
    st.error(f"연산 오류 발생: {e}")
