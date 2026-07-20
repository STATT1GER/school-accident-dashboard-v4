from __future__ import annotations

import streamlit as st

from components.cards import insight_card, kpi_card, path_card, path_focus_card, risk_row
from components.charts import risk_gauge, time_profile
from components.layout import footer, init_page, page_header, section_header
from components.sankey import top_paths
from utils.color import PLOT_CONFIG
from utils.helper import mode_or
from utils.loader import load_sample_data

init_page("오늘의 학교 안전상황", "🛡️")
df = load_sample_data()

paths = top_paths(df, 8)
peak_time = mode_or(df, "사고시간_정리")
hot_place = mode_or(df, "사고장소_정리")
peak_share = float(df["사고시간_정리"].value_counts(normalize=True).iloc[0])
hot_share = float(df["사고장소_정리"].value_counts(normalize=True).iloc[0])
top_path_share = float(paths.iloc[0]["비율"]) if not paths.empty else 0.0
risk_score = min(96, max(45, round(45 + peak_share * 80 + hot_share * 60 + top_path_share * 100)))

page_header(
    "TODAY'S SCHOOL SAFETY",
    "오늘의 학교 안전상황",
    "특정 미래 날짜를 예측하지 않고, 합성 패턴에서 반복되는 사고경로와 상대 위험도를 현재 운영 관점으로 요약합니다.",
    "PATH-FIRST VIEW",
)

c1, c2, c3, c4 = st.columns(4, gap="medium")
with c1:
    kpi_card("상대 위험도", f"{risk_score}", "관찰 필요", "orange", "반복 신호의 집중도를 0~100으로 환산")
with c2:
    kpi_card("핵심 위험시간", peak_time, "우선 관찰", "orange", "가장 반복되는 일과 구간")
with c3:
    kpi_card("핵심 위험장소", hot_place, f"{hot_share:.1%}", "blue", "공간별 합성 신호 비중 1위")
with c4:
    kpi_card("대표 경로 비중", f"{top_path_share:.1%}", "반복 경로", "purple", "동일 4단계 경로의 전체 비중")

section_header("오늘의 핵심 사고경로", "가장 먼저 확인해야 할 시간 → 장소 → 활동 → 사고형태의 반복 흐름입니다.")
left, right = st.columns([1.42, 0.58], gap="large")
with left:
    if not paths.empty:
        first = paths.iloc[0]
        path_focus_card(first["사고경로"], int(first["사고건수"]), float(first["비율"]))
    else:
        st.info("표시할 사고경로가 없습니다.")
with right:
    st.plotly_chart(risk_gauge(risk_score), use_container_width=True, config=PLOT_CONFIG)
    st.markdown("<div class='state-pill watch'>경로가 반복되는 구간을 우선 관찰하세요</div>", unsafe_allow_html=True)

section_header("반복 사고경로 TOP 3", "위험장소 순위보다 먼저, 실제 개입 시나리오로 연결할 수 있는 경로를 제시합니다.")
for idx, row in paths.head(3).iterrows():
    path_card(row["사고경로"], int(row["사고건수"]), float(row["비율"]), idx + 1)

left, right = st.columns([1.35, 0.65], gap="large")
with left:
    section_header("학교 일과 상대 위험 흐름", "가장 높은 구간을 100으로 두고 일과별 상대 위험도를 표시합니다.")
    st.plotly_chart(time_profile(df), use_container_width=True, config=PLOT_CONFIG)
with right:
    section_header("즉시 확인할 운영 지점")
    insight_card(f"{peak_time} 전후 관찰", "사고가 집중되는 구간 전후에 복도·계단과 활동공간의 교사 관찰 위치를 먼저 확인합니다.", "TIME WINDOW", "orange")
    insight_card(f"{hot_place} 동선 분리", "진입과 이탈이 겹치는 지점을 찾아 이동 방향과 대기 위치를 분리하는 운영안을 검토합니다.", "SPACE ACTION", "blue")

section_header("보조 위험장소 우선순위", "사고경로를 해석한 뒤 공간 점검 순서를 보조적으로 확인합니다.")
place_counts = df["사고장소_정리"].value_counts().head(4)
for rank, (name, count) in enumerate(place_counts.items(), 1):
    risk_row(rank, name, int(count), count / len(df), "orange" if rank == 1 else "blue")

footer()
