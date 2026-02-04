"""Scam intent detection module."""

import re
from typing import Optional

from openai import OpenAI

from app.config import settings


class ScamDetector:
    """Detects scam intent in messages using LLM and pattern matching."""

    def __init__(self):
        self._client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def detect_scam_intent(
        self, message: str, conversation_history: list[dict[str, str]] | None = None
    ) -> tuple[bool, float]:
        """
        Detect if a message indicates scam intent.
        Returns (is_scam, confidence) tuple.
        """
        message_lower = message.lower().strip()

        # Quick pattern-based pre-filter for obvious scam signals
        scam_patterns = [
            r"\b(urgent|immediately|act now|limited time)\b",
            r"\b(won.*?(?:lottery|prize|cash))\b",
            r"\b(claim your|claim now)\b",
            r"\b(kyc|verification|update.*account)\b",
            r"\b(click.*link|click here)\b",
            r"\b(otp|one.?time.?password)\b",
            r"\b(bank.*account|upi|paytm|gpay|phonepe)\b",
            r"\b(refund|money.*transfer)\b",
            r"\b(inheritance|beneficiary)\b",
            r"\b(verify.*identity|confirm.*details)\b",
            r"https?://[^\s]+",  # URLs often in scam messages
            r"\d{10,}",  # Long number sequences (account numbers)
        ]

        pattern_matches = sum(1 for p in scam_patterns if re.search(p, message_lower, re.I))
        if pattern_matches >= 2:
            return True, 0.85  # High confidence from multiple signals

        # Use LLM for nuanced detection when available
        if self._client:
            return self._llm_detect(message, conversation_history or [])

        # Fallback: single strong pattern
        if pattern_matches >= 1 and len(message) > 20:
            return True, 0.7
        return False, 0.0

    def _llm_detect(
        self, message: str, conversation_history: list[dict[str, str]]
    ) -> tuple[bool, float]:
        """Use LLM for scam intent detection."""
        system_prompt = """You are a scam intent classifier. Analyze if the message indicates a financial scam, phishing attempt, or fraud (lottery, KYC, refund, inheritance, investment scam, etc.).
Respond with ONLY "YES" or "NO" followed by a confidence score 0-1. Example: "YES 0.9" or "NO 0.2".
Be cautious: generic greetings or normal questions should be NO. Focus on requests for money, account details, OTP, verification links, or too-good-to-be-true offers."""

        messages = [{"role": "system", "content": system_prompt}]
        for msg in conversation_history[-6:]:  # Last 6 turns for context
            role = "user" if msg.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": msg.get("content", "")})
        messages.append({"role": "user", "content": message})

        try:
            response = self._client.chat.completions.create(
                model=settings.model,
                messages=messages,
                max_tokens=20,
                temperature=0,
            )
            text = response.choices[0].message.content.strip().upper()
            if "YES" in text:
                import re as re2
                nums = re2.findall(r"0?\.\d+|1\.0", text)
                conf = float(nums[0]) if nums else 0.8
                return True, min(conf, 1.0)
            return False, 0.0
        except Exception:
            return False, 0.0
