import streamlit as st
import pandas as pd

@st.cache_data
def load_and_analyze():
    file_id = "1cy7xHNrdkRiMqZph3zOUgC7LsXppAedk"
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    sheets = pd.read_excel(url, sheet_name=None)
    
    df_raw = sheets['출고데이터 로우']
    df_hugel = sheets.get('휴젤거래처', pd.DataFrame(columns=['거래처명']))
    
    # 데이터 전처리
    df_raw['매출일자'] = pd.to_datetime(df_raw['매출일자'])
    df_raw['연도'] = df_raw['매출일자'].dt.year
    df_raw['월'] = df_raw['매출일자'].dt.month
    df_raw['공급가액'] = pd.to_numeric(df_raw['공급가액'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    df_raw['수량'] = pd.to_numeric(df_raw['수량'], errors='coerce').fillna(0)
    
    # 단가 정보가 없을 경우를 대비해 공급가액/수량으로 계산 (VAT 별도)
    df_raw['단가_계산'] = df_raw.apply(lambda x: x['공급가액'] / x['수량'] if x['수량'] > 0 else 0, axis=1)
    
    return df_raw, df_hugel

try:
    df, df_hugel = load_and_analyze()
    st.title("🏥 제휴사별 정밀 실적 분석 (항목 1-4, 8-10)")

    # --- [1-4번] 제휴사별 성과 분석 ---
    st.header("📍 1-4. 제휴사별 통합 실적")
    partners = df['제휴사'].unique()
    for partner in partners:
        with st.expander(f"🏢 {partner} 실적 상세"):
            p_df = df[df['제휴사'] == partner]
            # 달성률 및 YoY 표
            perf = p_df.groupby(['연도', '월'])['공급가액'].sum().unstack(level=0).fillna(0)
            st.table(perf)
            
            c1, c2 = st.columns(2)
            with c1:
                st.write("**지역별 현황**")
                st.table(p_df.groupby('지역')['공급가액'].sum().nlargest(5))
            with c2:
                st.write("**진료과별 현황**")
                st.table(p_df.groupby('진료과')['공급가액'].sum().nlargest(5))

    # --- [8번] 뉴메코(메디톡스) 심층 분석 ---
    st.header("📍 8. 뉴메코(메디톡스) 전략 분석")
    nm_df = df[df['제휴사'] == '뉴메코'].copy()
    
    # 8-1. 휴젤 직거래처 대조 분석
    hugel_list = set(df_hugel['거래처명'].unique())
    nm_buy_hugel = nm_df[nm_df['거래처명'].isin(hugel_list)]
    
    # 8-2. 코어톡스 수익성 (매입가 31500 -> 30000 변동, VAT 포함 기준 주의)
    core_df = nm_df[nm_df['제품명 변환'].str.contains('코어톡스', na=False)].copy()
    
    # 매입가 VAT 별도 환산: 31,500/1.1 = 28,636원 | 30,000/1.1 = 27,273원
    def get_cost(date):
        if date >= pd.Timestamp('2026-02-02'):
            return 30000 / 1.1
        else:
            return 31500 / 1.1

    core_df['매입가_별도'] = core_df['매출일자'].apply(get_cost)
    core_df['개당수익'] = core_df['단가_계산'] - core_df['매입가_별도']
    core_df['총수익'] = core_df['개당수익'] * core_df['수량']

    # 8-3. 100개 이상 VIP (33,000원 판매가 기준)
    vip_25 = core_df[(core_df['연도'] == 2025) & (core_df['수량'] >= 100)]['거래처명'].nunique()
    vip_26 = core_df[(core_df['연도'] == 2026) & (core_df['수량'] >= 100)]['거래처명'].nunique()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📋 타사(휴젤) 거래처 침투")
        st.metric("휴젤 직거래처 중 구매처", f"{nm_buy_hugel['거래처명'].nunique()}곳")
        st.write("침투 거래처 매출 총액:", f"{nm_buy_hugel['공급가액'].sum():,.0f}원")
    with col2:
        st.subheader("📋 코어톡스 이익 및 VIP")
        profit_26 = core_df[core_df['연도'] == 2026]['총수익'].sum()
        st.metric("26년 누적 수익 (추정)", f"{profit_26:,.0f}원")
        st.write(f"100개↑ VIP 업체: 25년({vip_25}곳) → 26년({vip_26}곳)")

    # --- [9, 10번] SKBS 및 로파마 분석 ---
    st.header("📍 9-10. SKBS 및 로파마 상세")
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("SKBS 품목별 특성")
        sk_res = df[df['제휴사'] == 'SKBS'].groupby('제품명 변환')['공급가액'].sum().reset_index()
        st.table(sk_res.sort_values(by='공급가액', ascending=False))
    with col4:
        st.subheader("로파마 스위칭 분석")
        lo_df = df[df['제휴사'] == '로파마']
        akari_users = set(lo_df[lo_df['제품명 변환'].str.contains('아카리작스', na=False)]['거래처명'].unique())
        rice_users = set(lo_df[lo_df['제품명 변환'].str.contains('라이스정', na=False)]['거래처명'].unique())
        
        switched = akari_users.intersection(rice_users)
        st.write(f"아카리작스 사용자: {len(akari_users)}곳")
        st.write(f"라이스정 병행/전환: {len(switched)}곳")
        st.warning(f"미전환 타겟 업체: {len(akari_users - rice_users)}곳")

except Exception as e:
    st.error(f"오류 발생: {e}")
