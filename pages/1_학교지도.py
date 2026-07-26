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
# 0. 지도 시각화 설정
# ============================================================

CONCENTRATION_COLORSCALE = [
    [0.00, "rgba(255,255,255,0.00)"],
    [0.15, "rgba(255,214,10,0.08)"],
    [0.40, "rgba(255,214,10,0.24)"],
    [0.65, "rgba(255,159,10,0.42)"],
    [0.85, "rgba(255,105,10,0.58)"],
    [1.00, "rgba(255,69,58,0.72)"],
]


# assets/school_map.png 실제 크기: 1600 × 900
MAP_IMAGE_WIDTH = 1600.0
MAP_IMAGE_HEIGHT = 900.0

MAP_X_MAX = 100.0
MAP_Y_MAX = MAP_X_MAX * MAP_IMAGE_HEIGHT / MAP_IMAGE_WIDTH  # 56.25


# ============================================================
# 1. 계단·복도 표시용 세부 구역 설정
# ============================================================

# 실제 데이터에서 사용될 가능성이 있는 지도구역명
MOBILITY_SOURCE_ZONES = {
    "계단·복도",
    "이동(계단·복도)",
}


# 지도 이미지 기준 좌표
# X: 왼쪽 0 → 오른쪽 100
# Y: 위쪽 0 → 아래쪽 100
MOBILITY_ZONE_LAYOUT = {
    "서쪽 계단": {
        "x": 12.5,
        "y": 49.5,
    },
    "중앙 복도": {
        "x": 39.5,
        "y": 49.0,
    },
    "동쪽 계단": {
        "x": 67.0,
        "y": 49.5,
    },
}


# 일과 구간별 시각화용 분산 비율
MOBILITY_SPLIT_PROFILES = {
    "전체 일과": {
        "서쪽 계단": 0.28,
        "중앙 복도": 0.44,
        "동쪽 계단": 0.28,
    },
    "등교·하교": {
        "서쪽 계단": 0.38,
        "중앙 복도": 0.34,
        "동쪽 계단": 0.28,
    },
    "수업시간": {
        "서쪽 계단": 0.22,
        "중앙 복도": 0.52,
        "동쪽 계단": 0.26,
    },
    "쉬는시간": {
        "서쪽 계단": 0.30,
        "중앙 복도": 0.46,
        "동쪽 계단": 0.24,
    },
    "점심시간": {
        "서쪽 계단": 0.24,
        "중앙 복도": 0.48,
        "동쪽 계단": 0.28,
    },
    "방과후": {
        "서쪽 계단": 0.32,
        "중앙 복도": 0.36,
        "동쪽 계단": 0.32,
    },
}


# ============================================================
# 2. 교실·학습공간 표시용 세부 구역 설정
# ============================================================

# 데이터에 따라 명칭이 조금 다를 가능성을 고려해 두 가지를 지원
CLASSROOM_SOURCE_ZONES = {
    "교실·학습공간",
    "교실·학습",
}


# 가상학교 지도상의 교실 위치
CLASSROOM_ZONE_LAYOUT = {
    # 지도 상단의 1-1 교실, 1-2 교실 주변
    "1학년 교실": {
        "x": 25.0,
        "y": 29.0,
    },

    # 지도 하단의 2-1 교실, 2-2 교실 주변
    "2학년 교실": {
        "x": 25.0,
        "y": 72.0,
    },

    # 지도 상단의 과학실과 도서실 주변
    "과학·도서실": {
        "x": 52.5,
        "y": 29.0,
    },

    # 지도 하단의 특별실 주변
    "특별실": {
        "x": 59.0,
        "y": 72.0,
    },
}


# 일과 구간별 교실·학습공간 시각화용 분산 비율
CLASSROOM_SPLIT_PROFILES = {
    "전체 일과": {
        "1학년 교실": 0.29,
        "2학년 교실": 0.27,
        "과학·도서실": 0.24,
        "특별실": 0.20,
    },
    "등교·하교": {
        "1학년 교실": 0.34,
        "2학년 교실": 0.31,
        "과학·도서실": 0.20,
        "특별실": 0.15,
    },
    "수업시간": {
        "1학년 교실": 0.27,
        "2학년 교실": 0.26,
        "과학·도서실": 0.27,
        "특별실": 0.20,
    },
    "쉬는시간": {
        "1학년 교실": 0.31,
        "2학년 교실": 0.29,
        "과학·도서실": 0.22,
        "특별실": 0.18,
    },
    "점심시간": {
        "1학년 교실": 0.34,
        "2학년 교실": 0.32,
        "과학·도서실": 0.18,
        "특별실": 0.16,
    },
    "방과후": {
        "1학년 교실": 0.23,
        "2학년 교실": 0.22,
        "과학·도서실": 0.25,
        "특별실": 0.30,
    },
}


