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
    show_viewport_guide()

 

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

@st.dialog("화면 표시 안내")
def _show_viewport_dialog() -> None:
    st.markdown(
        """
        이 대시보드는 넓은 화면에 최적화되어 있습니다.

        화면에서 글자나 그래프가 겹치거나 오른쪽으로 밀려 보인다면
        브라우저 화면 비율을 조정해 주세요.
        """
    )

    st.info(
        """
        **권장 화면 비율: 80%~100%**

        - 화면 축소: `Ctrl` + `-`
        - 화면 확대: `Ctrl` + `+`
        - 기본 비율로 복원: `Ctrl` + `0`

        Mac에서는 `Ctrl` 대신 `⌘ Command`를 사용해 주세요.
        """
    )

    st.caption(
        "화면이 정상적으로 보이면 별도의 조정 없이 그대로 이용하셔도 됩니다."
    )

    st.markdown(
        """
        <div style="
            margin-top: 14px;
            margin-bottom: 16px;
            padding: 13px 15px;
            background: #F5F5F7;
            border: 1px solid #E5E5EA;
            border-radius: 12px;
            font-size: 13px;
            line-height: 1.6;
            color: #1D1D1F;
        ">
            <b>대시보드 관련 문의</b><br>
            대시보드가 정상적으로 작동하지 않는다면
            <a href="tel:01065637891"
               style="color:#0066CC; font-weight:700; text-decoration:none;">
                010-6563-7891
            </a>
            으로 연락 혹은 문자 부탁드립니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "대시보드 시작하기",
        type="primary",
        use_container_width=True,
        key="viewport_guide_close",
    ):
        st.rerun()

def show_viewport_guide() -> None:
    """
    사용자가 앱에 처음 접속했을 때 화면 비율 안내 팝업을 한 번 표시합니다.

    페이지 이동이나 위젯 조작으로 앱이 다시 실행되더라도
    동일한 접속 세션에서는 다시 표시하지 않습니다.
    """

    state_key = "viewport_guide_seen"

    if not st.session_state.get(state_key, False):
        # 팝업을 호출하기 전에 True로 바꿔야
        # 사용자가 X 버튼으로 닫더라도 다음 실행에서 반복되지 않습니다.
        st.session_state[state_key] = True
        _show_viewport_dialog()

