$ErrorActionPreference = "Stop"

$projectRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Project virtual environment not found. Create it and install requirements.txt before running checks."
}

$checkScript = @'
import ast
from pathlib import Path
from unittest.mock import Mock, patch

root = Path.cwd()
source_files = [
    path for path in root.rglob("*.py")
    if ".venv" not in path.parts and "__pycache__" not in path.parts
]
for path in source_files:
    ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
print(f"Syntax passed: {len(source_files)} Python files.")

from brain.brain import format_spoken_answer
from brain.command_parser import parse_command
from core import web_search

assert parse_command("Talk less") == {"intent": "memory", "action": "set_response_style", "style": "brief"}
assert parse_command("Quiet mode") == {"intent": "memory", "action": "set_response_style", "style": "quiet"}
assert parse_command("Give me more detail") == {"intent": "memory", "action": "set_response_style", "style": "detailed"}
assert format_spoken_answer("One. Two. Three. Four.", max_sentences=2) == "One. Two."

assert parse_command("What is Windows Security?") == {
    "intent": "ask_ai",
    "query": "What is Windows Security?",
}
assert parse_command("Open example.com") == {
    "intent": "open_website",
    "url": "https://example.com",
}
assert parse_command("Open https://example.com/path") == {
    "intent": "open_website",
    "url": "https://example.com/path",
}
with patch(
    "brain.command_parser.extract_intent",
    return_value={"intent": "open_resource", "query": "YouTube"},
) as extract:
    assert parse_command("Open YouTube") == {
        "intent": "open_resource",
        "query": "YouTube",
    }
    extract.assert_called_once()
assert parse_command("Open bluetooth settings") == {
    "intent": "open_system_settings",
    "uri": "ms-settings:bluetooth",
}
with patch(
    "brain.command_parser.extract_intent",
    return_value={"intent": "open_website", "url": "https://example.com/"},
) as extract:
    result = parse_command("Open cool project")
    assert result == {
        "intent": "open_website",
        "url": "https://example.com/",
    }
    extract.assert_called_once()

website_results = [
    {
        "title": "Example Video Site",
        "url": "https://videos.example/",
        "text": "Official website.",
    }
]
with patch.object(web_search, "_fetch_search_results", return_value=website_results) as fetch, \
     patch.object(web_search.webbrowser, "open", return_value=True) as browser:
    result = web_search.open_website_by_name("Example Video Site")
    assert result == {"status": "opened", "title": "Example Video Site"}
    fetch.assert_called_once_with("Example Video Site official website", max_results=5)
    browser.assert_called_once_with("https://videos.example/", new=2)

from core import controller

with patch.object(
    controller,
    "resolve_resource",
    return_value={"status": "not_found"},
), patch.object(
    controller,
    "open_website_by_name",
    return_value={"status": "opened", "title": "Example Video Site"},
) as website_lookup:
    assert controller.execute({
        "intent": "open_resource",
        "query": "Example Video Site",
    }) == "Opening Example Video Site in your default browser."
    website_lookup.assert_called_once_with("Example Video Site")

search_phrases = {
    "search for latest AI news": "latest AI news",
    "search the web for YouTube": "YouTube",
    "look up weather online": "weather",
    "find information about Python on the web": "information about Python",
}
for phrase, expected_query in search_phrases.items():
    assert web_search.should_search_web_first(phrase), phrase
    assert web_search._search_query(phrase) == expected_query, phrase

results = [
    {
        "title": "Python",
        "url": "https://www.python.org/",
        "text": "Python information.",
    }
]
summary_model = Mock(return_value="Here is what I found.")
with patch.object(web_search.webbrowser, "open", return_value=True) as browser, \
     patch.object(web_search, "_fetch_search_results", return_value=results):
    history = [{"role": "assistant", "content": "We were discussing Python."}]
    search_result = web_search.search_web(
        "search for latest Python release",
        summarizer=summary_model,
        history=history,
    )
    assert search_result["status"] == "ok"
    assert search_result["query"] == "latest Python release"
    browser.assert_called_once_with(
        "https://duckduckgo.com/?q=latest+Python+release",
        new=2,
    )
    assert "We were discussing Python." in summary_model.call_args.args[0]

print("Routing and browser-backed conversational search smoke checks passed.")
'@

Push-Location $projectRoot
try {
    $checkScript | & $python -
    if ($LASTEXITCODE -ne 0) {
        throw "US AI checks failed with code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
