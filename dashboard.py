import streamlit as st
import json
import os
import time

# 웹 브라우저 탭 이름 및 레이아웃 설정
st.set_page_config(page_title="Bifrost SRE Dashboard", page_icon="🛡️", layout="wide")

st.title("Bifrost 지능형 관제 대시보드")
st.markdown("현재 인프라 상태와 Gemini AI의 분석 리포트를 실시간으로 모니터링합니다.")

def load_data():
    """main.py가 생성한 최신 JSON 데이터를 읽어옵니다."""
    if os.path.exists("incident_data.json"):
        with open("incident_data.json", "r") as f:
            return json.load(f)
    return None

# 데이터 자동 새로고침을 위한 빈 컨테이너 생성
placeholder = st.empty()

# 무한 루프를 돌며 데이터를 주기적으로 화면에 갱신 (스트리밍 효과)
while True:
    data = load_data()
    
    with placeholder.container():
        if data:
            # 상단 상태 요약 패널
            st.subheader(f"최신 위협 알림: {data['alert_name']}")
            
            # 3개의 주요 메트릭을 열(Column)로 나누어 배치
            col1, col2, col3 = st.columns(3)
            col1.metric("타겟 (공격자) IP", data["target_ip"])
            col2.metric("EC2 평균 CPU 사용률", data["cpu_usage"])
            col3.metric("현재 진행 상태", data["status"])
            
            st.divider()
            
            # AI 리포트 및 컨텍스트 데이터 패널
            col_ai, col_context = st.columns([1, 1])
            
            with col_ai:
                st.markdown("### Gemini AI 분석 리포트")
                st.info(data["ai_analysis"])
                
                st.markdown("### 최근 GitHub 배포 이력")
                st.code(data["github_commits"], language="markdown")
                
            with col_context:
                st.markdown("### 시스템 로그 스트리밍 (Loki)")
                st.code(data["loki_logs"], language="bash")
                
            st.caption(f"마지막 데이터 갱신 시각: {data['timestamp']} (KST)")
        else:
            st.warning("수집된 장애/위협 데이터가 없습니다. 모니터링 대기 중...")
            
    # 3초마다 화면을 새로고침
    time.sleep(3)
