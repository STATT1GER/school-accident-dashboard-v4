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
                <div class="path-meta">{count:,}건 · 해당 범위의 {share:.1%}</div>
            </div>
            <div class="path-arrow">→</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def intervention_card(
    scope_name: str,
    core_time: str,
    core_place: str,
    activity: str,
    accident_form: str,
    recommendation: str,
    count: int,
    share: float,
) -> None:
    st.markdown(
        f"""
        <div class="intervention-card">
            <div class="intervention-label">RECOMMENDED INTERVENTION · {html.escape(scope_name)}</div>
            <div class="intervention-grid">
                <div><span>핵심 위험시간</span><b>{html.escape(core_time)}</b></div>
                <div><span>핵심 위험장소</span><b>{html.escape(core_place)}</b></div>
            </div>
            <div class="intervention-point">
                <span>우선 개입 시점</span>
                <strong>{html.escape(core_time)} · {html.escape(core_place)}</strong>
            </div>
            <div class="intervention-context">{html.escape(activity)} → {html.escape(accident_form)} · {count:,}건 ({share:.1%})</div>
            <p>{html.escape(recommendation)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
