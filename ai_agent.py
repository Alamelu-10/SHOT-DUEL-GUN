"""
ai_agent.py
------------
Defines AIAgent: the "Strategy Analyzer".

AIAgent never plays a move on behalf of either human player. Its sole
job is: given the current GameState and a chosen player number, print
(or otherwise log) a full, human-readable explanation of the Minimax +
Alpha-Beta analysis, and return the recommended action + score so the
UI (console or Tkinter) can display it.
"""

from game import Game, GameState
from minimax import Minimax


class AIAgent:
    """The AI Strategy Analyzer -- observes, never plays."""

    def __init__(self, max_depth: int = 3, log=None):
        self.max_depth = max_depth
        self._log_fn = log if log is not None else print
        self.minimax = Minimax(max_depth=max_depth, log=self._log_fn)

    def analyze(self, state: GameState, analyzed_num: int):
        """
        Runs the full visible analysis for `analyzed_num` (1 or 2) and
        returns (best_action, best_score).
        """
        opponent_num = 2 if analyzed_num == 1 else 1

        self._log_fn("=" * 40)
        self._log_fn("       AI STRATEGY ANALYZER")
        self._log_fn("=" * 40)
        self._log_fn("")
        self._log_fn("Current State:")
        self._log_fn(f"P{analyzed_num} Lives: {state.player(analyzed_num).lives}")
        self._log_fn(f"P{analyzed_num} Bullets: {state.player(analyzed_num).bullets}")
        self._log_fn("")
        self._log_fn(f"P{opponent_num} Lives: {state.opponent(analyzed_num).lives}")
        self._log_fn(f"P{opponent_num} Bullets: {state.opponent(analyzed_num).bullets}")
        self._log_fn("")
        self._log_fn(f"Search Depth: {self.max_depth}")
        self._log_fn("")
        self._log_fn("Possible Actions:")
        for action in Game.valid_actions(state, analyzed_num):
            self._log_fn(f"- {action}")
        self._log_fn("")

        best_action, best_score = self.minimax.analyze(state, analyzed_num)

        self._log_fn("")
        self._log_fn("Recommended Strategy:")
        self._log_fn(str(best_action).upper())
        self._log_fn("")
        self._log_fn("Evaluation Score:")
        self._log_fn(f"{best_score:+.0f}")

        return best_action, best_score
