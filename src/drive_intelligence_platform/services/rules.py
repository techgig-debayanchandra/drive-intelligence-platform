"""Rule engine for user-defined organization policies."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from drive_intelligence_platform.schemas import RecommendationPayload, ScannedFile


@dataclass(slots=True)
class RuleMatch:
    """A matched rule result."""

    name: str
    recommendation: RecommendationPayload


class RuleEngine:
    """Evaluate YAML-defined matching rules."""

    def __init__(self, rules_path: Path) -> None:
        self.rules_path = rules_path

    def load_rules(self) -> list[dict]:
        """Load rules from YAML if available."""

        if not self.rules_path.exists():
            return []
        data = yaml.safe_load(self.rules_path.read_text(encoding="utf-8")) or {}
        return list(data.get("rules", []))

    def match(self, file_item: ScannedFile) -> RuleMatch | None:
        """Return the first rule that matches the file item."""

        for rule in self.load_rules():
            when = rule.get("when", {})
            extension = when.get("extension")
            keywords = [str(keyword).lower() for keyword in when.get("keywords", [])]
            if extension and extension.lower() != file_item.extension.lower():
                continue
            if keywords and not any(keyword in file_item.name.lower() for keyword in keywords):
                continue
            then = rule.get("then", {})
            recommendation = RecommendationPayload(
                source_path=file_item.path,
                category=str(then.get("category", "Unsorted")),
                subcategory=str(then.get("subcategory", "")),
                suggested_folder=Path(str(then.get("suggested_folder", "Archives/Unsorted"))),
                reason=f"Matched rule {rule.get('name', 'unnamed')}",
                confidence=0.99,
            )
            return RuleMatch(name=str(rule.get("name", "unnamed")), recommendation=recommendation)
        return None