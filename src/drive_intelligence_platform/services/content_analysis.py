"""Content analysis for documents, text files, and code files."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ContentAnalysisResult:
    """Structured content analysis output."""

    keywords: list[str]
    topics: list[str]
    summary: str
    entities: list[str]
    project_names: list[str]


class ContentAnalyzer:
    """Extract lightweight metadata from text-like files."""

    def analyze(self, path: Path) -> ContentAnalysisResult:
        """Analyze supported content types."""

        text = self._read_text(path)
        keywords = self._extract_keywords(text)
        topics = self._infer_topics(text, path)
        entities = self._extract_entities(text)
        project_names = self._extract_project_names(text)
        summary = self._summarize(text, keywords)
        return ContentAnalysisResult(
            keywords=keywords,
            topics=topics,
            summary=summary,
            entities=entities,
            project_names=project_names,
        )

    def _read_text(self, path: Path) -> str:
        """Read textual content from supported file types."""

        suffix = path.suffix.lower()
        if suffix == ".json":
            try:
                return json.dumps(json.loads(path.read_text(encoding="utf-8")), indent=2)
            except Exception:
                return path.read_text(encoding="utf-8", errors="ignore")
        return path.read_text(encoding="utf-8", errors="ignore")

    def _extract_keywords(self, text: str) -> list[str]:
        """Compute a small frequency-based keyword list."""

        words = re.findall(r"[A-Za-z][A-Za-z0-9_+-]{2,}", text.lower())
        stop_words = {
            "the",
            "and",
            "for",
            "with",
            "that",
            "this",
            "from",
            "have",
            "your",
            "about",
            "into",
            "will",
            "where",
            "what",
            "when",
            "then",
        }
        counts: dict[str, int] = {}
        for word in words:
            if word in stop_words:
                continue
            counts[word] = counts.get(word, 0) + 1
        return [word for word, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:12]]

    def _infer_topics(self, text: str, path: Path) -> list[str]:
        """Infer high-level topics using simple rules."""

        normalized = f"{path.name} {text}".lower()
        topics: list[str] = []
        rules = {
            "python": ["python", ".py", "pytest", "pip"],
            "etl": ["etl", "pipeline", "extract", "transform", "load"],
            "oracle": ["oracle", "sql", "pl/sql", "database"],
            "cloud": ["aws", "azure", "gcp", "cloud"],
            "architecture": ["architecture", "design", "diagram", "component"],
            "finance": ["invoice", "budget", "finance", "tax"],
        }
        for topic, keywords in rules.items():
            if any(keyword in normalized for keyword in keywords):
                topics.append(topic)
        return topics[:5]

    def _extract_entities(self, text: str) -> list[str]:
        """Extract capitalized tokens that likely represent entities."""

        matches = re.findall(r"\b[A-Z][A-Za-z0-9_+-]{2,}\b", text)
        filtered = [token for token in matches if token.lower() not in {"the", "and", "from", "with"}]
        return list(dict.fromkeys(filtered[:20]))

    def _extract_project_names(self, text: str) -> list[str]:
        """Infer project names from common naming patterns."""

        project_matches = re.findall(r"(?:project|repo|workspace)[:\s]+([A-Za-z0-9_\-]+)", text, flags=re.IGNORECASE)
        return list(dict.fromkeys(project_matches[:20]))

    def _summarize(self, text: str, keywords: list[str]) -> str:
        """Create a compact summary from the file content."""

        clean = " ".join(text.split())
        if len(clean) <= 240:
            return clean
        prefix = clean[:220]
        keyword_text = ", ".join(keywords[:5])
        return f"{prefix}... Keywords: {keyword_text}" if keyword_text else f"{prefix}..."