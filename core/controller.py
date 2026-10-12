import os
import platform
import webbrowser
from urllib.parse import urlparse

from actions.system_control import (
    get_current_time_and_date,
    get_open_windows,
    get_system_status,
    lock_screen,
    media_next,
    media_play_pause,
    media_previous,
    take_screenshot,
    timer_manager,
    volume_down,
    volume_mute,
    volume_up,
)

from memory import memory

from .resource_controller import open_resource
from .resource_resolver import resolve_resource
from .web_search import open_website_by_name


def execute(request):
    if not isinstance(request, dict):
        return "I couldn't understand that request."

    intent = request.get("intent")

    # ==========================================
    # SYSTEM CONTROLS
    # ==========================================
    if intent == "system_control":
        action = request.get("action")
        if action == "volume_up":
            return volume_up()
        if action == "volume_down":
            return volume_down()
        if action == "volume_mute":
            return volume_mute()
        if action == "media_play_pause":
            return media_play_pause()
        if action == "media_next":
            return media_next()
        if action == "media_prev":
            return media_previous()
        if action == "system_status":
            return get_system_status()
        if action == "screenshot":
            return take_screenshot()
        if action == "lock_screen":
            return lock_screen()
        if action == "get_time":
            return get_current_time_and_date()
        if action == "list_windows":
            return get_open_windows()
        if action == "timer":
            seconds = request.get("seconds", 60)
            label = request.get("label")
            return timer_manager.set_timer(seconds, label)
        if action == "list_timers":
            return timer_manager.list_timers()
        return "Unknown system control action."

    # ==========================================
    # MEMORY & PERSONALIZATION
    # ==========================================
    if intent == "memory":
        action = request.get("action")
        if action == "set_name":
            name = request.get("name")
            return memory.set_user_name(name)
        if action == "get_name":
            name = memory.get_user_name()
            if name:
                return f"Your name is {name}."
            return "I don't know your name yet. You can tell me by saying 'My name is...'"
        if action == "remember_fact":
            key = request.get("key", "")
            value = request.get("value", "")
            return memory.remember_fact(key, value)
        if action == "list_facts":
            facts = memory.list_facts()
            if not facts:
                return "I don't have any saved facts about you yet."
            items = [f"{k} is {v}" for k, v in facts.items()]
            return "Here is what I remember: " + "; ".join(items) + "."
        if action == "add_note":
            note = request.get("note", "")
            return memory.add_note(note)
        if action == "get_notes":
            notes = memory.get_notes()
            if not notes:
                return "You have no saved notes."
            note_lines = [f"{idx + 1}. {n['content']}" for idx, n in enumerate(notes)]
            return "Here are your notes: " + " ".join(note_lines)
        if action == "clear_notes":
            return memory.clear_notes()
        if action == "set_response_style":
            style = request.get("style", "brief")
            return memory.set_response_style(style)
        return "Unknown memory action."

    # ==========================================
    # WEBSITES
    # ==========================================
    if intent == "open_website":
        url = request.get("url", "")
        if not isinstance(url, str):
            return "I couldn't open that website because its URL is invalid."

        candidate = url.strip()
        if not candidate:
            return "I couldn't open that website because its URL is invalid."
        if "://" not in candidate and not candidate.startswith("www."):
            candidate = f"https://{candidate}"

        try:
            parsed_url = urlparse(candidate)
        except ValueError:
            return "I couldn't open that website because its URL is invalid."
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.hostname:
            return "I couldn't open that website because its URL is invalid."
        if parsed_url.username or parsed_url.password:
            return "I couldn't open that website because its URL is invalid."
        try:
            if webbrowser.open(candidate, new=2):
                return "Opening the website in your default browser."
            return "I couldn't open the website in your default browser."
        except webbrowser.Error as exc:
            return f"I couldn't open the website in your default browser: {exc}"

    # ==========================================
    # SYSTEM SETTINGS
    # ==========================================
    if intent == "open_system_settings":
        uri = request.get("uri", "")
        if not isinstance(uri, str) or any(char in uri for char in "\r\n"):
            return "I couldn't open that settings page because its URI is invalid."
        scheme = uri.partition(":")[0].lower()
        if platform.system() != "Windows":
            return "This settings page can only be opened on Windows."
        if scheme not in {"ms-settings", "windowsdefender"}:
            return "I couldn't open that settings page because its URI is invalid."
        try:
            os.startfile(uri)
            return "Opening the requested Windows settings page."
        except OSError as exc:
            return f"I couldn't open the requested Windows settings page: {exc}"

    # Normal AI question
    if intent == "ask_ai":
        return None

    # Open something on the PC
    if intent == "open_resource":
        query = request.get("query", "").strip()
        if not query:
            return "I couldn't determine what you want me to open."

        resolution = resolve_resource(query)
        if resolution["status"] == "not_found":
            website_result = open_website_by_name(query)
            if website_result["status"] == "opened":
                return f"Opening {website_result['title']} in your default browser."
            if website_result["status"] == "error":
                return f"I couldn't find {query} on this computer, and the website lookup failed."
            return f"I couldn't find {query} on this computer."
        if resolution["status"] == "ambiguous":
            candidates = resolution.get("candidates", [])
            names = [candidate["name"] for candidate in candidates]
            if len(names) == 1:
                return f"I found {names[0]}, but I'm not confident it's what you meant."
            return "I found multiple possible matches: " + ", ".join(names) + "."
        if resolution["status"] == "found":
            resource = resolution["resource"]
            result = open_resource(resource)
            return result["message"]

    return "I don't know how to handle that request yet."