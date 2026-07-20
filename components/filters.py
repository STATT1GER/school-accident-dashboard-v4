from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.color import TIME_ORDER


def analysis_filters(df: pd.DataFrame, key_prefix: str = "analysis") -> dict:
    years = sorted(int(x) for x in df["연도"].dropna().unique())
    available_times = set(df["사고시간_정리"].dropna().astype(str).unique())
    times = [x for x in TIME_ORDER if x in available_times]
    places = sorted(df["사고장소_정리"].dropna().astype(str).unique())

    with st.container():
        st.markdown("<div class='filter-title'>분석 조건</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([0.9, 1.5, 1.5])
        with c1:
            year = st.multiselect("연도", years, default=years, key=f"{key_prefix}_year")
        with c2:
            time = st.multiselect("사고시간", times, default=times, key=f"{key_prefix}_time")
        with c3:
            place = st.multiselect("사고장소", places, default=places, key=f"{key_prefix}_place")

    return {"year": year, "time": time, "place": place}


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    out = df.copy()
    if filters.get("year"):
        out = out[out["연도"].isin(filters["year"])]
    if filters.get("time"):
        out = out[out["사고시간_정리"].isin(filters["time"])]
    if filters.get("place"):
        out = out[out["사고장소_정리"].isin(filters["place"])]
    return out
