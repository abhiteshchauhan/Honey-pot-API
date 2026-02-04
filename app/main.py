"""Agentic Honey-Pot API - Main entry point."""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import MessageEvent, HoneyPotResponse, ExtractedIntelligence, EngagementMetrics
from app.scam_detector import ScamDetector
from app.agent import HoneyPotAgent


app = FastAPI(
    title="Agentic Honey-Pot API",
    description="AI-powered scam detection and intelligence extraction",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

detector = ScamDetector()
agent = HoneyPotAgent()

# Per-conversation state: scam detected, accumulated intelligence
_conversation_state: dict[str, dict] = {}


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """Verify the API key from request header."""
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "agentic-honeypot"}


@app.post(
    "/webhook",
    response_model=HoneyPotResponse,
    summary="Receive scam message and respond",
)
async def handle_message(
    event: MessageEvent,
    _: str = Depends(verify_api_key),
):
    """
    Accept incoming message events from the Mock Scammer API.
    Detects scam intent, hands off to the autonomous agent when detected,
    and returns structured response with extracted intelligence.
    """
    cid = event.conversation_id
    message = event.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Initialize or get conversation state
    if cid not in _conversation_state:
        _conversation_state[cid] = {
            "scam_detected": False,
            "intelligence": ExtractedIntelligence(),
        }

    state = _conversation_state[cid]

    # Build conversation history for context (for scam detection)
    history = agent.get_conversation_history(cid)

    # Detect scam intent if not already detected
    if not state["scam_detected"]:
        is_scam, confidence = detector.detect_scam_intent(message, history)
        if is_scam and confidence >= 0.6:
            state["scam_detected"] = True

    # If scam detected, hand off to agent
    if state["scam_detected"]:
        response_text, extracted, metrics = agent.generate_response(
            conversation_id=cid,
            scammer_message=message,
            existing_intelligence=state["intelligence"],
        )
        state["intelligence"] = extracted
    else:
        # Not a scam - respond neutrally to avoid exposure
        response_text = _neutral_response(message)
        metrics = EngagementMetrics(
            conversation_turns=0,
            agent_activated=False,
        )
        extracted = state["intelligence"]

    return HoneyPotResponse(
        scam_detected=state["scam_detected"],
        response_message=response_text,
        engagement_metrics=metrics,
        extracted_intelligence=extracted,
        conversation_id=cid,
    )


def _neutral_response(message: str) -> str:
    """Respond neutrally when scam not yet detected (avoid exposure)."""
    msg_lower = message.lower()
    if any(w in msg_lower for w in ["hi", "hello", "hey"]):
        return "Hi, who's this?"
    return "Okay."
