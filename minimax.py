"""
minimax.py
-----------
Implements Minimax with Alpha-Beta Pruning for the Shotgun Duel
Strategy Analyzer.

IMPORTANT: the AI never plays the game. This module only ANALYZES a
given GameState for a chosen player ("the analyzed player") and reports
the strategically best action, assuming the opponent always responds
in the way that is worst for the analyzed player.

Search-depth convention
------------------------
Because both players choose simultaneously, one full "round" of real
play = one action from the analyzed player (MAX) followed by one
reaction from the opponent (MIN), which are then resolved together by
Game.resolve_round(). This module treats the configurable `depth`
parameter as **the number of such rounds to look ahead**, matching the
project's "Depth = 3" default: 3 full rounds of simulated play.

For each candidate action of the analyzed player, every possible
opponent response is explored (this reproduces exactly the
"Player 1 Action x Player 2 Action" matrix requested), then, if more
rounds remain, the resulting state becomes the root of another
MAX/MIN round, recursively.
"""

from game import Game, Action, GameState


class Minimax:
    """Runs a depth-limited (round-limited) Minimax search with Alpha-Beta Pruning."""

    def __init__(self, max_depth: int = 3, verbose: bool = True, log=None):
        """
        max_depth : number of future ROUNDS to search (default 3).
        verbose   : if True and no `log` callback is given, print to stdout.
        log       : optional callback log(message: str) -> None, used so
                    a GUI can capture the trace instead of the console.
        """
        self.max_depth = max_depth
        self.verbose = verbose
        self._log_fn = log if log is not None else (print if verbose else (lambda m: None))

        # Statistics, reset at the start of every analysis.
        self.nodes_generated = 0
        self.nodes_evaluated = 0
        self.nodes_pruned = 0

    # ------------------------------------------------------------------
    # Heuristic evaluation function
    # ------------------------------------------------------------------
    @staticmethod
    def evaluate(state: GameState, analyzed_num: int) -> float:
        """
        Scores a GameState from the analyzed player's point of view.

            Score = (Player Lives x 100) - (Opponent Lives x 100)
                     + (Player Bullets x 10) - (Opponent Bullets x 5)

        Plus large overriding bonuses/penalties for an outright win/loss,
        since ending the duel is always more important than any
        positional (ammo/life) advantage.
        """
        player = state.player(analyzed_num)
        opponent = state.opponent(analyzed_num)

        if opponent.lives <= 0 and player.lives <= 0:
            return 0  # simultaneous mutual elimination -> neutral
        if opponent.lives <= 0:
            return 10_000  # analyzed player wins outright
        if player.lives <= 0:
            return -10_000  # analyzed player loses outright

        score = (player.lives * 100) - (opponent.lives * 100)
        score += (player.bullets * 10) - (opponent.bullets * 5)
        return score

    # ------------------------------------------------------------------
    # Core recursive Minimax + Alpha-Beta search (round-based)
    # ------------------------------------------------------------------
    def _search(self, state: GameState, rounds_left: int, alpha: float, beta: float,
                analyzed_num: int, opponent_num: int, indent: int) -> float:
        """
        Explores one full round (analyzed player's action x opponent's
        reaction), then recurses into the next round if rounds_left > 1.
        Returns the Minimax value of `state` from the analyzed player's
        perspective.
        """
        if rounds_left == 0 or state.is_terminal():
            value = self.evaluate(state, analyzed_num)
            self.nodes_evaluated += 1
            self._log(indent, f"Evaluation = {value:.0f}")
            self._log(indent, "")
            return value

        analyzed_label = f"Player {analyzed_num}"
        opponent_label = f"Player {opponent_num}"

        analyzed_actions = Game.valid_actions(state, analyzed_num)
        best_value = float("-inf")

        for a_action in analyzed_actions:
            self.nodes_generated += 1
            self._log(indent, f"{analyzed_label} \u2192 {a_action}")

            opponent_actions = Game.valid_actions(state, opponent_num)
            worst_for_analyzed = float("inf")
            local_beta = beta

            for o_action in opponent_actions:
                self.nodes_generated += 1
                self._log(indent + 1, f"{opponent_label} \u2192 {o_action}")

                if analyzed_num == 1:
                    new_state = Game.resolve_round(state, a_action, o_action)
                else:
                    new_state = Game.resolve_round(state, o_action, a_action)

                if rounds_left == 1 or new_state.is_terminal():
                    value = self.evaluate(new_state, analyzed_num)
                    self.nodes_evaluated += 1
                    self._log(indent + 2, f"Evaluation = {value:.0f}")
                    self._log(indent + 1, "")
                else:
                    value = self._search(
                        new_state, rounds_left - 1, alpha, local_beta,
                        analyzed_num, opponent_num, indent + 2,
                    )

                if value < worst_for_analyzed:
                    worst_for_analyzed = value
                local_beta = min(local_beta, worst_for_analyzed)

                # Alpha-Beta cutoff on the MIN (opponent) side.
                if local_beta <= alpha:
                    remaining = opponent_actions[opponent_actions.index(o_action) + 1:]
                    if remaining:
                        self.nodes_pruned += len(remaining)
                        self._log(
                            indent + 1,
                            f"ALPHA-BETA CUTOFF (MIN): after {o_action} against "
                            f"{a_action}, beta {local_beta:+.0f} <= alpha {alpha:+.0f}; "
                            f"skipped {len(remaining)} opponent response(s).",
                        )
                        self._log(indent + 1, "")
                    break

            if worst_for_analyzed > best_value:
                best_value = worst_for_analyzed
            alpha = max(alpha, best_value)

            # Alpha-Beta cutoff on the MAX (analyzed player) side.
            if alpha >= beta:
                remaining = analyzed_actions[analyzed_actions.index(a_action) + 1:]
                if remaining:
                    self.nodes_pruned += len(remaining)
                    self._log(
                        indent,
                        f"ALPHA-BETA CUTOFF (MAX): after {a_action}, "
                        f"alpha {alpha:+.0f} >= beta {beta:+.0f}; "
                        f"skipped {len(remaining)} player action(s).",
                    )
                    self._log(indent, "")
                break

        return best_value

    # ------------------------------------------------------------------
    # Top-level entry point used by AIAgent
    # ------------------------------------------------------------------
    def analyze(self, state: GameState, analyzed_num: int):
        """
        Runs the full, visible Minimax + Alpha-Beta analysis for the
        chosen player (1 or 2) and returns (best_action, best_score).
        """
        self.nodes_generated = 0
        self.nodes_evaluated = 0
        self.nodes_pruned = 0

        opponent_num = 2 if analyzed_num == 1 else 1
        analyzed_label = f"Player {analyzed_num}"
        opponent_label = f"Player {opponent_num}"

        self._log(0, "MINIMAX SEARCH")
        self._log(0, "")

        alpha, beta = float("-inf"), float("inf")
        best_action = None
        best_score = float("-inf")

        analyzed_actions = Game.valid_actions(state, analyzed_num)

        for a_action in analyzed_actions:
            self.nodes_generated += 1
            self._log(0, f"{analyzed_label} \u2192 {a_action}")

            opponent_actions = Game.valid_actions(state, opponent_num)
            worst_for_analyzed = float("inf")
            local_beta = beta

            for o_action in opponent_actions:
                self.nodes_generated += 1
                self._log(1, f"{opponent_label} \u2192 {o_action}")

                if analyzed_num == 1:
                    new_state = Game.resolve_round(state, a_action, o_action)
                else:
                    new_state = Game.resolve_round(state, o_action, a_action)

                if self.max_depth <= 1 or new_state.is_terminal():
                    value = self.evaluate(new_state, analyzed_num)
                    self.nodes_evaluated += 1
                    self._log(2, f"Evaluation = {value:.0f}")
                    self._log(1, "")
                else:
                    value = self._search(
                        new_state, self.max_depth - 1, alpha, local_beta,
                        analyzed_num, opponent_num, 2,
                    )

                if value < worst_for_analyzed:
                    worst_for_analyzed = value
                local_beta = min(local_beta, worst_for_analyzed)

                if local_beta <= alpha:
                    remaining = opponent_actions[opponent_actions.index(o_action) + 1:]
                    if remaining:
                        self.nodes_pruned += len(remaining)
                        self._log(
                            1,
                            f"ALPHA-BETA CUTOFF (MIN): after {o_action} against "
                            f"{a_action}, beta {local_beta:+.0f} <= alpha {alpha:+.0f}; "
                            f"skipped {len(remaining)} opponent response(s).",
                        )
                        self._log(1, "")
                    break

            self._log(0, "")

            if worst_for_analyzed > best_score:
                best_score = worst_for_analyzed
                best_action = a_action
            alpha = max(alpha, best_score)

        self._log(0, "ALPHA-BETA PRUNING")
        self._log(0, "")
        self._log(0, f"Branches pruned: {self.nodes_pruned}")
        self._log(0, f"Nodes generated: {self.nodes_generated}")
        self._log(0, f"Nodes evaluated: {self.nodes_evaluated}")
        self._log(0, f"Search depth: {self.max_depth}")
        self._log(0, "")
        self._log(0, "OPTIMAL ACTION:")
        self._log(0, "")
        self._log(0, f"{best_action.emoji} {str(best_action).upper()}")
        self._log(0, "")
        self._log(0, f"Evaluation Score: {best_score:+.0f}")

        return best_action, best_score

    # ------------------------------------------------------------------
    def _log(self, indent: int, message: str):
        self._log_fn(("    " * indent) + message)