# ============================================================
# 3. 지도 텍스트 표시 위치
# ============================================================

TEXT_POSITION_MAP = {
    # 계단·복도
    "서쪽 계단": "middle left",
    "중앙 복도": "bottom center",
    "동쪽 계단": "middle right",

    # 교실·학습공간
    "1학년 교실": "top center",
    "2학년 교실": "bottom center",
    "과학·도서실": "top center",
    "특별실": "bottom center",

    # 기타 공간
    "강당": "top center",
    "강당·체육공간": "top center",
    "급식실": "top center",
    "급식·위생공간": "top center",
    "운동장": "top center",
    "보건실": "top center",
    "보건·위생공간": "top center",
    "정문·외부동선": "bottom center",
}


# ============================================================
# 4. 지도 좌표 및 표시 데이터 변환 함수
# ============================================================

def map_y_to_plot_y(value: float) -> float:
    """
    이미지 기준 Y좌표를 Plotly 기준 Y좌표로 변환합니다.

    이미지:
        위쪽 = 0
        아래쪽 = 100

    Plotly:
        아래쪽 = 0
        위쪽 = MAP_Y_MAX
    """
    return (100.0 - float(value)) * MAP_Y_MAX / 100.0


def allocate_split_counts(
    total_count: int,
    ratios: list[float],
) -> list[int]:
    """
    전체 건수를 지정한 비율에 따라 정수 건수로 배분합니다.

    배분된 건수의 합계는 항상 원래 전체 건수와 일치합니다.
    전체 건수가 세부 구역 수 이상이면 각 구역에 최소 1건을 배치합니다.
    """
    group_count = len(ratios)

    if total_count <= 0:
        return [0] * group_count

    ratios_array = np.asarray(
        ratios,
        dtype=float,
    )

    if ratios_array.sum() <= 0:
        ratios_array = np.ones(
            group_count,
            dtype=float,
        )

    ratios_array = ratios_array / ratios_array.sum()

    # 전체 건수가 구역 수보다 작은 경우
    # 비율이 큰 구역부터 한 건씩 배정
    if total_count < group_count:
        result = [0] * group_count
        priority_order = np.argsort(-ratios_array)

        for idx in priority_order[:total_count]:
            result[int(idx)] = 1

        return result

    # 각 구역에 최소 한 건씩 우선 배정
    counts = np.ones(
        group_count,
        dtype=int,
    )

    remaining = total_count - group_count

    raw_additional_counts = ratios_array * remaining
    additional_counts = np.floor(
        raw_additional_counts
    ).astype(int)

    counts += additional_counts

    remainder = total_count - int(counts.sum())

    if remainder > 0:
        fractional_parts = (
            raw_additional_counts
            - additional_counts
        )

        priority_order = np.argsort(
            -fractional_parts
        )

        for idx in priority_order[:remainder]:
            counts[int(idx)] += 1

    return counts.tolist()


def apply_zone_split(
    work,
    source_zones: set[str],
    zone_layout: dict,
    split_profile: dict,
):
    """
    하나의 넓은 원본 지도구역을 여러 개의 표시용 세부 구역으로 분산합니다.

    원본 지도구역과 원본 좌표는 수정하지 않고 다음 표시용 컬럼만 수정합니다.

    - 지도구역_표시
    - 지도X_표시
    - 지도Y_표시
    """
    source_values = (
        work["지도구역"]
        .astype(str)
        .str.strip()
    )

    source_mask = source_values.isin(
        source_zones
    )

    if not source_mask.any():
        return work

    zone_names = list(
        zone_layout.keys()
    )

    ratios = [
        split_profile.get(
            zone_name,
            0,
        )
        for zone_name in zone_names
    ]

    source_rows = work.loc[
        source_mask
    ].copy()

    # 같은 조건을 선택했을 때 매번 동일하게 분산되도록 고정 정렬
    if "사고ID" in source_rows.columns:
        source_rows = source_rows.sort_values(
            by="사고ID",
            kind="stable",
        )
    else:
        source_rows = source_rows.sort_index()

    source_indices = source_rows.index.tolist()

    split_counts = allocate_split_counts(
        total_count=len(source_indices),
        ratios=ratios,
    )

    assigned_labels: list[str] = []

    for zone_name, zone_count in zip(
        zone_names,
        split_counts,
    ):
        assigned_labels.extend(
            [zone_name] * zone_count
        )

    assigned_labels = assigned_labels[
        :len(source_indices)
    ]

    # 예상치 못한 길이 차이에 대한 방어 처리
    while len(assigned_labels) < len(source_indices):
        assigned_labels.append(
            zone_names[0]
        )

    work.loc[
        source_indices,
        "지도구역_표시",
    ] = assigned_labels

    # 세부 구역별 표시 좌표 적용
    for zone_name, layout in zone_layout.items():
        detail_mask = (
            work["지도구역_표시"]
            .eq(zone_name)
        )

        work.loc[
            detail_mask,
            "지도X_표시",
        ] = float(layout["x"])

        work.loc[
            detail_mask,
            "지도Y_표시",
        ] = float(layout["y"])

    return work


