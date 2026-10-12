"""
player.py
----------
Defines the Player class: a simple, cloneable data holder for one
human participant in Shotgun Duel.

This class holds NO rules and NO decision logic. It only tracks state
(lives, bullets). All rules for how those numbers change live in
game.py, and all decision-making lives in minimax.py / ai_agent.py.
"""


class Player:
    """One duelist: tracks lives and bullets only."""

    STARTING_LIVES = 3
    STARTING_BULLETS = 0

    def __init__(self, name: str):
        self.name = name
        self.lives = Player.STARTING_LIVES
        self.bullets = Player.STARTING_BULLETS

    def is_alive(self) -> bool:
        return self.lives > 0

    def clone(self) -> "Player":
        """Deep-enough copy so the AI can simulate futures safely."""
        new_player = Player(self.name)
        new_player.lives = self.lives
        new_player.bullets = self.bullets
        return new_player

    def lives_display(self) -> str:
        return "❤️" * self.lives if self.lives > 0 else "💀"

    def bullets_display(self) -> str:
        return f"🔫 x{self.bullets}"

    def __repr__(self):
        return f"{self.name}(lives={self.lives}, bullets={self.bullets})"
