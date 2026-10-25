"""One module per figure. Each has NAME, TITLE, ALT and draw(theme) -> Canvas."""

from . import graphiti, honcho, letta, map, mem0, overview, series, textual

FIGURES = {module.NAME: module for module in (series, overview, map, textual, mem0, graphiti, letta, honcho)}
