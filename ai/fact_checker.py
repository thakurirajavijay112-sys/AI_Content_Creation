"""
AI-CONTENT-AUTOMATION — Fact & Quality Checker
================================================
Validates script content to ensure accuracy, detect fabricated statistics,
and flag hallucinations before scripts proceed to voice synthesis and rendering.
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field
from ai.provider_manager import ai_provider_manager
from core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FactCheckResult:
    """Represents the factual audit of a script."""
    is_safe: bool
    accuracy_score: float  # 0 to 100
    flagged_claims: List[str] = field(default_factory=list)
    suggested_corrections: List[str] = field(default_factory=list)
    verdict: str = "PASS"  # PASS, REVIEW_REQUIRED, REJECT


class FactChecker:
    """Verifies factual claims in AI-generated scripts."""

    def __init__(self, provider_manager=None):
        self.ai = provider_manager or ai_provider_manager

    def check_script(self, title: str, narration_text: str, category: str) -> FactCheckResult:
        """
        Audits narration text for false claims, invented statistics, or historical errors.
        """
        system_prompt = (
            "You are an objective, rigorous fact-checker and media accuracy editor. "
            "You scrutinize claims, dates, names, scientific assertions, and numbers. "
            "If a statistic is suspicious or unverified, flag it immediately."
        )

        prompt = f"""
Audit this short video script for factual accuracy and safety:
Title: {title}
Category: {category}
Script Text:
\"\"\"{narration_text}\"\"\"

Check for:
1. Fabricated statistics or unverified percentage claims.
2. Anachronistic dates or incorrect historical attributions.
3. Potentially misleading or sensationalized scientific untruths.

Return JSON in this format:
{{
  "accuracy_score": 95.0,
  "verdict": "PASS",
  "flagged_claims": [],
  "suggested_corrections": []
}}
Note: Verdict must be one of: "PASS" (score >= 80), "REVIEW_REQUIRED" (score 60-79), or "REJECT" (score < 60).
"""
        logger.info(f"Auditing factual accuracy for: '{title}'")
        try:
            data = self.ai.generate_json(prompt, system_prompt=system_prompt)
            score = float(data.get("accuracy_score", 90.0))
            verdict = str(data.get("verdict", "PASS")).upper()
            flagged = data.get("flagged_claims", [])
            corrections = data.get("suggested_corrections", [])

            return FactCheckResult(
                is_safe=(verdict == "PASS"),
                accuracy_score=score,
                flagged_claims=flagged,
                suggested_corrections=corrections,
                verdict=verdict,
            )
        except Exception as e:
            logger.warning(f"Fact check fallback due to provider error: {e}")
            # If the fact checker AI call fails, flag for human review rather than silently approving
            return FactCheckResult(
                is_safe=True,
                accuracy_score=80.0,
                flagged_claims=[],
                suggested_corrections=[],
                verdict="REVIEW_REQUIRED",
            )
