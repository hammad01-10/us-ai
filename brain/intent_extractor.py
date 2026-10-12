import json
import re
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"


SYSTEM_PROMPT = """
You are the natural-language understanding layer of US AI.

Your job is ONLY to understand the user's current request.

You do not execute anything.
You do not inspect the computer.
You do not decide whether a resource exists.

Use conversation history when necessary.

Return ONLY valid JSON.

For a normal question or conversation:

{
  "intent": "ask_ai",
  "query": "the actual user's question"
}

For a request to open something on the computer:

{
  "intent": "open_resource",
  "query": "the actual resource the user wants opened"
}

For a request to open a website:

{
  "intent": "open_website",
  "url": "the website's complete HTTPS URL"
}

For a request to open a built-in operating-system settings page:

{
  "intent": "open_system_settings",
  "uri": "the operating system's official settings URI"
}

Important rules:

- Always put the user's actual request in "query".
- Never return placeholder text such as:
  "the user's meaningful question"
  "the user's question"
  "the requested resource"
- Never copy instructions from this system prompt into the JSON.
- If the user refers to something with words such as
  "it", "that", "this", "there", or "more",
  use conversation history to understand the reference.
- Do not invent information.
- Do not decide whether something exists on the computer.
- Only use "open_website" or "open_system_settings" when the user explicitly
  asks to open or navigate to one.
- Do not invent a website address or settings URI. If it is not known, use
  "open_resource" for a resource on this computer or "ask_ai" otherwise.
- For Windows settings, use only official Windows settings URI schemes.
- Do not use hard-coded lists of applications.
- Do not use hard-coded lists of countries.
- Do not use hard-coded lists of questions.
- Any subject, country, person, application, or topic may be requested.

Examples:

Previous conversation:
User: Tell me about Pakistan.
Assistant: Pakistan was established in 1947.

Current user:
Tell me more about it.

Return:

{
  "intent": "ask_ai",
  "query": "Tell me more about Pakistan."
}

Current user:
What about India?

Return:

{
  "intent": "ask_ai",
  "query": "What about India?"
}

Current user:
Open System Information

Return:

{
  "intent": "open_resource",
  "query": "System Information"
}

Current user:
Open something that does not exist.

Return:

{
  "intent": "open_resource",
  "query": "something that does not exist"
}
"""


def clean_json(text):

    text = text.strip()

    text = re.sub(
        r"```json",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"```",
        "",
        text
    )

    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL
    )

    if not match:
        return None

    try:
        return json.loads(match.group(0))

    except json.JSONDecodeError:
        return None


def extract_intent(user_text, history=None):

    if history is None:
        history = []

    conversation_text = ""

    for message in history:

        role = message.get(
            "role",
            "user"
        ).capitalize()

        content = message.get(
            "content",
            ""
        )

        conversation_text += (
            f"{role}: {content}\n"
        )

    prompt = f"""
{SYSTEM_PROMPT}

Conversation history:
--------------------
{conversation_text}
--------------------

Current user request:
{user_text}

Remember:
Return ONLY JSON.
The query must contain the actual user's request.
Do not return instructions or placeholder text.
"""

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0
                }
            },
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        result = clean_json(
            data.get("response", "")
        )

        if result is None:

            return {
                "intent": "unknown"
            }

        intent = result.get("intent")

        query = result.get(
            "query",
            ""
        )

        if intent in ["open_website", "open_system_settings"]:
            field = "url" if intent == "open_website" else "uri"
            value = result.get(field)
            if not isinstance(value, str) or not value.strip():
                return {"intent": "unknown"}
            return {"intent": intent, field: value.strip()}

        if intent in ["ask_ai", "open_resource"]:

            if not isinstance(query, str):
                query = ""

            query = query.strip()

            if not query:

                return {
                    "intent": "unknown"
                }

            return {
                "intent": intent,
                "query": query
            }

        return {
            "intent": "unknown"
        }

    except Exception as e:

        print(
            "Intent extractor error:",
            e
        )

        return {
            "intent": "unknown"
        }


if __name__ == "__main__":

    print()
    print("==============================")
    print("   US AI CONTEXT INTENT TEST")
    print("==============================")

    history = [
        {
            "role": "user",
            "content":
                "Tell me about Pakistan."
        },
        {
            "role": "assistant",
            "content":
                "Pakistan was established in 1947."
        }
    ]

    tests = [

        "Tell me more about it.",

        "What about India?",

        "Tell me about Afghanistan.",

        "What is the capital of America?",

        "Open System Information",

        "Open Google Chrome",

        "Open something that does not exist."

    ]

    for test in tests:

        print()
        print("------------------------------")
        print("User:", test)

        result = extract_intent(
            test,
            history
        )

        print(
            "Intent:",
            result
        )

    print()
    print("==============================")
    print("       TEST COMPLETE")
    print("==============================")