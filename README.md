# Shotgun Duel: Two-Player Strategic Game with Minimax and Alpha-Beta Pruning

A **Human vs Human** duel where a separate **AI Strategy Analyzer**
observes the game and recommends the strategically best action using
**Minimax with Alpha-Beta Pruning**. The AI never plays a move for
either player — it only analyzes and advises.

## Project Structure

```
shotgun_duel/
├── main.py       # Tkinter GUI: the playable 2-player game + Analyzer panel
├── player.py     # Player class (lives, bullets)
├── game.py       # Action enum, GameState, Game (all rules live here)
├── ai_agent.py   # AIAgent: the "Strategy Analyzer" that reports results
├── minimax.py    # Minimax + Alpha-Beta search + heuristic evaluation
└── README.md
```

## Running the Project

```bash
cd shotgun_duel
python main.py
```

Requires only the Python standard library (`tkinter` ships with most
Python installations; on Debian/Ubuntu, if missing, install with
`sudo apt-get install python3-tk`).

---

## 1. Game Rules

- Two human players, each starting with **3 lives** and **0 bullets**.
- Each round, **both players secretly and simultaneously** choose one
  of three actions:
  - **🔄 Reload** — gain 1 bullet. Never causes damage.
  - **🛡️ Block** — absorbs an incoming shot this round. No damage to
    the blocking player, regardless of what the opponent did.
  - **💥 Fire** — requires at least 1 bullet; the bullet is *always*
    consumed, hit or miss. If the opponent was **Reloading**, they
    lose 1 life. If the opponent **Blocked** or also **Fired**,
    nobody is hurt by that shot.
- The duel ends the instant either player's lives reach 0. The other
  player wins (or it's a draw if both reach 0 in the same round).

## 2. The AI Strategy Analyzer

The AI is **not** a player. At any point, either human can click
"Analyze for Player 1" or "Analyze for Player 2" to ask: *given the
current state, what should this player logically do next, assuming
the opponent will always respond in the worst possible way for them?*

The analyzer:
1. Reads the current `GameState`.
2. Generates every legal action for the chosen player (Fire is
   excluded if that player has 0 bullets).
3. For each candidate action, generates every legal opponent response.
4. Simulates the resulting state for every action pair.
5. Recursively searches further rounds (configurable depth, default 3).
6. Assumes the opponent always picks the response that is *worst* for
   the analyzed player (the Minimax "minimizing" player).
7. Prunes branches with Alpha-Beta Pruning wherever a branch can no
   longer affect the final decision.
8. Scores every leaf state with a heuristic evaluation function.
9. Returns the action with the best guaranteed (worst-case) score.
10. Displays search statistics, the recommendation, and the actual
    alpha-beta cutoff decisions in the optional AI Thinking panel.

The desktop window sizes itself to the available screen area. On narrow
windows the player panels stack vertically; the analysis controls and
pruning log remain scrollable and usable at smaller resolutions.

Humans are always free to ignore the recommendation — it is advisory
only.

## 3. Minimax Explanation

Because actions are simultaneous, one **round** = the analyzed
player's action (the **maximizing** node) followed by the opponent's
reaction (the **minimizing** node). `Game.resolve_round()` is then
applied to produce the next `GameState`. This reproduces exactly the
"Player 1 Action × Player 2 Action" matrix requested in the spec.

`Minimax.max_depth` (default **3**) sets **how many such rounds** are
searched into the future. At depth 1, the analyzer evaluates only the
immediate round (a single 3×3, or smaller, action matrix — this
matches the simplest example in the spec exactly). At depth 3
(default), the analyzer looks three full rounds ahead, so the tree
alternates MAX → MIN → MAX → MIN → MAX → MIN before scoring the
resulting leaves — giving a much stronger, longer-horizon
recommendation at the cost of a larger (though still pruned) search
tree.

At every leaf (either because the depth budget is exhausted or
because a player has already died), `Minimax.evaluate()` scores the
state and the value is propagated back up: MAX nodes keep the
**highest** score seen among their children (the analyzed player's
best guaranteed outcome), MIN nodes keep the **lowest** (the
opponent's best guaranteed outcome against the analyzed player).

## 4. Alpha-Beta Pruning Explanation

`alpha` = the best score the analyzed (maximizing) player can already
guarantee somewhere in the tree explored so far.
`beta` = the best (lowest) score the opponent (minimizing player) can
already guarantee.

While iterating a node's children, the instant `beta <= alpha` is
true, we know a smarter choice was already found elsewhere in the
tree, so the remaining sibling actions **at that node are skipped
entirely** — their `GameState`s are never even generated. The console
trace and the optional UI pruning log report each cutoff, its alpha/beta
comparison, and how many sibling actions were skipped. `Branches
pruned`, `Nodes generated`, and `Nodes evaluated` are reported at the
end of every analysis so the benefit is directly observable.

## 5. Heuristic Evaluation Function

Implemented in `Minimax.evaluate()`, scored from the **analyzed
player's** point of view:

```
Score = (Player Lives × 100) − (Opponent Lives × 100)
        + (Player Bullets × 10) − (Opponent Bullets × 5)
```

| Term                          | Weight | Why |
|--------------------------------|-------:|-----|
| Player's own lives              | ×100   | Staying alive matters more than anything except winning/losing outright |
| Opponent's lives (subtracted)   | ×100   | Symmetric — the opponent's safety is exactly as important to deny |
| Player's own bullets            | ×10    | Ammo is a resource advantage — more options next round (Fire becomes available) |
| Opponent's bullets (subtracted) | ×5     | Opponent ammo is a threat, but weighted less than the player's own, since Block can neutralize it |
| Opponent eliminated              | **+10,000** | Outright win — always dominates any positional score |
| Player eliminated                | **−10,000** | Outright loss — always dominates any positional score |

The huge win/loss bonus/penalty guarantees the AI never trades a
game-ending outcome for a minor ammo/life advantage elsewhere in the
tree.

## 6. Game-State Representation

A `GameState` bundles two `Player` objects (`p1`, `p2`, each just
`lives` and `bullets`) plus a `round_number`. It is fully **cloneable**
(`GameState.clone()`), so every hypothetical branch explored by
Minimax gets its own independent copy — the AI's "thinking" never
touches the real, on-screen game state. `Game.resolve_round()` is the
single function (used by both the real game and the simulated search)
that turns one `GameState` plus a pair of chosen `Action`s into the
next `GameState`.

## 7. How Simultaneous Actions Are Handled

In the real GUI: each player's chosen `Action` is stored in
`self.pending_action[player_num]`, and the on-screen status for that
player only ever shows a generic **"✅ Ready (hidden until reveal)"**
message — never the actual action — until **both** players have
chosen. Only then does the "Reveal Actions" button become clickable,
and only then is `Game.resolve_round()` called with both actions at
once, so neither player's choice can be influenced by seeing the
other's pick first.

In the AI's search tree, "simultaneity" is modeled the standard way
adversarial-search engines handle simultaneous-move games: the
analyzed player's action is chosen first in the search order (as the
MAX layer), then the opponent's counter-action is explored as if it
were chosen with full knowledge of the analyzed player's pick (the MIN
layer). This produces the analyzed player's **worst-case-guaranteed**
best action — a standard and safe approximation for simultaneous games
also known as treating it as a "one-shot game with a pessimistic
opponent."

