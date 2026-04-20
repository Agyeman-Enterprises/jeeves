"""
Intent Classifier - Maps natural language queries to structured intents.
Uses LLM to classify user queries into structured intents.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from app.services.ollama_service import OllamaService

LOGGER = logging.getLogger(__name__)

# Load prompt from file
PROMPT_PATH = Path(__file__).parent.parent / "ai" / "intent_classifier_prompt.txt"


def _load_classifier_prompt() -> str:
    """Load intent classifier prompt from file."""
    if PROMPT_PATH.exists():
        try:
            return PROMPT_PATH.read_text(encoding="utf-8")
        except Exception as exc:
            LOGGER.warning("Failed to load classifier prompt: %s", exc)
    
    # Fallback to default prompt
    return """You are JARVIS, the Executive AI Assistant.

Your job: Convert NATURAL LANGUAGE into a JSON INTENT OBJECT.

=== MASTER INTENTS ===

ceo_briefing → Full executive summary across all businesses.
portfolio_alerts → Risk, anomalies, cash runway, warnings.
business_insight(business_name) → KPIs for a specific business.
compare_businesses(list) → Compare multiple companies.
next_shift → Show next Amion hospital shift.
renewals_status → DEA, license, credential renewals.
pay_my_bills → Pay bills or show obligations.
send_email(to,subject,body) → Generate/send email.

=== OUTPUT FORMAT ===

{
  "intent": "<intent_id>",
  "parameters": { ... }
}

