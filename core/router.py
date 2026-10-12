import re


def clean_text(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    return " ".join(text.split())


def route_request(text):

    original = text.strip()
    clean = clean_text(original)

    # Open application
    if clean.startswith("open "):

        return {
            "intent": "open_app",
            "target": clean[5:].strip()
        }

    # Web search
    if (
        clean.startswith("search ")
        or clean.startswith("search for ")
        or clean.startswith("look up ")
    ):

        query = clean

        if query.startswith("search for "):
            query = query[11:]

        elif query.startswith("search "):
            query = query[7:]

        elif query.startswith("look up "):
            query = query[8:]

        return {
            "intent": "web_search",
            "query": query
        }

    # Everything else → AI
    return {
        "intent": "ask_ai",
        "query": original
    }


if __name__ == "__main__":

    tests = [
        "open Chrome.",
        "open hPanel.",
        "search for latest NVIDIA drivers.",
        "what is the history of Pakistan?"
    ]

    for test in tests:
        print()
        print("User:", test)
        print("Route:", route_request(test))