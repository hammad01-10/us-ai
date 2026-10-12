import re
from .intent_extractor import extract_intent

_WINDOWS_SETTINGS_URI = {
    "bluetooth settings": "ms-settings:bluetooth",
    "network settings": "ms-settings:network",
    "wifi settings": "ms-settings:network-wifi",
    "wireless settings": "ms-settings:network-wifi",
    "display settings": "ms-settings:display",
    "sound settings": "ms-settings:sound",
    "volume settings": "ms-settings:sound",
    "privacy settings": "ms-settings:privacy",
    "update settings": "ms-settings:windowsupdate",
    "windows update settings": "ms-settings:windowsupdate",
    "system settings": "ms-settings:",
    "about settings": "ms-settings:about",
}

_OPEN_REQUEST = re.compile(
    r"^\s*(?:(?:please|can you|could you|would you)\s+)?"
    r"(?:open|launch|start|visit|go to|navigate to)\b",
    flags=re.IGNORECASE,
)

_DIRECT_WEBSITE = re.compile(
    r"^\s*(?:(?:please|can you|could you|would you)\s+)?"
    r"(?:open|launch|start|visit|go to|navigate to)\s+"
    r"(?P<target>https?://[^\s]+|(?:www\.)?(?:[a-z0-9-]+\.)+[a-z]{2,}(?:[:/][^\s]*)?)"
    r"\s*[:?.!]*\s*$",
    flags=re.IGNORECASE,
)

_WINDOWS_SETTINGS_REQUEST = re.compile(
    r"^\s*(?:(?:please|can you|could you|would you)\s+)?"
    r"(?:open|launch|start)\s+(?:the\s+)?(?P<target>.+?)\s*\??\s*$",
    flags=re.IGNORECASE,
)

_TIME_REQUEST = re.compile(
    r"^\s*(?:(?:what|tell me)\s+(?:is\s+)?(?:the\s+|today'?s\s+|current\s+)?(?:time|date|day)(?:\s+is\s+it)?|what\s+time\s+is\s+it|what\s+day\s+is\s+it|today'?s\s+date)\s*\??\s*$",
    flags=re.IGNORECASE,
)

_VOLUME_UP = re.compile(
    r"^\s*(?:(?:turn|bring)\s+(?:the\s+)?volume\s+up|volume\s+up|increase\s+(?:the\s+)?volume|make\s+it\s+louder)\s*$",
    flags=re.IGNORECASE,
)

_VOLUME_DOWN = re.compile(
    r"^\s*(?:(?:turn|bring)\s+(?:the\s+)?volume\s+down|volume\s+down|decrease\s+(?:the\s+)?volume|lower\s+the\s+volume|make\s+it\s+quieter)\s*$",
    flags=re.IGNORECASE,
)

_VOLUME_MUTE = re.compile(
    r"^\s*(?:mute(?:\s+the\s+volume|\s+audio)?|unmute(?:\s+the\s+volume|\s+audio)?|silence\s+audio)\s*$",
    flags=re.IGNORECASE,
)

_MEDIA_PLAY_PAUSE = re.compile(
    r"^\s*(?:(?:play|resume|continue|unpause)\b(?=.*\b(?:music|song|track|video|tab|chrome|google|youtube|paused|pause)\b).*|"
    r"(?:pause|stop)\b(?=.*\b(?:music|song|track|video|tab|chrome|google|youtube|playing)\b).*|"
    r"pause\s+music|pause|media\s+play|media\s+pause)\s*$",
    flags=re.IGNORECASE,
)

_MEDIA_NEXT = re.compile(
    r"^\s*(?:next\s+song|next\s+track|skip\s+song|skip\s+track|skip)\s*$",
    flags=re.IGNORECASE,
)

_MEDIA_PREV = re.compile(
    r"^\s*(?:previous\s+song|previous\s+track|prev\s+song|prev\s+track)\s*$",
    flags=re.IGNORECASE,
)

_SYSTEM_STATUS = re.compile(
    r"^\s*(?:system\s+status|battery\s+status|battery\s+percentage|how\s+much\s+ram|memory\s+usage|pc\s+status|system\s+info)\s*\??\s*$",
    flags=re.IGNORECASE,
)

_SCREENSHOT = re.compile(
    r"^\s*(?:take\s+(?:a\s+)?screenshot|capture\s+(?:the\s+)?screen|screen\s+capture)\s*$",
    flags=re.IGNORECASE,
)

_LOCK_SCREEN = re.compile(
    r"^\s*(?:lock\s+(?:the\s+)?screen|lock\s+(?:the\s+)?computer|lock\s+pc|lock\s+workstation)\s*$",
    flags=re.IGNORECASE,
)

