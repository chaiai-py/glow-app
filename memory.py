import uuid
from azure.cosmos import CosmosClient
from config import COSMOS_ENDPOINT, COSMOS_KEY, COSMOS_DB, COSMOS_CONTAINER
from azure.cosmos import PartitionKey
from datetime import datetime
import re

container = None


def get_container():
    global container

    if container is not None:
        return container

    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = client.create_database_if_not_exists(id=COSMOS_DB)
    container = database.create_container_if_not_exists(
        id=COSMOS_CONTAINER,
        partition_key=PartitionKey(path="/user_id")
    )
    return container

def get_memory(user_id: str):
    try:
        return get_container().read_item(item=user_id, partition_key=user_id)
    except Exception as e:
        print(f"Memory read warning: {e}")
        return None


def extract_entities(text: str):
    if not text:
        return []

    capitalized = re.findall(r"\b[A-Z][a-z]+\b", text)
    return list(dict.fromkeys([word for word in capitalized if len(word) > 2]))


def analyze_sentiment(text: str):
    if not text:
        return "neutral"

    positive = ["good", "great", "love", "happy", "awesome", "excellent", "yes", "sure"]
    negative = ["bad", "sad", "wrong", "no", "hate", "stress", "hard"]
    lower = text.lower()
    score = sum(1 for word in positive if word in lower) - sum(1 for word in negative if word in lower)

    if score > 0:
        return "positive"
    if score < 0:
        return "negative"
    return "neutral"


def extract_key_topics(text: str):
    if not text:
        return []

    tokens = re.findall(r"\b[a-z]{4,}\b", text.lower())
    stop_words = {"this", "that", "with", "from", "your", "their", "which", "there", "what", "when", "where", "will", "have", "more", "about", "could"}
    topics = [token for token in tokens if token not in stop_words]
    return list(dict.fromkeys(topics))[:5]


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text.split()))


def build_context_window(history: list, summary: str = "", max_tokens: int = 700) -> str:
    if not history:
        return f"Summary: {summary}" if summary else ""

    context_parts = []
    total_tokens = 0

    if summary:
        summary_text = f"Summary: {summary}"
        context_parts.append(summary_text)
        total_tokens += estimate_tokens(summary_text)

    quiz_context = ""
    recent_quiz_entries = [entry for entry in history[-10:]  if isinstance(entry, dict) and entry.get("quiz_state")]
    if recent_quiz_entries:
        quiz_context = "User is currently in a quiz session. Remember previous answers, score, and question progress."
        quiz_tokens = estimate_tokens(quiz_context)
        if total_tokens + quiz_tokens <= max_tokens:
            context_parts.append(quiz_context)
            total_tokens += quiz_tokens

    for entry in reversed(history):
        entry_text = ""

    # ✅ HANDLE TYPES SAFELY
        if isinstance(entry, dict):
            entry_text = entry.get("message") or entry.get("content") or ""
            intent = entry.get("intent", "user")
        elif isinstance(entry, str):
            entry_text = entry
            intent = "user"
        else:
            entry_text = str(entry)
            intent = "user"

        entry_text = entry_text.strip()

        if not entry_text:
            continue

        # ✅ SAFE PREFIX
        prefix = "Assistant: " if intent == "assistant" else "User: "

        item_text = f"{prefix}{entry_text}"
        item_tokens = estimate_tokens(item_text)

        if total_tokens + item_tokens > max_tokens:
            break

        context_parts.append(item_text)
        total_tokens += item_tokens


    return "\n".join(reversed(context_parts))


def generate_conversation_summary(history: list, max_items: int = 10):
    if not history:
        return ""

    recent = history[-max_items:]
    summary_parts = []
    for item in recent:
        msg = item.get("message", "")
        intent = item.get("intent", "")
        if intent:
            summary_parts.append(f"[{intent}] {msg}")
        else:
            summary_parts.append(msg)
    return " | ".join(summary_parts)


def build_memory_entry(message: str, intent: str, quiz_state: dict = None):
    return {
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "intent": intent,
        "entities": extract_entities(message),
        "sentiment": analyze_sentiment(message),
        "key_topics": extract_key_topics(message),
        "quiz_state": quiz_state or {}
    }


def save_memory(user_id: str, message: str, intent: str, quiz_state: dict = None):
    existing = get_memory(user_id)
    memory_container = get_container()

    if existing:
        history = existing.get("history", [])
        history.append(build_memory_entry(message, intent, quiz_state=quiz_state))
        if len(history) > 50:
            history = history[-50:]

        existing["history"] = history
        existing["last_intent"] = intent
        existing["quiz_state"] = quiz_state or existing.get("quiz_state", {})
        existing["conversation_summary"] = generate_conversation_summary(history)
        memory_container.upsert_item(existing)
    else:
        history = [build_memory_entry(message, intent, quiz_state=quiz_state)]
        memory_container.upsert_item({
            "id": user_id,
            "user_id": user_id,
            "history": history,
            "last_intent": intent,
            "quiz_state": quiz_state or {},
            "conversation_summary": generate_conversation_summary(history),
            "goals": [],
            "preferences": {},
            "quiz_performance": {},
            "user_profile": {}
        })


def save_to_cosmos(message: str, response: str, intent: str, user_id: str):
    container = get_container()
    container.upsert_item({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "content": f"{message} {response}",
        "intent": intent,
        "category": intent,
    })
