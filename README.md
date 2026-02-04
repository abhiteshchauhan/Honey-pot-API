# Agentic Honey-Pot API

AI-powered scam detection and autonomous engagement system that detects scam messages and extracts actionable intelligence (bank accounts, UPI IDs, phishing links) through multi-turn conversations.

## Features

- **Scam Detection**: LLM + pattern-based detection with configurable confidence threshold
- **Autonomous Agent**: Maintains human persona, engages scammers, extracts intelligence
- **Structured Output**: JSON response with scam status, engagement metrics, extracted data
- **API Key Auth**: Secured public endpoint for Mock Scammer API integration

## Setup

1. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   copy .env.example .env
   # Edit .env: set API_KEY and OPENAI_API_KEY
   ```

4. **Run the API**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

## API

### POST /webhook

Receives message events from the Mock Scammer API.

**Headers:**
- `X-API-Key`: Your API key

**Request body:**
```json
{
  "conversation_id": "conv_123",
  "message": "You have won 10 lakh! Click here to claim...",
  "sender": "scammer",
  "timestamp": "2025-02-05T12:00:00Z"
}
```

**Response:**
```json
{
  "scam_detected": true,
  "response_message": "Wow really? Send me the link please",
  "engagement_metrics": {
    "conversation_turns": 3,
    "engagement_duration_seconds": 45.2,
    "scam_detected_at_turn": 1,
    "agent_activated": true
  },
  "extracted_intelligence": {
    "bank_account_numbers": ["123456789012"],
    "upi_ids": ["scammer@paytm"],
    "phishing_urls": ["https://evil.com/claim"],
    "other_relevant_info": []
  },
  "conversation_id": "conv_123",
  "timestamp": "2025-02-05T12:01:00Z"
}
```

## Deployment

Deploy to any platform supporting Python (Railway, Render, Fly.io). Set `API_KEY` and `OPENAI_API_KEY` as environment variables. Expose the `/webhook` endpoint publicly.

## License

MIT
