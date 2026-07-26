from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from components.cards import insight_card, kpi_card, risk_row
from components.layout import footer, init_page, page_header, section_header
from components.sankey import top_paths
from utils.color import PLOT_CONFIG
from utils.helper import asset_path, mode_or
from utils.loader import load_sample_data


# ============================================================
# 0. 이미지 처리 함수
# ============================================================




CONCENTRATION_COLORSCALE = [
    [0.00, "rgba(255,255,255,0.00)"],
    [0.15, "rgba(255,214,10,0.08)"],
    [0.40, "rgba(255,214,10,0.24)"],
    [0.65, "rgba(255,159,10,0.42)"],
    [0.85, "rgba(255,105,10,0.58)"],
    [1.00, "rgba(255,69,58,0.72)"],
]

# assets/school_map.png의 실제 크기: 1600 × 900 (16:9)
# Plotly 데이터 좌표도 같은 종횡비로 고정합니다.
MAP_IMAGE_WIDTH = 1600.0
MAP_IMAGE_HEIGHT = 900.0
MAP_X_MAX = 100.0
MAP_Y_MAX = MAP_X_MAX * MAP_IMAGE_HEIGHT / MAP_IMAGE_WIDTH  # 56.25


def map_y_to_plot_y(value: float) -> float:
    """이미지 기준 위쪽 0~아래쪽 100 좌표를 Plotly 표준 Y좌표로 변환합니다."""
    return (100.0 - float(value)) * MAP_Y_MAX / 100.0


def build_concentration_surface(
    agg,
    grid_size: int = 180,
    sigma_x: float = 4.8,
    sigma_y_percent: float = 5.8,
):
    """
    지도구역 중심점과 상대 사고집중도로 등고선 표면을 만듭니다.

    X축은 0~100, Y축은 지도 이미지의 실제 16:9 비율에 맞춘
    0~56.25 좌표계를 사용합니다. 등고선, 마커, 배경 이미지가 모두
    같은 데이터 축을 사용하므로 브라우저 폭이나 Streamlit 배포환경이
    달라져도 위치가 어긋나지 않습니다.
    """
    grid_x = np.linspace(0, MAP_X_MAX, grid_size)
    grid_y = np.linspace(0, MAP_Y_MAX, grid_size)
    xx, yy = np.meshgrid(grid_x, grid_y)
    surface = np.zeros_like(xx, dtype=float)

    # 기존 0~100 세로좌표에서 사용하던 퍼짐 정도를 16:9 좌표로 환산
    sigma_y = sigma_y_percent * MAP_Y_MAX / 100.0

    for row in agg.itertuples(index=False):
        x0 = float(row.지도X)
        y0 = float(row.지도Y_플롯)
        concentration = float(row.상대사고집중도)

        zone_surface = concentration * np.exp(
            -0.5
            * (
                ((xx - x0) / sigma_x) ** 2
                + ((yy - y0) / sigma_y) ** 2
            )
        )

        surface = np.maximum(surface, zone_surface)

    return grid_x, grid_y, surface


def image_to_data_uri(image_path: Path) -> str:
    """
    로컬 이미지 파일을 Plotly layout image에서 안정적으로 사용할 수 있는
    Base64 data URI로 변환합니다.

    Streamlit Cloud에서도 로컬 파일 경로를 직접 참조하지 않고
    Plotly JSON 내부에 이미지가 포함되도록 하기 위한 처리입니다.
    """
    if not image_path.exists():
        raise FileNotFoundError(f"지도 이미지 파일을 찾을 수 없습니다: {image_path}")

    mime_type, _ = mimetypes.guess_type(image_path.name)
    mime_type = mime_type or "image/png"

    encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


# ============================================================
# 1. 페이지 초기화 및 데이터 로드
# ============================================================

init_page("학교지도", "🗺️")
df = load_sample_data()

page_header(
    "SPATIAL INTERVENTION MAP",
    "학교지도",
    "가상 학교 1층 배치도 위에 일과 구간별 상대 사고집중도를 겹쳐 표시하여 공간적 개입 우선순위를 확인합니다.",
    "VIRTUAL 1F CAMPUS",
)


# ============================================================
# 2. 지도 조건 선택
# ============================================================

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
    filtered = filtered[
        filtered["사고시간_정리"].isin(selected_times)
    ].copy()

