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



def fetch_weather(lat: float, lon: float) -> Optional[dict]:
    """Open-Meteo에서 시간별/일별 예보 가져오기"""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation_probability,"
                  "relative_humidity_2m,wind_speed_10m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min",
        "wind_speed_unit": "ms",
        "timezone": "Asia/Seoul",
        "forecast_days": FORECAST_DAYS,
    }
    try:
        res = requests.get(FORECAST_URL, params=params, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"❌ 날씨 정보를 가져오지 못했습니다: {e}")
        return None

    

def build_report(city: str, data: dict) -> tuple:
    """화면 출력용 텍스트와 JSON 저장용 데이터를 함께 만든다."""
    hourly, daily = data["hourly"], data["daily"]
    lines, saved = [], {"city": city, "days": []}
    bar = "=" * 70
    sub = "-" * 56

    lines += [bar, f"🌤️ {city} 날씨 예보 (오전 6시 / 오후 3시 기준)", bar]

    for i, date_str in enumerate(daily["time"]):
        d = datetime.strptime(date_str, "%Y-%m-%d")
        label = DAY_LABELS[i] if i < len(DAY_LABELS) else f"{i}일 후"
        lines += ["", f"📅 {label} ({d:%m.%d.})", sub]
        day_info = {"date": date_str, "times": {}}

        for hour, title in TARGET_HOURS:
            idx = hourly["time"].index(f"{date_str}T{hour:02d}:00")
            info = {
                "날씨": WEATHER_CODES.get(hourly["weather_code"][idx], "알 수 없음"),
                "기온": round(hourly["temperature_2m"][idx]),
                "강수확률": hourly["precipitation_probability"][idx],
                "습도": hourly["relative_humidity_2m"][idx],
                "풍속": round(hourly["wind_speed_10m"][idx]),
            }
            day_info["times"][f"{hour:02d}:00"] = info
            lines += [
                f"  {title} {hour:02d}:00",
                f"    날씨: {info['날씨']}",
                f"    기온: {info['기온']} °C",
                f"    강수확률: {info['강수확률']}%",
                f"    습도: {info['습도']}%",
                f"    풍속: {info['풍속']} m/s",
                "",
            ]

        tmin = round(daily["temperature_2m_min"][i])
        tmax = round(daily["temperature_2m_max"][i])
        day_info["최저기온"], day_info["최고기온"] = tmin, tmax
        lines += [f"  🌡️ 일일 기온: 최저 {tmin} °C / 최고 {tmax} °C", "", bar]
        saved["days"].append(day_info)

    return "\n".join(lines), saved