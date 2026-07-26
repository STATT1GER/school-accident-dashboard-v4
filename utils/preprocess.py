from __future__ import annotations

import numpy as np
import pandas as pd

from utils.color import TIME_ORDER
from utils.map_geometry import apply_virtual_map_coordinates

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

    if "학년급" not in data.columns:
        data["학년급"] = np.where(data["학년"].le(2), "저학년", "고학년")

    # 실제 분석자료에 층 변수가 없으므로 UI와 분석 데이터에서도 사용하지 않습니다.
    data = data.drop(columns=["층"], errors="ignore")
    data = apply_virtual_map_coordinates(data)

    data["시간순서"] = pd.Categorical(data["사고시간_정리"], categories=TIME_ORDER, ordered=True)
    data["일자"] = data["사고일자"].dt.date
    data["연월"] = data["사고일자"].dt.to_period("M").astype(str)
    return data