def split_demo_zones_for_display(
    source_df,
    selected_time_group: str,
):
    """
    지도 시연용으로 넓은 공간 범주를 세부 구역으로 분산합니다.

    계단·복도:
        서쪽 계단 / 중앙 복도 / 동쪽 계단

    교실·학습공간:
        1학년 교실 / 2학년 교실 / 과학·도서실 / 특별실

    원본 데이터는 변경하지 않고 표시용 컬럼만 생성합니다.
    """
    work = source_df.copy()

    # 기본적으로 원본 지도구역과 원본 좌표를 사용
    work["지도구역_표시"] = (
        work["지도구역"]
        .astype(str)
    )

    work["지도X_표시"] = (
        work["지도X"]
        .astype(float)
    )

    work["지도Y_표시"] = (
        work["지도Y"]
        .astype(float)
    )

    # --------------------------------------------------------
    # 계단·복도 분산
    # --------------------------------------------------------

    mobility_profile = MOBILITY_SPLIT_PROFILES.get(
        selected_time_group,
        MOBILITY_SPLIT_PROFILES["전체 일과"],
    )

    work = apply_zone_split(
        work=work,
        source_zones=MOBILITY_SOURCE_ZONES,
        zone_layout=MOBILITY_ZONE_LAYOUT,
        split_profile=mobility_profile,
    )

    # --------------------------------------------------------
    # 교실·학습공간 분산
    # --------------------------------------------------------

    classroom_profile = CLASSROOM_SPLIT_PROFILES.get(
        selected_time_group,
        CLASSROOM_SPLIT_PROFILES["전체 일과"],
    )

    work = apply_zone_split(
        work=work,
        source_zones=CLASSROOM_SOURCE_ZONES,
        zone_layout=CLASSROOM_ZONE_LAYOUT,
        split_profile=classroom_profile,
    )

    return work


def build_concentration_surface(
    agg,
    grid_size: int = 180,
    sigma_x: float = 4.2,
    sigma_y_percent: float = 5.0,
):
    """
    지도구역 중심점과 상대 사고집중도로 등고선 표면을 만듭니다.

    지도 이미지, 등고선, 중심 마커가 모두 같은 데이터 좌표계를 사용합니다.
    """
    grid_x = np.linspace(
        0,
        MAP_X_MAX,
        grid_size,
    )

    grid_y = np.linspace(
        0,
        MAP_Y_MAX,
        grid_size,
    )

    xx, yy = np.meshgrid(
        grid_x,
        grid_y,
    )

    surface = np.zeros_like(
        xx,
        dtype=float,
    )

    # 이미지 기준 0~100 Y좌표에서 사용하던 퍼짐값을
    # Plotly의 0~56.25 좌표계에 맞게 변환
    sigma_y = (
        sigma_y_percent
        * MAP_Y_MAX
        / 100.0
    )

    for row in agg.itertuples(
        index=False
    ):
        x0 = float(
            row.지도X
        )

        y0 = float(
            row.지도Y_플롯
        )

        concentration = float(
            row.상대사고집중도
        )

        zone_surface = concentration * np.exp(
            -0.5
            * (
                ((xx - x0) / sigma_x) ** 2
                + ((yy - y0) / sigma_y) ** 2
            )
        )

        # 겹치는 구역은 값을 합산하지 않고 가장 강한 신호를 사용
        surface = np.maximum(
            surface,
            zone_surface,
        )

    return grid_x, grid_y, surface