_LIST_WINDOWS = re.compile(
    r"^\s*(?:what(?:'?s|\s+is)\s+open(?:\s+on\s+(?:my\s+)?(?:desktop|screen|computer|pc))?|"
    r"(?:list|show)\s+(?:open|running)\s+(?:apps?|windows?|applications?|programs?)|"
    r"what\s+(?:apps?|windows?|programs?)\s+(?:are\s+)?(?:open|running)|"
    r"what\s+do\s+i\s+have\s+open|what(?:'?s|\s+is)\s+running)\s*\??\s*$",
    flags=re.IGNORECASE,
)

_TIMER_SET = re.compile(
    r"^\s*set\s+(?:a\s+)?timer\s+(?:for\s+)?(?P<amount>\d+)\s*(?P<unit>seconds?|secs?|minutes?|mins?|hours?|hrs?)(?:\s+(?:for|called)\s+(?P<label>.+))?\s*$",
    flags=re.IGNORECASE,
)

_TIMER_LIST = re.compile(
    r"^\s*(?:list\s+timers|show\s+timers|active\s+timers)\s*\??\s*$",
    flags=re.IGNORECASE,
)

_NAME_SET = re.compile(
    r"^\s*(?:my\s+name\s+is|call\s+me|remember\s+that\s+my\s+name\s+is)\s+(?P<name>[a-zA-Z\s]+)\s*$",
    flags=re.IGNORECASE,
)

_NAME_GET = re.compile(
    r"^\s*(?:what\s+is\s+my\s+name|what'?s\s+my\s+name|who\s+am\s+i|do\s+you\s+know\s+my\s+name)\s*\??\s*$",
    flags=re.IGNORECASE,
)

_NOTE_ADD = re.compile(
    r"^\s*(?:take\s+a\s+note|note\s+down|add\s+(?:a\s+)?note)\s*[:\-]?\s*(?P<note>.+)\s*$",
    flags=re.IGNORECASE,
)

_NOTE_GET = re.compile(
    r"^\s*(?:read\s+(?:my\s+)?notes|show\s+(?:my\s+)?notes|what\s+are\s+my\s+notes|list\s+(?:my\s+)?notes)\s*\??\s*$",
    flags=re.IGNORECASE,
)

_NOTE_CLEAR = re.compile(
    r"^\s*(?:clear\s+(?:all\s+)?(?:my\s+)?notes|delete\s+all\s+(?:my\s+)?notes)\s*$",
    flags=re.IGNORECASE,
)

_REMEMBER_FACT = re.compile(
    r"^\s*remember\s+that\s+(?P<fact>.+)\s*$",
    flags=re.IGNORECASE,
)

_FACTS_GET = re.compile(
    r"^\s*(?:what\s+do\s+you\s+remember\s+about\s+me|what\s+do\s+you\s+know\s+about\s+me|what\s+are\s+my\s+facts|list\s+facts)\s*\??\s*$",
    flags=re.IGNORECASE,
)

_RESPONSE_STYLE_SET = re.compile(
    r"^\s*(?:talk\s+less|be\s+more\s+concise|be\s+brief|switch\s+to\s+brief\s+mode|set\s+brief\s+mode|use\s+brief\s+mode|brief\s+mode|quiet\s+mode|be\s+quiet|keep\s+it\s+short|talk\s+more|be\s+more\s+detailed|give\s+me\s+more\s+detail|switch\s+to\s+detailed\s+mode|set\s+detailed\s+mode|use\s+detailed\s+mode|detailed\s+mode)\s*\??\s*$",
    flags=re.IGNORECASE,
)


def _normalize_website_url(target):
    candidate = target.strip().strip("\"'[]()")
    if not candidate:
        return None
    if candidate.lower().startswith(("http://", "https://")):
        return candidate
    if re.match(r"^(?:www\.)?(?:[a-z0-9-]+\.)+[a-z]{2,}(?::\d+)?(?:[/?#][^\s]*)?$", candidate, flags=re.IGNORECASE):
        return "https://" + candidate
    return None


def _normalize_setting_uri(target):
    normalized = target.strip().lower().rstrip("?!. ")
    if not normalized:
        return None
    alias = normalized.replace(" the ", " ").replace("my ", "")
    return _WINDOWS_SETTINGS_URI.get(alias)


