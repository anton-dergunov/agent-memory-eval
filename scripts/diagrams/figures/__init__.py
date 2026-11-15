"""One module per figure. Each has NAME, TITLE, ALT and draw(theme) -> Canvas."""

from . import (conversation, graphiti, honcho, letta, map, mem0, mem0_prompt, mem0_ranking, mem0_update, overview,
               profile_diff, series, textual)

FIGURES = {module.NAME: module for module in (series, overview, map, conversation, textual, profile_diff,
                                              mem0, mem0_update, mem0_prompt, mem0_ranking, graphiti, letta,
                                              honcho)}
