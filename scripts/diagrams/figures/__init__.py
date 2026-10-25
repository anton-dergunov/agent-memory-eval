"""One module per figure. Each has NAME, TITLE, ALT and draw(theme) -> Canvas."""

from . import mem0

FIGURES = {module.NAME: module for module in (mem0,)}
