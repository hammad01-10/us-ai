import re
from rapidfuzz import process, fuzz

from .resource_index import build_resource_index


def normalize(text):

    text = text.lower()

    text = re.sub(
        r"[^\w\s]",
        " ",
        text
    )

    return " ".join(text.split())


def find_candidates(user_text, limit=8):

    index = build_resource_index()

    resources = index["resources"]

    query = normalize(user_text)

    names = {}

    for resource in resources:

        name = normalize(
            resource["name"]
        )

        if name:
            names[name] = resource

    matches = process.extract(
        query,
        names.keys(),
        scorer=fuzz.WRatio,
        limit=limit
    )

    candidates = []

    for name, score, _ in matches:

        resource = names[name]

        candidates.append({
            "id": resource["id"],
            "name": resource["name"],
            "type": resource["type"],
            "score": round(score, 1)
        })

    return candidates


if __name__ == "__main__":

    tests = [
        "system information",
        "control panel",
        "task manager",
        "google chrome",
        "hpanel",
        "something that does not exist"
    ]

    print()
    print("==============================")
    print("      US AI RESOURCE MATCHER")
    print("==============================")

    for test in tests:

        print()
        print("Query:", test)

        candidates = find_candidates(test)

        for candidate in candidates:

            print(
                f"- {candidate['name']} "
                f"| {candidate['type']} "
                f"| {candidate['score']}%"
            )
