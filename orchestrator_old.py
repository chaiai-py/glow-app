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

# 🔍 DEBUG
print("KEY:", AZURE_OPENAI_API_KEY)
print("ENDPOINT:", AZURE_OPENAI_ENDPOINT)
print("MODEL:", AZURE_OPENAI_DEPLOYMENT)

# 🔗 Azure OpenAI Client
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-02-15-preview",
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
)

MODEL = AZURE_OPENAI_DEPLOYMENT


# 🧠 INTENT CLASSIFIER
def classify_intent_llm(message: str) -> str:
    try:
        prompt = f"""
        Classify this message into ONE of these:
        career, learning, finance, wellness

        Message: "{message}"

        Only return one word.
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


# 🤖 MAIN HANDLER WITH RAG & MEMORY
def handle_message(message: str, user_id: str = "default"):
    try:
        # 1️⃣ Classify intent
        intent = classify_intent_llm(message)
        print(f"Detected intent: {intent}")

        # 2️⃣ Get user memory
        memory_data = get_memory(user_id)
        memory_context = ""
        if memory_data:
            history = memory_data.get("history", [])
            memory_context = "\n".join(history[-5:]) if history else ""  # Last 5 messages
        
        # 3️⃣ Get knowledge context from Azure AI Search
        search_context = search_knowledge(message)
        context_text = "\n".join(search_context) if search_context else "No additional context found."

        # 4️⃣ Route to appropriate agent based on intent
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

        # 5️⃣ Save to memory
        try:
            save_memory(user_id, message, intent)
        except Exception as e:
            print(f"Memory save error: {e}")

        return response, intent

    except Exception as e:
        print("LLM ERROR:", e)
        return "Something went wrong. Please try again.", "error"