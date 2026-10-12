from .pc_inspector import inspect_pc
import time


_RESOURCE_INDEX_CACHE = None
_RESOURCE_INDEX_CACHE_TIME = 0.0
_RESOURCE_INDEX_CACHE_TTL = 10.0


def build_resource_index():
    global _RESOURCE_INDEX_CACHE, _RESOURCE_INDEX_CACHE_TIME
    now = time.monotonic()
    if (
        _RESOURCE_INDEX_CACHE is not None
        and now - _RESOURCE_INDEX_CACHE_TIME < _RESOURCE_INDEX_CACHE_TTL
    ):
        return _RESOURCE_INDEX_CACHE

    pc = inspect_pc()

    resources = []

    # Installed programs
    for program in pc["installed_programs"]:
        resources.append({
            "id": f"program:{program.lower()}",
            "name": program,
            "type": "installed_program"
        })

    # Desktop shortcuts and application launchers
    for shortcut in pc["shortcuts"]:
        resources.append({
            "id": f"shortcut:{shortcut['path'].lower()}",
            "name": shortcut["name"],
            "type": shortcut.get("type", "shortcut"),
            "path": shortcut["path"]
        })

    # Windows system resources
    for tool in pc["windows_tools"]:
        resources.append({
            "id": f"windows:{tool['path'].lower()}",
            "name": tool["name"],
            "type": "windows_system_resource",
            "path": tool["path"]
        })

    _RESOURCE_INDEX_CACHE = {
        "system": pc["system"],
        "resources": resources
    }
    _RESOURCE_INDEX_CACHE_TIME = now
    return _RESOURCE_INDEX_CACHE


if __name__ == "__main__":

    print()
    print("==============================")
    print("       US AI RESOURCE INDEX")
    print("==============================")

    index = build_resource_index()

    print()
    print(f"Total resources: {len(index['resources'])}")

    print()
    print("Sample resources:")
    print("------------------------------")

    for resource in index["resources"][:30]:
        print(
            f"{resource['type']}: "
            f"{resource['name']}"
        )

    print()
    print("==============================")
    print("RESOURCE INDEX COMPLETE")
    print("==============================")