if filtered.empty:
    st.warning("현재 조건에 해당하는 합성 사고 신호가 없습니다.")
    st.stop()


# ============================================================
# 3. 핵심 지표 계산
# ============================================================

zone_counts = filtered["지도구역"].value_counts()
hot_zone = str(zone_counts.index[0])
hot_place = mode_or(
    filtered[filtered["지도구역"] == hot_zone],
    "사고장소_정리",
)
paths = top_paths(filtered, 3)
hot_share = float(zone_counts.iloc[0] / len(filtered))

c1, c2, c3, c4 = st.columns(4)

with c1:
    kpi_card(
        "표시 사고 신호",
        f"{len(filtered):,}건",
        "조건 적용",
        "blue",
    )

with c2:
    kpi_card(
        "핵심 개입구역",
        hot_zone,
        "최빈 구역",
        "orange",
    )

with c3:
    kpi_card(
        "대표 공간유형",
        hot_place,
        "우선 점검",
        "blue",
    )

with c4:
    kpi_card(
        "상위 구역 비중",
        f"{hot_share:.1%}",
        "선택 범위 내",
        "purple",
    )

st.info(
    "상대 사고집중도는 선택한 조건에서 사고 건수가 가장 많은 공간을 100으로 두고 "
    "다른 공간을 상대적으로 환산한 비교지표입니다. 학생 수, 공간 이용량, 통행량과 "
    "체류시간이 반영되지 않았으므로 실제 사고확률이나 절대적인 위험도를 의미하지 않습니다."
)


# ============================================================
# 4. 가상학교 지도 + 상대 사고집중도 히트맵
# ============================================================

section_header(
    "상대 사고집중도 히트맵",
    "가상학교 1층 배치도를 배경으로 사용하고, 사고장소 범주를 동일한 0~100 상대좌표에 겹쳐 표시합니다.",
)

# 프로젝트의 assets/school_map.png를 불러와 Plotly 내부에 직접 삽입합니다.
map_path = asset_path("school_map.png")

try:
    school_map_uri = image_to_data_uri(map_path)
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

# 지도구역별 집계
agg = (
    filtered
    .groupby("지도구역", observed=False)
    .agg(
        사고건수=("사고ID", "size"),
        지도X=("지도X", "mean"),
        지도Y=("지도Y", "mean"),
        대표공간=(
            "사고장소_정리",
            lambda x: x.mode().iloc[0] if not x.mode().empty else "-",
        ),
    )
    .reset_index()
)

maximum = max(int(agg["사고건수"].max()), 1)
agg["상대사고집중도"] = agg["사고건수"] / maximum * 100

# 원자료의 지도Y는 이미지의 위쪽이 0, 아래쪽이 100입니다.
# Plotly는 아래쪽이 0인 좌표계를 사용하므로 명시적으로 변환합니다.
# 축 자체를 뒤집는 방식보다 배포환경과 Plotly 버전에 덜 민감합니다.
agg["지도Y_플롯"] = agg["지도Y"].map(map_y_to_plot_y)

fig = go.Figure()

# ------------------------------------------------------------
# 4-1. 지도 배경 이미지
# ------------------------------------------------------------
# xref/yref를 paper로 사용하면 그래프 축의 반전 여부와 관계없이
# 이미지가 플롯 영역 전체를 정확하게 채웁니다.
fig.add_layout_image(
    dict(
        source=school_map_uri,

        # 핵심: paper 좌표가 아니라 등고선·마커와 동일한 데이터 축 사용
        xref="x",
        yref="y",
        x=0,
        y=MAP_Y_MAX,
        sizex=MAP_X_MAX,
        sizey=MAP_Y_MAX,
        xanchor="left",
        yanchor="top",
        sizing="stretch",
        layer="below",
        opacity=1.0,
    )
)

# ------------------------------------------------------------
# 4-2. 지도구역 중심과 동일한 기준으로 등고선 생성
# ------------------------------------------------------------
grid_x, grid_y, concentration_surface = build_concentration_surface(agg)

