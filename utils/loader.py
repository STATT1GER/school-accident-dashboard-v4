from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from utils.helper import PROJECT_ROOT
from utils.preprocess import preprocess_data, validate_columns


@st.cache_data(show_spinner=False)
def load_sample_data() -> pd.DataFrame:
    path = PROJECT_ROOT / "data" / "sample.csv"
    data = pd.read_csv(path, encoding="utf-8-sig")
    return preprocess_data(data)


@st.cache_data(show_spinner=False)
def load_uploaded_data(file_name: str, file_bytes: bytes) -> pd.DataFrame:
    from io import BytesIO
    buffer = BytesIO(file_bytes)
    suffix = Path(file_name).suffix.lower()
    if suffix == ".csv":
        try:
            data = pd.read_csv(buffer, encoding="utf-8-sig")
        except UnicodeDecodeError:
            buffer.seek(0)
            data = pd.read_csv(buffer, encoding="cp949")
    elif suffix in {".xlsx", ".xls"}:
        data = pd.read_excel(buffer)
    else:
        raise ValueError("CSV 또는 XLSX 파일만 지원합니다.")

    missing = validate_columns(data)
    if missing:
        raise ValueError("필수 열 누락: " + ", ".join(missing))
    return preprocess_data(data)