## 8. Time Complexity

Let **b** = branching factor (up to 3 actions per player, less when a
player has 0 bullets) and **d** = `max_depth` (rounds searched, each
round expanding both players' actions).

- Each round expands roughly `b × b` state transitions.
- Plain Minimax over `d` rounds: **O((b²)^d)** = **O(b^(2d))**.
- With Alpha-Beta Pruning: best case roughly **O(b^d)** (the square
  root of the unpruned tree) when move ordering is favorable; worst
  case still `O(b^(2d))` if no cutoffs occur. In practice, the
  `Branches pruned` counter shown after every analysis demonstrates a
  substantial reduction versus `Nodes generated`.

## 9. Space Complexity

**O(b × d)** — as a depth-first search, only one path of `GameState`
clones (plus that path's sibling candidates at each level) is held in
memory at any time; the full tree is never materialized at once.

## 10. Sample Game Execution (GUI flow)

```
================================
          SHOTGUN DUEL
================================

PLAYER 1
Lives   : ❤️❤️❤️
Bullets : 🔫 x2

PLAYER 2
Lives   : ❤️❤️❤️
Bullets : 🔫 x1

[Player 1 selects Fire — hidden]
[Player 2 selects Reload — hidden]

[Reveal Actions] pressed

ROUND RESULT
--------------------------------
Player 1: 💥 Fire
Player 2: 🔄 Reload

💥 Player 2 was shot! Player 2 loses one life.

CURRENT STATE
--------------------------------
Player 1: ❤️❤️❤️ | Bullets: 🔫 x1
Player 2: ❤️❤️   | Bullets: 🔫 x2
```

## 11. Sample AI Analysis Output

With `Search Depth = 1` (a single round, exactly reproducing the
spec's example format), given P1 has 1 bullet and P2 has 2 bullets:

```
================================
       AI STRATEGY ANALYZER
================================

Current State:
P1 Lives: 3
P1 Bullets: 1

P2 Lives: 3
P2 Bullets: 2

Search Depth: 1

Possible Actions:
- Reload
- Block
- Fire

MINIMAX SEARCH

Player 1 → Reload
    Player 2 → Reload
        Evaluation = 5
    Player 2 → Block
        Evaluation = 10
    Player 2 → Fire
        Evaluation = -85

Player 1 → Block
    Player 2 → Reload
        Evaluation = -5
    Player 2 → Block
        Evaluation = 0
    Player 2 → Fire
        Evaluation = 5

Player 1 → Fire
    Player 2 → Reload
        Evaluation = 85
    Player 2 → Block
        Evaluation = -10
    ALPHA-BETA CUTOFF (MIN): after Block against Reload, beta -10 <= alpha +5; skipped 1 opponent response(s).

ALPHA-BETA PRUNING

Branches pruned: 1
Nodes generated: 11
Nodes evaluated: 8
Search depth: 1

OPTIMAL ACTION:

🛡️ BLOCK

Evaluation Score: -5

Recommended Strategy:
BLOCK

Evaluation Score:
-5
```

(This is real, program-generated output — captured directly from
running `AIAgent(max_depth=1).analyze(state, 1)` on the exact state
shown above, nothing is hard-coded. Note the Alpha-Beta cutoff: once
`Fire → Block` returns `-10`, the search already knows Fire's
worst-case (`-10`) cannot beat Reload's best guaranteed floor so far,
so the `Fire → Fire` branch is skipped entirely and reported as
pruned. The analyzer recommends **Block** here because it is the only
action with no catastrophic downside — Reload and Fire both risk a
`-85`/`-10` outcome if the opponent fires back, while Block's worst
case is a mild `-5`. Increasing the Search Depth spinner to 2 or 3
produces a deeper, correspondingly larger trace with many more real
Alpha-Beta cutoffs, since the branching multiplies with every
additional round.)

## 12. Simple Flowchart

```
                +---------------------------+
                |   Both players choose an  |
                |  action (hidden from each |
                |          other)            |
                +-------------+-------------+
                              |
                              v
                +---------------------------+
                |  "Reveal Actions" pressed  |
                +-------------+-------------+
                              |
                              v
                +---------------------------+
                |   Game.resolve_round()     |
                | applies Reload/Block/Fire  |
                |   rules simultaneously     |
                +-------------+-------------+
                              |
                              v
                +---------------------------+
                |   Is a player's lives = 0? |
                +------+--------------+-----+
                       | yes           | no
                       v               v
              +----------------+  +--------------------------+
              |  Duel ends,    |  |  Round counter increments, |
              |  winner shown  |  |  players choose again      |
              +----------------+  +--------------------------+

           (At ANY point, a player may instead click "Analyze")

                +---------------------------+
                |  AIAgent.analyze(state,    |
                |        player_num)          |
                +-------------+-------------+
                              v
                +---------------------------+
                |  Minimax generates every   |
                |  P1 action × P2 response   |
                |  and recurses `depth`       |
                |  rounds ahead               |
                +-------------+-------------+
                              v
                +---------------------------+
                |  Alpha-Beta prunes any     |
                |  branch that can't change  |
                |  the final decision        |
                +-------------+-------------+
                              v
                +---------------------------+
                |  Leaf states scored by the |
                |  heuristic evaluate()      |
                +-------------+-------------+
                              v
                +---------------------------+
                |  Best (max-of-min) action  |
                |  and score displayed        |
                +---------------------------+
```

## 13. Instructions for Running the Project

1. Ensure Python 3.8+ is installed with Tkinter available
   (`python3 -m tkinter` should open a tiny test window; if it errors,
   install with e.g. `sudo apt-get install python3-tk`).
2. From the `shotgun_duel/` folder, run:
   ```bash
   python main.py
   ```
3. Both players take turns clicking Reload / Block / Fire — each
   selection is hidden from the other player until "Reveal Actions" is
   clicked.
4. At any time, click "Analyze for Player 1" or "Analyze for Player 2"
   to see the Minimax + Alpha-Beta recommendation for the current
   state in the scrollable panel at the bottom. Adjust the "Search
   Depth (rounds)" spinner to see shallower or deeper analysis.
5. Click "Restart Duel" to reset both players to 3 lives / 0 bullets.

## 14. Possible Future Improvements

- Move-ordering heuristics (e.g., always evaluate Fire first when the
  player has bullets) to increase Alpha-Beta cutoff rates.
- An iterative-deepening option so the analyzer can search as deep as
  time allows rather than a fixed round count.
- Highlighting the exact recommended action's button in the GUI after
  an analysis runs.
- A running history/log panel of every round played, exportable at the
  end of a duel.
- Support for more than 2 simultaneous-choice actions (e.g., a "Reload
  x2" or "Feint" action) to enrich the strategy space, still fully
  compatible with the same Minimax + Alpha-Beta engine.

## 15. Design Notes

- `Game.resolve_round()` is the single source of truth for the rules,
  used identically by the real game and by every simulated branch in
  `minimax.py` — the AI can never reason about rules that don't match
  reality.
- The AI is purely observational: nothing in `ai_agent.py` or
  `minimax.py` ever calls `Game.resolve_round()` against the *real*
  `self.state` in `main.py` — it always works on cloned, hypothetical
  states, and only ever *returns* a recommendation string.
