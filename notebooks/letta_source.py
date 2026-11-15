"""Letta's own prompts and tool descriptions, read from its repository.

The Letta notebook drives these with a local loop. This module only fetches the
text, at a pinned commit, so that what the model is told is Letta's wording and
not a paraphrase. Letta is Apache-2.0: https://github.com/letta-ai/letta
"""

import ast
import re
import urllib.request

# The last commit on the `archive` branch, which holds the Python server.
LETTA_COMMIT = "56ba9c25552605eec89de8ed3dc6394b625c1993"
RAW = f"https://raw.githubusercontent.com/letta-ai/letta/{LETTA_COMMIT}/letta/"


def fetch(path: str) -> str:
    with urllib.request.urlopen(RAW + path, timeout=30) as response:
        return response.read().decode()


def system_prompt(name: str) -> str:
    """The PROMPT string from one of Letta's `prompts/system_prompts/<name>.py` files."""
    tree = ast.parse(fetch(f"prompts/system_prompts/{name}.py"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and node.targets[0].id == "PROMPT":
            return ast.literal_eval(node.value).strip()
    raise KeyError(name)


def persona(name: str) -> str:
    return fetch(f"personas/examples/{name}.txt").strip()


_JSON_TYPE = {"str": "string", "int": "integer", "bool": "boolean"}
_functions = None


def _examples_section(docstring):
    """letta.functions.schema_generator.extract_examples_section, unchanged in behaviour."""
    if not docstring or "Examples:" not in docstring:
        return None
    lines, inside, out = docstring.strip().splitlines(), False, []
    for line in lines:
        stripped = line.strip()
        if not inside and stripped.startswith("Examples:"):
            inside = True
            out.append(line)
            continue
        if inside:
            if stripped and not line.startswith(" ") and stripped.endswith(":"):
                break
            out.append(line)
    return "\n".join(out).strip()


def tool_declaration(name: str) -> dict:
    """Build a tool's description for the model from its Python docstring, as Letta does."""
    global _functions
    if _functions is None:
        source = ast.parse(fetch("functions/function_sets/base.py"))
        _functions = {node.name: node for node in source.body
                      if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    function = _functions[name]
    description, _, rest = ast.get_docstring(function).partition("Args:")
    raw = ast.get_docstring(function, clean=False)
    arguments_text = re.split(r"\n\s*(Returns|Examples):", rest)[0]

    arguments = [a for a in function.args.args if a.arg not in ("self", "agent_state")]
    required = len(arguments) - len(function.args.defaults)
    properties, current = {}, None
    for line in arguments_text.splitlines():
        match = re.match(r"\s+(\w+)(?: \([^)]*\))?: (.*)", line)
        if match and match.group(1) in {a.arg for a in arguments}:
            current = match.group(1)
            properties[current] = {"description": match.group(2)}
        elif current and line.strip():
            properties[current]["description"] += " " + line.strip()

    for argument in arguments:
        annotation = ast.unparse(argument.annotation) if argument.annotation else "str"
        spec = properties.setdefault(argument.arg, {"description": ""})
        if "list" in annotation.lower():
            spec.update(type="array", items={"type": "string"})
        else:
            spec["type"] = _JSON_TYPE.get(re.sub(r"Optional\[(.*)\]", r"\1", annotation), "string")

    # Letta's generate_schema: the summary line, then the rest of the description, then the
    # docstring's Examples section, copied as it stands (letta/functions/schema_generator.py).
    summary, _, more = description.strip().partition("\n")
    description = summary.strip() + ("\n\n" + more.strip() if more.strip() else "")
    examples = _examples_section(raw)
    if examples:
        description += "\n\n" + examples
    return {
        "name": name,
        "description": description,
        "parameters_json_schema": {
            "type": "object",
            "properties": properties,
            "required": [a.arg for a in arguments[:required]],
        },
    }
