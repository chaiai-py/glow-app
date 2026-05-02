"""
🤖 ORCHESTRATOR MODULE
Central orchestration engine for the GLOW agentic personal assistant.
Handles intent classification, multi-agent routing, RAG integration, memory management, and safety validation.

Architecture:
- Safety Validation: All requests pass through safety checks
- Intent Classification: Determines user domain (career, learning, finance, wellness)
- Multi-Agent Routing: Routes to specialized agents based on intent
- RAG Integration: Azure AI Search for knowledge grounding
- Memory Management: Cosmos DB for conversation history and goal tracking
- Analytics: Tracks progress and detects trends
"""

from dotenv import load_dotenv
import os
load_dotenv(dotenv_path="/Users/charleneannecordero/glow-app/.env")

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
    search_knowledge
)
from memory import get_memory, save_memory
from safety_evaluator import validate_request, get_safety_disclaimer
from task_tracker import (
    create_goal,
    log_progress,
    detect_trends,
    create_study_plan,
    analyze_expenses,
    track_habit,
    get_active_goals
)

# 🔗 Azure OpenAI Client
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-02-15-preview",
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
)

MODEL = AZURE_OPENAI_DEPLOYMENT

# 🔍 DEBUG
print("✅ Orchestrator: Config loaded")
print(f"✅ Orchestrator: Model = {MODEL}")


# 🧠 INTENT CLASSIFIER
def classify_intent_llm(message: str) -> str:
    """
    Classify user message into one of: career, learning, finance, wellness, general.
    Uses Azure OpenAI for intelligent intent classification.
    """
    try:
        prompt = f"""
        Classify this message into ONE of these categories:
        - career: Job search, career advice, professional development
        - learning: Education, studying, skill development, exam prep
        - finance: Money management, budgeting, investments, expenses
        - wellness: Health, exercise, mental health, habits, routines
        - general: Other topics

        Message: "{message}"

        Return only the category name (one word).
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
        print(f"❌ Intent classification error: {e}")
        return "general"


# 🤖 MAIN ORCHESTRATION ENGINE
def handle_message(message: str, user_id: str = "default") -> tuple:
    """
    Main orchestration function that:
    1. Validates request for safety
    2. Classifies intent
    3. Retrieves user memory
    4. Searches knowledge base (RAG)
    5. Routes to appropriate agent
    6. Saves to memory
    
    Returns:
        (response: str, intent: str)
    """
    try:
        # 1️⃣ SAFETY VALIDATION
        print(f"🔐 Validating request for user: {user_id}")
        
        # Perform safety checks
        intent_temp = classify_intent_llm(message)
        validation = validate_request(user_id, message, intent_temp, intent_temp)
        
        if not validation["is_valid"]:
            error_msg = validation["errors"][0]
            print(f"⛔ Safety validation failed: {error_msg}")
            return error_msg, "blocked"
        
        if validation["warnings"]:
            print(f"⚠️ Warnings: {validation['warnings']}")
        
        # 2️⃣ INTENT CLASSIFICATION
        print(f"🧠 Classifying intent for message: {message[:50]}...")
        intent = classify_intent_llm(message)
        print(f"✅ Intent classified as: {intent}")

        # 3️⃣ RETRIEVE USER MEMORY & CONTEXT
        memory_data = get_memory(user_id)
        memory_context = ""
        active_goals = ""
        
        if memory_data:
            history = memory_data.get("history", [])
            memory_context = "\n".join(history[-5:]) if history else ""
            print(f"✅ Memory retrieved: {len(history)} previous messages")
        
        # Get active goals for context
        goals_result = get_active_goals(user_id)
        if goals_result["status"] == "success" and goals_result["goals"]:
            active_goals = "\n".join([f"- {g['title']} (Domain: {g['domain']})" for g in goals_result["goals"][:3]])
            print(f"✅ Active goals loaded: {goals_result['count']} goals")
        
        # 4️⃣ RAG: SEARCH KNOWLEDGE BASE
        print(f"🔍 Searching knowledge base...")
        search_context = search_knowledge(message)
        context_text = "\n".join(search_context) if search_context else "No additional knowledge found."
        print(f"✅ Knowledge base search complete")

        # 5️⃣ ROUTE TO SPECIALIZED AGENT
        print(f"🎯 Routing to {intent} agent...")
        
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
        
        print(f"✅ Agent response generated ({len(response)} chars)")
        
        # 6️⃣ SAVE TO MEMORY
        try:
            save_memory(user_id, message, intent)
            print(f"💾 Memory saved successfully")
        except Exception as e:
            print(f"⚠️ Memory save warning: {e}")
        
        # Add safety disclaimer
        response_with_disclaimer = f"{response}\n\n{validation['disclaimer']}"
        
        return response_with_disclaimer, intent

    except Exception as e:
        print(f"❌ Orchestration error: {e}")
        return "Something went wrong. Please try again.", "error"


# 📋 HANDLE GOAL CREATION (Extended functionality)
def create_user_goal(user_id: str, goal_title: str, domain: str, details: dict) -> dict:
    """
    Create a structured goal with tracking.
    
    Args:
        user_id: User ID
        goal_title: Goal title
        domain: learning, career, finance, or wellness
        details: {target_date, steps, metrics}
    
    Returns:
        Goal creation result
    """
    try:
        result = create_goal(
            user_id=user_id,
            goal_title=goal_title,
            domain=domain,
            target_date=details.get("target_date"),
            steps=details.get("steps", []),
            metrics=details.get("metrics", {})
        )
        return result
    except Exception as e:
        print(f"❌ Goal creation error: {e}")
        return {"status": "error", "message": str(e)}


# 📈 HANDLE PROGRESS TRACKING (Extended functionality)
def track_user_progress(user_id: str, goal_id: str, metric_data: dict) -> dict:
    """
    Log progress and detect trends.
    
    Args:
        user_id: User ID
        goal_id: Goal ID
        metric_data: {metric_name, metric_value, note}
    
    Returns:
        Progress tracking result with trend analysis
    """
    try:
        # Log progress
        log_result = log_progress(
            user_id=user_id,
            goal_id=goal_id,
            metric_name=metric_data.get("metric_name"),
            metric_value=metric_data.get("metric_value"),
            note=metric_data.get("note", "")
        )
        
        if log_result["status"] == "success":
            # Detect trends
            trend_result = detect_trends(user_id, goal_id, metric_data.get("metric_name"))
            return {
                "status": "success",
                "progress_logged": log_result,
                "trend_analysis": trend_result
            }
        return log_result
    except Exception as e:
        print(f"❌ Progress tracking error: {e}")
        return {"status": "error", "message": str(e)}
