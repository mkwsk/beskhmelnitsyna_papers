from __future__ import annotations

import os
from typing import Any, Dict, Iterable, Optional

import requests

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

if load_dotenv:
    load_dotenv()


class YandexFormsError(RuntimeError):
    pass


def _env(name: str, default: Optional[str] = None) -> str:
    value = os.environ.get(name, default)
    if value is None or value == "":
        raise YandexFormsError(f"Environment variable {name} is not set")
    return value


class YandexFormsClient:
    def __init__(self) -> None:
        self.base_url = os.environ.get("FORMS_PUBLIC_API", "https://api.forms.yandex.net/v1").rstrip("/")
        token = _env("FORMS_TOKEN")
        org_id = _env("ORG_ID")
        org_header = os.environ.get("ORG_HEADER", "X-Org-Id")
        auth_scheme = os.environ.get("AUTH_SCHEME", "OAuth")
        self.headers = {
            "Authorization": f"{auth_scheme} {token}",
            org_header: org_id,
        }

    def _request(self, method: str, path: str, *, expected: Iterable[int] = (200,), **kwargs: Any) -> requests.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = requests.request(method, url, headers=self.headers, timeout=60, **kwargs)
        if response.status_code not in set(expected):
            raise YandexFormsError(f"{method} {url} failed: {response.status_code} {response.text}")
        return response

    def create_survey(self, payload: Dict[str, Any]) -> str:
        response = self._request("POST", "/surveys/", json=payload, expected=(201,))
        return response.json()["id"]

    def add_question(self, survey_id: str, payload: Dict[str, Any]) -> int:
        response = self._request("POST", f"/surveys/{survey_id}/questions/", json=payload, expected=(201,))
        return int(response.json()["id"])

    def move_question(self, survey_id: str, question_id: int, payload: Dict[str, Any]) -> None:
        self._request("POST", f"/surveys/{survey_id}/questions/{question_id}/move/", json=payload, expected=(200,))

    def publish(self, survey_id: str) -> None:
        self._request("POST", f"/surveys/{survey_id}/publish/", expected=(200,))

    def unpublish(self, survey_id: str) -> None:
        self._request("POST", f"/surveys/{survey_id}/unpublish/", expected=(200,))

    def fetch_answers_page(self, survey_id: str, *, page_size: int = 50, next_path: Optional[str] = None) -> Dict[str, Any]:
        if next_path:
            path = next_path
            if path.startswith("/v1"):
                path = path[3:]
        else:
            path = f"/surveys/{survey_id}/answers?page_size={page_size}"
        response = self._request("GET", path, expected=(200,))
        return response.json()
