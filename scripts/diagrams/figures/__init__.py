"""One module per figure. Each has NAME, TITLE, ALT and draw(theme) -> Canvas."""

from . import (answer_loss, assistants_timeline, chatgpt_context, claude_code_memory, codex_memory, observer_reflector, products_map, benchmark_types, conversation, decision_guide, eval_pipeline, feeding, lme_history, trimming_check, graphiti, graphiti_cost, graphiti_dates, graphiti_floor, graphiti_graph, graphiti_matching, graphiti_steps, graphiti_walk, honcho, honcho_conflict, honcho_cost, honcho_deriver, honcho_dream, honcho_levels, honcho_read, honcho_retire, honcho_window, letta, letta_block_diff, letta_chain, letta_context, letta_cost, letta_search, letta_sleeptime, letta_turn, map, mem0, mem0_prompt, mem0_ranking, mem0_update, overview,
               profile_diff, series, textual)

FIGURES = {module.NAME: module for module in (series, overview, map, conversation, textual, profile_diff,
                                              mem0, mem0_update, mem0_prompt, mem0_ranking, graphiti, graphiti_steps, graphiti_graph, graphiti_matching, graphiti_floor, graphiti_walk, graphiti_dates, graphiti_cost, letta, letta_context, letta_turn, letta_search, letta_sleeptime, letta_block_diff, letta_cost, letta_chain,
                                              honcho, honcho_levels, honcho_deriver, honcho_dream, honcho_retire, honcho_read, honcho_window, honcho_conflict, honcho_cost,
                                              benchmark_types, lme_history, eval_pipeline, trimming_check,
                                              answer_loss, feeding, decision_guide,
                                              assistants_timeline, products_map, chatgpt_context, codex_memory,
                                              claude_code_memory, observer_reflector)}
