"""Honcho's own prompts and tool schemas, read from its repository.

The Honcho notebook drives these with small local functions. This module only
fetches the text, at the commit of the release the experiment ran (v3.3.0), and
fills its slots, so that what the model is told is Honcho's wording and not a
paraphrase. Honcho is AGPL-3.0: https://github.com/plastic-labs/honcho
"""

import ast
import inspect
import urllib.request

HONCHO_COMMIT = "608aec8a928da13c540262ed980c569448fb53ab"   # v3.3.0
RAW = f"https://raw.githubusercontent.com/plastic-labs/honcho/{HONCHO_COMMIT}/"

_sources = {}


def fetch(path: str) -> str:
    if path not in _sources:
        with urllib.request.urlopen(RAW + path, timeout=30) as response:
            _sources[path] = response.read().decode()
    return _sources[path]


def _tree(path):
    return ast.parse(fetch(path))


def _function(path, name, cls=None):
    body = _tree(path).body
    if cls:
        body = next(n for n in body if isinstance(n, ast.ClassDef) and n.name == cls).body
    return next(n for n in body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)


def _constant(path, name, cls=None):
    """A module-level (or class-level) string constant."""
    body = _tree(path).body
    if cls:
        body = next(n for n in body if isinstance(n, ast.ClassDef) and n.name == cls).body
    for node in body:
        targets = node.targets if isinstance(node, ast.Assign) else [getattr(node, "target", None)]
        if any(getattr(t, "id", None) == name for t in targets):
            return ast.literal_eval(node.value)
    raise KeyError(name)


def _fill(node, values):
    """Render a string or f-string node, filling each {expression} from `values`.

    The keys of `values` are the expressions as written in Honcho's source, for
    example "peer_id" or "self.peer_card_update_instruction".
    """
    if isinstance(node, ast.Constant):
        return node.value
    out = []
    for part in node.values:
        if isinstance(part, ast.Constant):
            out.append(part.value)
        else:
            out.append(str(values[ast.unparse(part.value)]))
    return "".join(out)


def _returns(function):
    nodes = [n for n in ast.walk(function) if isinstance(n, ast.Return) and n.value is not None]
    return [n.value for n in sorted(nodes, key=lambda n: n.lineno)]


def _assigned(function, name):
    """The values assigned to a local name, in source order."""
    nodes = [n for n in ast.walk(function)
             if isinstance(n, ast.Assign) and any(getattr(t, "id", None) == name for t in n.targets)]
    return [n.value for n in sorted(nodes, key=lambda n: n.lineno)]


# The deriver: one prompt per batch of new messages ---------------------------

DERIVER = "src/deriver/prompts.py"


def deriver_message(idx, peer, target, created_at, content):
    """format_deriver_message: one message in its tag (the source escapes '<message' inside content)."""
    node = _returns(_function(DERIVER, "format_deriver_message"))[0]
    return _fill(node, {"idx": idx, "peer": peer, "is_target": "true" if peer == target else "false",
                        "time_str": created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        "safe_content": content})


def deriver_prompt(peer_id, messages):
    """minimal_deriver_prompt, with no custom instructions."""
    call = _returns(_function(DERIVER, "minimal_deriver_prompt"))[0]     # c(f"""...""")
    text = _fill(call.args[0], {"instructions_section": "", "peer_id": peer_id, "messages": messages})
    return inspect.cleandoc(text)


# The dream: two agents with tools ---------------------------------------------

SPECIALISTS = "src/dreamer/specialists.py"


def peer_card_section():
    return _constant(SPECIALISTS, "PEER_CARD_SYSTEM_SECTION")


def deduction_system_prompt():
    node = _returns(_function(SPECIALISTS, "build_system_prompt", "DeductionSpecialist"))[0]
    return _fill(node, {"peer_card_section": peer_card_section()})


def induction_system_prompt():
    return _fill(_returns(_function(SPECIALISTS, "build_system_prompt", "InductionSpecialist"))[0], {})


def _target_observee(observed):
    node = _returns(_function(SPECIALISTS, "_build_target_observee_context", "BaseSpecialist"))[0]
    return _fill(node, {"observed": observed})


def _peer_card_context(peer_card, cls):
    if not peer_card:
        return ""
    node = _returns(_function(SPECIALISTS, "_build_peer_card_context", "BaseSpecialist"))[-1]
    instruction = _constant(SPECIALISTS, "peer_card_update_instruction", cls)
    return _fill(node, {"facts": "\n".join(f"- {fact}" for fact in peer_card),
                        "self.peer_card_update_instruction": instruction})


