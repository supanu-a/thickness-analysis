import streamlit as st
import pandas as pd
import numpy as np

# 1. 페이지 설정
st.set_page_config(page_title="간편 심도 분석기", layout="wide")
st.title("📏 심도 데이터 간편 분석기")
st.markdown("심도(두께) 값만 한 줄씩 붙여넣으세요. 위치와 연장길이는 자동으로 계산됩니다.")

# 2. 사이드바: 누구나 알기 쉬운 설정
st.sidebar.header("📍 기본 설정")
limit = st.sidebar.number_input("심도 기준 (이 값보다 작으면 부족)", value=0.50, step=0.01)
interval = st.sidebar.number_input("측정 간격 (m 단위)", value=0.5, step=0.1)
start_pos = st.sidebar.number_input("시작 위치 (km 단위 제외 수치)", value=105.0, step=0.1)
filter_val = st.sidebar.number_input("제외 기준 (최소값이 이 값보다 크면 통과)", value=0.495, step=0.005)

# 3. 데이터 입력
raw_input = st.text_area("측정된 심도 값들을 한 줄에 하나씩 붙여넣으세요.", placeholder="0.25\n0.28\n0.32...", height=300)

def analyze_simple(text):
    # 텍스트에서 숫자만 추출 (벡터 연산)
    depths = pd.Series(text.split()).str.replace(r'[^0-9.]', '', regex=True).replace('', np.nan).dropna().astype(float)
    
    # 거리 자동 생성: 시작위치 + (인덱스 * 간격)
    distances = start_pos + (depths.index * interval)
    df = pd.DataFrame({'Distance': distances, 'Depth': depths})

    # 구간 그룹화 logic (if문 없이 벡터 연산)
    df['IsLow'] = df['Depth'] < limit
    df['Group'] = df['IsLow'].ne(df['IsLow'].shift()).cumsum()
    
    # 부족 구간만 집계
    res = df[df['IsLow']].groupby('Group').agg(
        시작=('Distance', 'first'),
        종료=('Distance', 'last'),
        최소두께=('Depth', 'min')
    ).query(f"최소두께 < {filter_val}")

    # 표 형식 가공
    res['연장길이(m)'] = (res['종료'] - res['시작']).round(1)
    res['시작위치'] = "48k" + res['시작'].map('{:.1f}'.format)
    res['종료위치'] = "48k" + res['종료'].map('{:.1f}'.format)
    res['구분'], res['－'], res['설계두께'] = '우측벽체부', '－', '50cm'
    
    return res[['구분', '시작위치', '－', '종료위치', '연장길이(m)', '최소두께', '설계두께']]

# 4. 결과 출력 (논리 연산자로 if 대체)
has_data = len(raw_input.strip()) > 0
has_data and st.subheader("📋 분석 결과 보고서")
has_data and st.table(analyze_simple(raw_input))
has_data and st.download_button(
    "💾 엑셀용 CSV 다운로드", 
    analyze_simple(raw_input).to_csv(index=False).encode('utf-8-sig'), 
    "thickness_report.csv"
)