def image_to_data_uri(
    image_path: Path,
) -> str:
    """
    로컬 지도 이미지를 Base64 data URI로 변환합니다.

    Streamlit Cloud에서도 로컬 파일 경로 문제 없이
    Plotly 내부에 이미지가 포함되도록 합니다.
    """
    if not image_path.exists():
        raise FileNotFoundError(
            f"지도 이미지 파일을 찾을 수 없습니다: {image_path}"
        )

    mime_type, _ = mimetypes.guess_type(
        image_path.name
    )

    mime_type = mime_type or "image/png"

    encoded = base64.b64encode(
        image_path.read_bytes()
    ).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


# ============================================================
# 5. 페이지 초기화 및 데이터 로드
# ============================================================

init_page(
    "학교지도",
    "🗺️",
)

df = load_sample_data()

page_header(
    "SPATIAL INTERVENTION MAP",
    "학교지도",
    (
        "가상 학교 1층 배치도 위에 일과 구간별 상대 사고집중도를 "
        "겹쳐 표시하여 공간적 개입 우선순위를 확인합니다."
    ),
    "VIRTUAL 1F CAMPUS",
)


# ============================================================
# 6. 지도 조건 선택
# ============================================================

st.markdown(
    """
    <div class="control-heading">지도 조건</div>
    <div class="control-caption">
        일과 구간을 선택하여 시간대별 공간 집중도를 비교합니다.
    </div>
    """,
    unsafe_allow_html=True,
)

time_group = st.radio(
    "일과 구간",
    [
        "전체 일과",
        "등교·하교",
        "수업시간",
        "쉬는시간",
        "점심시간",
        "방과후",
    ],
    horizontal=True,
    index=0,
    key="map_time_group",
)

TIME_GROUP_MAP = {
    "전체 일과": None,

    "등교·하교": [
        "등교 전",
        "하교",
    ],

    "수업시간": [
        "1교시",
        "2교시",
        "3교시",
        "4교시",
        "5교시",
        "6교시",
    ],

    "쉬는시간": [
        "쉬는시간",
    ],

    "점심시간": [
        "점심시간",
        "식사시간",
    ],

    "방과후": [
        "방과후",
    ],
}

filtered = df.copy()

selected_times = TIME_GROUP_MAP[
    time_group
]

if selected_times is not None:
    filtered = filtered[
        filtered["사고시간_정리"]
        .isin(selected_times)
    ].copy()

if filtered.empty:
    st.warning(
        "현재 조건에 해당하는 합성 사고 신호가 없습니다."
    )
    st.stop()


# ------------------------------------------------------------
# 계단·복도와 교실·학습공간을 표시용 세부 구역으로 분산
# ------------------------------------------------------------

display_filtered = split_demo_zones_for_display(
    source_df=filtered,
    selected_time_group=time_group,
)


# ============================================================
# 7. 핵심 지표 계산
# ============================================================

zone_counts = (
    display_filtered["지도구역_표시"]
    .value_counts()
)

hot_zone = str(
    zone_counts.index[0]
)

hot_place = mode_or(
    display_filtered[
        display_filtered["지도구역_표시"]
        .eq(hot_zone)
    ],
    "사고장소_정리",
)

# 사고경로 분석은 표시용 구역이 아니라 원본 변수 기준으로 유지
paths = top_paths(
    filtered,
    3,
)

hot_share = float(
    zone_counts.iloc[0]
    / len(display_filtered)
)

c1, c2, c3, c4 = st.columns(
    4
)

with c1:
    kpi_card(
        "표시 사고 신호",
        f"{len(display_filtered):,}건",
        "조건 적용",
        "blue",
    )

with c2:
    kpi_card(
        "핵심 개입구역",
        hot_zone,
        "지도 표시 기준",
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
    "상대 사고집중도는 선택한 조건에서 사고 건수가 가장 많은 공간을 "
    "100으로 두고 다른 공간을 상대적으로 환산한 비교지표입니다. "
    "학생 수, 공간 이용량, 통행량과 체류시간이 반영되지 않았으므로 "
    "실제 사고확률이나 절대적인 위험도를 의미하지 않습니다. "
    "계단·복도는 서쪽 계단, 중앙 복도, 동쪽 계단으로 나누고, "
    "교실·학습공간은 1학년 교실, 2학년 교실, 과학·도서실, "
    "특별실로 나누어 지도 시연용으로 표시합니다."
)


# ============================================================
# 8. 가상학교 지도 + 상대 사고집중도 히트맵
# ============================================================

section_header(
    "상대 사고집중도 히트맵",
    (
        "가상학교 1층 배치도를 배경으로 사용하고, "
        "사고장소 범주를 지도 표시용 세부 구역에 겹쳐 표시합니다."
    ),
)

map_path = asset_path(
    "school_map.png"
)

try:
    school_map_uri = image_to_data_uri(
        map_path
    )