def parse_command(user_text, history=None):
    """
    Understands user's request. Fast-routes system controls, memory, and timer
    actions with sub-millisecond latency. Explicit open/launch requests go
    through resource extraction, while general queries go to ask_ai.
    """
    clean_text = user_text.strip()
    if not clean_text:
        return {"intent": "unknown"}

    # 1. Fast System & Media Controls
    if _TIME_REQUEST.match(clean_text):
        return {"intent": "system_control", "action": "get_time"}

    if _VOLUME_UP.match(clean_text):
        return {"intent": "system_control", "action": "volume_up"}

    if _VOLUME_DOWN.match(clean_text):
        return {"intent": "system_control", "action": "volume_down"}

    if _VOLUME_MUTE.match(clean_text):
        return {"intent": "system_control", "action": "volume_mute"}

    if _MEDIA_PLAY_PAUSE.match(clean_text):
        return {"intent": "system_control", "action": "media_play_pause"}

    if _MEDIA_NEXT.match(clean_text):
        return {"intent": "system_control", "action": "media_next"}

    if _MEDIA_PREV.match(clean_text):
        return {"intent": "system_control", "action": "media_prev"}

    if _SYSTEM_STATUS.match(clean_text):
        return {"intent": "system_control", "action": "system_status"}

    if _SCREENSHOT.match(clean_text):
        return {"intent": "system_control", "action": "screenshot"}

    if _LOCK_SCREEN.match(clean_text):
        return {"intent": "system_control", "action": "lock_screen"}

    if _LIST_WINDOWS.match(clean_text):
        return {"intent": "system_control", "action": "list_windows"}

    m_timer = _TIMER_SET.match(clean_text)
    if m_timer:
        amount = int(m_timer.group("amount"))
        unit = m_timer.group("unit").lower()
        label = m_timer.group("label")
        multiplier = 1
        if unit.startswith("min"):
            multiplier = 60
        elif unit.startswith("hour") or unit.startswith("hr"):
            multiplier = 3600
        seconds = amount * multiplier
        return {"intent": "system_control", "action": "timer", "seconds": seconds, "label": label}

    if _TIMER_LIST.match(clean_text):
        return {"intent": "system_control", "action": "list_timers"}

    # 2. Fast Memory Controls
    m_name_set = _NAME_SET.match(clean_text)
    if m_name_set:
        return {"intent": "memory", "action": "set_name", "name": m_name_set.group("name").strip()}

    if _NAME_GET.match(clean_text):
        return {"intent": "memory", "action": "get_name"}

    m_note_add = _NOTE_ADD.match(clean_text)
    if m_note_add:
        return {"intent": "memory", "action": "add_note", "note": m_note_add.group("note").strip()}

    if _NOTE_GET.match(clean_text):
        return {"intent": "memory", "action": "get_notes"}

    if _NOTE_CLEAR.match(clean_text):
        return {"intent": "memory", "action": "clear_notes"}

    m_fact = _REMEMBER_FACT.match(clean_text)
    if m_fact:
        fact_text = m_fact.group("fact").strip()
        # Parse "X is Y" if possible
        if " is " in fact_text:
            key, _, val = fact_text.partition(" is ")
            return {"intent": "memory", "action": "remember_fact", "key": key.strip(), "value": val.strip()}
        return {"intent": "memory", "action": "remember_fact", "key": fact_text, "value": "true"}

    if _FACTS_GET.match(clean_text):
        return {"intent": "memory", "action": "list_facts"}

    m_style = _RESPONSE_STYLE_SET.match(clean_text)
    if m_style:
        lowered = clean_text.lower()
        if any(phrase in lowered for phrase in ["quiet mode", "be quiet", "keep it short"]):
            return {"intent": "memory", "action": "set_response_style", "style": "quiet"}
        if any(phrase in lowered for phrase in ["talk less", "be more concise", "be brief", "brief mode", "set brief mode", "use brief mode"]):
            return {"intent": "memory", "action": "set_response_style", "style": "brief"}
        return {"intent": "memory", "action": "set_response_style", "style": "detailed"}

    # 3. Explicit Open/Launch Requests
    website_match = _DIRECT_WEBSITE.match(clean_text)
    if website_match:
        url = _normalize_website_url(website_match.group("target"))
        if url:
            return {"intent": "open_website", "url": url}

    settings_match = _WINDOWS_SETTINGS_REQUEST.match(clean_text)
    if settings_match:
        target = settings_match.group("target").strip().lower()
        uri = _normalize_setting_uri(target)
        if uri:
            return {"intent": "open_system_settings", "uri": uri}

    if _OPEN_REQUEST.search(clean_text):
        result = extract_intent(clean_text, history)
        if isinstance(result, dict):
            intent = result.get("intent")
            if intent in {"open_resource", "open_website", "open_system_settings"}:
                return result

    # 4. Standard conversational query
    return {"intent": "ask_ai", "query": clean_text}
