from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from utils.color import (
    APPLE_BLUE, APPLE_BLUE_LIGHT, INK, MUTED, HAIRLINE, TIME_ORDER
)


def base_layout(fig: go.Figure, height: int = 380, margin: dict | None = None) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=margin or dict(l=12, r=12, t=32, b=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Pretendard, sans-serif", color=INK, size=13),
        hoverlabel=dict(bgcolor="white", font_size=13, font_color=INK),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=HAIRLINE, tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor="#ECECF0", zeroline=False, tickfont=dict(color=MUTED))
    return fig


def time_profile(df: pd.DataFrame) -> go.Figure:
    counts = (
        df.groupby("사고시간_정리", observed=False)
        .size()
        .reindex(TIME_ORDER, fill_value=0)
        .reset_index(name="사고건수")
    )
    maximum = max(int(counts["사고건수"].max()), 1)
    counts["상대위험도"] = counts["사고건수"] / maximum * 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=counts["사고시간_정리"], y=counts["상대위험도"],
        mode="lines+markers", line=dict(color=APPLE_BLUE, width=3),
        marker=dict(size=9, color="white", line=dict(color=APPLE_BLUE, width=3)),
        fill="tozeroy", fillcolor="rgba(0,102,204,0.08)",
        customdata=counts[["사고건수"]],
        hovertemplate="%{x}<br><b>상대 위험도 %{y:.0f}</b><br>합성 신호 %{customdata[0]:,}건<extra></extra>",
    ))
    fig.update_layout(showlegend=False)
    fig.update_yaxes(title="상대 위험도", range=[0, 110])
    return base_layout(fig, 370)


def category_bar(df: pd.DataFrame, column: str, top_n: int = 10, height: int = 420, color_map: dict | None = None) -> go.Figure:
    temp = df[column].value_counts().head(top_n).sort_values().rename_axis(column).reset_index(name="사고건수")
    colors = [color_map.get(x, APPLE_BLUE_LIGHT) if color_map else APPLE_BLUE_LIGHT for x in temp[column]]
    fig = go.Figure(go.Bar(
        x=temp["사고건수"], y=temp[column], orientation="h",
        marker_color=colors, marker_line_width=0,
        text=temp["사고건수"].map(lambda x: f"{x:,}"), textposition="outside",
        hovertemplate="%{y}<br><b>%{x:,}건</b><extra></extra>",
    ))
    fig.update_layout(showlegend=False)
    return base_layout(fig, height, dict(l=12, r=54, t=24, b=18))


def weekday_time_heatmap(df: pd.DataFrame) -> go.Figure:
    weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일"]
    pivot = pd.crosstab(df["요일"], df["사고시간_정리"]).reindex(index=weekdays, columns=TIME_ORDER, fill_value=0)
    maximum = max(int(pivot.to_numpy().max()), 1)
    risk = pivot / maximum * 100
    fig = go.Figure(go.Heatmap(
        z=risk.values, x=risk.columns, y=risk.index,
        customdata=pivot.values,
        colorscale=[[0, "#F5F5F7"], [0.35, "#BDE0FF"], [1, "#0066CC"]],
        colorbar=dict(title="상대 위험도", thickness=10, len=0.75),
        hovertemplate="%{y} · %{x}<br><b>상대 위험도 %{z:.0f}</b><br>합성 신호 %{customdata:,}건<extra></extra>",
    ))
    return base_layout(fig, 390)


def risk_gauge(score: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"font": {"size": 48, "color": INK}},
        title={"text": "상대 위험도", "font": {"size": 15, "color": MUTED}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 0, "tickfont": {"color": "rgba(0,0,0,0)"}},
            "bar": {"color": APPLE_BLUE, "thickness": 0.22},
            "bgcolor": "#ECECF0", "borderwidth": 0,
            "steps": [{"range": [0, 100], "color": "#ECECF0"}],
        },
    ))
    fig.update_layout(height=280, margin=dict(l=24, r=24, t=40, b=18), paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter, sans-serif"))
    return fig


def floor_distribution(df: pd.DataFrame) -> go.Figure:
    temp = df["층"].value_counts().sort_index().rename_axis("층").reset_index(name="사고건수")
    fig = go.Figure(go.Pie(
        labels=temp["층"].map(lambda x: f"{x}층"), values=temp["사고건수"], hole=0.62,
        marker=dict(colors=["#D9EFFF", "#A7D8FF", "#5AB0F5", "#0066CC"], line=dict(color="white", width=4)),
        hovertemplate="%{label}<br><b>%{value:,}건</b><extra></extra>",
    ))
    fig.update_layout(showlegend=True, annotations=[dict(text="층별", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color=MUTED))])
    return base_layout(fig, 330)