def deduction_user_prompt(observed, peer_card):
    """The prompt without exploration hints (surprisal sampling is off by default)."""
    node = _returns(_function(SPECIALISTS, "build_user_prompt", "DeductionSpecialist"))[-1]
    return _fill(node, {"target_observee_context": _target_observee(observed),
                        "peer_card_context": _peer_card_context(peer_card, "DeductionSpecialist")})


def induction_user_prompt(observed):
    node = _returns(_function(SPECIALISTS, "build_user_prompt", "InductionSpecialist"))[-1]
    return _fill(node, {"target_observee_context": _target_observee(observed)})


def max_iterations(cls):
    node = _returns(_function(SPECIALISTS, "get_max_iterations", cls))[0]
    return ast.literal_eval(node)


# Tools: the schemas the agents are given ---------------------------------------

TOOLS_FILE = "src/utils/agent_tools.py"


def _tools():
    """The TOOLS dict, with its two schema-building calls replaced by the dicts they return."""
    schemas = {name: _returns(_function(TOOLS_FILE, name))[0]
               for name in ("_deductive_observation_item_schema", "_inductive_observation_item_schema")}

    class Inline(ast.NodeTransformer):
        def visit_Call(self, node):
            return schemas[node.func.id]

    for node in _tree(TOOLS_FILE).body:
        if isinstance(node, ast.AnnAssign) and node.target.id == "TOOLS":
            return ast.literal_eval(Inline().visit(node.value))
    raise KeyError("TOOLS")


def tool_set(name):
    """A named tool list, e.g. DEDUCTION_SPECIALIST_TOOLS: Honcho's schemas, in order."""
    tools = _tools()
    for node in _tree(TOOLS_FILE).body:
        if isinstance(node, ast.AnnAssign) and node.target.id == name:
            return [tools[element.slice.value] for element in node.value.elts]
    raise KeyError(name)


def declarations(tools):
    """Honcho's schemas as Gemini function declarations (the same JSON schema, renamed key)."""
    return [{"function_declarations": [
        {"name": t["name"], "description": t["description"],
         "parameters_json_schema": t["input_schema"]} for t in tools]}]


# The dialectic: Honcho's agent for questions about a peer ---------------------

DIALECTIC = "src/dialectic/prompts.py"
CORE = "src/dialectic/core.py"


def dialectic_system_prompt(observed, peer_card, available_tools):
    """agent_system_prompt for a peer's own representation (observer == observed)."""
    function = _function(DIALECTIC, "agent_system_prompt")
    card = _fill(_assigned(function, "peer_card_section")[-1],
                 {"observed": observed, "chr(10).join(observer_peer_card)": "\n".join(peer_card)}) \
        if peer_card else ""
    perspective = _fill(_assigned(function, "perspective_section")[-1],
                        {"observed": observed, "peer_card_section": card})
    explanation = _fill(_assigned(function, "peer_card_explanation")[-1], {}) if peer_card is not None else ""
    groups = ast.literal_eval(next(n.value for n in _tree(DIALECTIC).body
                                   if isinstance(n, ast.AnnAssign) and n.target.id == "_PAIR_TOOL_GROUPS"))
    parts = []                                   # _render_tool_groups
    for heading, items in groups:
        lines = [f"- `{name}`: {desc}" for name, desc in items if name in available_tools]
        if lines:
            parts.append(f"**{heading}**\n" + "\n".join(lines))
    return _fill(_returns(function)[-1], {"perspective_section": perspective,
                                          "peer_card_explanation": explanation,
                                          "tools_section": "\n\n".join(parts),
                                          "_custom_instructions_suffix(custom_instructions)": ""})


def dialectic_user_message(query, prefetched):
    """The first user message: the query, then the observations found for it in advance."""
    function = _function(CORE, "_prepare_messages", "DialecticAgent")
    node = _assigned(function, "user_content")[0]
    heading = ast.literal_eval(_returns(_function(CORE, "_prefetch_heading", "DialecticAgent"))[0])
    intro = ast.literal_eval(_returns(_function(CORE, "_prefetch_intro", "DialecticAgent"))[0])
    return _fill(node, {"query": query, "self._prefetch_heading()": heading,
                        "self._prefetch_intro()": intro, "prefetched_observations": prefetched})
