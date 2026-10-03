"""
날씨 예보 프로그램 (Open-Meteo API 사용)
- 사용자에게 지역을 입력받음 (기본값: 천안)
- 오늘, 내일, 모레까지 3일간의 날씨를 오전 6시, 오후 3시 기준으로 표시
- Open-Meteo API 사용 (인증키 불필요, 무료)

GitHub 날씨 리포트 링크: https://github.com/<내_아이디>/<저장소_이름>
"""

import json
from datetime import datetime
from typing import Optional

import requests

DEFAULT_CITY = "천안"
FORECAST_DAYS = 3                      # 2일 이상 자유롭게 설정 가능
TARGET_HOURS = [(6, "🌅 오전"), (15, "🌇 오후")]
DAY_LABELS = ["오늘", "내일", "모레", "글피", "그글피"]

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# 자주 쓰는 지역은 좌표를 미리 등록 (없으면 지오코딩 API로 검색)
KNOWN_CITIES = {
    "서울": (37.5665, 126.9780),
    "부산": (35.1796, 129.0756),
    "천안": (36.8151, 127.1139),
    "대전": (36.3504, 127.3845),
    "대구": (35.8714, 128.6014),
    "광주": (35.1595, 126.8526),
    "제주": (33.4996, 126.5312),
}

# WMO 날씨 코드 -> 한글 설명
WEATHER_CODES = {
    0: "맑음", 1: "대체로 맑음", 2: "구름 조금", 3: "흐림",
    45: "안개", 48: "서리 안개",
    51: "약한 이슬비", 53: "이슬비", 55: "강한 이슬비",
    61: "약한 비", 63: "비", 65: "강한 비",
    71: "약한 눈", 73: "눈", 75: "강한 눈",
    80: "약한 소나기", 81: "소나기", 82: "강한 소나기",
    95: "뇌우", 96: "우박을 동반한 뇌우", 99: "강한 우박을 동반한 뇌우",
}


def get_coordinates(city: str) -> Optional[tuple]:
    """도시 이름 -> (위도, 경도)"""
    if city in KNOWN_CITIES:
        return KNOWN_CITIES[city]
    try:
        res = requests.get(
            GEOCODING_URL,
            params={"name": city, "count": 1, "language": "ko"},
            timeout=10,
        )
        res.raise_for_status()
        results = res.json().get("results")
        if results:
            return results[0]["latitude"], results[0]["longitude"]
    except requests.RequestException as e:
        print(f"❌ 지역 검색 중 오류가 발생했습니다: {e}")
    return None