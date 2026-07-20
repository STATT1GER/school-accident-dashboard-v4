from __future__ import annotations

import numpy as np
import pandas as pd

from utils.color import TIME_ORDER

REQUIRED_COLUMNS = [
    "사고ID", "연도", "사고일자", "월", "요일", "학년",
    "사고시간_정리", "사고장소_정리", "사고당시활동_정리", "사고형태_정리"
]


def validate_columns(df: pd.DataFrame) -> list[str]:
    return [col for col in REQUIRED_COLUMNS if col not in df.columns]


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["사고일자"] = pd.to_datetime(data["사고일자"], errors="coerce")
    data["연도"] = pd.to_numeric(data["연도"], errors="coerce").astype("Int64")
    data["월"] = pd.to_numeric(data["월"], errors="coerce").astype("Int64")
    data["학년"] = pd.to_numeric(data["학년"], errors="coerce").astype("Int64")
    data["층"] = pd.to_numeric(data.get("층", 1), errors="coerce").fillna(1).astype(int)
    data["지도X"] = pd.to_numeric(data.get("지도X", np.nan), errors="coerce")
    data["지도Y"] = pd.to_numeric(data.get("지도Y", np.nan), errors="coerce")

    if "학년급" not in data.columns:
        data["학년급"] = np.where(data["학년"].le(2), "저학년", "고학년")

    data["시간순서"] = pd.Categorical(data["사고시간_정리"], categories=TIME_ORDER, ordered=True)
    data["일자"] = data["사고일자"].dt.date
    data["연월"] = data["사고일자"].dt.to_period("M").astype(str)
    return data
