"""
main.py
--------
Tkinter GUI entry point for Shotgun Duel.

This file is PURELY presentational. It imports and calls the exact
same, unmodified game engine and AI as before:

    - player.py   : Player (lives, bullets)              -- UNCHANGED
    - game.py      : Action, GameState, Game (the rules)   -- UNCHANGED
    - minimax.py   : Minimax + Alpha-Beta search and cutoff details
    - ai_agent.py  : AIAgent (the Strategy Analyzer)         -- UNCHANGED

Features:
- AAA Cyberpunk/Gaming aesthetic with elevated cards and glowing borders.
- Turn-based secret action selection ("✓ ACTION LOCKED", "PLAYER 2 — YOUR TURN", "✓ BOTH PLAYERS READY").
- Dramatic "3... 2... 1... REVEAL!" countdown animation.
- Card damage flash, floating "-1 LIFE" badge, and cracked heart animations.
- Interactive AI Strategy Analyzer with searching ticker, "Why?" toggle, and collapsible "Show AI Thinking" panel with search statistics and actual Alpha-Beta cutoff events.
- End-of-game victory celebration overlay with "PLAY AGAIN" control.

Run with:
    python main.py
"""

import tkinter as tk
from tkinter import font as tkfont

from player import Player
from game import Game, Action, GameState
from ai_agent import AIAgent


# ============================================================================
# PREMIUM CYBER-GAMING THEME & COLOR PALETTE
# ============================================================================
BG_MAIN = "#0a0d14"           # Deep space obsidian background
BG_PANEL = "#121624"          # Elevated container background
CARD_BG = "#181e30"           # Card background
CARD_BORDER = "#2b3554"       # Glowing border outline
CARD_BORDER_LIT = "#43527a"   # Active border highlight

TEXT_LIGHT = "#f8fafc"        # Crisp white text
TEXT_MUTED = "#94a3b8"        # Secondary muted text
TEXT_FAINT = "#64748b"        # Faint subtext

ACCENT = "#ff4d6d"            # Glowing title accent
ACCENT_PRIMARY = "#2563eb"    # Primary action button blue
ACCENT_PRIMARY_HOVER = "#3b82f6"
CYAN = "#06b6d4"              # Cyber cyan accent
VIOLET = "#c084fc"            # AI Analyzer cosmic violet accent
GOOD = "#10b981"              # Green success / Block / Locked-in
GOOD_HOVER = "#34d399"
WARN = "#f59e0b"              # Ammo warning amber

P1_COLOR = "#3b82f6"          # Player 1 vibrant sapphire blue
P2_COLOR = "#f43f5e"          # Player 2 vibrant crimson red

RELOAD_COLOR = "#0284c7"
RELOAD_HOVER = "#38bdf8"
BLOCK_COLOR = "#059669"
BLOCK_HOVER = "#34d399"
FIRE_COLOR = "#e11d48"
FIRE_HOVER = "#fb7185"

DISABLED_BG = "#1e2333"
DISABLED_FG = "#475569"

FONT_FAMILY = "Segoe UI"
MONO_FAMILY = "Consolas"


class HoverButton(tk.Button):
    """A tk.Button with smooth hover effects, active styling, and click animations."""

    def __init__(self, master, base_bg, hover_bg, **kwargs):
        super().__init__(
            master, bg=base_bg, activebackground=hover_bg,
            relief="flat", bd=0, cursor="hand2", **kwargs
        )
        self._base_bg = base_bg
        self._hover_bg = hover_bg
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _event):
        if str(self["state"]) != "disabled":
            self.config(bg=self._hover_bg)

    def _on_leave(self, _event):
        if str(self["state"]) != "disabled":
            self.config(bg=self._base_bg)

    def set_palette(self, base_bg, hover_bg):
        self._base_bg = base_bg
        self._hover_bg = hover_bg
        self.config(bg=base_bg, activebackground=hover_bg)


ACTION_STYLE = {
    Action.RELOAD: dict(base=RELOAD_COLOR, hover=RELOAD_HOVER, icon="🔄"),
    Action.BLOCK: dict(base=BLOCK_COLOR, hover=BLOCK_HOVER, icon="🛡️"),
    Action.FIRE: dict(base=FIRE_COLOR, hover=FIRE_HOVER, icon="💥"),
}


class ShotgunDuelApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Shotgun Duel — Minimax + Alpha-Beta Strategy Analyzer")
        self.configure(bg=BG_MAIN)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = min(1100, max(360, screen_width - 48))
        window_height = min(900, max(480, screen_height - 80))
        self.geometry(
            f"{window_width}x{window_height}+"
            f"{max(0, (screen_width - window_width) // 2)}+"
            f"{max(0, (screen_height - window_height) // 2)}"
        )
        self.minsize(min(640, window_width), min(480, window_height))

        self._fonts = {
            "title": tkfont.Font(family=FONT_FAMILY, size=28, weight="bold"),
            "subtitle": tkfont.Font(family=FONT_FAMILY, size=10),
            "card_name": tkfont.Font(family=FONT_FAMILY, size=13, weight="bold"),
            "lives": tkfont.Font(family="Segoe UI Emoji", size=26),
            "bullets": tkfont.Font(family=FONT_FAMILY, size=15, weight="bold"),
            "section": tkfont.Font(family=FONT_FAMILY, size=12, weight="bold"),
            "button": tkfont.Font(family=FONT_FAMILY, size=11, weight="bold"),
            "big_button": tkfont.Font(family=FONT_FAMILY, size=14, weight="bold"),
            "badge": tkfont.Font(family=FONT_FAMILY, size=10, weight="bold"),
            "body": tkfont.Font(family=FONT_FAMILY, size=10),
            "mono": tkfont.Font(family=MONO_FAMILY, size=11, weight="bold"),
        }

        # ---- Unmodified game engine -----------------------------------
        self.game = Game()
        self.state = GameState(Player("Player 1"), Player("Player 2"))
        self.pending_action = {1: None, 2: None}
        self.round_number = 1

        self._last_actions = None
        self._last_outcome_lines = []
        self._last_winner_msg = None
        self._is_revealing = False

        # AI UI State
        self._ai_show_why = False
        self._ai_show_thinking = False
        self._current_ai_data = None

        self._build_scrollable_viewport()
        self._build_layout()
        self._refresh_state_view()

    # ------------------------------------------------------------------
    # Scrollable Viewport Construction
    # ------------------------------------------------------------------
    def _build_scrollable_viewport(self):
        self.canvas = tk.Canvas(self, bg=BG_MAIN, highlightthickness=0, bd=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=BG_MAIN)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_frame_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_frame_id, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ------------------------------------------------------------------
    # Style Helpers & Animations
    # ------------------------------------------------------------------
    def _card(self, parent, **kwargs):
        frame = tk.Frame(
            parent, bg=CARD_BG, highlightbackground=CARD_BORDER,
            highlightthickness=2, bd=0, **kwargs
        )
        return frame

    def _badge(self, parent, text, bg, fg=TEXT_LIGHT, font=None):
        return tk.Label(
            parent, text=text, bg=bg, fg=fg, font=font or self._fonts["badge"],
            padx=14, pady=4,
        )

    def _flash_card_damage(self, player_num):
        panel = self.p1_panel if player_num == 1 else self.p2_panel
        card = panel["card"]
        orig_bg = CARD_BG
        orig_border = CARD_BORDER

        card.config(bg="#7f1d1d", highlightbackground="#ef476f")
        pop_badge = tk.Label(card, text="−1 LIFE", bg="#ef476f", fg="white",
                             font=self._fonts["badge"], padx=8, pady=2)
        pop_badge.place(relx=0.5, rely=0.4, anchor="center")

        def _restore():
            card.config(bg=orig_bg, highlightbackground=orig_border)
            pop_badge.destroy()

        self.after(450, _restore)

    def _flash_card_block(self, player_num):
        panel = self.p1_panel if player_num == 1 else self.p2_panel
        card = panel["card"]
        orig_bg = CARD_BG
        orig_border = CARD_BORDER

        card.config(bg="#064e3b", highlightbackground="#10b981")
        pop_badge = tk.Label(card, text="🛡️ BLOCKED", bg="#10b981", fg="white",
                             font=self._fonts["badge"], padx=8, pady=2)
        pop_badge.place(relx=0.5, rely=0.4, anchor="center")

        def _restore():
            card.config(bg=orig_bg, highlightbackground=orig_border)
            pop_badge.destroy()

        self.after(450, _restore)

    # ------------------------------------------------------------------
    # Layout Construction
    # ------------------------------------------------------------------
    def _build_layout(self):
        root = self.scrollable_frame

        # ---- Header Banner -----------------------------------------------
        header = tk.Frame(root, bg=BG_MAIN)
        header.pack(fill="x", pady=(20, 8), padx=28)

        title = tk.Label(
            header, text="🔫  S H O T G U N   D U E L", font=self._fonts["title"],
            bg=BG_MAIN, fg=ACCENT,
        )
        title.pack()

        subtitle = tk.Label(
            header, text="A Human vs Human Duel  ·  Analyzed by Minimax + Alpha-Beta Pruning",
            font=self._fonts["subtitle"], bg=BG_MAIN, fg=TEXT_MUTED,
        )
        subtitle.pack(pady=(3, 0))

        # ---- Turn Status Header ------------------------------------------
        self.turn_status_label = tk.Label(
            root, text="PLAYER 1 — YOUR TURN", font=self._fonts["section"],
            bg=BG_MAIN, fg=CYAN,
        )
        self.turn_status_label.pack(pady=(4, 6))

        # ---- Player cards + action panels row ---------------------------
        arena = tk.Frame(root, bg=BG_MAIN)
        self.arena = arena
        arena.pack(fill="x", padx=28, pady=(4, 6))
        arena.columnconfigure(0, weight=1)
        arena.columnconfigure(1, weight=0)
        arena.columnconfigure(2, weight=1)
        arena.bind("<Configure>", self._on_arena_configure)

        self.p1_panel = self._build_duelist_column(arena, player_num=1, color=P1_COLOR)
        self.p1_panel["column"].grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        vs_frame = tk.Frame(arena, bg=BG_MAIN)
        self.vs_frame = vs_frame
        vs_frame.grid(row=0, column=1, padx=8)
        tk.Label(vs_frame, text="⚔️", font=tkfont.Font(size=22), bg=BG_MAIN).pack()
        tk.Label(vs_frame, text="VS", font=tkfont.Font(family=FONT_FAMILY, size=16, weight="bold"),
                 bg=BG_MAIN, fg=TEXT_FAINT).pack()

        self.p2_panel = self._build_duelist_column(arena, player_num=2, color=P2_COLOR)
        self.p2_panel["column"].grid(row=0, column=2, sticky="nsew", padx=(12, 0))

        # ---- Reveal / Restart Controls ------------------------------------
        controls = tk.Frame(root, bg=BG_MAIN)
        self.main_controls = controls
        controls.pack(fill="x", pady=(12, 8))

        self.reveal_btn = HoverButton(
            controls, base_bg=DISABLED_BG, hover_bg=DISABLED_BG,
            text="🔓  REVEAL ACTIONS", font=self._fonts["big_button"],
            fg="white", padx=32, pady=14, state="disabled",
            command=self._reveal_actions_animated,
        )
        self.reveal_btn.pack(side="left", padx=10)

        self.restart_btn = HoverButton(
            controls, base_bg="#1c2336", hover_bg="#2c3652",
            text="🔄  Restart Duel", font=self._fonts["button"],
            fg=TEXT_LIGHT, padx=22, pady=12,
            command=self._restart,
        )
        self.restart_btn.pack(side="left", padx=10)
        controls.bind("<Configure>", self._on_main_controls_configure)

        # ---- Round Result Card ----------------------------------------
        self.result_card = self._card(root, padx=20, pady=14)
        self.result_card.pack(fill="x", padx=28, pady=(4, 12))
        self._build_result_card_contents(initial=True)

        # ---- AI Strategy Analyzer Panel -----------------------------------
        analyzer_card = self._card(root, padx=22, pady=16)
        analyzer_card.pack(fill="both", expand=True, padx=28, pady=(0, 28))

        analyzer_header = tk.Frame(analyzer_card, bg=CARD_BG)
        analyzer_header.pack(fill="x")
        tk.Label(
            analyzer_header, text="🧠 AI STRATEGY ANALYZER", font=self._fonts["section"],
            bg=CARD_BG, fg=VIOLET,
        ).pack(side="left")
        tk.Label(
            analyzer_header, text="(analysis only — does not play automatically)",
            font=self._fonts["subtitle"], bg=CARD_BG, fg=TEXT_FAINT,
        ).pack(side="left", padx=(10, 0))

        analyzer_controls = tk.Frame(analyzer_card, bg=CARD_BG)
        analyzer_controls.pack(fill="x", pady=(12, 8))
        analyzer_buttons = tk.Frame(analyzer_controls, bg=CARD_BG)
        analyzer_buttons.pack(fill="x")

        self.analyze_p1_btn = HoverButton(
            analyzer_buttons, base_bg="#1e2638", hover_bg="#3b82f6",
            text="Analyze Player 1", fg=TEXT_LIGHT, font=self._fonts["button"],
            padx=16, pady=9, command=lambda: self._run_analysis_animated(1),
        )
        self.analyze_p1_btn.pack(side="left", padx=(0, 10))

        self.analyze_p2_btn = HoverButton(
            analyzer_buttons, base_bg="#1e2638", hover_bg="#f43f5e",
            text="Analyze Player 2", fg=TEXT_LIGHT, font=self._fonts["button"],
            padx=16, pady=9, command=lambda: self._run_analysis_animated(2),
        )
        self.analyze_p2_btn.pack(side="left", padx=(0, 10))
        analyzer_buttons.bind("<Configure>", self._on_analyzer_buttons_configure)

        depth_controls = tk.Frame(analyzer_controls, bg=CARD_BG)
        depth_controls.pack(fill="x", pady=(8, 0))
        tk.Label(depth_controls, text="Search Depth:", bg=CARD_BG, fg=TEXT_MUTED,
                 font=self._fonts["body"]).pack(side="left", padx=(4, 4))
        self.depth_var = tk.IntVar(value=3)
        depth_spin = tk.Spinbox(
            depth_controls, from_=1, to=5, textvariable=self.depth_var, width=3,
            bg="#0d111a", fg=TEXT_LIGHT, buttonbackground="#1e2638",
            relief="flat", justify="center", font=self._fonts["body"],
            insertbackground=TEXT_LIGHT,
        )
        depth_spin.pack(side="left")

        # ---- AI Summary Result Area -------------------------------------
        self.ai_result_frame = tk.Frame(analyzer_card, bg=CARD_BG)
        self.ai_result_frame.pack(fill="both", expand=True, pady=(12, 0))
        self._build_ai_placeholder()

    def _on_arena_configure(self, event):
        compact = event.width < 820
        if compact == getattr(self, "_compact_arena", None):
            return

        self._compact_arena = compact
        if compact:
            self.p1_panel["column"].grid_configure(
                row=0, column=0, columnspan=3, padx=0, pady=(0, 8)
            )
            self.vs_frame.grid_configure(row=1, column=0, columnspan=3, padx=0, pady=2)
            self.p2_panel["column"].grid_configure(
                row=2, column=0, columnspan=3, padx=0, pady=(8, 0)
            )
        else:
            self.p1_panel["column"].grid_configure(
                row=0, column=0, columnspan=1, padx=(0, 12), pady=0
            )
            self.vs_frame.grid_configure(row=0, column=1, columnspan=1, padx=8, pady=0)
            self.p2_panel["column"].grid_configure(
                row=0, column=2, columnspan=1, padx=(12, 0), pady=0
            )

    def _on_main_controls_configure(self, event):
        compact = event.width < 430
        side = "top" if compact else "left"
        fill = "x" if compact else "none"
        self.reveal_btn.pack_configure(side=side, fill=fill, padx=10, pady=4 if compact else 0)
        self.restart_btn.pack_configure(side=side, fill=fill, padx=10, pady=4 if compact else 0)

    def _on_analyzer_buttons_configure(self, event):
        compact = event.width < 390
        side = "top" if compact else "left"
        fill = "x" if compact else "none"
        self.analyze_p1_btn.pack_configure(
            side=side, fill=fill, padx=(0, 10) if not compact else 0,
            pady=3 if compact else 0,
        )
        self.analyze_p2_btn.pack_configure(
            side=side, fill=fill, padx=(0, 10) if not compact else 0,
            pady=3 if compact else 0,
        )

    # ------------------------------------------------------------------
    def _build_duelist_column(self, parent, player_num, color):
        column = tk.Frame(parent, bg=BG_MAIN)

        # --- Player card -------------------------------------------------
        card = self._card(column, padx=18, pady=16)
        card.pack(fill="x")

        header_row = tk.Frame(card, bg=CARD_BG)
        header_row.pack(fill="x")

        name_chip = tk.Label(
            header_row, text=f"PLAYER {player_num}", bg=color, fg="white",
            font=self._fonts["card_name"], padx=16, pady=5,
        )
        name_chip.pack(side="left")

        stats_container = tk.Frame(card, bg=CARD_BG)
        stats_container.pack(fill="x", pady=(14, 0))

        # Lives section
        lives_box = tk.Frame(stats_container, bg="#0d111a", highlightbackground=CARD_BORDER,
                             highlightthickness=1, padx=14, pady=10)
        lives_box.pack(side="left", expand=True, fill="both", padx=(0, 6))

        tk.Label(lives_box, text="LIVES", font=self._fonts["subtitle"], bg="#0d111a",
                 fg=TEXT_FAINT).pack(anchor="w")
        lives_var = tk.StringVar()
        lives_label = tk.Label(lives_box, textvariable=lives_var, font=self._fonts["lives"],
                                bg="#0d111a", fg=TEXT_LIGHT)
        lives_label.pack(anchor="w", pady=(2, 0))

        # Ammo section
        bullets_box = tk.Frame(stats_container, bg="#0d111a", highlightbackground=CARD_BORDER,
                               highlightthickness=1, padx=14, pady=10)
        bullets_box.pack(side="left", expand=True, fill="both", padx=(6, 0))

        tk.Label(bullets_box, text="AMMO", font=self._fonts["subtitle"], bg="#0d111a",
                 fg=TEXT_FAINT).pack(anchor="w")
        bullets_var = tk.StringVar()
        bullets_badge = tk.Label(bullets_box, textvariable=bullets_var, font=self._fonts["bullets"],
                                  bg="#1c2336", fg=WARN, padx=12, pady=3)
        bullets_badge.pack(anchor="w", pady=(4, 0))

        # --- Action Panel --------------------------------------------------
        action_card = self._card(column, padx=16, pady=16)
        action_card.pack(fill="x", pady=(12, 0))

        action_header = tk.Frame(action_card, bg=CARD_BG)
        action_header.pack(fill="x")

        tk.Label(action_header, text=f"PLAYER {player_num} ACTION", font=self._fonts["section"],
                 bg=CARD_BG, fg=TEXT_LIGHT).pack(side="left")

        status_badge = self._badge(action_header, "Waiting...", bg="#0d111a", fg=TEXT_MUTED)
        status_badge.pack(side="right")

        btn_frame = tk.Frame(action_card, bg=CARD_BG)
        btn_frame.pack(fill="x", pady=(14, 0))

        buttons = {}
        for action in (Action.RELOAD, Action.BLOCK, Action.FIRE):
            style = ACTION_STYLE[action]
            b = HoverButton(
                btn_frame, base_bg=style["base"], hover_bg=style["hover"],
                text=f"{style['icon']}  {str(action).upper()}",
                font=self._fonts["button"], fg="white",
                padx=6, pady=14, width=10,
                command=lambda a=action, p=player_num: self._select_action(p, a),
            )
            b.pack(side="left", expand=True, fill="x", padx=4)
            buttons[action] = b

        return {
            "column": column, "card": card, "action_card": action_card,
            "lives": lives_var, "bullets": bullets_var,
            "status_badge": status_badge, "buttons": buttons,
        }

    def _build_result_card_contents(self, initial=False):
        for w in self.result_card.winfo_children():
            w.destroy()

        header_row = tk.Frame(self.result_card, bg=CARD_BG)
        header_row.pack(fill="x")

        round_text = f"ROUND {self.round_number} RESULT" if not initial else "ROUND RESULT"
        tk.Label(header_row, text=round_text, font=self._fonts["section"],
                 bg=CARD_BG, fg=TEXT_LIGHT).pack(side="left")

        if initial or self._last_actions is None:
            tk.Label(
                self.result_card, text="Select an action for both Player 1 and Player 2, then press Reveal Actions.",
                font=self._fonts["body"], bg=CARD_BG, fg=TEXT_MUTED,
            ).pack(anchor="w", pady=(8, 0))
            return

        moves_card = tk.Frame(self.result_card, bg="#0d111a", highlightbackground=CARD_BORDER,
                              highlightthickness=1, padx=16, pady=12)
        moves_card.pack(fill="x", pady=(12, 10))

        p1_action, p2_action = self._last_actions
        p1_style = ACTION_STYLE[p1_action]
        p2_style = ACTION_STYLE[p2_action]

        p1_row = tk.Frame(moves_card, bg="#0d111a")
        p1_row.pack(fill="x", pady=(2, 2))
        tk.Label(p1_row, text="PLAYER 1  →  ", font=self._fonts["button"], bg="#0d111a", fg=P1_COLOR).pack(side="left")
        tk.Label(p1_row, text=f"{p1_style['icon']} {str(p1_action).upper()}", font=self._fonts["button"],
                 bg="#0d111a", fg=TEXT_LIGHT).pack(side="left")

        p2_row = tk.Frame(moves_card, bg="#0d111a")
        p2_row.pack(fill="x", pady=(2, 2))
        tk.Label(p2_row, text="PLAYER 2  →  ", font=self._fonts["button"], bg="#0d111a", fg=P2_COLOR).pack(side="left")
        tk.Label(p2_row, text=f"{p2_style['icon']} {str(p2_action).upper()}", font=self._fonts["button"],
                 bg="#0d111a", fg=TEXT_LIGHT).pack(side="left")

        outcome_box = tk.Frame(self.result_card, bg=CARD_BG)
        outcome_box.pack(fill="x", pady=(4, 0))

        for line in self._last_outcome_lines:
            tk.Label(
                outcome_box, text=line, font=self._fonts["body"],
                bg=CARD_BG, fg=TEXT_LIGHT, justify="left", anchor="w", wraplength=980,
            ).pack(anchor="w", pady=(2, 0))

        if self._last_winner_msg:
            victory_banner = tk.Frame(self.result_card, bg="#1e1b4b", padx=16, pady=12,
                                      highlightbackground=GOOD, highlightthickness=2)
            victory_banner.pack(fill="x", pady=(14, 0))

            tk.Label(
                victory_banner, text="✨  🎉  🏆  DUEL VICTORY  🏆  🎉  ✨",
                font=self._fonts["badge"], bg="#1e1b4b", fg=WARN,
            ).pack(anchor="center")

            tk.Label(
                victory_banner, text=self._last_winner_msg,
                font=tkfont.Font(family=FONT_FAMILY, size=18, weight="bold"),
                bg="#1e1b4b", fg=GOOD,
            ).pack(anchor="center", pady=(4, 6))

            HoverButton(
                victory_banner, base_bg=GOOD, hover_bg=GOOD_HOVER,
                text="🔄  PLAY AGAIN", font=self._fonts["big_button"], fg="white",
                padx=24, pady=8, command=self._restart,
            ).pack(anchor="center", pady=(6, 2))

    def _build_ai_placeholder(self):
        for w in self.ai_result_frame.winfo_children():
            w.destroy()
        placeholder_box = tk.Frame(self.ai_result_frame, bg="#0d111a", padx=18, pady=16,
                                   highlightbackground=CARD_BORDER, highlightthickness=1)
        placeholder_box.pack(fill="x", pady=(4, 0))
        tk.Label(
            placeholder_box,
            text="Click \"Analyze Player 1\" or \"Analyze Player 2\" to view optimal strategy.",
            font=self._fonts["body"], bg="#0d111a", fg=TEXT_MUTED,
        ).pack(anchor="w")

    # ------------------------------------------------------------------
    # Secret Action Selection & Dramatic Countdown Reveal
    # ------------------------------------------------------------------
    def _select_action(self, player_num, action):
        if self.state.is_terminal() or self._is_revealing:
            return
        valid = Game.valid_actions(self.state, player_num)
        if action not in valid:
            return

        self.pending_action[player_num] = action
        panel = self.p1_panel if player_num == 1 else self.p2_panel

        for act, btn in panel["buttons"].items():
            style = ACTION_STYLE[act]
            if act == action:
                btn.config(bg=GOOD, fg="white", activebackground=GOOD_HOVER)
                btn.set_palette(GOOD, GOOD_HOVER)
            elif act in valid:
                btn.set_palette(style["base"], style["hover"])

        panel["status_badge"].config(text="✓ ACTION LOCKED", bg="#064e3b", fg=GOOD_HOVER)

        # Update turn helper status
        p1_done = self.pending_action[1] is not None
        p2_done = self.pending_action[2] is not None

        if p1_done and not p2_done:
            self.turn_status_label.config(text="PLAYER 2 — YOUR TURN", fg=P2_COLOR)
        elif p2_done and not p1_done:
            self.turn_status_label.config(text="PLAYER 1 — YOUR TURN", fg=P1_COLOR)
        elif p1_done and p2_done:
            self.turn_status_label.config(text="✓ BOTH PLAYERS READY", fg=GOOD_HOVER)
            self._set_reveal_enabled(True)

    def _set_reveal_enabled(self, enabled: bool):
        if enabled:
            self.reveal_btn.config(state="normal", text="🔓  REVEAL ACTIONS")
            self.reveal_btn.set_palette(ACCENT_PRIMARY, ACCENT_PRIMARY_HOVER)
        else:
            self.reveal_btn.config(state="disabled")
            self.reveal_btn.set_palette(DISABLED_BG, DISABLED_BG)

    def _reveal_actions_animated(self):
        a1 = self.pending_action[1]
        a2 = self.pending_action[2]
        if a1 is None or a2 is None or self._is_revealing:
            return

        self._is_revealing = True
        self._set_reveal_enabled(False)

        # Countdown animation sequence: 3... 2... 1... REVEAL!
        def _count_3():
            self.reveal_btn.config(text="3...")
            self.after(250, _count_2)

        def _count_2():
            self.reveal_btn.config(text="2...")
            self.after(250, _count_1)

        def _count_1():
            self.reveal_btn.config(text="1...")
            self.after(250, _count_reveal)

        def _count_reveal():
            self.reveal_btn.config(text="💥 REVEAL!")
            self.after(250, _execute_reveal)

        def _execute_reveal():
            old_state = self.state
            new_state = Game.resolve_round(self.state, a1, a2)

            self._last_actions = (a1, a2)
            self._last_outcome_lines = self._describe_outcome(a1, a2, old_state, new_state)
            self._last_winner_msg = None

            self.state = new_state
            self.pending_action = {1: None, 2: None}

            # Reveal move badges
            self.p1_panel["status_badge"].config(text=f"{a1.emoji} {str(a1).upper()}", bg="#1c2336", fg=TEXT_LIGHT)
            self.p2_panel["status_badge"].config(text=f"{a2.emoji} {str(a2).upper()}", bg="#1c2336", fg=TEXT_LIGHT)

            # Animate card hit/block flashes
            p1_hit = new_state.p1.lives < old_state.p1.lives
            p2_hit = new_state.p2.lives < old_state.p2.lives

            if p1_hit:
                self._flash_card_damage(1)
            elif a1 == Action.BLOCK and a2 == Action.FIRE:
                self._flash_card_block(1)

            if p2_hit:
                self._flash_card_damage(2)
            elif a2 == Action.BLOCK and a1 == Action.FIRE:
                self._flash_card_block(2)

            self._refresh_state_view()

            if self.state.is_terminal():
                winner = self.state.winner()
                if winner == "DRAW":
                    self._last_winner_msg = "🤝  IT'S A DRAW!"
                else:
                    self._last_winner_msg = f"🏆  {winner} WINS THE DUEL!"
                self.turn_status_label.config(text="🏆 GAME OVER", fg=GOOD_HOVER)
                for panel in (self.p1_panel, self.p2_panel):
                    for b in panel["buttons"].values():
                        b.config(state="disabled", bg=DISABLED_BG, fg=DISABLED_FG)
            else:
                self.round_number += 1
                self.turn_status_label.config(text="PLAYER 1 — YOUR TURN", fg=CYAN)
                for panel in (self.p1_panel, self.p2_panel):
                    panel["status_badge"].config(text="Waiting...", bg="#0d111a", fg=TEXT_MUTED)

            self._build_result_card_contents()
            self._is_revealing = False

        _count_3()

    @staticmethod
    def _describe_outcome(a1, a2, old_state, new_state):
        p1_hit = new_state.p1.lives < old_state.p1.lives
        p2_hit = new_state.p2.lives < old_state.p2.lives
        msgs = []
        if p2_hit:
            msgs.append("💥 PLAYER 2 HIT!  −1 LIFE")
        if p1_hit:
            msgs.append("💥 PLAYER 1 HIT!  −1 LIFE")
        if a1 == Action.FIRE and a2 == Action.BLOCK:
            msgs.append("🛡️ Player 2 blocked the shot! No damage taken.")
        if a2 == Action.FIRE and a1 == Action.BLOCK:
            msgs.append("🛡️ Player 1 blocked the shot! No damage taken.")
        if a1 == Action.FIRE and a2 == Action.FIRE:
            msgs.append("💥💥 Both players fired simultaneously! Shots traded — no damage taken.")
        if not msgs:
            msgs.append("🔄 Both players maneuvered safely — no damage taken this round.")
        return msgs

    def _restart(self):
        self.state = GameState(Player("Player 1"), Player("Player 2"))
        self.pending_action = {1: None, 2: None}
        self.round_number = 1
        self._last_actions = None
        self._last_outcome_lines = []
        self._last_winner_msg = None
        self._is_revealing = False

        self.turn_status_label.config(text="PLAYER 1 — YOUR TURN", fg=CYAN)

        for panel in (self.p1_panel, self.p2_panel):
            panel["status_badge"].config(text="Waiting...", bg="#0d111a", fg=TEXT_MUTED)
            for action, b in panel["buttons"].items():
                style = ACTION_STYLE[action]
                b.set_palette(style["base"], style["hover"])
                b.config(state="normal", fg="white")

        self._set_reveal_enabled(False)
        self._build_result_card_contents(initial=True)
        self._build_ai_placeholder()
        self._refresh_state_view()

    def _refresh_state_view(self):
        self.p1_panel["lives"].set(self.state.p1.lives_display())
        self.p1_panel["bullets"].set(self.state.p1.bullets_display())
        self.p2_panel["lives"].set(self.state.p2.lives_display())
        self.p2_panel["bullets"].set(self.state.p2.bullets_display())

        for player_num, panel in ((1, self.p1_panel), (2, self.p2_panel)):
            valid = Game.valid_actions(self.state, player_num)
            terminal = self.state.is_terminal()
            for action, btn in panel["buttons"].items():
                style = ACTION_STYLE[action]
                if terminal:
                    btn.config(state="disabled", bg=DISABLED_BG, fg=DISABLED_FG)
                    continue

                if self.pending_action[player_num] == action:
                    btn.config(state="normal", fg="white", text=f"{style['icon']}  {str(action).upper()}")
                    btn.set_palette(GOOD, GOOD_HOVER)
                elif action in valid:
                    btn.config(state="normal", fg="white", text=f"{style['icon']}  {str(action).upper()}")
                    btn.set_palette(style["base"], style["hover"])
                else:
                    label = f"{style['icon']}  {str(action).upper()} (No Ammo)" \
                        if action == Action.FIRE else f"{style['icon']}  {str(action).upper()}"
                    btn.config(state="disabled", bg=DISABLED_BG, fg=DISABLED_FG, text=label)

    # ------------------------------------------------------------------
    # Interactive AI Strategy Analyzer with Alpha-Beta cutoff details
    # ------------------------------------------------------------------
    def _run_analysis_animated(self, player_num):
        for w in self.ai_result_frame.winfo_children():
            w.destroy()

        loading_box = tk.Frame(self.ai_result_frame, bg="#0d111a", padx=18, pady=18,
                               highlightbackground=CARD_BORDER, highlightthickness=1)
        loading_box.pack(fill="x", pady=(4, 0))

        lbl = tk.Label(loading_box, text="Analyzing ●", font=self._fonts["body"],
                       bg="#0d111a", fg=CYAN)
        lbl.pack(anchor="w")

        # Ticker animation
        self.after(120, lambda: lbl.config(text="Analyzing ●●"))
        self.after(240, lambda: lbl.config(text="Analyzing ●●●"))
        self.after(360, lambda: self._execute_analysis(player_num))

    def _execute_analysis(self, player_num):
        opponent_num = 2 if player_num == 1 else 1

        prune_events = []
        cutoff_count = 0

        def collect_prune_events(message):
            nonlocal cutoff_count
            if "ALPHA-BETA CUTOFF" in message:
                cutoff_count += 1
                if len(prune_events) < 100:
                    prune_events.append(message.strip())

        agent = AIAgent(max_depth=self.depth_var.get(), log=collect_prune_events)
        best_action, best_score = agent.analyze(self.state, player_num)

        stats = {
            "depth": agent.minimax.max_depth,
            "moves_checked": agent.minimax.nodes_generated,
            "pruned": agent.minimax.nodes_pruned,
            "cutoff_count": cutoff_count,
            "prune_events": prune_events,
        }

        reason = self._explain_move(self.state, player_num, opponent_num, best_action)
        self._current_ai_data = (player_num, opponent_num, best_action, best_score, stats, reason)

        # Reset toggles
        self._ai_show_why = False
        self._ai_show_thinking = False

        self._render_ai_summary()

    @staticmethod
    def _explain_move(state, player_num, opponent_num, action) -> str:
        me = state.player(player_num)
        opp = state.opponent(player_num)

        if action == Action.FIRE:
            if opp.bullets == 0:
                return f"Player {opponent_num} has no bullets, so firing now puts them under maximum pressure."
            return f"Firing exerts immediate pressure on Player {opponent_num} while maintaining offensive tempo."

        if action == Action.BLOCK:
            if opp.bullets > 0:
                return f"Player {opponent_num} has ammo ready — blocking neutralizes their potential offensive threat cleanly."
            return "Blocking keeps your position completely safe without risking damage."

        if action == Action.RELOAD:
            if me.bullets == 0:
                return "You have 0 bullets — reloading is essential before Fire becomes available again."
            return "Reloading builds your ammo advantage now while your opponent poses minimal immediate risk."

        return "This move maximizes your evaluation advantage according to Minimax depth search."

    def _render_ai_summary(self):
        for w in self.ai_result_frame.winfo_children():
            w.destroy()

        if not self._current_ai_data:
            return

        player_num, opponent_num, action, score, stats, reason = self._current_ai_data
        state = self.state
        p1, p2 = state.p1, state.p2

        card = tk.Frame(self.ai_result_frame, bg="#0d111a", highlightbackground=CYAN,
                        highlightthickness=2, padx=18, pady=16)
        card.pack(fill="both", expand=True)

        self.after(350, lambda: card.config(highlightbackground=CARD_BORDER))

        # 1. Current State
        state_row = tk.Frame(card, bg="#0d111a")
        state_row.pack(fill="x", anchor="w")
        tk.Label(state_row, text="Current State:", font=self._fonts["section"],
                 bg="#0d111a", fg=TEXT_LIGHT).pack(anchor="w")

        p1_str = f"P1  {p1.lives_display()}   |   {p1.bullets_display()}"
        p2_str = f"P2  {p2.lives_display()}   |   {p2.bullets_display()}"

        tk.Label(state_row, text=p1_str, font=self._fonts["mono"], bg="#0d111a", fg=P1_COLOR).pack(anchor="w", pady=(3, 0))
        tk.Label(state_row, text=p2_str, font=self._fonts["mono"], bg="#0d111a", fg=P2_COLOR).pack(anchor="w")

        # 2. Best Move Hero Box
        style = ACTION_STYLE[action]
        best_box = tk.Frame(card, bg="#1c2336", padx=16, pady=12, highlightbackground=CARD_BORDER, highlightthickness=1)
        best_box.pack(fill="x", pady=(14, 10))

        top_info = tk.Frame(best_box, bg="#1c2336")
        top_info.pack(fill="x")

        tk.Label(top_info, text=f"BEST MOVE FOR PLAYER {player_num}", font=self._fonts["subtitle"],
                 bg="#1c2336", fg=TEXT_MUTED).pack(side="left")

        tk.Label(top_info, text="CONFIDENCE: HIGH", font=self._fonts["badge"],
                 bg="#064e3b", fg=GOOD_HOVER, padx=8, pady=2).pack(side="right")

        move_label = tk.Label(
            best_box, text=f"{style['icon']}  {str(action).upper()}",
            font=tkfont.Font(family=FONT_FAMILY, size=22, weight="bold"),
            bg="#1c2336", fg=style["base"],
        )
        move_label.pack(anchor="w", pady=(4, 0))

        # 3. Interactive Toggle Buttons Row ([ Why? ] & [ Show AI Thinking ])
        toggles_row = tk.Frame(card, bg="#0d111a")
        toggles_row.pack(fill="x", pady=(6, 8))

        why_txt = "▼ Hide Explanation" if self._ai_show_why else "[ Why? ]"
        HoverButton(
            toggles_row, base_bg="#1c2336", hover_bg="#2c3652",
            text=why_txt, font=self._fonts["button"], fg=CYAN,
            padx=12, pady=6, command=self._toggle_why,
        ).pack(side="left", padx=(0, 8))

        thinking_txt = "▼ Hide AI Thinking" if self._ai_show_thinking else "[ Show AI Thinking ]"
        HoverButton(
            toggles_row, base_bg="#1c2336", hover_bg="#2c3652",
            text=thinking_txt, font=self._fonts["button"], fg=VIOLET,
            padx=12, pady=6, command=self._toggle_thinking,
        ).pack(side="left")

        # 4. Collapsible "Why?" Section
        if self._ai_show_why:
            why_box = tk.Frame(card, bg="#181e30", padx=14, pady=10,
                               highlightbackground=CARD_BORDER, highlightthickness=1)
            why_box.pack(fill="x", pady=(0, 10))
            tk.Label(
                why_box, text=f'"{reason}"', font=self._fonts["body"], bg="#181e30", fg=TEXT_LIGHT,
                justify="left", anchor="w", wraplength=940,
            ).pack(anchor="w")

        # 5. Collapsible "AI Thinking" section with actual search cutoffs.
        if self._ai_show_thinking:
            thinking_box = tk.Frame(card, bg="#181e30", padx=14, pady=12,
                                     highlightbackground=VIOLET, highlightthickness=1)
            thinking_box.pack(fill="x", pady=(0, 10))

            tk.Label(thinking_box, text="🧠 AI Search Statistics:", font=self._fonts["section"],
                     bg="#181e30", fg=VIOLET).pack(anchor="w", pady=(0, 6))

            # AI Statistics Chips rendered inside [ Show AI Thinking ]
            chips_row = tk.Frame(thinking_box, bg="#181e30")
            chips_row.pack(fill="x", anchor="w", pady=(0, 10))

            chip_side = "top" if getattr(self, "_compact_arena", False) else "left"
            self._stat_chip(chips_row, "Search Depth", stats["depth"], CYAN, chip_side)
            self._stat_chip(chips_row, "Moves Checked", stats["moves_checked"], WARN, chip_side)
            self._stat_chip(chips_row, "Branches Pruned", stats["pruned"], GOOD, chip_side)

            tk.Label(
                thinking_box,
                text="Alpha-Beta Pruning Log — real cutoffs from this search:",
                font=self._fonts["subtitle"], bg="#181e30", fg=TEXT_MUTED,
            ).pack(anchor="w", pady=(4, 4))

            log_frame = tk.Frame(thinking_box, bg="#0d111a")
            log_frame.pack(fill="x", expand=True)
            log_scrollbar = tk.Scrollbar(log_frame, orient="vertical")
            log_scrollbar.pack(side="right", fill="y")
            prune_log = tk.Text(
                log_frame, height=8, wrap="word", state="disabled",
                bg="#0d111a", fg=TEXT_LIGHT, insertbackground=TEXT_LIGHT,
                font=self._fonts["mono"], relief="flat", padx=8, pady=6,
                yscrollcommand=log_scrollbar.set,
            )
            prune_log.pack(side="left", fill="both", expand=True)
            log_scrollbar.config(command=prune_log.yview)
            prune_log.tag_configure("cutoff", foreground=GOOD)
            prune_log.tag_configure("empty", foreground=TEXT_MUTED)
            prune_log.bind(
                "<MouseWheel>",
                lambda event, widget=prune_log: self._scroll_pruning_log(event, widget),
            )

            prune_log.configure(state="normal")
            if stats["prune_events"]:
                for event in stats["prune_events"]:
                    prune_log.insert("end", f"• {event}\n", "cutoff")
                omitted = stats["cutoff_count"] - len(stats["prune_events"])
                if omitted:
                    prune_log.insert(
                        "end", f"\n… and {omitted} more cutoff events (showing first 100).\n",
                        "empty",
                    )
            else:
                prune_log.insert(
                    "end",
                    "No branches were cut off: the alpha-beta bounds did not cross "
                    "during this search.",
                    "empty",
                )
            prune_log.configure(state="disabled")

    @staticmethod
    def _scroll_pruning_log(event, widget):
        if event.delta:
            widget.yview_scroll(int(-event.delta / 120), "units")
        elif getattr(event, "num", None) == 4:
            widget.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5:
            widget.yview_scroll(1, "units")
        return "break"

    def _toggle_why(self):
        self._ai_show_why = not self._ai_show_why
        self._render_ai_summary()

    def _toggle_thinking(self):
        self._ai_show_thinking = not self._ai_show_thinking
        self._render_ai_summary()

    def _stat_chip(self, parent, label, value, color, side="left"):
        chip = tk.Frame(parent, bg="#1c2336", padx=16, pady=10,
                        highlightbackground=CARD_BORDER, highlightthickness=1)
        chip.pack(
            side=side, fill="x" if side == "top" else "none",
            padx=(0, 14) if side == "left" else 0,
            pady=(0, 6) if side == "top" else 0,
        )
        tk.Label(chip, text=str(value), font=tkfont.Font(family=FONT_FAMILY, size=17, weight="bold"),
                 bg="#1c2336", fg=color).pack(anchor="w")
        tk.Label(chip, text=label, font=self._fonts["subtitle"], bg="#1c2336",
                 fg=TEXT_FAINT).pack(anchor="w", pady=(1, 0))


def main():
    app = ShotgunDuelApp()
    app.mainloop()


if __name__ == "__main__":
    main()
