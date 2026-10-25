"""Colours and type for the architecture diagrams, in a light and a dark theme.

The neutrals are the blog's own (`assets/css/main.css` there), so a figure sits on that page
as if drawn for it. Each role has three colours: `accent` for strokes, icons and labels,
`wash` for the fill of a box in that role, and `ink` for text on that wash.

Roles mean the same thing in every figure:

- person: the user and what they say
- llm: a step where a model is called, so it costs a model call
- code: a step that is plain code, no model
- store: the memory itself
- prompt: what the answering model is given
- stale: a fact that has been replaced, closed or withdrawn
- both: both the old and the new value of a fact reached the prompt
"""

from __future__ import annotations

from dataclasses import dataclass

ROLES = ("person", "llm", "code", "store", "prompt", "stale", "both")


@dataclass(frozen=True)
class Role:
    accent: str
    wash: str
    ink: str


@dataclass(frozen=True)
class Theme:
    name: str
    paper: str      # the figure's background
    card: str       # the fill of an ordinary box
    surface: str    # a band or panel behind boxes
    ink: str
    muted: str
    faint: str
    line: str
    roles: dict[str, Role]

    def __getitem__(self, role: str) -> Role:
        return self.roles[role]


LIGHT = Theme(
    name="light",
    paper="#FBFAF6", card="#FFFFFF", surface="#F2F0E8",
    ink="#22241F", muted="#62645B", faint="#8A8C82", line="#DEDCD2",
    roles={
        "person": Role("#8E6027", "#F2E9DA", "#5E3F16"),
        "llm":    Role("#6B4E8C", "#ECE6F2", "#4A3366"),
        "code":   Role("#4A5866", "#E6EAEE", "#323E4A"),
        "store":  Role("#395A44", "#E1E9DF", "#2E4A38"),
        "prompt": Role("#2F5D7C", "#E0EAF0", "#21455E"),
        "stale":  Role("#9C4B33", "#F4E4DE", "#7A3825"),
        "both":   Role("#8A5D0C", "#F5EAD2", "#6E4B0B"),
    },
)

DARK = Theme(
    name="dark",
    paper="#161814", card="#1D201B", surface="#1A1C18",
    ink="#E7E5DB", muted="#A3A69B", faint="#808378", line="#32362D",
    roles={
        "person": Role("#D2A469", "#2E2718", "#E8C99C"),
        "llm":    Role("#B9A0DA", "#29223A", "#D6C6EC"),
        "code":   Role("#A7B6C6", "#222A31", "#C9D4DF"),
        "store":  Role("#93BD9E", "#22301F", "#B4D6BC"),
        "prompt": Role("#8DB8D8", "#1C2A35", "#B7D3E8"),
        "stale":  Role("#E29278", "#331F19", "#F0B5A2"),
        "both":   Role("#DDB25E", "#33280F", "#EDCD8C"),
    },
)

THEMES = {"light": LIGHT, "dark": DARK}

# Type scale, in px at the figure's natural width of 880. In a 700 px column the smallest
# size comes out at about 10 px, so a blog page should let the figures run wider than its text.
TITLE, SUBTITLE, HEAD, BODY, SMALL, TINY = 23, 15, 15, 14, 13.5, 12.5


def _luminance(hex_colour: str) -> float:
    r, g, b = (int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5))
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def check(theme: Theme) -> list[str]:
    """Every pairing of text and background that the figures use, below WCAG AA (4.5:1)."""
    pairs = [("ink on paper", theme.ink, theme.paper), ("ink on card", theme.ink, theme.card),
             ("muted on paper", theme.muted, theme.paper), ("muted on card", theme.muted, theme.card)]
    for name, role in theme.roles.items():
        pairs += [(f"{name} ink on wash", role.ink, role.wash),
                  (f"{name} accent on paper", role.accent, theme.paper),
                  (f"{name} accent on card", role.accent, theme.card),
                  (f"{name} accent on wash", role.accent, role.wash)]
    return [f"{theme.name}: {what} is {contrast(fg, bg):.2f}:1"
            for what, fg, bg in pairs if contrast(fg, bg) < 4.5]
