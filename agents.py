import requests
from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_KEY,
    AZURE_SEARCH_INDEX
)

# -----------------------------
# 🔎 SEARCH (RAG)
# -----------------------------
def search_knowledge(query):
    url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX}/docs/search?api-version=2023-11-01"

    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_SEARCH_KEY
    }

    body = {
        "search": query,
        "top": 3
    }

    try:
        res = requests.post(url, headers=headers, json=body)
        data = res.json()

        return [doc.get("content", "") for doc in data.get("value", [])]

    except Exception as e:
        print("SEARCH ERROR:", e)
        return []


# -----------------------------
# 🧠 LLM CALL (Azure OpenAI)
# -----------------------------
def call_llm(prompt):
    url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version=2024-02-15-preview"

    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_API_KEY
    }

    body = {
        "messages": [
            {"role": "system", "content": """You are an intelligent AI life coach. 
             When conducting a quiz:
             1. If the user provides an answer, evaluate it immediately (Correct/Incorrect).
             2. Provide a brief explanation and a piece of trivia.
             3. Ask a NEW and DIFFERENT question to continue the quiz. 
             Never repeat the same question twice. Ask only ONE question at a time."""},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    try:
        res = requests.post(url, headers=headers, json=body)
        data = res.json()

        # 🔥 Debug if needed
        if "choices" not in data:
            print("LLM ERROR RESPONSE:", data)
            return "Error: Unable to generate response."

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("LLM ERROR:", e)
        return "Error calling AI."


# -----------------------------
# 🧩 BASE PROMPT BUILDER
# -----------------------------
def build_prompt(role, message, memory, context):
    return f"""
You are a {role}.

User message:
{message}

User history:
{memory}

Relevant knowledge:
{context}

IMPORTANT: Format your response with:
- Clear paragraphs separated by blank lines
- Use numbered lists (1., 2., 3., etc.) for steps or multiple points
- Use bullet points (- ) for sub-items
- Use bold text with **text** for important terms
- Keep sentences clear and actionable

If the user is participating in a quiz:
1. Check if the 'User message' is an answer to the last question in 'User history'.
2. If it is an answer, provide feedback (correct/incorrect) and trivia, then ask a NEW question.
3. If the user is just starting, ask the first question.
4. Ensure you always progress to a different question and never loop.

Give clear, actionable, and helpful advice.
"""


# -----------------------------
# 🎯 AGENTS
# -----------------------------
def career_agent(message, memory):
    context = search_knowledge(message)

    prompt = build_prompt(
        "career coach",
        message,
        memory,
        context
    )

    return call_llm(prompt)


def learning_agent(message, memory):
    context = search_knowledge(message)

    prompt = build_prompt(
        "learning coach",
        message,
        memory,
        context
    )

    return call_llm(prompt)


def finance_agent(message, memory):
    context = search_knowledge(message)

    prompt = build_prompt(
        "financial advisor",
        message,
        memory,
        context
    )

    return call_llm(prompt)


def wellness_agent(message, memory):
    context = search_knowledge(message)

    prompt = build_prompt(
        "wellness coach",
        message,
        memory,
        context
    )

    return call_llm(prompt)


def general_agent(message, memory):
    context = search_knowledge(message)

    prompt = build_prompt(
        "life optimization assistant",
        message,
        memory,
        context
    )

    return call_llm(prompt)