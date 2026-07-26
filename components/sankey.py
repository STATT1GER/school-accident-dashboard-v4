from __future__ import annotations

import textwrap

import pandas as pd
import plotly.graph_objects as go

from utils.color import APPLE_BLUE, APPLE_BLUE_LIGHT, SUCCESS, WARNING, INK

STAGES = ["사고시간_정리", "사고장소_정리", "사고당시활동_정리", "사고형태_정리"]
STAGE_COLORS = [APPLE_BLUE, APPLE_BLUE_LIGHT, SUCCESS, WARNING]
STAGE_X = [0.02, 0.31, 0.60, 0.88]


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _wrap_label(value: object, width: int = 9) -> str:
    text = str(value)
    if len(text) <= width:
        return text
    return "<br>".join(textwrap.wrap(text, width=width, break_long_words=True, break_on_hyphens=False))


def _stage_y(count: int) -> list[float]:
    if count <= 1:
        return [0.5]
    return [(idx + 0.5) / count for idx in range(count)]


def build_sankey(
    df: pd.DataFrame,
    min_count: int = 8,
    top_n_per_stage: int | None = 5,
    aggregate_other: bool = True,
    height: int = 620,
) -> go.Figure:

    work = df[STAGES].dropna().astype(str).copy()

    if work.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="표시할 사고경로가 없습니다.",
            showarrow=False,
            x=0.5,
            y=0.5
        )
        fig.update_layout(
            height=height,
            paper_bgcolor="rgba(0,0,0,0)"
        )
        return fig

    # ========================================================
    # 단계별 상위 범주만 유지
    # ========================================================

    if top_n_per_stage is not None:

        for col in STAGES:

            keep = set(
                work[col]
                .value_counts()
                .head(top_n_per_stage)
                .index
            )

            if aggregate_other:

                work[col] = work[col].where(
                    work[col].isin(keep),
                    "기타"
                )

            else:

                work = work[
                    work[col].isin(keep)
                ].copy()

    # ========================================================
    # 단계 간 연결 빈도 계산
    # ========================================================

    link_records: list[tuple[int, str, str, int]] = []
    used_keys: set[str] = set()

    for stage_idx in range(len(STAGES) - 1):

        source_col = STAGES[stage_idx]
        target_col = STAGES[stage_idx + 1]

        links = (
            work
            .groupby(
                [source_col, target_col],
                observed=False
            )
            .size()
            .reset_index(name="count")
        )

        links = links[
            links["count"] >= max(1, min_count)
        ]

        for _, row in links.iterrows():

            source_value = str(row[source_col])
            target_value = str(row[target_col])

            source_key = f"{stage_idx}|{source_value}"
            target_key = f"{stage_idx + 1}|{target_value}"

            used_keys.update([
                source_key,
                target_key
            ])

            link_records.append(
                (
                    stage_idx,
                    source_value,
                    target_value,
                    int(row["count"])
                )
            )

    if not link_records:

        fig = go.Figure()

        fig.add_annotation(
            text="현재 표시 기준을 충족하는 사고경로가 없습니다.",
            showarrow=False,
            x=0.5,
            y=0.5
        )

        fig.update_layout(
            height=height,
            paper_bgcolor="rgba(0,0,0,0)"
        )

        return fig

    # ========================================================
    # 노드 구성
    # ========================================================

    labels: list[str] = []
    original_labels: list[str] = []
    colors: list[str] = []
    node_x: list[float] = []

    node_index: dict[str, int] = {}
    stage_node_counts: list[int] = []

    for stage_idx, col in enumerate(STAGES):

        ordered_values = [
            str(value)
            for value in work[col].value_counts().index
            if f"{stage_idx}|{value}" in used_keys
        ]

        stage_node_counts.append(
            len(ordered_values)
        )

        for value in ordered_values:

            key = f"{stage_idx}|{value}"

            node_index[key] = len(labels)

            labels.append(
                _wrap_label(value)
            )

            original_labels.append(value)

            colors.append(
                _rgba(
                    STAGE_COLORS[stage_idx],
                    0.92
                )
            )

            # 단계별 가로 위치만 고정
            node_x.append(
                STAGE_X[stage_idx]
            )

    # ========================================================
    # 링크 구성
    # ========================================================

    sources: list[int] = []
    targets: list[int] = []
    values: list[int] = []
    link_colors: list[str] = []
    link_customdata: list[str] = []

    for (
        stage_idx,
        source_value,
        target_value,
        count
    ) in link_records:

        source_key = f"{stage_idx}|{source_value}"
        target_key = f"{stage_idx + 1}|{target_value}"

        if (
            source_key not in node_index
            or target_key not in node_index
        ):
            continue

        sources.append(
            node_index[source_key]
        )

        targets.append(
            node_index[target_key]
        )

        values.append(count)

        link_colors.append(
            _rgba(
                STAGE_COLORS[stage_idx],
                0.18
            )
        )

        link_customdata.append(
            f"{source_value} → {target_value}"
        )

    # 노드 수가 많을수록 높이 확대
    max_stage_nodes = max(
        stage_node_counts,
        default=1
    )

    dynamic_height = max(
        height,
        max_stage_nodes * 78 + 180
    )

    # ========================================================
    # Sankey 생성
    # ========================================================

    fig = go.Figure(
        go.Sankey(

            # fixed 대신 snap 사용
            # 노드 높이와 흐름을 고려해 자동 배치
            arrangement="snap",

            textfont=dict(
                color="#111111",
                size=11,
                family="Inter, Pretendard, sans-serif"
            ),

            node=dict(

                # 노드 사이 픽셀 간격
                pad=34,

                thickness=18,

                line=dict(
                    color="rgba(0,0,0,0)",
                    width=0
                ),

                label=labels,
                customdata=original_labels,
                color=colors,

                # x만 지정하고 y는 지정하지 않음
                x=node_x,

                hovertemplate=(
                    "<b>%{customdata}</b>"
                    "<extra></extra>"
                ),
            ),

            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=link_colors,
                customdata=link_customdata,

                hovertemplate=(
                    "%{customdata}<br>"
                    "<b>%{value:,}건</b>"
                    "<extra></extra>"
                ),
            ),
        )
    )

    fig.update_layout(
        height=dynamic_height,

        margin=dict(
            l=40,
            r=120,
            t=40,
            b=30
        ),

        paper_bgcolor="rgba(0,0,0,0)",

        font=dict(
            family="Inter, Pretendard, sans-serif",
            color=INK,
            size=11
        ),
    )

    return fig

def top_paths(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["사고경로", "사고건수", "비율"])
    paths = df.groupby(STAGES, observed=False).size().reset_index(name="사고건수")
    paths = paths.sort_values("사고건수", ascending=False).head(top_n).reset_index(drop=True)
    paths["사고경로"] = paths[STAGES].astype(str).agg(" → ".join, axis=1)
    paths["비율"] = paths["사고건수"] / max(len(df), 1)
    return paths[["사고경로", "사고건수", "비율"]]
