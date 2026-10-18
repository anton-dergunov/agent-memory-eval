"""Arms by name. Imported lazily, so an arm's dependencies are only needed when it runs."""

import importlib

ARMS = {
    "full-context": ("full_context", "FullContext"),
    "retrieval": ("retrieval", "Retrieval"),
    "textual": ("textual", "TextualMemory"),
    "mem0": ("mem0", "Mem0Arm"),
    "honcho": ("honcho", "HonchoArm"),
    "graphiti": ("graphiti", "GraphitiArm"),
    "letta": ("letta", "LettaArm"),
}


def build(name: str):
    module, cls = ARMS[name]
    return getattr(importlib.import_module(f"{__name__}.{module}"), cls)()
