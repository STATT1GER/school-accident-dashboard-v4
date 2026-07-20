# 학교안전 사고경로 관제 대시보드 v4

학교안전사고의 **시간 → 장소 → 활동 → 사고형태** 경로를 중심으로 위험신호와 개입 지점을 보여주는 Streamlit UI 프로토타입입니다.

## v4 핵심 방향

- 단순 EDA보다 **사고경로를 최우선**으로 표시합니다.
- 특정 미래 날짜를 예측하는 모델이 아닙니다.
- 합성 데이터에서 반복되는 흐름을 **상대 위험도**로 표현합니다.
- 사고심각도는 보상·진단 근거가 없으므로 사용하지 않습니다.
- 사고분석 첫 탭은 `사고경로`이며, 전체·저학년·고학년을 구분합니다.
- Sankey는 `간단히 보기`와 `자세히 보기`를 모두 제공합니다.

## 데이터 안내

이 프로젝트에는 실제 학교안전사고 원자료가 포함되어 있지 않습니다.

- `data/sample.csv`는 합성 예시 데이터입니다.
- 실제 학교명, 학생정보, 실제 사고ID, 개별 사고기록을 포함하지 않습니다.
- `심각도` 필드는 제거했습니다.
- 지도는 실제 학교와 관계없는 가상 배치도입니다.

## 화면 구성

1. **메인 화면**
   - 축소된 경로 중심 메시지 패널
   - 확대된 가상학교 안전지도

2. **오늘의 학교 안전상황**
   - 상대 위험도
   - 핵심 4단계 사고경로
   - 반복 사고경로 TOP 3
   - 일과 상대 위험 흐름
   - 보조 위험장소 순위

3. **학교지도**
   - 연도 선택 제거
   - 층 선택형 버튼
   - 일과 구간 선택형 버튼
   - 동일 가상학교 지도 위 상대 위험 히트맵

4. **사고분석**
   - 사고경로 → 시간 분석 → 장소 분석 → 활동·형태 순서
   - 전체·저학년·고학년 경로 탭
   - 간단 Sankey / 상세 Sankey
   - 월별 추이 제거
   - 요일 × 사고시간 전체 너비
   - 장소 선택형 활동 분포
   - 활동 선택형 사고형태 분포
   - 사고심각도 및 활동×형태 히트맵 제거

## 실행 방법

프로젝트 폴더에서 PowerShell을 열고 실행합니다.

```powershell
uv sync
uv run python -m streamlit run app.py
```

`uv sync`가 실행되면 `.venv`가 생성됩니다. v4의 `.vscode/settings.json`에는 존재하지 않는 `.venv\Scripts\python.exe`를 미리 강제 지정하지 않으므로, 가상환경 생성 전 인터프리터 경고가 발생하지 않습니다.

가상환경 생성 후 VS Code에서:

1. `Ctrl + Shift + P`
2. `Python: Select Interpreter`
3. `.venv\Scripts\python.exe` 선택

## 프로젝트 구조

```text
school_accident_dashboard_v4/
├── app.py
├── pages/
├── components/
├── utils/
├── assets/
├── data/sample.csv
├── .streamlit/config.toml
├── .vscode/
├── pyproject.toml
├── requirements.txt
├── V4_DESIGN_SPEC.md
└── README.md
```
