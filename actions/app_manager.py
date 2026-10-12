import os
import re
import subprocess
from pathlib import Path
from rapidfuzz import process, fuzz


def normalize_name(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)

    text = re.sub(
        r"\b(the|please|application|app)\b",
        "",
        text
    )

    return " ".join(text.split())


def find_shortcuts():

    locations = [
        Path(os.environ["USERPROFILE"]) / "Desktop",
        Path(os.environ["APPDATA"]) /
        "Microsoft/Windows/Start Menu/Programs",
        Path(os.environ["PROGRAMDATA"]) /
        "Microsoft/Windows/Start Menu/Programs",
    ]

    shortcuts = {}

    for location in locations:

        if not location.exists():
            continue

        for shortcut in location.rglob("*.lnk"):

            name = normalize_name(shortcut.stem)

            if name:
                shortcuts[name] = shortcut

    return shortcuts


def find_application(app_name):

    shortcuts = find_shortcuts()
    app_name = normalize_name(app_name)

    if not app_name:
        return {
            "status": "not_found"
        }

    # 1. Exact match
    if app_name in shortcuts:
        return {
            "status": "found",
            "name": app_name,
            "path": shortcuts[app_name]
        }

    # 2. Strong partial match
    partial_matches = []

    for name, shortcut in shortcuts.items():

        if app_name in name or name in app_name:
            partial_matches.append((name, shortcut))

    if len(partial_matches) == 1:

        name, shortcut = partial_matches[0]

        return {
            "status": "found",
            "name": name,
            "path": shortcut
        }

    # 3. Fuzzy matching
    match = process.extractOne(
        app_name,
        shortcuts.keys(),
        scorer=fuzz.WRatio
    )

    if match:

        matched_name, score, _ = match

        print(
            f"Fuzzy match: '{app_name}' "
            f"-> '{matched_name}' "
            f"({score:.0f}%)"
        )

        # Very strong match
        if score >= 90:

            return {
                "status": "found",
                "name": matched_name,
                "path": shortcuts[matched_name]
            }

        # Possible match — ask user
        if score >= 70:

            return {
                "status": "uncertain",
                "name": matched_name,
                "score": score,
                "path": shortcuts[matched_name]
            }

    return {
        "status": "not_found"
    }


def open_application(app_name):

    result = find_application(app_name)

    if result["status"] == "not_found":

        return {
            "status": "not_found",
            "message": f"I couldn't find {app_name}."
        }

    if result["status"] == "uncertain":

        return {
            "status": "uncertain",
            "message": (
                f"I found {result['name']}. "
                f"Did you mean {result['name']}?"
            ),
            "name": result["name"]
        }

    try:

        subprocess.Popen(
            ["explorer.exe", str(result["path"])]
        )

        return {
            "status": "opened",
            "message": f"Opening {result['name']}."
        }

    except Exception as e:

        return {
            "status": "error",
            "message": f"I couldn't open {result['name']}: {e}"
        }


if __name__ == "__main__":

    print()
    print("==============================")
    print("      US AI APP MANAGER")
    print("==============================")
    print()

    tests = [
        "chrome.",
        "google chrome.",
        "hPanel",
        "H Penel",
        "Edge Panel",
        "each panel"
    ]

    for test in tests:

        result = find_application(test)

        print()
        print(f"Input: {test}")
        print(f"Result: {result}")