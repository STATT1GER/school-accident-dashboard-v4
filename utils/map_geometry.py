from __future__ import annotations

import hashlib

import pandas as pd

# assets/school_map.png의 0~100 상대좌표에 맞춘 가상학교 1층 앵커입니다.
CLASSROOM_ANCHORS = [
    (18.0, 27.0), (32.0, 27.0), (46.0, 27.0), (60.0, 27.0),
    (18.0, 70.0), (32.0, 70.0), (60.0, 70.0),
]
MOBILITY_ANCHORS = [(11.0, 50.0), (39.0, 50.0), (68.0, 50.0)]

PLACE_ANCHORS: dict[str, tuple[str, list[tuple[float, float]]]] = {
    "강당·체육관": ("강당", [(84.0, 27.0)]),
    "강당(체육관)": ("강당", [(84.0, 27.0)]),
    "강당": ("강당", [(84.0, 27.0)]),
    "운동장": ("운동장", [(84.0, 75.0)]),
    "놀이터·기타 체육공간": ("운동장", [(84.0, 75.0)]),
    "교실·학습공간": ("교실·학습공간", CLASSROOM_ANCHORS),
    "계단·복도": ("계단·복도", MOBILITY_ANCHORS),
    "계단, 복도": ("계단·복도", MOBILITY_ANCHORS),
    "급식·위생공간": ("급식실", [(84.0, 51.0)]),
    "급식·위생·보건공간": ("급식실", [(84.0, 51.0)]),
    "화장실·위생공간": ("보건·위생공간", [(47.0, 70.0)]),
    "보건·위생공간": ("보건·위생공간", [(47.0, 70.0)]),
    "교무실·행정실": ("교실·학습공간", [(60.0, 70.0)]),
    "교문·외부동선": ("정문·외부동선", [(40.0, 90.0)]),
    "교통공간": ("정문·외부동선", [(40.0, 90.0)]),
    "교외·체험·자연공간": ("정문·외부동선", [(40.0, 90.0)]),
}


def _stable_parts(identifier: object) -> tuple[int, int, int]:
    digest = hashlib.sha256(str(identifier).encode("utf-8")).digest()
    return digest[0], digest[1], digest[2]


def virtual_map_position(place: object, identifier: object) -> tuple[str, float, float]:
    """사고장소 범주를 가상학교 1층 지도상의 재현 가능한 시연 좌표로 변환합니다."""
    place_text = str(place)
    zone, anchors = PLACE_ANCHORS.get(
        place_text,
        ("기타 학교공간", [(39.0, 50.0)]),
    )
    a, b, c = _stable_parts(identifier)
    anchor_x, anchor_y = anchors[a % len(anchors)]

    # 실행할 때마다 바뀌지 않는 작은 흔들림입니다. 실제 사고 지점을 뜻하지 않습니다.
    jitter_x = ((b / 255.0) - 0.5) * (3.6 if zone != "계단·복도" else 4.8)
    jitter_y = ((c / 255.0) - 0.5) * (3.2 if zone != "계단·복도" else 2.0)
    x = min(98.0, max(2.0, anchor_x + jitter_x))
    y = min(98.0, max(2.0, anchor_y + jitter_y))
    return zone, round(x, 2), round(y, 2)


def apply_virtual_map_coordinates(data: pd.DataFrame) -> pd.DataFrame:
    """지도용 층 정보를 사용하지 않고 모든 행을 1층 가상 배치도에 재매핑합니다."""
    out = data.copy()
    identifiers = out.get("사고ID", out.index.astype(str))
    mapped = [
        virtual_map_position(place, identifier)
        for place, identifier in zip(out["사고장소_정리"], identifiers)
    ]
    mapped_df = pd.DataFrame(mapped, columns=["지도구역", "지도X", "지도Y"], index=out.index)
    out[["지도구역", "지도X", "지도Y"]] = mapped_df
    return out
