from __future__ import annotations

import html
import streamlit as st


def kpi_card(label: str, value: str, delta: str = "", tone: str = "blue", caption: str = "") -> None:
    delta_html = f"<div class='kpi-delta {tone}'>{html.escape(delta)}</div>" if delta else ""
    caption_html = f"<div class='kpi-caption'>{html.escape(caption)}</div>" if caption else ""
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{html.escape(label)}</div>
            <div class="kpi-row">
                <div class="kpi-value">{html.escape(value)}</div>{delta_html}
            </div>
            {caption_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_card(title: str, body: str, label: str = "INSIGHT", tone: str = "blue") -> None:
    st.markdown(
        f"""
        <div class="insight-card {tone}">
            <div class="insight-label">{html.escape(label)}</div>
            <h3>{html.escape(title)}</h3>
            <p>{html.escape(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def risk_row(rank: int, name: str, count: int, share: float, tone: str = "blue") -> None:
    width = max(4, min(100, share * 100))
    st.markdown(
        f"""
        <div class="risk-row">
            <div class="risk-rank">{rank:02d}</div>
            <div class="risk-main">
                <div class="risk-title"><b>{html.escape(name)}</b><span>{count:,}건 · {share:.1%}</span></div>
                <div class="risk-track"><div class="risk-fill {tone}" style="width:{width:.1f}%"></div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def path_card(path: str, count: int, share: float, rank: int = 1) -> None:
    st.markdown(
        f"""
        <div class="path-card">
            <div class="path-rank">#{rank}</div>
            <div class="path-content">
                <div class="path-route">{html.escape(path)}</div>
                <div class="path-meta">{count:,}건 · 전체 경로의 {share:.1%}</div>
            </div>
            <div class="path-arrow">→</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def path_focus_card(path: str, count: int, share: float, label: str = "핵심 사고경로") -> None:
    stages = [part.strip() for part in str(path).split("→")]
    while len(stages) < 4:
        stages.append("-")
    stage_names = ["시간", "장소", "활동", "사고형태"]
    stage_html = ""
    for idx, (stage_name, value) in enumerate(zip(stage_names, stages[:4])):
        arrow = "<div class='path-focus-arrow'>→</div>" if idx < 3 else ""
        stage_html += (
            "<div class='path-focus-stage'>"
            f"<span>{html.escape(stage_name)}</span><b>{html.escape(value)}</b>"
            "</div>" + arrow
        )
    st.markdown(
        f"""
        <div class="path-focus-card">
            <div class="path-focus-top">
                <div><span>{html.escape(label)}</span><h3>반복되는 4단계 위험 흐름</h3></div>
                <div class="path-focus-metric"><b>{count:,}건</b><span>{share:.1%}</span></div>
            </div>
            <div class="path-focus-grid">{stage_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
