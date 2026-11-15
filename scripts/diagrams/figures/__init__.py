"""One module per figure. Each has NAME, TITLE, ALT and draw(theme) -> Canvas."""

from . import (conversation, graphiti, graphiti_cost, graphiti_dates, graphiti_floor, graphiti_graph, graphiti_matching, graphiti_steps, graphiti_walk, honcho, letta, letta_block_diff, letta_chain, letta_context, letta_cost, letta_search, letta_sleeptime, letta_turn, map, mem0, mem0_prompt, mem0_ranking, mem0_update, overview,
               profile_diff, series, textual)

FIGURES = {module.NAME: module for module in (series, overview, map, conversation, textual, profile_diff,
                                              mem0, mem0_update, mem0_prompt, mem0_ranking, graphiti, graphiti_steps, graphiti_graph, graphiti_matching, graphiti_floor, graphiti_walk, graphiti_dates, graphiti_cost, letta, letta_context, letta_turn, letta_search, letta_sleeptime, letta_block_diff, letta_cost, letta_chain,
                                              honcho)}
