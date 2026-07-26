from __future__ import annotations

import streamlit as st

from components.cards import insight_card
from components.layout import footer, init_page, page_header, section_header
from utils.helper import asset_path
from utils.loader import load_sample_data

init_page("학교안전 대시보드", "🛡️")
df = load_sample_data()

page_header(
    "SCHOOL SAFETY COMMAND CENTER",
    "학교의 하루를 더 안전하게.",
    "사고 건수를 나열하기보다 반복되는 사고경로를 빠르게 읽고, 교사가 먼저 개입할 지점을 찾는 학교안전 관제 UI입니다.",
    "UI PROTOTYPE · V4",
)

left, right = st.columns([0.76, 1.24], gap="large")
with left:
    st.markdown(
        """
        <div class="hero-panel dark compact">
            <div class="hero-kicker">2026 SCHOOL SAFETY</div>
            <div class="hero-title">단순 사고 건수 비교가 아닌,<br> 사고가 발생하는 경로의 흐름을 탐색합니다.</div>
            <div class="hero-copy">사고 반복 경로를 중심으로 위험 신호와 개입 지점을 보여줍니다.</div>
            <div class="hero-stat-row">
                <div><b>4단계</b><span>핵심 사고경로</span></div>
                <div><b>2개</b><span>관제 화면</span></div>
                <div><b>100%</b><span>합성 시연 데이터</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with right:
    st.image(str(asset_path("school_map.png")), use_container_width=True)
    st.markdown(
        "<div class='map-preview-caption'><b>가상학교 1층 안전지도</b><span>학교지도 화면에서 동일 배치도 위에 상대 사고집중도 히트맵을 겹쳐 확인합니다.</span></div>",
        unsafe_allow_html=True,
    )

section_header("대시보드 구성", "공간적 개입 우선순위 확인 → 사고 반복 경로 분석 → 추천 개입 지점 도출 순서로 설계했습니다.")
c1, c2 = st.columns(2, gap="large")
with c1:
    insight_card("학교지도", "가상 학교 1층 배치도 위에 시간대별 상대 사고집중도를 표시하여 공간적 개입 우선순위를 확인합니다.", "01 · MAP", "green")
    st.page_link("pages/1_학교지도.py", label="학교지도 열기 →")
with c2:
    insight_card("사고분석", "전체·저학년·고학년의 사고 반복 경로를 비교하고, 우선 개입이 필요한 시간과 장소를 확인합니다.", "02 · PATH ANALYTICS", "orange")
    st.page_link("pages/2_사고분석.py", label="사고분석 열기 →")

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
section_header("데이터 사용 원칙")
st.markdown(
    """
    <div class="principle-grid">
        <div><b>실제 원자료 미포함</b><span>학교명, 학생정보, 실제 사고ID와 개별 사고 기록을 포함하지 않습니다.</span></div>
        <div><b>경로 중심 합성 패턴</b><span>시간→장소→활동→형태의 연결 관계를 보여주기 위한 합성 예시 데이터만 사용합니다.</span></div>
        <div><b>예측모델이 아닌 관제 UI</b><span>특정 미래 날짜를 예측하지 않으며 반복 사고경로와 상대 사고집중도를 전달하는 시연 화면입니다.</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)
footer()
