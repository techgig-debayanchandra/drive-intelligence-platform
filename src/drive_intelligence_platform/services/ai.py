"""AI-backed recommendation generation across multiple providers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol
from urllib import error, request

from openai import OpenAI

from drive_intelligence_platform.core.config import AppSettings
from drive_intelligence_platform.schemas import RecommendationPayload, ScannedFile


class RecommendationServiceProtocol(Protocol):
    """Protocol for AI recommendation providers."""

    def recommend(self, file_item: ScannedFile, context: dict[str, object]) -> RecommendationPayload | None:
        """Return a structured recommendation or ``None`` when unavailable."""

    def recommend_folder_group(self, files: list[ScannedFile], context: dict[str, object]) -> dict[str, object] | None:
        """Return a folder-level recommendation plan or ``None`` when unavailable."""


def create_ai_recommendation_service(settings: AppSettings) -> RecommendationServiceProtocol | None:
    """Build the configured AI recommendation provider."""

    provider = settings.ai_provider.lower()
    if provider == "disabled":
        return None
    if provider == "ollama":
        return OllamaRecommendationService.from_settings(settings)
    return OpenAIRecommendationService.from_settings(settings)


class OpenAIRecommendationService:
    """Generate organization recommendations with an OpenAI model when heuristics are uncertain."""

    def __init__(self, settings: AppSettings, client: OpenAI | None = None) -> None:
        self.settings = settings
        self.client = client if client is not None else self._build_client(settings)

    @classmethod
    def from_settings(cls, settings: AppSettings) -> "OpenAIRecommendationService | None":
        """Create a service only when an API key is configured."""

        if not settings.openai_api_key:
            return None
        return cls(settings)

    def recommend(self, file_item: ScannedFile, context: dict[str, object]) -> RecommendationPayload | None:
        """Ask the model for a structured recommendation.

        Returns ``None`` if the call fails or the response cannot be parsed.
        """

        if self.client is None:
            return None

        prompt = self._build_prompt(file_item, context)
        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": "You classify files into archive organization folders. Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            content = response.choices[0].message.content or "{}"
            payload = json.loads(content)
            return self._payload_to_recommendation(file_item, payload, default_reason="AI recommendation")
        except Exception:
            return None

    def recommend_folder_group(self, files: list[ScannedFile], context: dict[str, object]) -> dict[str, object] | None:
        """Ask the model for a single folder-level organization decision."""

        if self.client is None or not files:
            return None

        prompt = self._build_folder_prompt(files, context)
        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a folder-organization planner. Return only valid JSON and prioritize preserving cohesive folders.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
        except Exception:
            return None

    def _build_client(self, settings: AppSettings) -> OpenAI | None:
        """Create an OpenAI client when an API key is configured."""

        if not settings.openai_api_key:
            return None
        return OpenAI(api_key=settings.openai_api_key)

    def _build_prompt(self, file_item: ScannedFile, context: dict[str, object]) -> str:
        """Build a concise JSON-oriented prompt."""

        return json.dumps(
            {
                "file": {
                    "path": str(file_item.path),
                    "name": file_item.name,
                    "extension": file_item.extension,
                    "folder_path": str(file_item.folder_path),
                    "file_kind": file_item.file_kind,
                    "size_bytes": file_item.size_bytes,
                },
                "context": context,
                "required_output": {
                    "category": "string",
                    "subcategory": "string",
                    "suggested_folder": "string",
                    "reason": "string",
                    "confidence": "number between 0 and 1",
                },
            },
            indent=2,
        )

    def _build_folder_prompt(self, files: list[ScannedFile], context: dict[str, object]) -> str:
        """Build folder-level planning prompt."""

        return json.dumps(
            {
                "folder": {
                    "path": str(files[0].folder_path),
                    "file_count": len(files),
                    "kinds": sorted({item.file_kind for item in files}),
                    "extensions": sorted({item.extension for item in files}),
                    "sample_files": [item.name for item in files[:25]],
                },
                "context": context,
                "required_output": {
                    "preserve_folder": "boolean",
                    "suggested_folder": "string",
                    "reason": "string",
                    "confidence": "number between 0 and 1",
                    "category": "string",
                    "subcategory": "string",
                },
            },
            indent=2,
        )

    def _payload_to_recommendation(
        self,
        file_item: ScannedFile,
        payload: dict[str, object],
        default_reason: str,
    ) -> RecommendationPayload:
        """Convert model JSON into RecommendationPayload."""

        return RecommendationPayload(
            source_path=file_item.path,
            category=str(payload.get("category", "Unsorted")),
            subcategory=str(payload.get("subcategory", "")),
            suggested_folder=Path(str(payload.get("suggested_folder", "Archives/Unsorted"))),
            reason=str(payload.get("reason", default_reason)),
            confidence=float(payload.get("confidence", 0.5)),
        )


class OllamaRecommendationService:
    """Generate organization recommendations with a local Ollama model."""

    def __init__(self, settings: AppSettings, api_url: str, timeout_seconds: float = 45.0) -> None:
        self.settings = settings
        self.api_url = api_url
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_settings(cls, settings: AppSettings) -> "OllamaRecommendationService":
        """Create an Ollama provider using configured endpoint/model."""

        base_url = settings.ollama_base_url.rstrip("/")
        return cls(settings, api_url=f"{base_url}/api/generate", timeout_seconds=settings.ai_request_timeout_s)

    def recommend(self, file_item: ScannedFile, context: dict[str, object]) -> RecommendationPayload | None:
        """Query Ollama and parse a JSON recommendation."""

        model_payload = self._generate_json(self._build_prompt(file_item, context))
        if model_payload is None:
            return None
        return RecommendationPayload(
            source_path=file_item.path,
            category=str(model_payload.get("category", "Unsorted")),
            subcategory=str(model_payload.get("subcategory", "")),
            suggested_folder=Path(str(model_payload.get("suggested_folder", "Archives/Unsorted"))),
            reason=str(model_payload.get("reason", "Ollama recommendation")),
            confidence=float(model_payload.get("confidence", 0.5)),
        )

    def recommend_folder_group(self, files: list[ScannedFile], context: dict[str, object]) -> dict[str, object] | None:
        """Ask Ollama once per folder group for cohesive planning guidance."""

        if not files:
            return None
        prompt = self._build_folder_prompt(files, context)
        return self._generate_json(prompt)

    def _build_prompt(self, file_item: ScannedFile, context: dict[str, object]) -> str:
        """Build a strict JSON-only recommendation prompt for Ollama."""

        return json.dumps(
            {
                "task": "You are a file-organization agent. Output only valid JSON.",
                "file": {
                    "path": str(file_item.path),
                    "name": file_item.name,
                    "extension": file_item.extension,
                    "folder_path": str(file_item.folder_path),
                    "file_kind": file_item.file_kind,
                    "size_bytes": file_item.size_bytes,
                },
                "context": context,
                "constraints": [
                    "Preserve folder coherence for mixed project folders.",
                    "Do not scatter related files unless confidence is very high.",
                    "Prefer conservative organization with clear rationale.",
                ],
                "required_output": {
                    "category": "string",
                    "subcategory": "string",
                    "suggested_folder": "string",
                    "reason": "string",
                    "confidence": "number between 0 and 1",
                },
            },
            indent=2,
        )

    def _build_folder_prompt(self, files: list[ScannedFile], context: dict[str, object]) -> str:
        """Build folder-level prompt for one-call planning."""

        return json.dumps(
            {
                "task": "You are a folder-organization agent. Output only valid JSON.",
                "folder": {
                    "path": str(files[0].folder_path),
                    "file_count": len(files),
                    "kinds": sorted({item.file_kind for item in files}),
                    "extensions": sorted({item.extension for item in files}),
                    "sample_files": [item.name for item in files[:25]],
                },
                "context": context,
                "constraints": [
                    "Preserve coherent project/album folders by default.",
                    "Avoid scattering mixed-content folders.",
                    "Move only when confidence is high and reason is explicit.",
                ],
                "required_output": {
                    "preserve_folder": "boolean",
                    "suggested_folder": "string",
                    "reason": "string",
                    "confidence": "number between 0 and 1",
                    "category": "string",
                    "subcategory": "string",
                },
            },
            indent=2,
        )

    def _generate_json(self, prompt: str) -> dict[str, object] | None:
        """Call Ollama generate endpoint and parse JSON response."""

        payload = {
            "model": self.settings.ollama_model,
            "stream": False,
            "format": "json",
            "prompt": prompt,
            "options": {"temperature": 0.1},
        }
        req = request.Request(
            self.api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
            content = data.get("response", "{}")
            return json.loads(content)
        except (error.URLError, TimeoutError, ValueError, json.JSONDecodeError, OSError):
            return None