except FileNotFoundError as exc:
    st.error(
        str(exc)
    )
    st.stop()


# ------------------------------------------------------------
# 지도 표시용 구역별 사고 집계
# ------------------------------------------------------------

agg = (
    display_filtered
    .groupby(
        "지도구역_표시",
        observed=False,
    )
    .agg(
        사고건수=(
            "사고ID",
            "size",
        ),
        지도X=(
            "지도X_표시",
            "mean",
        ),
        지도Y=(
            "지도Y_표시",
            "mean",
        ),
        대표공간=(
            "사고장소_정리",
            lambda x: (
                x.mode().iloc[0]
                if not x.mode().empty
                else "-"
            ),
        ),
    )
    .reset_index()
    .rename(
        columns={
            "지도구역_표시": "지도구역",
        }
    )
)

maximum = max(
    int(
        agg["사고건수"].max()
    ),
    1,
)

agg["상대사고집중도"] = (
    agg["사고건수"]
    / maximum
    * 100
)

# 이미지 좌표의 Y값을 Plotly 좌표로 변환
agg["지도Y_플롯"] = (
    agg["지도Y"]
    .map(map_y_to_plot_y)
)

agg["텍스트위치"] = (
    agg["지도구역"]
    .map(TEXT_POSITION_MAP)
    .fillna("top center")
)


# ============================================================
# 9. Plotly 지도 생성
# ============================================================

fig = go.Figure()


# ------------------------------------------------------------
# 9-1. 지도 배경 이미지
# ------------------------------------------------------------

fig.add_layout_image(
    dict(
        source=school_map_uri,
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
# 9-2. 지도구역별 상대 사고집중도 등고선
# ------------------------------------------------------------

grid_x, grid_y, concentration_surface = (
    build_concentration_surface(
        agg
    )
)

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
            tickvals=[
                0,
                25,
                50,
                75,
                100,
            ],
        ),
        hoverinfo="skip",
        opacity=0.90,
    )
)


# ------------------------------------------------------------
# 9-3. 지도구역 중심 마커와 구역명
# ------------------------------------------------------------

fig.add_trace(
    go.Scatter(
        x=agg["지도X"],
        y=agg["지도Y_플롯"],
        mode="markers+text",
        text=agg["지도구역"],
        textposition=agg["텍스트위치"],
        textfont=dict(
            size=11,
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
        customdata=agg[
            [
                "대표공간",
                "사고건수",
                "상대사고집중도",
            ]
        ],
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
# 9-4. 축과 그래프 레이아웃
# ------------------------------------------------------------

fig.update_xaxes(
    range=[
        0,
        MAP_X_MAX,
    ],
    visible=False,
    fixedrange=True,
    showgrid=False,
    zeroline=False,
    constrain="domain",
)

fig.update_yaxes(
    range=[
        0,
        MAP_Y_MAX,
    ],
    visible=False,
    fixedrange=True,
    showgrid=False,
    zeroline=False,
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
    "재현 가능한 시연 좌표이며 실제 사고 발생 위치가 아닙니다. "
    "계단·복도는 서쪽 계단, 중앙 복도, 동쪽 계단으로 분산했고, "
    "교실·학습공간은 1학년 교실, 2학년 교실, 과학·도서실, "
    "특별실로 분산했습니다."
)


# ============================================================
# 10. 공간 우선순위 및 대응 제안
# ============================================================

left, right = st.columns(
    [
        0.9,
        1.1,
    ],
    gap="large",
)

with left:
    section_header(
        "공간적 개입 우선순위"
    )

    for idx, (name, count) in enumerate(
        zone_counts.head(5).items(),
        start=1,
    ):
        risk_row(
            idx,
            str(name),
            int(count),
            count / len(display_filtered),
            "orange" if idx <= 2 else "blue",
        )

with right:
    section_header(
        "지도 기반 대응 제안"
    )

    insight_card(
        f"{hot_zone} 우선 관찰",
        (
            "현재 선택 조건에서 사고 신호가 가장 많이 모인 "
            "지도 표시 구역입니다. 진입·이탈 동선과 교사 관찰 "
            "위치를 함께 점검하세요."
        ),
        "MAP PRIORITY",
        "orange",
    )

    if not paths.empty:
        insight_card(
            "대표 경로와 공간 연결",
            (
                f"{paths.iloc[0]['사고경로']} 경로가 반복됩니다. "
                "해당 공간에서 활동 전환이 시작되기 전에 "
                "개입 시나리오를 설계하세요."
            ),
            "PATH LINK",
            "blue",
        )

footer()