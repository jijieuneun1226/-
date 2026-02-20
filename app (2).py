import streamlit as st
import pandas as pd

# 데이터 로드 (공유해주신 구글 시트 기반)
def load_data():
    # 실제 연동 시 구글 시트 API 또는 CSV 다운로드 링크 사용
    df = pd.read_excel('25년_부터_매출.xlsx')
    return df

df = load_data()

# 부가세 제외 계산 (이미 제외되어 있다면 생략 가능)
st.title("🏥 2026년 제휴사별 영업 성과 대시보드")

# 1. 전년 동기 대비 성장률 분석 (25년 1~2월 vs 26년 1~2월)
st.subheader("1. 전년 동기간 대비(YoY) 매출 현황")
# (Pandas 피벗 테이블로 비교표 생성 코드)
st.table(summary_df)

# 2. 뉴메코(메디톡스) 집중 분석 섹션
st.subheader("2. 뉴메코 코어톡스 전략 분석")
col1, col2 = st.columns(2)
with col1:
    st.write("VIP 거래처(100개 이상) 현황")
    # vip_df 로직 계산
    st.dataframe(vip_df)
    
# 3. 상세 인사이트 자동 도출
st.info(f"현재 뉴메코의 대량 구매처는 전년 동기 대비 {growth_rate}% 증가하였습니다.")
