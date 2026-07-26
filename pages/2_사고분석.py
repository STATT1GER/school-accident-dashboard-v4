from __future__ import annotations

import pandas as pd
import streamlit as st

from components.cards import intervention_card, kpi_card, path_card
from components.charts import category_bar, time_profile, weekday_time_heatmap
from components.filters import analysis_filters, apply_filters
from components.layout import footer, init_page, page_header, section_header
from components.sankey import build_sankey, top_paths
from utils.color import PLACE_COLORS, PLOT_CONFIG
from utils.loader import load_sample_data

init_page("사고분석", "📊")
df = load_sample_data()

page_header(
    "PATH-FIRST ACCIDENT ANALYTICS",
    "사고분석",
    "사고 반복 경로를 첫 화면에 배치하고, 시간·장소·활동·사고형태는 우선 개입 지점을 해석하기 위한 보조 분석으로 제공합니다.",
    "4-STAGE FLOW · V4",
)

filters = analysis_filters(df)
filtered = apply_filters(df, filters)
if filtered.empty:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다. 필터를 조정해주세요.")
    st.stop()

paths = top_paths(filtered, 12)
top_path_share = float(paths.iloc[0]["비율"]) if not paths.empty else 0.0
if not paths.empty:
    top_stages = [part.strip() for part in str(paths.iloc[0]["사고경로"]).split("→")]
else:
    top_stages = ["-", "-", "-", "-"]
while len(top_stages) < 4:
    top_stages.append("-")
peak_time, hot_place = top_stages[0], top_stages[1]

c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi_card("분석 사고 신호", f"{len(filtered):,}건", "필터 적용", "blue")
with c2:
    kpi_card("핵심 위험시간", peak_time, "대표 경로 기준", "orange")
with c3:
    kpi_card("핵심 위험장소", hot_place, "대표 경로 기준", "blue")
with c4:
    kpi_card("대표 사고경로 비중", f"{top_path_share:.1%}", "선택 범위 내 최빈 경로", "purple")

st.info(
    "상대 사고집중도는 선택한 범위에서 사고 건수가 가장 많은 구간을 100으로 환산한 비교지표입니다. "
    "학생 수와 공간 이용량이 반영된 실제 사고확률은 아닙니다."
)

st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
path_tab, time_tab, place_tab, activity_tab = st.tabs(["사고경로", "시간 분석", "장소 분석", "활동·형태"])


def recommendation_for(activity: str, core_time: str, core_place: str) -> str:
    if "이동" in activity or "보행" in activity:
        return f"{core_time}이 시작되기 전 {core_place}의 이동 방향을 안내하고, 계단 입구와 복도 교차지점의 대기를 줄이며 필요 시 교사 관찰 위치를 배치합니다."
    if "놀이" in activity or "휴식" in activity:
        return f"{core_time} 전 {core_place}에서 활동 가능 공간과 이동공간을 분리하고, 학생 간 접촉이 집중되는 구역의 놀이 규칙을 안내합니다."
    if "구기" in activity or "라켓" in activity or "체육" in activity:
        return f"{core_time} 활동 시작 전 {core_place}의 종목별 공간과 출입동선을 분리하고, 동시 이용인원과 장비 사용규칙을 안내합니다."
    if "수업" in activity or "실습" in activity:
        return f"{core_time} 수업 시작 전 {core_place}의 장비와 활동공간을 점검하고, 학생 간 작업 간격과 이동순서를 안내합니다."
    return f"{core_time}이 시작되기 전 {core_place}의 이용인원과 이동동선을 확인하고, 대표 사고경로가 완성되기 전 관찰·안내·공간분리 조치를 배치합니다."


