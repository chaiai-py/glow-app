"""
🤖 ORCHESTRATOR MODULE (FIXED + STABLE VERSION)
"""

from dotenv import load_dotenv
import os
load_dotenv()

from openai import AzureOpenAI
from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT
)

from agents import (
    career_agent,
    learning_agent,
    finance_agent,
    wellness_agent,
    general_agent,
    search_knowledge,
    search_quiz_document
)

from memory import get_memory, save_memory, build_context_window
from safety_evaluator import validate_request, get_safety_disclaimer
from task_tracker import (
    create_goal,
    log_progress,
    detect_trends,
    get_active_goals
)

# 🔗 Azure OpenAI Client
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-02-15-preview",
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
)

MODEL = AZURE_OPENAI_DEPLOYMENT

print("✅ Orchestrator loaded")
print(f"MODEL: {MODEL}")


# =========================
# 🧠 INTENT CLASSIFIER
# =========================
def classify_intent_llm(message: str) -> str:
    try:
        prompt = f"""
        Classify into ONE:
        career, learning, finance, wellness, general

        Message: "{message}"
        """

        res = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        intent = res.choices[0].message.content.strip().lower()

        if intent not in ["career", "learning", "finance", "wellness"]:
            return "general"

        return intent

    except Exception as e:
        print("Intent error:", e)
        return "general"


# =========================
# 🤖 MAIN HANDLER
# =========================
def handle_message(message: str, user_id: str = "default"):

    try:
        print(f"🔐 Validating request for {user_id}")

        # Safety
        temp_intent = classify_intent_llm(message)
        validation = validate_request(user_id, message, temp_intent, temp_intent)

        if not validation.get("is_valid", True):
            return validation.get("errors", ["Blocked"])[0], "blocked"

        # Intent
        intent = classify_intent_llm(message)
        print("Intent:", intent)

        # =========================
        # 🧠 MEMORY (SAFE)
        # =========================
        memory_data = get_memory(user_id)

        if not isinstance(memory_data, dict):
            memory_data = {}

        history = memory_data.get("history", [])
        summary = memory_data.get("conversation_summary", "")

        if not isinstance(history, list):
            history = []

        if not isinstance(summary, str):
            summary = str(summary)

        memory_context = build_context_window(history, summary=summary, max_tokens=700)

        # =========================
        # 🎯 GOALS (SAFE)
        # =========================
        active_goals = ""
        goals_result = get_active_goals(user_id)

        if isinstance(goals_result, dict) and goals_result.get("status") == "success":
            goals = goals_result.get("goals", [])

            if isinstance(goals, list) and goals:
                active_goals = "\n".join([
                    f"- {g.get('title')} ({g.get('domain')})"
                    for g in goals[:3] if isinstance(g, dict)
                ])

        # =========================
        # 🔍 SEARCH (SAFE)
        # =========================
        search_context = search_knowledge(message)

        if isinstance(search_context, list):
            context_text = "\n".join(map(str, search_context))
        else:
            context_text = str(search_context or "")

        # =========================
        # 🧠 QUIZ HANDLER (SAFE)
        # =========================
        if "quiz" in message.lower():
            quiz_doc = search_quiz_document("quiz")

            if isinstance(quiz_doc, dict):
                choices = quiz_doc.get("choices", [])

                if isinstance(choices, list):
                    choices = ", ".join(map(str, choices))
                else:
                    choices = str(choices)

                return f"""
{quiz_doc.get('title', 'Quiz')}
{quiz_doc.get('content', '')}

Choices:
{choices}
""", intent

        # =========================
        # 🤖 AGENT ROUTING
        # =========================
        if intent == "career":
            response = career_agent(message, memory_context)

        elif intent == "learning":
            response = learning_agent(message, memory_context)

        elif intent == "finance":
            response = finance_agent(message, memory_context)

        elif intent == "wellness":
            response = wellness_agent(message, memory_context)

        else:
            response = general_agent(message, memory_context)

        # 🛡️ Ensure response is string
        if isinstance(response, dict):
            response = response.get("answer", str(response))
        else:
            response = str(response)

        # =========================
        # 💾 SAVE MEMORY (SAFE)
        # =========================
        try:
            save_memory(user_id, message, intent)
        except Exception as e:
            print("Memory warning:", e)

        # Disclaimer
        disclaimer = get_safety_disclaimer(intent)
        final_response = f"{response}\n\n{disclaimer}"

        return final_response, intent

    except Exception as e:
        print("❌ Orchestrator crash:", e)
        return "Something went wrong. Please try again.", "error"


# =========================
# 🎯 GOAL CREATION
# =========================
def create_user_goal(user_id: str, goal_title: str, domain: str, details):

    try:
        if not isinstance(details, dict):
            details = {}

        return create_goal(
            user_id=user_id,
            goal_title=goal_title,
            domain=domain,
            target_date= str(details.get("target_date") or ""),
            steps=details.get("steps", []),
            metrics=details.get("metrics", {})
        )

    except Exception as e:
        return {"status": "error", "message": str(e)}


# =========================
# 📈 PROGRESS TRACKING
# =========================
def track_user_progress(user_id: str, goal_id: str, metric_data):

    try:
        if not isinstance(metric_data, dict):
            metric_data = {}

        metric_name = str(metric_data.get("metric_name") or "progress")
        metric_value = metric_data.get("metric_value") or 0
        note = str(metric_data.get("note") or "")

        log_result = log_progress(
            user_id=user_id,
            goal_id=goal_id,
            metric_name=metric_name,
            metric_value=metric_value,
            note=note
        )

        if isinstance(log_result, dict) and log_result.get("status") == "success":
            trend = detect_trends(user_id, goal_id, metric_name)
            return {
                "status": "success",
                "progress": log_result,
                "trend": trend
            }

        return log_result

    except Exception as e:
        return {"status": "error", "message": str(e)}