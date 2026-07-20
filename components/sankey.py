from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from utils.color import APPLE_BLUE, APPLE_BLUE_LIGHT, SUCCESS, WARNING, INK

STAGES = ["사고시간_정리", "사고장소_정리", "사고당시활동_정리", "사고형태_정리"]
STAGE_COLORS = [APPLE_BLUE, APPLE_BLUE_LIGHT, SUCCESS, WARNING]


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


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
        fig.add_annotation(text="표시할 사고경로가 없습니다.", showarrow=False, x=0.5, y=0.5)
        fig.update_layout(height=height, paper_bgcolor="rgba(0,0,0,0)")
        return fig

    if top_n_per_stage is not None:
        for col in STAGES:
            keep = set(work[col].value_counts().head(top_n_per_stage).index)
            if aggregate_other:
                work[col] = work[col].where(work[col].isin(keep), "기타")
            else:
                work = work[work[col].isin(keep)]

    labels: list[str] = []
    colors: list[str] = []
    node_index: dict[str, int] = {}
    for stage_idx, col in enumerate(STAGES):
        values = list(work[col].value_counts().index)
        for value in values:
            key = f"{stage_idx}|{value}"
            node_index[key] = len(labels)
            labels.append(value)
            colors.append(_rgba(STAGE_COLORS[stage_idx], 0.92))

    sources: list[int] = []
    targets: list[int] = []
    values: list[int] = []
    link_colors: list[str] = []
    for stage_idx in range(len(STAGES) - 1):
        link = work.groupby([STAGES[stage_idx], STAGES[stage_idx + 1]], observed=False).size().reset_index(name="count")
        link = link[link["count"] >= max(1, min_count)]
        for _, row in link.iterrows():
            source_key = f"{stage_idx}|{row[STAGES[stage_idx]]}"
            target_key = f"{stage_idx + 1}|{row[STAGES[stage_idx + 1]]}"
            if source_key not in node_index or target_key not in node_index:
                continue
            sources.append(node_index[source_key])
            targets.append(node_index[target_key])
            values.append(int(row["count"]))
            link_colors.append(_rgba(STAGE_COLORS[stage_idx], 0.18))

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            pad=18, thickness=18,
            line=dict(color="rgba(0,0,0,0)", width=0),
            label=labels, color=colors,
            hovertemplate="%{label}<extra></extra>",
        ),
        link=dict(
            source=sources, target=targets, value=values, color=link_colors,
            hovertemplate="%{source.label} → %{target.label}<br><b>%{value:,}건</b><extra></extra>",
        ),
    ))
    fig.update_layout(
        height=height, margin=dict(l=18, r=18, t=28, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Pretendard, sans-serif", color=INK, size=12),
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