def render_path_scope(scope_df: pd.DataFrame, key_prefix: str, scope_name: str) -> None:
    if scope_df.empty:
        st.info(f"{scope_name} 조건에 해당하는 사고경로가 없습니다.")
        return

    section_header(f"{scope_name} 4단계 사고경로", "사고시간 → 사고장소 → 당시활동 → 사고형태의 연결을 간단히 또는 자세히 확인합니다.")
    st.markdown(
        """
        <div class="stage-strip">
            <span>① 사고시간</span><i>→</i><span>② 사고장소</span><i>→</i><span>③ 당시활동</span><i>→</i><span>④ 사고형태</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    simple_tab, detail_tab = st.tabs(["간단히 보기 · 단계별 상위 5개", "자세히 보기 · 전체 범주"])
    with simple_tab:
        st.caption("각 단계의 상위 5개 범주만 유지하고 나머지는 ‘기타’로 묶어 핵심 흐름을 빠르게 읽습니다.")
        st.plotly_chart(
            build_sankey(
                scope_df,
                min_count=max(5, len(scope_df) // 450),
                top_n_per_stage=5,
                aggregate_other=True,
                height=610,
            ),
            use_container_width=True,
            config=PLOT_CONFIG,
            key=f"{key_prefix}_simple_sankey",
        )
    with detail_tab:
        st.caption("전체 범주를 유지하되 노드를 단계별로 고정 배치하고 긴 글자는 줄바꿈하여 겹침을 줄였습니다.")
        st.plotly_chart(
            build_sankey(
                scope_df,
                min_count=max(2, len(scope_df) // 1400),
                top_n_per_stage=None,
                aggregate_other=False,
                height=720,
            ),
            use_container_width=True,
            config=PLOT_CONFIG,
            key=f"{key_prefix}_detail_sankey",
        )

    scope_paths = top_paths(scope_df, 12)
    left, right = st.columns([1.0, 1.0], gap="large")
    with left:
        section_header("상위 사고경로 TOP 5")
        for idx, row in scope_paths.head(5).iterrows():
            path_card(row["사고경로"], int(row["사고건수"]), float(row["비율"]), idx + 1)
    with right:
        section_header("사고 발생을 줄이기 위한 추천 개입 지점")
        top_row = scope_paths.iloc[0]
        stages = [part.strip() for part in str(top_row["사고경로"]).split("→")]
        while len(stages) < 4:
            stages.append("-")
        core_time, core_place, activity, accident_form = stages[:4]
        intervention_card(
            scope_name=scope_name,
            core_time=core_time,
            core_place=core_place,
            activity=activity,
            accident_form=accident_form,
            recommendation=recommendation_for(activity, core_time, core_place),
            count=int(top_row["사고건수"]),
            share=float(top_row["비율"]),
        )


with path_tab:
    all_grade_tab, low_grade_tab, high_grade_tab = st.tabs(["전체", "저학년", "고학년"])
    with all_grade_tab:
        render_path_scope(filtered, "all_grade", "전체")
    with low_grade_tab:
        render_path_scope(filtered[filtered["학년급"] == "저학년"], "low_grade", "저학년")
    with high_grade_tab:
        render_path_scope(filtered[filtered["학년급"] == "고학년"], "high_grade", "고학년")

with time_tab:
    section_header("시간대별 상대 사고집중도", "가장 많은 일과 구간을 100으로 두어 시간대별 사고 건수를 상대적으로 비교합니다.")
    st.plotly_chart(time_profile(filtered), use_container_width=True, config=PLOT_CONFIG, key="analysis_time_profile")
    section_header("요일 × 사고시간", "요일과 일과 구간의 결합 사고집중도를 넓은 화면으로 제시합니다.")
    st.plotly_chart(weekday_time_heatmap(filtered), use_container_width=True, config=PLOT_CONFIG, key="analysis_weekday_heatmap")

with place_tab:
    section_header("사고장소 분포", "사고장소별 사고 건수를 전체 너비로 비교합니다.")
    st.plotly_chart(
        category_bar(filtered, "사고장소_정리", 10, 460, PLACE_COLORS),
        use_container_width=True,
        config=PLOT_CONFIG,
        key="place_bar",
    )

    section_header("장소별 상세표")
    place_table = filtered.groupby("사고장소_정리", observed=False).agg(
        사고건수=("사고ID", "size"),
        대표활동=("사고당시활동_정리", lambda x: x.mode().iloc[0] if not x.mode().empty else "-"),
        대표사고형태=("사고형태_정리", lambda x: x.mode().iloc[0] if not x.mode().empty else "-"),
    ).sort_values("사고건수", ascending=False).reset_index()
    place_table["비율"] = place_table["사고건수"] / len(filtered)
    st.dataframe(
        place_table.style.format({"사고건수": "{:,}", "비율": "{:.1%}"}),
        use_container_width=True,
        hide_index=True,
    )

with activity_tab:
    section_header("장소를 기준으로 사고 당시 활동 탐색", "장소를 선택하면 해당 공간에서 반복되는 활동을 먼저 보여줍니다.")
    place_options = ["전체 장소"] + sorted(filtered["사고장소_정리"].dropna().unique().tolist())
    selected_place = st.selectbox("사고장소 선택", place_options, key="activity_place")
    activity_df = filtered if selected_place == "전체 장소" else filtered[filtered["사고장소_정리"] == selected_place]

    st.plotly_chart(
        category_bar(activity_df, "사고당시활동_정리", 10, 430),
        use_container_width=True,
        config=PLOT_CONFIG,
        key="activity_by_place_bar",
    )

    section_header("선택 활동의 사고형태", "장소 → 활동 → 사고형태 순서로 사고 흐름을 확인합니다.")
    activity_options = activity_df["사고당시활동_정리"].value_counts().index.tolist()
    selected_activity = st.selectbox("사고 당시 활동 선택", activity_options, key="activity_form_select")
    form_df = activity_df[activity_df["사고당시활동_정리"] == selected_activity]
    st.plotly_chart(
        category_bar(form_df, "사고형태_정리", 10, 390),
        use_container_width=True,
        config=PLOT_CONFIG,
        key="form_by_activity_bar",
    )


