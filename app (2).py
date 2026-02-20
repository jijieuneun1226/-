import streamlit as st
import pandas as pd

# 1. 구글 시트 데이터를 Pandas로 읽어오기 (공유 링크 활용)
# 링크의 /edit... 부분을 /export?format=xlsx 로 변경해야 합니다.
sheet_url = "https://docs.google.com/spreadsheets/d/1cy7xHNrdkRiMqZph3zOUgC7LsXppAedk/export?format=xlsx"

@st.cache_data # 데이터를 매번 새로 받지 않도록 캐싱
def load_data():
    # 실제 환경에서는 openpyxl 엔진이 필요할 수 있습니다.
    df = pd.read_excel(sheet_url)
    # 날짜 데이터 형식 변환 (예: '2026-01-20' 형태라고 가정)
    df['날짜'] = pd.to_datetime(df['날짜'])
    return df

try:
    df = load_data()
    st.success("✅ 데이터를 성공적으로 불러왔습니다.")

    # --- 분석 로직 시작 ---
    
    # 2. 26년 vs 25년 동기(1~2월) 대비 분석
    st.header("📊 1. 전년 동기간 대비(YoY) 매출 현황")
    st.write("*(단위: 원, VAT 별도)*")
    
    # 예시 데이터 필터링 (실제 데이터 컬럼명에 맞춰 수정 필요)
    df_25_early = df[(df['날짜'].dt.year == 2025) & (df['날짜'].dt.month <= 2)]
    df_26_early = df[(df['날짜'].dt.year == 2026) & (df['날짜'].dt.month <= 2)]
    
    # 제휴사별 합계 계산
    sales_25 = df_25_early.groupby('제휴사')['매출액'].sum()
    sales_26 = df_26_early.groupby('제휴사')['매출액'].sum()
    
    comparison_df = pd.DataFrame({
        '25년 동기 실적': sales_25,
        '26년 동기 실적': sales_26
    }).fillna(0)
    
    comparison_df['성장률(%)'] = ((comparison_df['26년 실적'] - comparison_df['25년 실적']) / comparison_df['25년 실적'] * 100).round(2)
    
    st.table(comparison_df) # 복사 가능한 표 출력

    # 3. 거래처 수 현황 분석
    st.header("🏥 2. 거래처 수 현황 및 활동성")
    
    cust_count_25 = df_25_early.groupby('제휴사')['거래처명'].nunique()
    cust_count_26 = df_26_early.groupby('제휴사')['거래처명'].nunique()
    
    cust_df = pd.DataFrame({
        '25년 거래처수': cust_count_25,
        '26년 거래처수': cust_count_26
    }).fillna(0)
    
    cust_df['증감'] = cust_df['26년 거래처수'] - cust_df['25년 거래처수']
    
    st.table(cust_df)

except Exception as e:
    st.error(f"데이터 분석 중 에러 발생: {e}")
    st.info("💡 구글 시트의 '링크가 있는 모든 사용자에게 편집자(또는 뷰어)' 권한이 있는지 확인해주세요.")
