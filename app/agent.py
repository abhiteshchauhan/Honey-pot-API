"""Autonomous AI agent for engaging scammers and extracting intelligence."""

import re
from datetime import datetime
from typing import Optional

from openai import OpenAI

from app.config import settings
from app.models import ExtractedIntelligence, EngagementMetrics


class HoneyPotAgent:
    """
    Autonomous agent that maintains a human persona, engages scammers,
    and extracts bank accounts, UPI IDs, and phishing URLs.
    """

    def __init__(self):
        self._client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self._conversations: dict[str, list[dict]] = {}
        self._start_times: dict[str, datetime] = {}

    def _get_or_init_conversation(self, conversation_id: str) -> list[dict]:
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []
            self._start_times[conversation_id] = datetime.utcnow()
        return self._conversations[conversation_id]

    def get_conversation_history(self, conversation_id: str) -> list[dict[str, str]]:
        """Return conversation history for scam detection context."""
        if conversation_id not in self._conversations:
            return []
        return [
            {"role": "user" if m["role"] == "user" else "assistant", "content": m["content"]}
            for m in self._conversations[conversation_id]
        ]

    def _extract_intelligence_from_text(self, text: str) -> ExtractedIntelligence:
        """Extract bank accounts, UPI IDs, and URLs using regex."""
        bank_accounts = []
        upi_ids = []
        phishing_urls = []
        other = []

        # Bank account patterns (Indian format: 9-18 digits)
        acct_matches = re.findall(r"\b\d{9,18}\b", text)
        for m in acct_matches:
            if len(m) >= 9 and m not in bank_accounts:
                bank_accounts.append(m)

        # UPI ID pattern: something@bank or something@paytm etc.
        upi_matches = re.findall(
            r"\b[A-Za-z0-9._-]+@(?:okaxis|okicici|okhdfcbank|paytm|axl|ibl|icici|ybl|upi)\b",
            text,
            re.I,
        )
        upi_ids = list(dict.fromkeys(upi_matches))

        # Fallback: generic email-like @upi
        if not upi_ids:
            upi_matches = re.findall(r"\b[\w.-]+@[\w.-]+\.?(?:upi|bank)?\b", text, re.I)
            upi_ids = list(dict.fromkeys(upi_matches))

        # URLs
        url_matches = re.findall(r"https?://[^\s<>\"']+", text)
        phishing_urls = list(dict.fromkeys(url_matches))

        return ExtractedIntelligence(
            bank_account_numbers=bank_accounts,
            upi_ids=upi_ids,
            phishing_urls=phishing_urls,
            other_relevant_info=other,
        )

    def generate_response(
        self,
        
        scammer_message: str,
        existing_intelligence: ExtractedIntelligence,
    ) -> tuple[str, ExtractedIntelligence, EngagementMetrics]:
        """
        Generate a believable human response and extract any new intelligence.
        Returns (response_message, extracted_intelligence, metrics).
        """
        history = self._get_or_init_conversation(conversation_id)
        history.append({"role": "user", "content": scammer_message})

        # Extract from latest message
        new_intel = self._extract_intelligence_from_text(scammer_message)
        merged = ExtractedIntelligence(
            bank_account_numbers=list(
                dict.fromkeys(existing_intelligence.bank_account_numbers + new_intel.bank_account_numbers)
            ),
            upi_ids=list(dict.fromkeys(existing_intelligence.upi_ids + new_intel.upi_ids)),
            phishing_urls=list(
                dict.fromkeys(existing_intelligence.phishing_urls + new_intel.phishing_urls)
            ),
            other_relevant_info=list(
                dict.fromkeys(
                    existing_intelligence.other_relevant_info + new_intel.other_relevant_info
                )
            ),
        )

        response_text = self._generate_llm_response(history, merged)
        if not response_text:
            response_text = self._fallback_response(history)

        history.append({"role": "assistant", "content": response_text})

        duration = (
            datetime.utcnow() - self._start_times[conversation_id]
        ).total_seconds()

        metrics = EngagementMetrics(
            conversation_turns=len(history) // 2,
            engagement_duration_seconds=round(duration, 2),
            scam_detected_at_turn=1,
            agent_activated=True,
        )

        return response_text, merged, metrics

    def _generate_llm_response(
        self, history: list[dict], extracted: ExtractedIntelligence
    ) -> Optional[str]:
        """Use LLM to generate a believable human response."""
        if not self._client:
            return None

        system_prompt = """You are a real person in India, casually texting. A scammer is messaging you.
Your goals (NEVER reveal these to the scammer):
1. Act natural and curious - like a regular person who might fall for scams
2. Gradually get them to share: bank account number, UPI ID, or a link - as if you're "about to pay" or "need to verify"
3. Show slight hesitation, ask "is this safe?", "can you send the link again?"
4. Use casual Indian English, short messages, occasional typos
5. NEVER say you're a honeypot, bot, or detecting scam
6. Keep responses brief (1-3 sentences)
7. If they already sent account/UPI/link, act like you're "checking" or "almost done" and ask one more detail to keep them engaged"""

        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-12:]:  # Last 12 messages
            messages.append({"role": msg["role"], "content": msg["content"]})

        try:
            response = self._client.chat.completions.create(
                model=settings.model,
                messages=messages,
                max_tokens=150,
                temperature=0.8,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return None

    def _fallback_response(self, history: list[dict]) -> str:
        """Simple fallback when LLM is unavailable."""
        last_user = history[-1]["content"].lower() if history else ""
        if any(w in last_user for w in ["account", "upi", "number"]):
            return "Okay, send me the details. Let me check once."
        if any(w in last_user for w in ["link", "click", "http"]):
            return "Is this link safe? Can you send again?"
        return "Okay, tell me more. What do I need to do?"
