"""
game.py
--------
Defines:
    - Action     : the three possible simultaneous choices.
    - GameState  : a full, cloneable snapshot of both players.
    - Game       : the ONLY place the rules of Shotgun Duel live.

Both the real, human-vs-human game loop (main.py) and the AI Strategy
Analyzer's simulated search (minimax.py) call the exact same
`Game.resolve_round`, so the AI is always reasoning about the true
rules of the game and can never "cheat".
"""

from enum import Enum
from player import Player


class Action(Enum):
    """The three simultaneous actions a player may choose each round."""
    RELOAD = "Reload"
    BLOCK = "Block"
    FIRE = "Fire"

    def __str__(self):
        return self.value

    @property
    def emoji(self):
        return {"Reload": "🔄", "Block": "🛡️", "Fire": "💥"}[self.value]


class GameState:
    """A complete, cloneable snapshot of both duelists at one round."""

    def __init__(self, p1: Player, p2: Player, round_number: int = 1):
        self.p1 = p1
        self.p2 = p2
        self.round_number = round_number

    def clone(self) -> "GameState":
        return GameState(self.p1.clone(), self.p2.clone(), self.round_number)

    def is_terminal(self) -> bool:
        """The duel ends the instant either player runs out of lives."""
        return self.p1.lives <= 0 or self.p2.lives <= 0

    def winner(self):
        """Returns 'P1', 'P2', 'DRAW', or None (duel still ongoing)."""
        if self.p1.lives <= 0 and self.p2.lives <= 0:
            return "DRAW"
        if self.p1.lives <= 0:
            return "P2"
        if self.p2.lives <= 0:
            return "P1"
        return None

    def player(self, num: int) -> Player:
        return self.p1 if num == 1 else self.p2

    def opponent(self, num: int) -> Player:
        return self.p2 if num == 1 else self.p1

    def __repr__(self):
        return (f"[Round {self.round_number}] "
                f"P1(lives={self.p1.lives}, bullets={self.p1.bullets}) | "
                f"P2(lives={self.p2.lives}, bullets={self.p2.bullets})")


class Game:
    """Owns the rules for validating and resolving a round."""

    # ------------------------------------------------------------------
    # Move generation
    # ------------------------------------------------------------------
    @staticmethod
    def valid_actions(state: GameState, player_num: int) -> list:
        """
        Reload and Block are always legal. Fire is only legal if the
        player currently has at least 1 bullet. A dead player (which
        should never actually be asked to move, since the duel ends
        immediately) has no valid actions.
        """
        player = state.player(player_num)
        if not player.is_alive():
            return []
        actions = [Action.RELOAD, Action.BLOCK]
        if player.bullets > 0:
            actions.append(Action.FIRE)
        return actions

    # ------------------------------------------------------------------
    # Round resolution (used by BOTH the real game and the AI's search)
    # ------------------------------------------------------------------
    @staticmethod
    def resolve_round(state: GameState, p1_action: Action, p2_action: Action) -> GameState:
        """
        Resolves one full simultaneous round and returns a NEW GameState.
        The input state is never mutated -- essential for safe Minimax
        recursion.

        Rules:
          - Reload   : +1 bullet to the caster. Never causes damage.
          - Fire     : -1 bullet from the caster (always consumed, even
                       on a miss). If the OPPONENT was Reloading, the
                       opponent loses 1 life. If the opponent Blocked or
                       also Fired, nobody is damaged by this shot.
          - Block    : no bullet change. Damage is handled above by
                       checking "did the opponent's action equal BLOCK".

        Both players' bullet/life changes are computed from the ORIGINAL
        (pre-round) actions, exactly as a true simultaneous round would
        behave -- one player's choice never affects the legality or
        cost of the other player's simultaneous choice.
        """
        new_state = state.clone()
        p1, p2 = new_state.p1, new_state.p2

        # --- Apply bullet cost / gain for each player independently ---
        if p1_action == Action.RELOAD:
            p1.bullets += 1
        elif p1_action == Action.FIRE:
            p1.bullets -= 1

        if p2_action == Action.RELOAD:
            p2.bullets += 1
        elif p2_action == Action.FIRE:
            p2.bullets -= 1

        # --- Apply damage based on the ORIGINAL simultaneous actions ---
        if p1_action == Action.FIRE and p2_action == Action.RELOAD:
            p2.lives -= 1
        if p2_action == Action.FIRE and p1_action == Action.RELOAD:
            p1.lives -= 1
        # Fire vs Block -> blocked, no damage.
        # Fire vs Fire   -> both shots "trade", no damage (kept simple).
        # Any combination of Reload/Block -> no damage.

        new_state.round_number += 1
        return new_state
