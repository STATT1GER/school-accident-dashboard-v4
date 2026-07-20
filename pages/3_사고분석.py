from __future__ import annotations

import pandas as pd
import streamlit as st

from components.cards import kpi_card, path_card
from components.charts import category_bar, floor_distribution, time_profile, weekday_time_heatmap
from components.filters import analysis_filters, apply_filters
from components.layout import footer, init_page, page_header, section_header
from components.sankey import build_sankey, top_paths
from utils.color import PLACE_COLORS, PLOT_CONFIG
from utils.helper import mode_or
from utils.loader import load_sample_data

init_page("사고분석", "📊")
df = load_sample_data()

page_header(
    "PATH-FIRST ACCIDENT ANALYTICS",
    "사고분석",
    "사고경로를 첫 화면에 배치하고, 시간·장소·활동·사고형태는 경로를 해석하기 위한 보조 분석으로 제공합니다.",
    "4-STAGE FLOW · V4",
)

filters = analysis_filters(df)
filtered = apply_filters(df, filters)
if filtered.empty:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다. 필터를 조정해주세요.")
    st.stop()

paths = top_paths(filtered, 12)
peak_time = mode_or(filtered, "사고시간_정리")
hot_place = mode_or(filtered, "사고장소_정리")
top_path_share = float(paths.iloc[0]["비율"]) if not paths.empty else 0.0
risk_index = min(100, round(48 + filtered["사고시간_정리"].value_counts(normalize=True).iloc[0] * 75 + filtered["사고장소_정리"].value_counts(normalize=True).iloc[0] * 65 + top_path_share * 100))

c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi_card("분석 신호", f"{len(filtered):,}건", "필터 적용", "blue")
with c2:
    kpi_card("핵심 위험시간", peak_time, "최빈 구간", "orange")
with c3:
    kpi_card("핵심 위험장소", hot_place, "우선 점검", "blue")
with c4:
    kpi_card("상대 위험도", f"{risk_index}", f"대표 경로 {top_path_share:.1%}", "purple")

st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
path_tab, time_tab, place_tab, activity_tab = st.tabs(["사고경로", "시간 분석", "장소 분석", "활동·형태"])


def render_path_scope(scope_df: pd.DataFrame, key_prefix: str, scope_name: str) -> None:
    if scope_df.empty:
        st.info(f"{scope_name} 조건에 해당하는 사고경로가 없습니다.")
        return

    section_header(f"{scope_name} 4단계 사고경로", "시간 → 장소 → 활동 → 사고형태의 연결을 간단히 또는 자세히 확인합니다.")
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
        st.caption("합성 데이터에 존재하는 전체 범주를 유지하여 세부 연결과 상대적으로 작은 경로까지 확인합니다.")
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
        section_header("상위 사고경로")
        for idx, row in scope_paths.head(5).iterrows():
            path_card(row["사고경로"], int(row["사고건수"]), float(row["비율"]), idx + 1)
    with right:
        section_header("경로 상세 탐색")
        selected_path = st.selectbox("확인할 경로", scope_paths["사고경로"].tolist(), key=f"{key_prefix}_path_select")
        selected = scope_paths[scope_paths["사고경로"] == selected_path].iloc[0]
        st.markdown(
            f"""
            <div class='detail-card'>
                <div class='detail-label'>SELECTED PATH · {scope_name}</div>
                <h3>{selected_path}</h3>
                <div class='detail-metrics'>
                    <div><b>{int(selected['사고건수']):,}</b><span>합성 신호</span></div>
                    <div><b>{float(selected['비율']):.1%}</b><span>해당 범위 비중</span></div>
                </div>
                <p>시간과 장소만 따로 보지 않고, 이 경로가 완성되는 활동 전환 지점에 교사 관찰·동선 분리·활동 규칙을 배치합니다.</p>
            </div>
            """,
            unsafe_allow_html=True,
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
    section_header("시간대별 상대 위험 프로파일", "가장 높은 일과 구간을 100으로 두어 상대 위험도를 비교합니다.")
    st.plotly_chart(time_profile(filtered), use_container_width=True, config=PLOT_CONFIG, key="analysis_time_profile")
    section_header("요일 × 사고시간", "월별 추이는 제거하고, 요일과 일과 구간의 결합 위험을 넓은 화면으로 제시합니다.")
    st.plotly_chart(weekday_time_heatmap(filtered), use_container_width=True, config=PLOT_CONFIG, key="analysis_weekday_heatmap")

with place_tab:
    c1, c2 = st.columns([1.35, 0.65], gap="large")
    with c1:
        section_header("사고장소 분포", "상위 장소를 사고건수 기준으로 정렬했습니다.")
        st.plotly_chart(category_bar(filtered, "사고장소_정리", 10, 440, PLACE_COLORS), use_container_width=True, config=PLOT_CONFIG, key="place_bar")
    with c2:
        section_header("층별 분포")
        st.plotly_chart(floor_distribution(filtered), use_container_width=True, config=PLOT_CONFIG, key="floor_donut")

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

    section_header("선택 활동의 사고형태", "교사가 이해하기 쉬운 단일 분포로 활동 이후 나타나는 사고형태를 확인합니다.")
    activity_options = activity_df["사고당시활동_정리"].value_counts().index.tolist()
    selected_activity = st.selectbox("사고 당시 활동 선택", activity_options, key="activity_form_select")
    form_df = activity_df[activity_df["사고당시활동_정리"] == selected_activity]
    st.plotly_chart(
        category_bar(form_df, "사고형태_정리", 10, 390),
        use_container_width=True,
        config=PLOT_CONFIG,
        key="form_by_activity_bar",
    )

section_header("합성 데이터 미리보기", "심각도는 유추하지 않으며 사고경로 구성에 필요한 필드만 표시합니다.")
preview_cols = ["사고일자", "학년", "학년급", "사고시간_정리", "사고장소_정리", "사고당시활동_정리", "사고형태_정리"]
st.dataframe(filtered[preview_cols].sort_values("사고일자", ascending=False).head(100), use_container_width=True, hide_index=True)

footer()
