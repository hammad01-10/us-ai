import json
import logging
from datetime import datetime
from pathlib import Path
from threading import Lock

MEMORY_DIR = Path.home() / ".us-ai"
MEMORY_FILE = MEMORY_DIR / "memory.json"


class MemoryManager:
    """Persistent storage for user profile, facts, and notes."""

    def __init__(self, file_path=MEMORY_FILE):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._data = {
            "user_profile": {"name": None},
            "facts": {},
            "notes": [],
            "settings": {"response_style": "brief"},
        }
        self._load()

    def _load(self):
        with self._lock:
            if not self.file_path.exists():
                self._save()
                return
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        self._data.update(loaded)
            except Exception as exc:
                logging.error(f"Failed to load memory file: {exc}")

    def _save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            logging.error(f"Failed to save memory file: {exc}")

    # ================= User Profile =================
    def set_user_name(self, name):
        with self._lock:
            clean_name = name.strip()
            self._data["user_profile"]["name"] = clean_name
            self._save()
            return f"I will remember that your name is {clean_name}."

    def get_user_name(self):
        with self._lock:
            return self._data["user_profile"].get("name")

    # ================= Facts =================
    def remember_fact(self, key, value):
        with self._lock:
            clean_key = key.strip().lower()
            clean_val = value.strip()
            self._data["facts"][clean_key] = clean_val
            self._save()
            return f"Got it. I'll remember that {key} is {clean_val}."

    def get_fact(self, key):
        with self._lock:
            return self._data["facts"].get(key.strip().lower())

    def list_facts(self):
        with self._lock:
            return dict(self._data["facts"])

    def set_response_style(self, style):
        with self._lock:
            normalized = str(style or "brief").strip().lower()
            if normalized in {"quiet", "silent", "whisper", "minimal"}:
                normalized = "quiet"
            elif normalized in {"brief", "short", "concise"}:
                normalized = "brief"
            elif normalized in {"detailed", "detailed mode", "verbose", "long"}:
                normalized = "detailed"
            else:
                normalized = "brief"

            self._data.setdefault("settings", {})["response_style"] = normalized
            self._save()
            return f"Response style set to {normalized}."

    def get_response_style(self):
        with self._lock:
            return str(self._data.get("settings", {}).get("response_style", "brief")).lower()

    def forget_fact(self, key):
        with self._lock:
            clean_key = key.strip().lower()
            if clean_key in self._data["facts"]:
                del self._data["facts"][clean_key]
                self._save()
                return f"I have forgotten about {clean_key}."
            return f"I don't have any record of {clean_key}."

    # ================= Notes =================
    def add_note(self, content):
        with self._lock:
            notes = self._data.setdefault("notes", [])
            note_id = len(notes) + 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            entry = {
                "id": note_id,
                "content": content.strip(),
                "created_at": timestamp,
            }
            notes.append(entry)
            self._save()
            return f"Note saved: {content.strip()}"

    def get_notes(self):
        with self._lock:
            return list(self._data.get("notes", []))

    def clear_notes(self):
        with self._lock:
            self._data["notes"] = []
            self._save()
            return "Cleared all your notes."

    # ================= Context for LLM =================
    def format_context_for_prompt(self):
        """Constructs a brief context string summarizing user profile and facts for the LLM."""
        with self._lock:
            lines = []
            name = self._data["user_profile"].get("name")
            if name:
                lines.append(f"User's Name: {name}")

            facts = self._data.get("facts", {})
            if facts:
                fact_strs = [f"- {k}: {v}" for k, v in list(facts.items())[:10]]
                lines.append("Known facts about user:\n" + "\n".join(fact_strs))

            notes = self._data.get("notes", [])
            if notes:
                recent_notes = [f"- {n['content']} ({n['created_at']})" for n in notes[-5:]]
                lines.append("Recent user notes:\n" + "\n".join(recent_notes))

            response_style = self._data.get("settings", {}).get("response_style", "brief")
            lines.append(f"Response style: {response_style}")

            return "\n\n".join(lines)


# Global singleton instance
memory = MemoryManager()
