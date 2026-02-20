import streamlit as st
import pandas as pd
import numpy as np

@st.cache_data
def load_all_sheets():
    file_id = "1cy7xHNrdkRiMqZph3zOUgC7LsXppAedk"
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    sheets = pd.read_excel(url, sheet_name=None)
    
    # 1. 시트별 데이터 로드
    df_raw = sheets['출고데이터 로우']
    df_hugel_ref = sheets.get('휴젤거래처', pd.DataFrame(columns=['거래처명']))
    
    # 2. 전처리
    df_raw['매출일자'] = pd.to_datetime(df_raw['매출일자'])
    df_raw['연도'] = df_raw['매출일자'].dt.year
    df_raw['공급가액'] = pd.to_numeric(df_raw['공급가액'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    df_raw['수량'] = pd.to_numeric(df_raw['수량'], errors='coerce').fillna(0)
    
    return df_raw, df_hugel_ref

try:
    df, df_hugel_list = load_all_sheets()
    st.title("🏥 제휴사별 정밀 전략 분석 보고서")

    # ---------------------------------------------------------
    # 8. 뉴메코(메디톡스) - 휴젤 이탈 및 수익성 분석
    # ---------------------------------------------------------
    st.header("📍 8. 뉴메코(메디톡스) 집중 분석")
    nm_df = df[df['제휴사'] == '뉴메코'].copy()
    
    # [분석 A] 휴젤 직거래처 이탈 및 뉴메코 유입 대조
    hugel_list = set(df_hugel_list['거래처명'].unique())
    # 뉴메코를 구매한 업체 중 휴젤 직거래처 리스트에 포함된 업체 추출
    migrated = nm_df[nm_df['거래처명'].isin(hugel_list)]
    
    # [분석 B] 코어톡스 매입가 변동 수익성 (2/2 기준 31,500 -> 30,000)
    core_df = nm_df[nm_df['제품명 변환'].str.contains('코어톡스', na=False)].copy()
    
    # 부가세 제외 공급가 환산 (31,500/1.1=28,636, 30,000/1.1=27,273)
    def calc_cost(date):
        return 27273 if date >= pd.Timestamp('2026-02-02') else 28636

    core_df['매입단가_별도'] = core_df['매출일자'].apply(calc_cost)
    core_df['판매단가_별도'] = core_df['공급가액'] / core_df['수량']
    core_df['수익'] = (core_df['판매단가_별도'] - core_df['매입단가_별도']) * core_df['수량']
    
    # [분석 C] 100개 이상 VIP (판매가 33,000원 기준)
    vip_count = core_df[(core_df['연도'] == 2026) & (core_df['수량'] >= 100)]['거래처명'].nunique()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📋 휴젤 직거래처 유입 현황")
        st.metric("리스트 내 전환 업체수", f"{migrated['거래처명'].nunique()}곳")
        st.write("해당 업체 뉴메코 총 매출:", f"{migrated['공급가액'].sum():,.0f}원")
        st.caption("※ 휴젤 직거래처 리스트와 뉴메코 주문 데이터를 1:1 매칭한 결과입니다.")
        
    with col2:
        st.subheader("📋 매입가 인하 수익 및 VIP")
        added_profit = (28636 - 27273) * core_df[core_df['매출일자'] >= pd.Timestamp('2026-02-02')]['수량'].sum()
        st.metric("2/2 이후 매입가 인하 이익분", f"{added_profit:,.0f}원")
        st.write(f"26년 코어톡스 100개↑ VIP:", f"{vip_count}곳")

    # ---------------------------------------------------------
    # 10. 로파마: 아카리작스 → 라이스정 스위칭 분석
    # ---------------------------------------------------------
    st.header("📍 10. 로파마 품목 스위칭 분석")
    lo_df = df[df['제휴사'] == '로파마']
    
    # 아카리작스 구매 이력이 있는 거래처 리스트
    akari_users = set(lo_df[lo_df['제품명 변환'].str.contains('아카리작스', na=False)]['거래처명'].unique())
    # 라이스정 구매 이력이 있는 거래처 리스트
    rice_users = set(lo_df[lo_df['제품명 변환'].str.contains('라이스정', na=False)]['거래처명'].unique())
    
    # 스위칭(병행) 성공 업체 vs 미전환 업체
    success_switch = akari_users.intersection(rice_users)
    failure_switch = akari_users - rice_users
    
    st.subheader("아카리작스 → 라이스정 전환 현황")
    c1, c2, c3 = st.columns(3)
    c1.metric("아카리작스 기존 고객", f"{len(akari_users)}곳")
    c2.metric("라이스정 전환/병행", f"{len(success_switch)}곳", f"{len(success_switch)/len(akari_users)*100:.1f}%")
    c3.metric("스위칭 미비 업체", f"{len(failure_switch)}곳", delta_color="inverse")
    
    if failure_switch:
        st.write("⚠️ **라이스정 미구매 업체 (영업 집중 타겟):**")
        st.table(list(failure_switch)[:10]) # 상위 10곳 노출

except Exception as e:
    st.error(f"정밀 분석 중 오류 발생: {e}")