=== NOW CLASSIFY THE USER MESSAGE ===
"""


def _build_intent_prompt() -> str:
    """Build the system prompt with all 53 intents."""
    prompt_parts = [
        "You are JARVIS, the executive assistant and intent router for the user.",
        "",
        "Your job is to classify natural-language requests into ONE of the INTENTS defined below.",
        "",
        "You MUST choose exactly one intent and produce a JSON object with:",
        "",
        '{',
        '  "intent": "<intent_name>",',
        '  "entities": { ... }',
        '}',
        "",
        "INTENTS (53 total, organized by domain):",
        "",
    ]

    # Group intents by domain
    domains = {}
    for intent, data in INTENT_SCHEMA.items():
        domain = data["domain"]
        if domain not in domains:
            domains[domain] = []
        domains[domain].append((intent, data))

    domain_order = ["business", "personal", "medical", "communication", "travel", "knowledge", "system"]

    for domain in domain_order:
        if domain not in domains:
            continue

        domain_name = domain.upper().replace("_", " ")
        prompt_parts.append(f"=== {domain_name} DOMAIN ===")

        for intent, data in domains[domain]:
            examples = data.get("examples", [])[:3]  # Top 3 examples
            required = data.get("required_entities", [])
            agent = data.get("agent", "Unknown")

            prompt_parts.append(f"\n{intent}")
            if required:
                prompt_parts.append(f"  Required entities: {', '.join(required)}")
            prompt_parts.append(f"  Agent: {agent}")
            prompt_parts.append(f"  Examples: {', '.join(examples)}")

        prompt_parts.append("")

    prompt_parts.extend([
        "RULES:",
        "- Always output machine-parseable JSON only.",
        "- Never include commentary or explanation.",
        "- Extract entities from the query when required.",
        "- If business names are ambiguous, return them exactly as provided.",
        "- For time/date entities, extract and normalize (e.g., 'tomorrow', 'Friday at 2pm').",
        "- If intent is unclear, choose the most likely based on keywords.",
        "",
        "Example outputs:",
        '{"intent": "ceo_briefing", "entities": {}}',
        '{"intent": "business_insight", "entities": {"business_name": "MedRx"}}',
        '{"intent": "schedule_meeting", "entities": {"time": "Friday at 2pm", "participant": "John"}}',
        '{"intent": "read_email", "entities": {}}',
    ])

    return "\n".join(prompt_parts)


INTENT_CLASSIFICATION_PROMPT = _load_classifier_prompt()


class IntentClassifier:
    """
    Classifies natural language queries into structured intents.
    Uses LLM to parse user intent and extract entities.
    """

    def __init__(self, ollama_service: Optional[OllamaService] = None):
        self.ollama = ollama_service or OllamaService()

    def classify(self, query: str) -> Dict[str, Any]:
        """
        Classify a user query into an intent with entities.

        Returns:
            {
                "intent": "ceo_briefing" | "schedule_meeting" | ...,
                "parameters": { ... }
            }
        """
        # Skip Ollama if no local models available (e.g. cloud deploy) — go straight to keyword fallback
        if not self.ollama.has_models():
            return self._fallback_classify(query)

        # Use LLM to classify intent
        prompt = f"{INTENT_CLASSIFICATION_PROMPT}\n\nUser query: {query}\n\nOutput JSON only:"

        try:
            response = self.ollama.generate(
                prompt=prompt,
                system_prompt="You are a precise intent classifier. Output only valid JSON, no commentary.",
                options={"temperature": 0.1},  # Low temperature for consistency
            )
            
            # Parse JSON response
            result = self._parse_json_response(response)
            
            # Normalize response format (handle both "entities" and "parameters")
            if "entities" in result and "parameters" not in result:
                result["parameters"] = result.pop("entities")
            
            return result
        except Exception as exc:
            LOGGER.exception("Error classifying intent: %s", exc)
            # Fallback to keyword-based classification
            return self._fallback_classify(query)

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Remove markdown code blocks if present
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
            raise

    def _fallback_classify(self, query: str) -> Dict[str, Any]:
        """Fallback keyword-based classification if LLM fails."""
        lower = query.lower()

        # Conversational / system queries — check FIRST to avoid false matches below
        if any(kw in lower for kw in ["hello", "hi jarvis", "hey", "good morning", "good evening"]):
            return {"intent": "general_query", "parameters": {"query": query}}
        if any(kw in lower for kw in ["what can you do", "what agents", "capabilities", "help me", "what do you know", "what are you able"]):
            return {"intent": "general_query", "parameters": {"query": query}}
        if any(kw in lower for kw in ["who are you", "what are you", "tell me about yourself", "introduce yourself"]):
            return {"intent": "general_query", "parameters": {"query": query}}

        # Business domain
        if any(kw in lower for kw in ["ceo briefing", "portfolio overview", "all businesses", "how are my businesses"]):
            return {"intent": "ceo_briefing", "parameters": {}}
        if any(kw in lower for kw in ["fire", "alert", "critical", "urgent", "worries", "red flag"]):
            return {"intent": "portfolio_alerts", "parameters": {}}
        if any(kw in lower for kw in ["tell me about", "insight for", "brief for", "how is"]) and any(kw in lower for kw in ["business", "company"]):
            return {"intent": "business_insight", "parameters": {"business_name": None}}
        if "compare" in lower and any(kw in lower for kw in ["business", "company"]):
            return {"intent": "compare_businesses", "parameters": {"businesses": []}}
        if any(kw in lower for kw in ["top performer", "best business", "winning"]):
            return {"intent": "top_performers", "parameters": {}}
        if any(kw in lower for kw in ["high risk", "needs attention", "underperforming"]):
            return {"intent": "high_risk_entities", "parameters": {}}
        if any(kw in lower for kw in ["revenue trend", "revenue drop", "revenue status"]):
            return {"intent": "revenue_trends", "parameters": {}}
        if any(kw in lower for kw in ["opportunity", "focus next", "growth opportunity"]):
            return {"intent": "opportunity_scan", "parameters": {}}
        if any(kw in lower for kw in ["ad performance", "ads performing", "advertising", "campaign", "ad spend", "roas", "how are my ads"]):
            return {"intent": "ad_performance", "parameters": {}}
        if any(kw in lower for kw in ["ceo summary", "enterprise overview", "what companies do i own", "summarize my businesses", "enterprise structure", "how is my enterprise organized"]):
            return {"intent": "enterprise_ceo_query", "parameters": {"query": query}}
        if any(kw in lower for kw in ["ops analysis", "operational", "bottleneck", "complexity", "operations analysis"]):
            return {"intent": "enterprise_ceo_analysis", "parameters": {"query": query, "lens": "ops"}}
        if any(kw in lower for kw in ["financial analysis", "finance summary", "revenue potential", "cost complexity", "risk level"]):
            return {"intent": "enterprise_ceo_analysis", "parameters": {"query": query, "lens": "finance"}}
        if any(kw in lower for kw in ["strategic recommendation", "strategy", "where should i focus", "what should i prioritize"]):
            return {"intent": "enterprise_ceo_analysis", "parameters": {"query": query, "lens": "strategy"}}
        if any(kw in lower for kw in ["generate social", "create instagram", "social media posts", "social content", "generate posts"]):
            return {"intent": "generate_social_content", "parameters": {"brand": "Needful Things", "count": 5}}
        if any(kw in lower for kw in ["content calendar", "social calendar"]):
            return {"intent": "generate_social_content", "parameters": {"brand": "Needful Things", "task_type": "content_calendar"}}
        if any(kw in lower for kw in ["hashtags", "hashtag"]):
            return {"intent": "generate_social_content", "parameters": {"brand": "Needful Things", "task_type": "hashtags"}}
        if any(kw in lower for kw in ["reels script", "tiktok script", "short video script"]):
            return {"intent": "generate_social_content", "parameters": {"brand": "Needful Things", "task_type": "reels_script"}}

        # Personal domain
        if any(kw in lower for kw in ["schedule", "calendar", "what's on my", "free time"]):
            return {"intent": "show_schedule", "parameters": {}}
        if any(kw in lower for kw in ["schedule", "book", "add meeting", "add appointment"]) and "meeting" in lower:
            return {"intent": "schedule_meeting", "parameters": {}}
        if any(kw in lower for kw in ["move", "reschedule"]) and any(kw in lower for kw in ["meeting", "appointment"]):
            return {"intent": "move_meeting", "parameters": {}}
        if any(kw in lower for kw in ["cancel", "remove"]) and any(kw in lower for kw in ["meeting", "appointment"]):
            return {"intent": "cancel_meeting", "parameters": {}}
        if any(kw in lower for kw in ["remind", "don't forget"]):
            return {"intent": "remind_me", "parameters": {}}
        if any(kw in lower for kw in ["morning brief", "daily brief", "agenda"]):
            return {"intent": "daily_brief", "parameters": {}}
        if "weekly review" in lower:
            return {"intent": "weekly_review", "parameters": {}}
        if "monthly planning" in lower:
            return {"intent": "monthly_planning", "parameters": {}}
        if any(kw in lower for kw in ["add task", "create task", "new task"]):
            return {"intent": "task_create", "parameters": {}}
        if any(kw in lower for kw in ["task", "todo", "what do i have"]):
            return {"intent": "task_list", "parameters": {}}
        if any(kw in lower for kw in ["financial", "spend", "money", "financial overview"]):
            return {"intent": "financial_summary", "parameters": {}}
        if any(kw in lower for kw in ["pay", "bill"]) and "pay" in lower:
            return {"intent": "pay_my_bills", "parameters": {}}
        if any(kw in lower for kw in ["license", "dea", "expiration", "renewal"]):
            return {"intent": "renewals_status", "parameters": {}}
        if any(kw in lower for kw in ["personal alert", "urgent personally"]):
            return {"intent": "personal_alerts", "parameters": {}}

        # Medical domain
        if any(kw in lower for kw in ["next shift", "call tonight", "shift"]):
            return {"intent": "next_shift", "parameters": {}}
        if any(kw in lower for kw in ["amion", "call schedule"]):
            return {"intent": "call_schedule", "parameters": {}}
        if any(kw in lower for kw in ["patient", "chart", "summary"]) and "patient" in lower:
            return {"intent": "patient_summary", "parameters": {"patient_name": None}}
        if any(kw in lower for kw in ["clinical note", "new note"]) and "patient" in lower:
            return {"intent": "new_clinical_note", "parameters": {"patient_name": None}}
        if any(kw in lower for kw in ["lab result", "lab work", "my labs", "lab test", "blood work"]):
            return {"intent": "lab_results", "parameters": {}}
        if any(kw in lower for kw in ["refill", "prescription"]):
            return {"intent": "prescription_refill", "parameters": {"patient_name": None}}
        if any(kw in lower for kw in ["clinical alert", "urgent clinic"]):
            return {"intent": "clinical_alerts", "parameters": {}}

        # Communication domain
        if any(kw in lower for kw in ["read email", "show email", "emails"]):
            return {"intent": "read_email", "parameters": {}}
        if any(kw in lower for kw in ["summarize email", "what did", "email say"]):
            return {"intent": "summarize_email", "parameters": {}}
        if any(kw in lower for kw in ["email", "send email"]) and "send" in lower or "email" in lower:
            return {"intent": "send_email", "parameters": {}}
        if "reply" in lower and "email" in lower:
            return {"intent": "reply_email", "parameters": {}}
        if "unread" in lower and "email" in lower:
            return {"intent": "unread_emails", "parameters": {}}
        if any(kw in lower for kw in ["text", "sms", "message"]):
            return {"intent": "send_sms", "parameters": {}}
        if "notification" in lower:
            return {"intent": "show_notifications", "parameters": {}}

        # Travel domain
        if any(kw in lower for kw in ["flight", "hotel", "travel", "book"]):
            return {"intent": "travel_planning", "parameters": {}}
        if "track" in lower and "flight" in lower:
            return {"intent": "track_flight", "parameters": {}}
        if "weather" in lower:
            return {"intent": "check_weather", "parameters": {}}
        if any(kw in lower for kw in ["directions", "how long", "drive to"]):
            return {"intent": "map_directions", "parameters": {}}

        # Knowledge domain
        if any(kw in lower for kw in ["find", "search", "file", "document"]):
            return {"intent": "search_files", "parameters": {}}
        if any(kw in lower for kw in ["open", "show"]) and any(kw in lower for kw in ["file", "document"]):
            return {"intent": "open_file", "parameters": {}}
        if any(kw in lower for kw in ["lookup", "what is", "protocol", "knowledge"]):
            return {"intent": "lookup_knowledge", "parameters": {}}
        if "summarize" in lower and any(kw in lower for kw in ["document", "pdf", "file"]):
            return {"intent": "summarize_document", "parameters": {}}
        if any(kw in lower for kw in ["remember", "save", "store"]):
            return {"intent": "update_memory", "parameters": {}}
        if any(kw in lower for kw in ["recall", "what did i tell", "remember"]):
            return {"intent": "retrieve_memory", "parameters": {}}
        if any(kw in lower for kw in ["forget", "delete memory"]):
            return {"intent": "delete_memory", "parameters": {}}

        # System domain
        if any(kw in lower for kw in ["director mode", "silent mode", "assistant mode", "change mode"]):
            return {"intent": "change_mode", "parameters": {}}
        if "restart" in lower:
            return {"intent": "restart_jarvis", "parameters": {}}
        if any(kw in lower for kw in ["stop listening", "mute"]):
            return {"intent": "stop_listening", "parameters": {}}
        if any(kw in lower for kw in ["go to sleep", "sleep mode"]):
            return {"intent": "go_to_sleep", "parameters": {}}
        if any(kw in lower for kw in ["hey jarvis", "wake up", "jarvis"]):
            return {"intent": "wake_up", "parameters": {}}

        # Default: try to route to general query
        LOGGER.warning("Could not classify query: %s", query)
        return {"intent": None, "parameters": {}}
