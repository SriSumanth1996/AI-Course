from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from services.keys import weather_api_key

_WEATHER_QUESTION = re.compile(
    r"\b("
    r"weather|forecast|temperature|humidity|rainfall|raining|rain|"
    r"snow|snowing|wind|windy|sunny|cloudy|umbrella|celsius|fahrenheit|"
    r"how hot|how cold|how warm"
    r")\b",
    re.IGNORECASE,
)
_PLACE_PATTERNS = (
    re.compile(
        r"\b(?:in|at|for|around|near)\s+([a-zA-Z][\w .'-]{0,40})",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b([a-zA-Z][\w .'-]{0,40}?)\s+(?:weather|forecast|temperature)\b",
        re.IGNORECASE,
    ),
)
_PLACE_TAIL = re.compile(
    r"\b(today|tomorrow|tonight|now|please|right|currently|this|morning|evening)\b.*$",
    re.IGNORECASE,
)
_NOT_A_PLACE = re.compile(
    r"\b(what|whats|what's|how|when|where|why|who|is|the|a|an|will|does|do)\b",
    re.IGNORECASE,
)


class WeatherError(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


WEATHER_DECISION_MODEL = "gpt-4o-mini"

WEATHER_DECISION_PROMPT = (
    "Decide whether the user question is about weather. "
    "A misspelling such as wether still counts when the question asks about "
    "conditions, the forecast, temperature, rain, wind, or humidity. "
    'Reply with only one JSON object: {"weather": true} or {"weather": false}. '
    "Do not name a place. Do not answer the question."
)

WEATHER_QUERY_PROMPT = (
    "This question is about weather. "
    "Return only the JSON object the Weather API current request needs. "
    "Use one field, q, set to the place named in the question. "
    "Keep the place words the user wrote. "
    "If the question names no place, set q to auto:ip. "
    'Example: {"q": "Mumbai"}'
)

WEATHER_ANSWER_NOTE = (
    "This question is about weather. "
    "Use the Weather API reading below for the conditions."
)


def is_weather_question(text: str) -> bool:
    return bool(_WEATHER_QUESTION.search(text or ""))


def _json_object(text: str) -> dict | None:
    raw = (text or "").strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.IGNORECASE | re.DOTALL)
    if fenced:
        raw = fenced.group(1).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        payload = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def parse_weather_decision(text: str) -> bool | None:
    payload = _json_object(text)
    if not payload or "weather" not in payload:
        return None
    value = payload["weather"]
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    return None


def parse_weather_query(text: str) -> str | None:
    payload = _json_object(text)
    if not payload:
        return None
    place = payload.get("q")
    if not isinstance(place, str):
        return None
    place = place.strip()
    return place or None


def place_from_question(text: str) -> str:
    for pattern in _PLACE_PATTERNS:
        match = pattern.search(text or "")
        if not match:
            continue
        place = _PLACE_TAIL.sub("", match.group(1))
        place = place.strip(" ?.,!\"'")
        if (
            place
            and place.lower() not in {"the", "a", "an", "my", "our"}
            and not _NOT_A_PLACE.search(place)
        ):
            return place
    return "auto:ip"


def attach_reading(
    messages: list[dict[str, str]],
    report: str,
    *,
    note: str = "",
) -> list[dict[str, str]]:
    reading = (report or "").strip()
    if not reading:
        return messages
    copied = [dict(message) for message in messages]
    lead = (note or "").strip()
    block = f"{lead}\n\n" if lead else ""
    for index in range(len(copied) - 1, -1, -1):
        if copied[index].get("role") != "user":
            continue
        copied[index]["content"] = (
            copied[index].get("content", "").rstrip()
            + "\n\n"
            + block
            + "Weather API reading:\n"
            + reading
        )
        break
    return copied


def _error_from_body(body: str, status: int) -> WeatherError:
    message = body.strip()
    try:
        payload = json.loads(body)
        message = str((payload.get("error") or {}).get("message") or message)
    except json.JSONDecodeError:
        pass
    low = message.lower()
    if status in {401, 403} or "api key" in low or "unauthorized" in low:
        code = "401"
    elif status == 402 or "quota" in low or "credit" in low:
        code = "402"
    elif status == 429 or "rate" in low:
        code = "429"
    elif status >= 500:
        code = "5xx"
    else:
        code = "connection"
    return WeatherError(code, f"Weather API could not answer: {message}")


def weather_request_url(place: str, key: str) -> str:
    query = urlencode({"key": key, "q": place or "auto:ip", "aqi": "no"})
    return f"https://api.weatherapi.com/v1/current.json?{query}"


def current_weather(place: str, *, api_key: str | None = None) -> str:
    if api_key is None:
        api_key = weather_api_key()
        if not api_key:
            raise WeatherError(
                "401",
                "Weather API could not answer: the API key was not found.",
            )
    url = weather_request_url(place, api_key)
    try:
        with urlopen(url, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise _error_from_body(detail, exc.code) from exc
    except TimeoutError as exc:
        raise WeatherError(
            "timeout",
            "Weather API could not answer: the request timed out.",
        ) from exc
    except URLError as exc:
        raise WeatherError(
            "connection",
            f"Weather API could not answer: {exc.reason}",
        ) from exc
    location = payload.get("location") or {}
    current = payload.get("current") or {}
    condition = (current.get("condition") or {}).get("text") or "Unknown"
    name = location.get("name") or place
    region = location.get("region") or ""
    country = location.get("country") or ""
    where = ", ".join(part for part in (name, region, country) if part)
    return (
        f"Place: {where}\n"
        f"Local time: {location.get('localtime') or 'unknown'}\n"
        f"Condition: {condition}\n"
        f"Temperature: {current.get('temp_c')} C\n"
        f"Feels like: {current.get('feelslike_c')} C\n"
        f"Humidity: {current.get('humidity')}%\n"
        f"Wind: {current.get('wind_kph')} km/h"
    )
