from .resource_index import build_resource_index
from rapidfuzz import process, fuzz
import re


def normalize(text):

    text = text.lower()

    text = re.sub(
        r"[^\w\s]",
        " ",
        text
    )

    return " ".join(text.split())


def resolve_resource(query):

    index = build_resource_index()

    resources = index["resources"]

    normalized_query = normalize(query)

    if not normalized_query:
        return {
            "status": "not_found",
            "query": query
        }

    names = {}

    for resource in resources:

        name = normalize(
            resource.get("name", "")
        )

        if name:
            names[name] = resource

    # ------------------------------------------
    # Exact match
    # ------------------------------------------

    if normalized_query in names:

        resource = names[normalized_query]

        return {
            "status": "found",
            "resource": resource
        }

    # ------------------------------------------
    # Fuzzy matching
    # ------------------------------------------

    matches = process.extract(
        normalized_query,
        names.keys(),
        scorer=fuzz.WRatio,
        limit=5
    )

    candidates = []

    for name, score, _ in matches:

        resource = names[name]

        candidate = dict(resource)

        candidate["score"] = round(
            score,
            1
        )

        candidates.append(candidate)

    # ------------------------------------------
    # Strong unique match
    # ------------------------------------------

    strong_matches = [
        candidate
        for candidate in candidates
        if candidate["score"] >= 90
    ]

    if len(strong_matches) == 1:

        return {
            "status": "found",
            "resource": strong_matches[0]
        }

    # ------------------------------------------
    # Multiple possible matches
    # ------------------------------------------

    if len(strong_matches) > 1:

        return {
            "status": "ambiguous",
            "candidates": strong_matches
        }

    # ------------------------------------------
    # Nothing reliable found
    # ------------------------------------------

    return {
        "status": "not_found",
        "query": query
    }


if __name__ == "__main__":

    print()
    print("==============================")
    print("      US AI RESOURCE RESOLVER")
    print("==============================")

    tests = [
        "system information",
        "control panel",
        "task manager",
        "google chrome",
        "hPanel",
        "something that does not exist"
    ]

    for test in tests:

        print()
        print("Query:", test)

        result = resolve_resource(test)

        print("Result:", result)