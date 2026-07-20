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
    "SPATIAL RISK MAP",
    "학교지도",
    "메인 화면과 동일한 가상 학교 배치도 위에 층·일과 구간별 상대 위험신호를 겹쳐 확인합니다.",
    "VIRTUAL CAMPUS",
)

st.markdown("<div class='control-heading'>지도 조건</div><div class='control-caption'>드롭다운 대신 층과 일과 구간을 한눈에 선택할 수 있도록 구성했습니다.</div>", unsafe_allow_html=True)
control_left, control_right = st.columns([0.95, 2.05], gap="large")
with control_left:
    floor_options = [f"{x}층" for x in sorted(df["층"].unique())] + ["전체"]
    floor = st.radio("층 선택", floor_options, horizontal=True, index=0, key="map_floor")
with control_right:
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
    "점심시간": ["점심시간"],
    "방과후": ["방과후"],
}

filtered = df.copy()
if floor != "전체":
    filtered = filtered[filtered["층"] == int(floor.replace("층", ""))]
selected_times = TIME_GROUP_MAP[time_group]
if selected_times is not None:
    filtered = filtered[filtered["사고시간_정리"].isin(selected_times)]

if filtered.empty:
    st.warning("현재 조건에 해당하는 합성 위험신호가 없습니다.")
    st.stop()

zone_counts = filtered["지도구역"].value_counts()
hot_zone = zone_counts.index[0]
hot_place = mode_or(filtered[filtered["지도구역"] == hot_zone], "사고장소_정리")
paths = top_paths(filtered, 3)
top_path_share = float(paths.iloc[0]["비율"]) if not paths.empty else 0.0
hot_share = float(zone_counts.iloc[0] / len(filtered))
risk_index = min(100, round(48 + hot_share * 90 + top_path_share * 120))

c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi_card("표시 위험신호", f"{len(filtered):,}건", "조건 적용", "blue")
with c2:
    kpi_card("최고 위험구역", hot_zone, f"{hot_share:.1%}", "orange")
with c3:
    kpi_card("대표 공간유형", hot_place, "우선 점검", "blue")
with c4:
    kpi_card("상대 위험도", f"{risk_index}", "빈도 집중도", "orange")

section_header("사고 위험 히트맵", "배경 도면과 가상 좌표를 동일한 0~100 스케일로 맞춰 위험신호를 겹쳤습니다.")

img = Image.open(asset_path("school_map.png"))
fig = go.Figure()
fig.add_layout_image(dict(
    source=img, x=0, y=100, sizex=100, sizey=100,
    xref="x", yref="y", xanchor="left", yanchor="top",
    sizing="stretch", layer="below", opacity=1.0,
))
fig.add_trace(go.Histogram2dContour(
    x=filtered["지도X"], y=filtered["지도Y"],
    ncontours=12, contours=dict(coloring="heatmap", showlines=False),
    colorscale=[
        [0, "rgba(255,255,255,0)"],
        [0.35, "rgba(255,214,10,0.14)"],
        [0.70, "rgba(255,159,10,0.30)"],
        [1, "rgba(255,69,58,0.58)"],
    ],
    showscale=False, hoverinfo="skip", opacity=0.88,
))

agg = filtered.groupby(["지도구역", "사고장소_정리"], observed=False).agg(
    사고건수=("사고ID", "size"), 지도X=("지도X", "mean"), 지도Y=("지도Y", "mean")
).reset_index()
agg["상대위험도"] = agg["사고건수"] / max(int(agg["사고건수"].max()), 1) * 100
fig.add_trace(go.Scatter(
    x=agg["지도X"], y=agg["지도Y"], mode="markers+text",
    text=agg["지도구역"], textposition="top center",
    marker=dict(
        size=(agg["사고건수"] / max(int(agg["사고건수"].max()), 1) * 34 + 16),
        color=agg["상대위험도"],
        colorscale=[[0, "#FFD60A"], [0.55, "#FF9F0A"], [1, "#FF453A"]],
        cmin=0, cmax=100, line=dict(color="white", width=2), opacity=0.92, showscale=False,
    ),
    customdata=agg[["사고장소_정리", "사고건수", "상대위험도"]],
    hovertemplate="<b>%{text}</b><br>%{customdata[0]}<br>합성 신호 %{customdata[1]:,}건<br>상대 위험도 %{customdata[2]:.0f}<extra></extra>",
))
fig.update_xaxes(range=[0, 100], visible=False, fixedrange=True)
fig.update_yaxes(range=[100, 0], visible=False, fixedrange=True, scaleanchor="x")
fig.update_layout(
    height=720, margin=dict(l=0, r=0, t=0, b=0),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False,
)
st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)

left, right = st.columns([0.9, 1.1], gap="large")
with left:
    section_header("공간별 위험 순위")
    for idx, (name, count) in enumerate(zone_counts.head(5).items(), 1):
        risk_row(idx, name, int(count), count / len(filtered), "orange" if idx <= 2 else "blue")
with right:
    section_header("지도 기반 대응 제안")
    insight_card(f"{hot_zone} 우선 관찰", "현재 선택 조건에서 가장 많은 위험신호가 겹친 구역입니다. 진입·이탈 동선과 교사 관찰 위치를 함께 점검하세요.", "MAP PRIORITY", "orange")
    if not paths.empty:
        insight_card("대표 경로와 공간 연결", f"{paths.iloc[0]['사고경로']} 경로가 반복됩니다. 해당 공간에서 활동 전환 시점을 중심으로 개입 시나리오를 설계하세요.", "PATH LINK", "blue")

footer()
