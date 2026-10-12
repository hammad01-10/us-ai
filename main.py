import sounddevice as sd

from brain.brain import ask_ai
from brain.command_parser import parse_command
from brain.conversation import ConversationManager
from config.settings import DEFAULT_MIC_DEVICE, DEFAULT_RECORD_SECONDS, DEFAULT_SAMPLE_RATE
from core.controller import execute
from core.web_search import (
    search_web,
    should_search_web_first,
    spoken_web_answer,
    web_search_failure_message,
)
from voice.stt import get_whisper_model, record_and_transcribe
from voice.tts import get_piper_voice, speak

SAMPLE_RATE = DEFAULT_SAMPLE_RATE
RECORD_SECONDS = DEFAULT_RECORD_SECONDS
DEVICE = DEFAULT_MIC_DEVICE


def get_answer(user_text, conversation=None):
    if not user_text:
        return "I didn't hear anything."

    history = conversation.get_previous_history() if conversation else []
    intent = parse_command(user_text, history)
    normalized_intent = intent.get("intent") if isinstance(intent, dict) else None

    # Handle desktop actions, system controls, and memory commands
    if normalized_intent in {
        "system_control",
        "memory",
        "open_resource",
        "open_website",
        "open_system_settings",
    }:
        result = execute(intent)
        if result:
            return result
        return f"I couldn't open or execute {intent.get('query', 'that')}."

    # Handle real-time web search queries
    web_result = None
    if should_search_web_first(user_text):
        web_result = search_web(user_text, history=history)
        if web_result.get("status") == "ok":
            return spoken_web_answer(web_result)
        if web_result.get("status") == "error":
            print(web_result.get("message", "Web search failed."))
        return web_search_failure_message(web_result)

    # Local LLM generation
    try:
        answer = ask_ai(user_text, history=history)
        if answer and answer.strip():
            return answer
    except Exception as exc:
        print(f"Local AI failed: {exc}")

    # Fallback to web search
    if web_result is None:
        web_result = search_web(user_text, history=history)
    if web_result.get("status") == "ok":
        return spoken_web_answer(web_result)

    return "I couldn't answer that right now."


def main():
    print("Loading US AI speech recognition & TTS...")
    # Preload Whisper and Piper models once so speech and answers are instant
    get_whisper_model()
    get_piper_voice()

    conversation = ConversationManager()

    print()
    print("==============================")
    print("        US AI ONLINE")
    print("==============================")
    print("Voice + AI + Memory + Desktop Control")
    print()
    print("US AI is ready. Press Ctrl+C to exit.")

    while True:
        try:
            user_text = record_and_transcribe(
                duration=RECORD_SECONDS,
                sample_rate=SAMPLE_RATE,
                device=DEVICE,
            )
        except KeyboardInterrupt:
            print("\nUS AI is shutting down.")
            break

        print()
        print("You said:")
        print(user_text)

        if not user_text:
            speak("I didn't hear anything.")
            continue

        conversation.add_user(user_text)
        answer = get_answer(user_text, conversation=conversation)
        conversation.add_assistant(answer)

        print()
        print("US AI:")
        print(answer)
        print("\nUS AI is speaking...")
        speak(answer, block=True)

        if user_text.lower() in {"exit", "shutdown", "turn off", "goodbye"}:
            break


if __name__ == "__main__":
    main()