fig.add_trace(
    go.Contour(
        x=grid_x,
        y=grid_y,
        z=concentration_surface,
        zmin=0,
        zmax=100,
        colorscale=CONCENTRATION_COLORSCALE,
        contours=dict(
            start=10,
            end=100,
            size=10,
            coloring="heatmap",
            showlines=True,
        ),
        line=dict(
            color="rgba(90,90,90,0.45)",
            width=0.8,
        ),
        showscale=True,
        colorbar=dict(
            title=dict(
                text="상대<br>사고집중도",
                side="right",
            ),
            thickness=12,
            len=0.62,
            x=1.02,
            y=0.5,
            outlinewidth=0,
            tickvals=[0, 25, 50, 75, 100],
        ),
        hoverinfo="skip",
        opacity=0.90,
    )
)

# ------------------------------------------------------------
# 4-3. 지도구역 중심 마커
# ------------------------------------------------------------
# 원의 크기로 사고건수를 다시 표현하면 등고선과 서로 다른 시각 신호가
# 만들어지므로, 위치 확인용 고정 크기 마커로 통일합니다.
fig.add_trace(
    go.Scatter(
        x=agg["지도X"],
        y=agg["지도Y_플롯"],
        mode="markers+text",
        text=agg["지도구역"],
        textposition="top center",
        textfont=dict(
            size=12,
            color="#1D1D1F",
            family="Inter, Pretendard, sans-serif",
        ),
        marker=dict(
            size=12,
            color=agg["상대사고집중도"],
            colorscale=CONCENTRATION_COLORSCALE,
            cmin=0,
            cmax=100,
            line=dict(
                color="white",
                width=2,
            ),
            opacity=1.0,
            showscale=False,
        ),
        customdata=agg[["대표공간", "사고건수", "상대사고집중도"]],
        hovertemplate=(
            "<b>%{text}</b><br>"
            "대표 공간: %{customdata[0]}<br>"
            "사고 시연 건수: %{customdata[1]:,}건<br>"
            "상대 사고집중도: %{customdata[2]:.0f}"
            "<extra></extra>"
        ),
    )
)

# ------------------------------------------------------------
# 4-4. 축과 레이아웃
# ------------------------------------------------------------
# 이미지, 등고선, 중심 마커가 같은 x/y 데이터 좌표를 사용합니다.
# 실제 지도 종횡비(16:9)는 scaleanchor로 고정합니다.
fig.update_xaxes(
    range=[0, MAP_X_MAX],
    visible=False,
    fixedrange=True,
    showgrid=False,
    zeroline=False,
    constrain="domain",
)

fig.update_yaxes(
    range=[0, MAP_Y_MAX],
    visible=False,
    fixedrange=True,
    showgrid=False,
    zeroline=False,

    # X와 Y의 1단위를 같은 픽셀 크기로 고정하여
    # 1600×900 지도 종횡비를 모든 화면에서 유지합니다.
    scaleanchor="x",
    scaleratio=1,
    constrain="domain",
)

fig.update_layout(
    height=570,
    margin=dict(
        l=0,
        r=74,
        t=0,
        b=0,
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    showlegend=False,
    hovermode="closest",
    dragmode=False,
)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={
        **PLOT_CONFIG,
        "scrollZoom": False,
        "displayModeBar": False,
    },
)

st.caption(
    "지도상의 점과 히트맵은 사고장소 범주를 가상 배치도에 나타내기 위한 "
    "재현 가능한 시연 좌표이며 실제 사고 발생 위치가 아닙니다."
)


# ============================================================
# 5. 공간 우선순위 및 대응 제안
# ============================================================

left, right = st.columns([0.9, 1.1], gap="large")

with left:
    section_header("공간적 개입 우선순위")

    for idx, (name, count) in enumerate(zone_counts.head(5).items(), 1):
        risk_row(
            idx,
            str(name),
            int(count),
            count / len(filtered),
            "orange" if idx <= 2 else "blue",
        )

with right:
    section_header("지도 기반 대응 제안")

    insight_card(
        f"{hot_zone} 우선 관찰",
        "현재 선택 조건에서 사고 신호가 가장 많이 모인 구역입니다. "
        "진입·이탈 동선과 교사 관찰 위치를 함께 점검하세요.",
        "MAP PRIORITY",
        "orange",
    )

    if not paths.empty:
        insight_card(
            "대표 경로와 공간 연결",
            f"{paths.iloc[0]['사고경로']} 경로가 반복됩니다. "
            "해당 공간에서 활동 전환이 시작되기 전에 개입 시나리오를 설계하세요.",
            "PATH LINK",
            "blue",
        )

footer()