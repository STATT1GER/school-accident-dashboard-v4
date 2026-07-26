from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st
from PIL import Image

from components.cards import insight_card, kpi_card, risk_row
from components.layout import footer, init_page, page_header, section_header
from components.sankey import top_paths
from utils.color import PLOT_CONFIG
from utils.helper import asset_path, mode_or
from utils.loader import load_sample_data

init_page("학교지도", "🗺️")
df = load_sample_data()

page_header(
    "SPATIAL INTERVENTION MAP",
    "학교지도",
    "메인 화면과 동일한 가상 학교 1층 배치도 위에 일과 구간별 상대 사고집중도를 표시하여 공간적 개입 우선순위를 확인합니다.",
    "VIRTUAL 1F CAMPUS",
)

st.markdown(
    "<div class='control-heading'>지도 조건</div>"
    "<div class='control-caption'>일과 구간을 선택하여 시간대별 공간 집중도를 비교합니다.</div>",
    unsafe_allow_html=True,
)
time_group = st.radio(
    "일과 구간",
    ["전체 일과", "등교·하교", "수업시간", "쉬는시간", "점심시간", "방과후"],
    horizontal=True,
    index=0,
    key="map_time_group",
)

TIME_GROUP_MAP = {
    "전체 일과": None,
    "등교·하교": ["등교 전", "하교"],
    "수업시간": ["1교시", "2교시", "3교시", "4교시", "5교시", "6교시"],
    "쉬는시간": ["쉬는시간"],
    "점심시간": ["점심시간", "식사시간"],
    "방과후": ["방과후"],
}

filtered = df.copy()
selected_times = TIME_GROUP_MAP[time_group]
if selected_times is not None:
    filtered = filtered[filtered["사고시간_정리"].isin(selected_times)]

if filtered.empty:
    st.warning("현재 조건에 해당하는 합성 사고 신호가 없습니다.")
    st.stop()

zone_counts = filtered["지도구역"].value_counts()
hot_zone = str(zone_counts.index[0])
hot_place = mode_or(filtered[filtered["지도구역"] == hot_zone], "사고장소_정리")
paths = top_paths(filtered, 3)
hot_share = float(zone_counts.iloc[0] / len(filtered))

c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi_card("표시 사고 신호", f"{len(filtered):,}건", "조건 적용", "blue")
with c2:
    kpi_card("핵심 개입구역", hot_zone, "최빈 구역", "orange")
with c3:
    kpi_card("대표 공간유형", hot_place, "우선 점검", "blue")
with c4:
    kpi_card("상위 구역 비중", f"{hot_share:.1%}", "선택 범위 내", "purple")

st.info(
    "상대 사고집중도는 선택한 조건에서 사고 건수가 가장 많은 공간을 100으로 두고 다른 공간을 상대적으로 환산한 비교지표입니다. "
    "학생 수, 공간 이용량, 통행량과 체류시간이 반영되지 않았으므로 실제 사고확률이나 절대적인 위험도를 의미하지 않습니다."
)

section_header("상대 사고집중도 히트맵", "가상학교 1층 배치도와 시연 좌표를 동일한 0~100 스케일로 맞췄습니다.")

img = Image.open(asset_path("school_map.png"))
fig = go.Figure()
fig.add_layout_image(dict(
    source=img,
    x=0,
    y=100,
    sizex=100,
    sizey=100,
    xref="x",
    yref="y",
    xanchor="left",
    yanchor="top",
    sizing="stretch",
    layer="below",
    opacity=1.0,
))
fig.add_trace(go.Histogram2dContour(
    x=filtered["지도X"],
    y=filtered["지도Y"],
    ncontours=12,
    contours=dict(coloring="heatmap", showlines=False),
    colorscale=[
        [0, "rgba(255,255,255,0)"],
        [0.35, "rgba(255,214,10,0.14)"],
        [0.70, "rgba(255,159,10,0.30)"],
        [1, "rgba(255,69,58,0.58)"],
    ],
    showscale=False,
    hoverinfo="skip",
    opacity=0.88,
))

agg = filtered.groupby("지도구역", observed=False).agg(
    사고건수=("사고ID", "size"),
    지도X=("지도X", "mean"),
    지도Y=("지도Y", "mean"),
    대표공간=("사고장소_정리", lambda x: x.mode().iloc[0] if not x.mode().empty else "-"),
).reset_index()
maximum = max(int(agg["사고건수"].max()), 1)
agg["상대사고집중도"] = agg["사고건수"] / maximum * 100
fig.add_trace(go.Scatter(
    x=agg["지도X"],
    y=agg["지도Y"],
    mode="markers+text",
    text=agg["지도구역"],
    textposition="top center",
    marker=dict(
        size=(agg["사고건수"] / maximum * 34 + 16),
        color=agg["상대사고집중도"],
        colorscale=[[0, "#FFD60A"], [0.55, "#FF9F0A"], [1, "#FF453A"]],
        cmin=0,
        cmax=100,
        line=dict(color="white", width=2),
        opacity=0.92,
        showscale=False,
    ),
    customdata=agg[["대표공간", "사고건수", "상대사고집중도"]],
    hovertemplate=(
        "<b>%{text}</b><br>%{customdata[0]}<br>"
        "사고 시연 건수 %{customdata[1]:,}건<br>"
        "상대 사고집중도 %{customdata[2]:.0f}<extra></extra>"
    ),
))
fig.update_xaxes(range=[0, 100], visible=False, fixedrange=True)
fig.update_yaxes(range=[100, 0], visible=False, fixedrange=True)
fig.update_layout(
    height=610,
    margin=dict(l=0, r=0, t=0, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    showlegend=False,
)
st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)
st.caption("지도상의 점은 사고장소 범주를 가상 배치도에 나타내기 위한 재현 가능한 시연 좌표이며 실제 사고 발생 위치가 아닙니다.")

left, right = st.columns([0.9, 1.1], gap="large")
with left:
    section_header("공간적 개입 우선순위")
    for idx, (name, count) in enumerate(zone_counts.head(5).items(), 1):
        risk_row(idx, str(name), int(count), count / len(filtered), "orange" if idx <= 2 else "blue")
with right:
    section_header("지도 기반 대응 제안")
    insight_card(
        f"{hot_zone} 우선 관찰",
        "현재 선택 조건에서 사고 신호가 가장 많이 모인 구역입니다. 진입·이탈 동선과 교사 관찰 위치를 함께 점검하세요.",
        "MAP PRIORITY",
        "orange",
    )
    if not paths.empty:
        insight_card(
            "대표 경로와 공간 연결",
            f"{paths.iloc[0]['사고경로']} 경로가 반복됩니다. 해당 공간에서 활동 전환이 시작되기 전에 개입 시나리오를 설계하세요.",
            "PATH LINK",
            "blue",
        )

footer()
