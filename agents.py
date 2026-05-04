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
        "search": query or "*",
        "top": 5,
        "queryType": "full",
        "searchFields": "content,title,category,keywords",
        "select": "content,title,category,source",
        "orderby": "@search.score desc"
    }

    try:
        res = requests.post(url, headers=headers, json=body)
        data = res.json()

        if "value" not in data:
            print("SEARCH ERROR: unexpected response", data)
            return []

        results = []
        for doc in data.get("value", []):
            text = doc.get("content", "")
            title = doc.get("title", "")
            category = doc.get("category", "")
            source = doc.get("source", "")
            if title:
                results.append(f"{title}: {text}")
            else:
                results.append(text)

        return results

    except Exception as e:
        print("SEARCH ERROR:", e)
        return []


def search_quiz_document(query):
    url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX}/docs/search?api-version=2023-11-01"

    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_SEARCH_KEY
    }

    body = {
        "search": query or "*",
        "top": 1,
        "queryType": "full",
        "searchFields": "content,title,category,keywords",
        "select": "title,content,choices,answer,category",
        "orderby": "@search.score desc"
    }

    try:
        res = requests.post(url, headers=headers, json=body)
        data = res.json()

        if "value" not in data or len(data["value"]) == 0:
            return None

        return data["value"][0]

    except Exception as e:
        print("QUIZ SEARCH ERROR:", e)
        return None


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
             1. First, ask how many questions the user wants (maximum 20).
             2. Randomly select quiz modes: multiple_choice, true_false, identification, enumeration based on topic.
             3. Ask only ONE question at a time and wait for the user's answer.
             4. For multiple_choice: Present options as A, B, C, D on separate lines.
             5. For true_false: Present True/False options.
             6. For identification: Ask for direct answer.
             7. For enumeration: Ask user to list items.
             8. When user answers, evaluate immediately (Correct/Incorrect).
             9. Provide brief explanation and trivia.
             10. Award points: 10 for correct, 0 for wrong.
             11. Show current score and progress.
             12. Ask a NEW and DIFFERENT question to continue.
             13. Remember previous answers and context in the conversation.
             Never repeat the same question twice. Always progress through the quiz."""},
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
            return {"text": "Error: Unable to generate response."}

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

User history (includes previous quiz answers and context):
{memory}

Relevant knowledge:
{context}

IMPORTANT: Format your response with:
- Clear paragraphs separated by blank lines
- Use numbered lists (1., 2., 3., etc.) for steps or multiple points
- Use bullet points (- ) for sub-items
- Use bold text with **text** for important terms
- Keep sentences clear and actionable

QUIZ HANDLING:
If the user is participating in a quiz:
1. Check the 'User history' for previous quiz context, answers, and current score.
2. If this is the first message about a quiz, ask how many questions they want (max 20).
3. Randomly select appropriate quiz modes based on topic: multiple_choice, true_false, identification, enumeration.
4. Ask only ONE question at a time.
5. When evaluating answers, reference previous context to maintain conversation flow.
6. Award points and track score throughout the quiz.
7. Ensure questions are different and progress logically.
8. Remember all previous answers and maintain conversation context.

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