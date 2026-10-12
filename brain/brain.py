import platform
import re
from datetime import datetime
import requests

from config.settings import OLLAMA_MODEL, OLLAMA_TIMEOUT, OLLAMA_URL
from memory import memory

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def format_spoken_answer(text, max_sentences=None, max_chars=None, style=None):
    """Condense verbose model output into a voice-friendly answer."""
    if text is None:
        return ""
    cleaned = str(text).strip()
    if not cleaned:
        return ""

    style = (style or memory.get_response_style() or "brief").lower()
    if style == "quiet":
        max_sentences = 1 if max_sentences is None else max_sentences
        max_chars = 150 if max_chars is None else max_chars
    elif max_sentences is None:
        max_sentences = 4 if style == "detailed" else 2
    if max_chars is None:
        max_chars = 420 if style == "detailed" else 260

    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = cleaned.replace("\n", " ")
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = cleaned.strip()

    sentences = [part.strip() for part in _SENTENCE_SPLIT_RE.split(cleaned) if part.strip()]
    if not sentences:
        return cleaned

    limited = sentences[:max_sentences]
    final = " ".join(limited)
    if len(final) > max_chars:
        words = final.split()
        trimmed = []
        current = 0
        for word in words:
            extra = len(word) + (1 if trimmed else 0)
            if current + extra > max_chars:
                break
            trimmed.append(word)
            current += extra
        final = " ".join(trimmed).rstrip(".") + "."

    final = re.sub(r"\s+([,.;:!?])", r"\1", final)
    return final if final.endswith((".", "!", "?")) else final + "."

SYSTEM_PROMPT = """You are US AI, a capable personal desktop assistant and attentive aide.

Guidelines:
- Speak with composed confidence, warmth, and understated wit when it feels natural.
- Sound articulate and polished, like a thoughtful human aide; avoid exaggerated formality, catchphrases, and forced jokes.
- Address the user by name only when they have shared it.
- Keep responses concise (1 to 3 spoken sentences) unless the user specifically asks for deep details or an explanation.
- Speak like a companion speaking aloud, avoiding complex markdown tables or excessive bullet points.
- Use conversation history to resolve pronouns ("it", "that", "he", "she", "next").
- Use the current date, time, and user memory provided in the context below to give accurate and personalized answers.
- Never claim a desktop action succeeded unless the action result confirms it.
"""


def build_system_context():
    """Builds dynamic real-time context including clock, system, and user memory."""
    now = datetime.now()
    time_str = now.strftime("%I:%M %p").lstrip("0")
    date_str = now.strftime("%A, %B %d, %Y")

    context_sections = [
        f"Current Date & Time: {time_str} on {date_str}",
        f"System: {platform.system()} {platform.release()}",
    ]

    mem_context = memory.format_context_for_prompt()
    if mem_context:
        context_sections.append(mem_context)

    return "\n\n".join(context_sections)


def ask_ai(prompt, history=None):
    if history is None:
        history = []

    conversation_text = ""
    for message in history:
        role = message.get("role", "user").capitalize()
        content = message.get("content", "")
        conversation_text += f"{role}: {content}\n"

    system_context = build_system_context()

    full_prompt = f"""{SYSTEM_PROMPT}

[System & User Context]
{system_context}

[Conversation History]
{conversation_text}

User: {prompt}

US AI:"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 70,
                },
            },
            timeout=OLLAMA_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        answer = data["response"].strip()
        return format_spoken_answer(answer, style=memory.get_response_style())
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Could not connect to Ollama. Please ensure the Ollama service is running on your machine."
        )


if __name__ == "__main__":
    print()
    print("==============================")
    print("       US AI BRAIN TEST")
    print("==============================")

    history = [
        {"role": "user", "content": "Do you know about the history of Pakistan?"},
        {"role": "assistant", "content": "Pakistan was established in 1947."},
    ]

    question = "Tell me more about it."
    print("User:", question)
    try:
        answer = ask_ai(question, history)
        print("US AI:", answer)
    except Exception as exc:
        print("Error:", exc)
