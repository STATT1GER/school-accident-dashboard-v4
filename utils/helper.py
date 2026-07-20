from __future__ import annotations

from pathlib import Path
import html
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def asset_path(name: str) -> Path:
    return PROJECT_ROOT / "assets" / name


def safe_pct(value: float, digits: int = 1) -> str:
    if pd.isna(value):
        return "0.0%"
    return f"{value * 100:.{digits}f}%"


def safe_text(value: object, fallback: str = "-") -> str:
    if value is None or pd.isna(value):
        return fallback
    return html.escape(str(value))


def mode_or(df: pd.DataFrame, column: str, fallback: str = "-") -> str:
    if column not in df.columns or df.empty:
        return fallback
    mode = df[column].dropna().mode()
    return str(mode.iloc[0]) if not mode.empty else fallback


def compact_number(value: int | float) -> str:
    value = float(value)
    if value >= 1_000_000:
        return f"{value/1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value/1_000:.1f}K"
    return f"{int(value):,}"
