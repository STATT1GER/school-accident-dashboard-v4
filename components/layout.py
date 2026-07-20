from __future__ import annotations

from pathlib import Path
import streamlit as st

from utils.helper import asset_path


def init_page(title: str, icon: str = "🛡️") -> None:
    st.set_page_config(
        page_title=f"{title} · 학교안전",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    css_path = asset_path("style.css")
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    render_sidebar()


def render_sidebar() -> None:
    with st.sidebar:
        st.image(str(asset_path("logo.png")), width=56)
        st.markdown("<div class='sidebar-brand'>School Safety</div>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-caption'>학교안전 사고관제 데모</div>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-rule'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='demo-note'><b>DEMO DATA</b><br>"
            "이 프로젝트는 실제 원자료가 아닌 합성 예시 데이터를 사용합니다.</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        st.caption("메뉴는 위쪽의 페이지 목록에서 선택하세요.")


def page_header(eyebrow: str, title: str, description: str, badge: str = "합성 데이터") -> None:
    st.markdown(
        f"""
        <div class="page-header">
            <div>
                <div class="eyebrow">{eyebrow}</div>
                <h1>{title}</h1>
                <p>{description}</p>
            </div>
            <div class="status-badge"><span></span>{badge}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, description: str | None = None, right_text: str | None = None) -> None:
    desc = f"<p>{description}</p>" if description else ""
    right = f"<div class='section-right'>{right_text}</div>" if right_text else ""
    st.markdown(
        f"""
        <div class="section-heading">
            <div><h2>{title}</h2>{desc}</div>{right}
        </div>
        """,
        unsafe_allow_html=True,
    )


def panel_start(extra_class: str = "") -> None:
    st.markdown(f"<div class='panel {extra_class}'>", unsafe_allow_html=True)


def panel_end() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def footer() -> None:
    st.markdown(
        """
        <div class="footer">
            <b>학교안전 사고관제 데모</b>
            <span>실제 학교·학생·사고 기록을 포함하지 않는 합성 데이터 기반 UI 시연물입니다.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
