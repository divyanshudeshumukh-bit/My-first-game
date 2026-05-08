import pygame
import random
import sys
import math

pygame.init()

# ──────────────────────────────────────────────
#  WINDOW & FPS
# ──────────────────────────────────────────────
W, H = 480, 820
FPS  = 60
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("🏏 Cricket Simulator")
clock  = pygame.time.Clock()

# ──────────────────────────────────────────────
#  PALETTE
# ──────────────────────────────────────────────
def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

BG      = hex2rgb("060f1e")
BG2     = hex2rgb("0b1d30")
BG3     = hex2rgb("0f2540")
BG4     = hex2rgb("1a3558")
ACCENT  = hex2rgb("00e676")
ACCENT2 = hex2rgb("00c853")
GOLD    = hex2rgb("ffd740")
RED     = hex2rgb("ff5252")
BLUE    = hex2rgb("8ab4f8")
TEXT    = hex2rgb("e8f0fe")
TEXT2   = hex2rgb("8fa8cc")
TEXT3   = hex2rgb("3f607f")
BORDER  = hex2rgb("1e3a5a")
WHITE   = (255, 255, 255)
BLACK   = (0,   0,   0)

def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def with_alpha(color, alpha):
    s = pygame.Surface((1, 1), pygame.SRCALPHA)
    s.fill((*color, alpha))
    return s

# ──────────────────────────────────────────────
#  FONTS  (fallback to system fonts gracefully)
# ──────────────────────────────────────────────
def load_font(size, bold=False):
    for name in ["DejaVu Sans", "Arial", "Helvetica", "FreeSans"]:
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            pass
    return pygame.font.Font(None, size)

def load_mono(size, bold=False):
    for name in ["DejaVu Sans Mono", "Courier New", "Courier", "FreeMono"]:
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            pass
    return pygame.font.Font(None, size)

F_TINY   = load_font(11)
F_SMALL  = load_font(13)
F_MED    = load_font(15, bold=True)
F_LARGE  = load_font(20, bold=True)
F_XL     = load_font(28, bold=True)
F_XXL    = load_font(42, bold=True)
F_SCORE  = load_font(52, bold=True)
F_MONO   = load_mono(13, bold=True)
F_MONO_S = load_mono(11)

# ──────────────────────────────────────────────
#  DRAWING HELPERS
# ──────────────────────────────────────────────
def draw_rect(surf, color, rect, radius=8, border_color=None, border_w=1):
    """Draw a rounded rectangle, optionally with a border."""
    r = pygame.Rect(rect)
    if len(color) == 4:  # RGBA
        s = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        pygame.draw.rect(s, color, (0, 0, r.w, r.h), border_radius=radius)
        surf.blit(s, r.topleft)
    else:
        pygame.draw.rect(surf, color, r, border_radius=radius)
    if border_color:
        pygame.draw.rect(surf, border_color, r, border_w, border_radius=radius)

def draw_text(surf, text, font, color, x, y, align="left", max_w=None):
    """Render text with optional truncation and alignment."""
    if max_w:
        while font.size(text)[0] > max_w and len(text) > 1:
            text = text[:-1]
    img = font.render(str(text), True, color)
    r   = img.get_rect()
    if align == "center": r.centerx = x
    elif align == "right": r.right  = x
    else:                  r.left   = x
    r.top = y
    surf.blit(img, r)
    return r.width

def draw_text_mid(surf, text, font, color, cy, max_w=None):
    """Horizontally centered text at a given y."""
    img = font.render(str(text), True, color)
    if max_w:
        r = img.get_rect(centerx=W//2, centery=cy)
    else:
        r = img.get_rect(centerx=W//2, centery=cy)
    surf.blit(img, r)

def draw_pill(surf, text, font, fg, bg, x, y, pad_x=10, pad_y=4, radius=20):
    img  = font.render(text, True, fg)
    tw   = img.get_width()
    th   = img.get_height()
    rect = pygame.Rect(x, y, tw + pad_x*2, th + pad_y*2)
    pygame.draw.rect(surf, bg, rect, border_radius=radius)
    surf.blit(img, (x + pad_x, y + pad_y))
    return rect

def draw_progress_bar(surf, x, y, w, h, pct, fg=ACCENT, bg=BG4, radius=4):
    pygame.draw.rect(surf, bg, (x, y, w, h), border_radius=radius)
    fill_w = max(0, int(w * min(1.0, pct)))
    if fill_w > 0:
        pygame.draw.rect(surf, fg, (x, y, fill_w, h), border_radius=radius)

def gradient_rect(surf, top_col, bot_col, rect):
    r = pygame.Rect(rect)
    for i in range(r.h):
        t = i / max(r.h - 1, 1)
        c = lerp_color(top_col, bot_col, t)
        pygame.draw.line(surf, c, (r.left, r.top + i), (r.right, r.top + i))

# ──────────────────────────────────────────────
#  BUTTON CLASS
# ──────────────────────────────────────────────
class Button:
    """A fully styled interactive button."""

    def __init__(self, rect, text, font=None,
                 bg=BG3, fg=TEXT, hover_bg=BG4,
                 active_bg=ACCENT, active_fg=BG,
                 border_col=BORDER, radius=10,
                 tag=None):
        self.rect       = pygame.Rect(rect)
        self.text       = text
        self.font       = font or F_MED
        self.bg         = bg
        self.fg         = fg
        self.hover_bg   = hover_bg
        self.active_bg  = active_bg
        self.active_fg  = active_fg
        self.border_col = border_col
        self.radius     = radius
        self.tag        = tag           # arbitrary data
        self.selected   = False
        self.hovered    = False
        self.pressed    = False
        self._anim      = 0.0           # 0-1 hover animation

    def update(self, dt):
        target = 1.0 if (self.hovered or self.selected) else 0.0
        self._anim += (target - self._anim) * min(1.0, dt * 12)

    def handle(self, event):
        """Returns True if clicked."""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed and self.rect.collidepoint(event.pos):
                self.pressed = False
                return True
            self.pressed = False
        return False

    def draw(self, surf):
        t   = self._anim
        bg  = lerp_color(self.bg, self.hover_bg, t)
        if self.selected:
            bg = self.active_bg
        fg  = self.active_fg if self.selected else lerp_color(self.fg, WHITE, t * 0.3)
        bc  = lerp_color(self.border_col, self.active_bg if self.selected else TEXT3, t)

        # press shrink
        r = self.rect.inflate(-4, -2) if self.pressed else self.rect

        pygame.draw.rect(surf, bg, r, border_radius=self.radius)
        pygame.draw.rect(surf, bc, r, 1, border_radius=self.radius)

        # glow when selected
        if self.selected:
            glow = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*self.active_bg, 40), (0, 0, r.w, r.h),
                             border_radius=self.radius)
            surf.blit(glow, r.topleft)

        # multi-line text support
        lines = self.text.split("\n")
        total_h = sum(self.font.get_height() for _ in lines) + (len(lines)-1)*2
        start_y = r.centery - total_h // 2
        for line in lines:
            img = self.font.render(line, True, fg)
            surf.blit(img, (r.centerx - img.get_width()//2, start_y))
            start_y += self.font.get_height() + 2


# ──────────────────────────────────────────────
#  TOAST / FLASH NOTIFICATION
# ──────────────────────────────────────────────
class Toast:
    def __init__(self):
        self.text    = ""
        self.color   = ACCENT
        self.timer   = 0.0
        self.dur     = 0.7
        self.active  = False

    def show(self, text, color=ACCENT, dur=0.7):
        self.text   = text
        self.color  = color
        self.timer  = 0.0
        self.dur    = dur
        self.active = True

    def update(self, dt):
        if self.active:
            self.timer += dt
            if self.timer >= self.dur:
                self.active = False

    def draw(self, surf):
        if not self.active:
            return
        t       = self.timer / self.dur
        alpha   = int(255 * (1 - t) * min(1.0, (1-t)*4))
        scale   = 1.0 + 0.25 * math.sin(t * math.pi)
        font    = F_SCORE
        img_raw = font.render(self.text, True, self.color)
        w0, h0  = img_raw.get_size()
        nw, nh  = int(w0*scale), int(h0*scale)
        if nw < 1 or nh < 1:
            return
        img_sc  = pygame.transform.smoothscale(img_raw, (nw, nh))
        img_sc.set_alpha(alpha)
        surf.blit(img_sc, (W//2 - nw//2, H//2 - 120 - nh//2))


# ──────────────────────────────────────────────
#  GAME DATA
# ──────────────────────────────────────────────
MAX_OVERS   = 5
MAX_WICKETS = 10

TEAMS = {
    "IND": "India",
    "SL":  "Sri Lanka",
    "AUS": "Australia",
    "ENG": "England",
}
TEAM_LIST = list(TEAMS.keys())

VENUES = {
    "Wankhede":     "Mumbai  ·  Wankhede Stadium",
    "Chinnaswamy":  "Bangalore  ·  M. Chinnaswamy",
    "Eden Gardens": "Kolkata  ·  Eden Gardens",
    "Arun Jaitley": "Delhi  ·  Arun Jaitley Stadium",
}
VENUE_LIST = list(VENUES.keys())

SHOT_OUTCOMES = {
    0: [0, 0, 0, 1, "W"],
    1: [0, 1, 1, 1, 2],
    2: [1, 2, 2, 2, 3],
    3: [2, 3, 3, 4, 3],
    4: [3, 4, 4, 6, 4],
    6: [4, 6, 6, 6, "W"],
}

COMMENTARY = {
    0:   ["Dot ball. Tight line and length.",
          "Defended safely back to the bowler.",
          "Played and missed! Big shout!"],
    1:   ["Quick single taken!", "Pushed into the gap — one run."],
    2:   ["Driven into the covers — two runs!", "Two through the gap!"],
    3:   ["Three runs! Deep cover fumbles!"],
    4:   ["FOUR! Beautifully timed drive!",
          "FOUR! Whipped through mid-wicket!",
          "FOUR! Past point — no stopping that!"],
    6:   ["SIX! Cleared the ropes!", "MAXIMUM! Into the stands!",
          "SIX! Upper deck — incredible!"],
    "W": ["OUT! Clean bowled!", "WICKET! Caught behind!",
          "OUT! LBW — plumb in front!", "WICKET! Caught in the deep!"],
}

OVER_RANGES = {
    "Defensive":  (3, 7,  0.08),
    "Balanced":   (5, 11, 0.18),
    "Aggressive": (9, 18, 0.38),
}


# ──────────────────────────────────────────────
#  TEAM (innings data)
# ──────────────────────────────────────────────
class Team:
    def __init__(self, code):
        self.code    = code
        self.name    = TEAMS[code]
        self.score   = 0
        self.wickets = 0
        self.overs   = 0
        self.balls   = 0

    @property
    def total_balls(self):
        return self.overs * 6 + self.balls

    @property
    def crr(self):
        return (self.score * 6 / self.total_balls) if self.total_balls > 0 else 0.0

    def fmt_overs(self):
        return f"{self.overs}.{self.balls}"

    def fmt_score(self):
        return f"{self.score}/{self.wickets}"

    def advance_ball(self):
        """Advance one ball. Returns True if over just completed."""
        self.balls += 1
        if self.balls == 6:
            self.overs += 1
            self.balls  = 0
            return True
        return False

    def innings_over(self):
        return self.wickets >= MAX_WICKETS or self.overs >= MAX_OVERS


# ──────────────────────────────────────────────
#  GAME STATE
# ──────────────────────────────────────────────
class GameState:
    def __init__(self):
        self.player_team  = "IND"
        self.venue        = "Wankhede"
        self.toss_call    = "Head"
        self.mode         = "ball"
        # set after toss
        self.bat1: Team   = None
        self.bat2: Team   = None
        self.innings      = 1
        self.target       = 0
        self.log          = []       # list of (over_str, result, comment)
        self.current_over = []       # results in current over
        self.game_over    = False

    @property
    def opp_team(self):
        choices = [c for c in TEAM_LIST if c != self.player_team]
        return choices[0]

    @property
    def batting_team(self) -> Team:
        return self.bat1 if self.innings == 1 else self.bat2

    def play_ball(self, shot_val):
        """Simulate one ball. Returns (result, comment, over_done)."""
        bat      = self.batting_team
        result   = random.choice(SHOT_OUTCOMES[shot_val])
        key      = "W" if result == "W" else result
        comment  = random.choice(COMMENTARY[key])
        over_tag = bat.fmt_overs()

        if result == "W":
            bat.wickets += 1
        else:
            bat.score += result

        self.current_over.append(result)
        over_done = bat.advance_ball()
        if over_done:
            self.current_over = []

        self.log.append((over_tag, result, comment))
        return result, comment, over_done

    def play_over(self, style):
        """Simulate a full over in over-mode. Returns (runs, wickets)."""
        bat   = self.batting_team
        mn, mx, wkt_ch = OVER_RANGES[style]
        total_runs = 0
        total_wkts = 0

        for _ in range(6):
            over_tag = bat.fmt_overs()
            if random.random() < wkt_ch and bat.wickets + total_wkts < MAX_WICKETS:
                total_wkts += 1
                self.log.append((over_tag, "W", random.choice(COMMENTARY["W"])))
                self.current_over.append("W")
            else:
                r = max(0, random.randint(mn, mx) // 6)
                bat.score  += r
                total_runs += r
                key = min(r, 6)
                self.log.append((over_tag, r, random.choice(COMMENTARY[key])))
                self.current_over.append(r)
            bat.advance_ball()

        bat.wickets += total_wkts
        self.current_over = []
        return total_runs, total_wkts

    def innings_done(self):
        return self.batting_team.innings_over()

    def chase_won(self):
        return self.innings == 2 and self.bat2.score >= self.target


# ──────────────────────────────────────────────
#  BASE SCREEN
# ──────────────────────────────────────────────
class Screen:
    def __init__(self, gs: GameState):
        self.gs      = gs
        self.next    = None   # set to a string to trigger transition
        self.buttons = []
        self.toast   = Toast()

    def handle(self, event):
        for btn in self.buttons:
            if btn.handle(event):
                self.on_button(btn)

    def on_button(self, btn: Button):
        pass

    def update(self, dt):
        for btn in self.buttons:
            btn.update(dt)
        self.toast.update(dt)

    def draw(self, surf):
        surf.fill(BG)
        for btn in self.buttons:
            btn.draw(surf)
        self.toast.draw(surf)

    # helpers
    def _header(self, surf, title, subtitle=""):
        gradient_rect(surf, BG2, BG, (0, 0, W, 90))
        draw_text_mid(surf, title, F_LARGE, TEXT, 32)
        if subtitle:
            draw_text_mid(surf, subtitle, F_SMALL, TEXT3, 58)
        pygame.draw.line(surf, BORDER, (0, 90), (W, 90), 1)
        # accent line
        pygame.draw.line(surf, ACCENT, (0, 0), (W, 0), 2)

    def _footer_hint(self, surf, text):
        pygame.draw.line(surf, BORDER, (0, H-36), (W, H-36), 1)
        draw_text_mid(surf, text, F_TINY, TEXT3, H-22)


# ──────────────────────────────────────────────
#  SCREEN 1 — MENU
# ──────────────────────────────────────────────
class MenuScreen(Screen):
    def __init__(self, gs):
        super().__init__(gs)
        self._sel_team   = TEAM_LIST.index(gs.player_team)
        self._sel_venue  = VENUE_LIST.index(gs.venue)
        self._sel_toss   = 0  # 0=Head 1=Tail
        self._sel_mode   = 0  # 0=ball 1=over
        self._build()

    def _build(self):
        self.buttons = []

        # ── Team buttons (row y=140)
        team_y = 138
        cols   = len(TEAM_LIST)
        bw     = (W - 32 - (cols-1)*8) // cols
        for i, code in enumerate(TEAM_LIST):
            x = 16 + i*(bw+8)
            b = Button((x, team_y, bw, 58),
                       f"{TEAMS[code]}", F_SMALL,
                       tag=("team", i))
            b.selected = (i == self._sel_team)
            self.buttons.append(b)

        # ── Venue buttons (y=264)
        v_y  = 262
        vw   = (W - 32 - 3*8) // 4
        for i, v in enumerate(VENUE_LIST):
            x = 16 + i*(vw+8)
            b = Button((x, v_y, vw, 40),
                       v, F_TINY,
                       active_bg=GOLD, active_fg=BG,
                       tag=("venue", i))
            b.selected = (i == self._sel_venue)
            self.buttons.append(b)

        # ── Toss buttons (y=360)
        t_y = 358
        for i, t in enumerate(["Head", "Tail"]):
            x = 16 + i*((W-40)//2 + 8)
            b = Button((x, t_y, (W-40)//2, 44),
                       f"🪙  {t}", F_MED,
                       active_bg=GOLD, active_fg=BG,
                       tag=("toss", i))
            b.selected = (i == self._sel_toss)
            self.buttons.append(b)

        # ── Mode buttons (y=456)
        m_y = 454
        labels = ["⚾  Ball-by-Ball", "🏃  Over Mode"]
        colors = [BLUE, ACCENT]
        for i, lbl in enumerate(labels):
            x = 16 + i*((W-40)//2 + 8)
            b = Button((x, m_y, (W-40)//2, 52),
                       lbl, F_MED,
                       active_bg=colors[i], active_fg=BG,
                       tag=("mode", i))
            b.selected = (i == self._sel_mode)
            self.buttons.append(b)

        # ── Start button
        b = Button((24, 548, W-48, 60), "▶   START MATCH", F_XL,
                   bg=ACCENT, fg=BG,
                   hover_bg=ACCENT2,
                   active_bg=ACCENT2, active_fg=BG,
                   border_col=ACCENT2, radius=14,
                   tag=("start", 0))
        self.buttons.append(b)

    def _refresh_selected(self, kind):
        for b in self.buttons:
            if b.tag and b.tag[0] == kind:
                idx = b.tag[1]
                if kind == "team":
                    b.selected = (idx == self._sel_team)
                elif kind == "venue":
                    b.selected = (idx == self._sel_venue)
                elif kind == "toss":
                    b.selected = (idx == self._sel_toss)
                elif kind == "mode":
                    b.selected = (idx == self._sel_mode)

    def on_button(self, btn):
        kind, idx = btn.tag
        if kind == "team":
            self._sel_team = idx
            self._refresh_selected("team")
        elif kind == "venue":
            self._sel_venue = idx
            self._refresh_selected("venue")
        elif kind == "toss":
            self._sel_toss = idx
            self._refresh_selected("toss")
        elif kind == "mode":
            self._sel_mode = idx
            self._refresh_selected("mode")
        elif kind == "start":
            self.gs.player_team = TEAM_LIST[self._sel_team]
            self.gs.venue       = VENUE_LIST[self._sel_venue]
            self.gs.toss_call   = ["Head", "Tail"][self._sel_toss]
            self.gs.mode        = ["ball", "over"][self._sel_mode]
            self.next = "toss"

    def draw(self, surf):
        surf.fill(BG)

        # header
        gradient_rect(surf, BG2, BG, (0, 0, W, 110))
        pygame.draw.line(surf, ACCENT, (0, 0), (W, 0), 3)
        draw_text_mid(surf, "🏏  CRICKET SIMULATOR", F_XL, TEXT, 30)
        draw_text_mid(surf, "T20 MATCH ENGINE", F_SMALL, TEXT3, 58)
        draw_text_mid(surf, "Select your preferences below", F_TINY, TEXT3, 80)
        pygame.draw.line(surf, BORDER, (0, 105), (W, 105), 1)

        # section labels
        labels_y = {
            "team":  (116, "TEAM"),
            "venue": (240, "VENUE"),
            "toss":  (334, "TOSS CALL"),
            "mode":  (430, "GAME MODE"),
        }
        for key, (y, lbl) in labels_y.items():
            draw_text(surf, f"◆  {lbl}", F_TINY, TEXT3, 18, y)

        for btn in self.buttons:
            btn.draw(surf)

        self.toast.draw(surf)


# ──────────────────────────────────────────────
#  SCREEN 2 — TOSS
# ──────────────────────────────────────────────
class TossScreen(Screen):
    def __init__(self, gs):
        super().__init__(gs)
        self._phase      = "flip"    # flip | result
        self._anim_t     = 0.0
        self._frames     = ["🪙","●","○","●","○","●","🪙"]
        self._frame_i    = 0
        self._frame_dt   = 0.0
        self._frame_spd  = 0.12
        self._done       = False
        self._result_txt = ""
        self._won        = False
        self._bat_first  = ""
        self._bowl_first = ""

        # Flip button
        self.buttons = [
            Button((W//2-110, 480, 220, 54), "🪙  FLIP THE COIN", F_MED,
                   bg=GOLD, fg=BG, hover_bg=GOLD,
                   active_bg=GOLD, active_fg=BG,
                   border_col=GOLD, radius=30,
                   tag="flip")
        ]
        # proceed (hidden until result)
        self._proceed_btn = Button((W//2-110, 580, 220, 50), "▶  START MATCH", F_MED,
                                   bg=ACCENT, fg=BG, hover_bg=ACCENT2,
                                   active_bg=ACCENT2, active_fg=BG,
                                   border_col=ACCENT, radius=30,
                                   tag="proceed")

    def handle(self, event):
        for btn in self.buttons:
            if btn.handle(event):
                self.on_button(btn)
        if self._done:
            if self._proceed_btn.handle(event):
                self.on_button(self._proceed_btn)

    def on_button(self, btn):
        if btn.tag == "flip" and not self._done:
            self._phase = "animating"
        elif btn.tag == "proceed":
            self.next = "match"

    def update(self, dt):
        super().update(dt)
        self._proceed_btn.update(dt)

        if self._phase == "animating":
            self._frame_dt += dt
            if self._frame_dt >= self._frame_spd:
                self._frame_dt = 0.0
                self._frame_i += 1
                if self._frame_i >= len(self._frames):
                    self._phase  = "result"
                    self._done   = True
                    self._resolve()

    def _resolve(self):
        gs = self.gs
        toss_result = random.choice(["Head", "Tail"])
        won         = (toss_result == gs.toss_call)
        winner_code = gs.player_team if won else gs.opp_team
        decision    = random.choice(["bat", "bowl"])

        self._won        = won
        self._result_txt = f"{'YOU WIN' if won else TEAMS[gs.opp_team]+' WINS'}  THE TOSS!"
        self._decision   = f"{TEAMS[winner_code]} elected to {decision} first"
        self._coin_icon  = "🌝" if toss_result == "Head" else "🌚"

        bat_first  = winner_code if decision == "bat" else gs.opp_team if won else gs.player_team
        bowl_first = gs.opp_team if bat_first == gs.player_team else gs.player_team

        self._bat_first  = bat_first
        self._bowl_first = bowl_first

        gs.bat1    = Team(bat_first)
        gs.bat2    = Team(bowl_first)
        gs.innings = 1

    def draw(self, surf):
        surf.fill(BG)
        gradient_rect(surf, BG2, BG, (0, 0, W, 100))
        pygame.draw.line(surf, GOLD, (0, 0), (W, 0), 3)
        draw_text_mid(surf, "THE TOSS", F_XL, GOLD, 32)
        draw_text_mid(surf, VENUES[self.gs.venue], F_SMALL, TEXT3, 60)
        pygame.draw.line(surf, BORDER, (0, 90), (W, 90), 1)

        # coin
        if self._phase == "animating":
            frame_char = self._frames[min(self._frame_i, len(self._frames)-1)]
            draw_text_mid(surf, frame_char * 4, F_SCORE, GOLD, 250)
        elif self._done:
            draw_text_mid(surf, self._coin_icon, F_SCORE, GOLD, 220)
            # result card
            draw_rect(surf, BG3, (30, 290, W-60, 130), radius=14, border_color=BORDER)
            res_col = ACCENT if self._won else RED
            draw_text_mid(surf, self._result_txt, F_MED, res_col, 320)
            draw_text_mid(surf, self._decision,   F_SMALL, TEXT2, 350)
            draw_text_mid(surf,
                          f"Bat: {TEAMS[self._bat_first]}   Bowl: {TEAMS[self._bowl_first]}",
                          F_SMALL, TEXT3, 378)
            self._proceed_btn.draw(surf)
        else:
            draw_text_mid(surf, "🪙", F_SCORE, GOLD, 250)
            draw_text_mid(surf, "Tap the coin to flip", F_SMALL, TEXT2, 380)
            for btn in self.buttons:
                btn.draw(surf)


# ──────────────────────────────────────────────
#  SCREEN 3 — MATCH
# ──────────────────────────────────────────────
class MatchScreen(Screen):
    def __init__(self, gs):
        super().__init__(gs)
        self._build_buttons()

    def _build_buttons(self):
        self.buttons = []
        gs = self.gs
        if gs.mode == "ball":
            shots  = [(0,"•"), (1,"1"), (2,"2"), (3,"3"), (4,"4"), (6,"6")]
            cols   = len(shots)
            bw     = (W - 32 - (cols-1)*6) // cols
            by     = H - 130
            colors = {4: (GOLD, BG), 6: (ACCENT, BG)}
            for i, (val, lbl) in enumerate(shots):
                x   = 16 + i*(bw+6)
                abg, afg = colors.get(val, (ACCENT, BG))
                b = Button((x, by, bw, 56), lbl, F_XL,
                           bg=BG3, fg=TEXT,
                           active_bg=abg, active_fg=afg,
                           radius=10, tag=val)
                self.buttons.append(b)
        else:
            strats = [
                ("Defensive",  "🛡️\nDefensive\n3-7 runs", BLUE),
                ("Balanced",   "⚖️\nBalanced\n5-11 runs", GOLD),
                ("Aggressive", "🔥\nAggressive\n9-18 runs", ACCENT),
            ]
            bw = (W - 48 - 2*8) // 3
            by = H - 148
            for i, (key, lbl, col) in enumerate(strats):
                x = 16 + i*(bw+8)
                b = Button((x, by, bw, 80), lbl, F_TINY,
                           bg=BG3, fg=TEXT2,
                           active_bg=col, active_fg=BG,
                           radius=12, tag=key)
                self.buttons.append(b)

    def on_button(self, btn):
        gs = self.gs
        if gs.game_over:
            return
        if gs.mode == "ball":
            result, comment, _ = gs.play_ball(btn.tag)
            if result == "W":
                self.toast.show("OUT!", RED, 0.8)
            elif result == 6:
                self.toast.show("SIX!", ACCENT, 0.7)
            elif result == 4:
                self.toast.show("FOUR!", GOLD, 0.7)
        else:
            runs, wkts = gs.play_over(btn.tag)
            self.toast.show(f"+{runs}", ACCENT, 0.7)

        self._check_end()

    def _check_end(self):
        gs = self.gs
        if gs.chase_won():
            gs.game_over = True
            self.next = "result"
            return
        if gs.innings_done():
            if gs.innings == 1:
                self.next = "break"
            else:
                gs.game_over = True
                self.next = "result"

    def draw(self, surf):
        surf.fill(BG)
        gs  = self.gs
        bat = gs.batting_team

        # ── Scoreboard area ──
        gradient_rect(surf, BG2, BG, (0, 0, W, 150))
        pygame.draw.line(surf, ACCENT, (0, 0), (W, 0), 3)

        venue_txt = VENUES[gs.venue]
        draw_text(surf, venue_txt, F_TINY, TEXT3, 12, 10)
        inn_txt = "1st Innings" if gs.innings == 1 else "2nd Innings · CHASE"
        draw_pill(surf, inn_txt, F_TINY, ACCENT, BG4, W-12-90, 7)

        # Big score
        draw_text(surf, bat.name, F_SMALL, TEXT2, 12, 30)
        score_str = bat.fmt_score()
        draw_text(surf, score_str, F_SCORE, TEXT, 12, 46)
        draw_text(surf, f"({bat.fmt_overs()} ov)", F_MED, TEXT2, 12, 106)
        draw_text(surf, f"CRR: {bat.crr:.2f}", F_SMALL, TEXT3, 120, 110)

        pygame.draw.line(surf, BORDER, (0, 145), (W, 145), 1)

        # Chase info
        cy = 148
        if gs.innings == 2:
            need = gs.target - bat.score
            balls_rem = MAX_OVERS*6 - bat.total_balls
            rrr = (need*6/balls_rem) if balls_rem > 0 else 99.99
            draw_text(surf, f"Target: {gs.target}", F_SMALL, GOLD, 12, cy+2)
            draw_text(surf, f"Need {need}  |  RRR {rrr:.2f}", F_SMALL, TEXT2, 150, cy+2)
            pct = bat.score / gs.target
            col = ACCENT if pct < 0.85 else GOLD
            draw_progress_bar(surf, 12, cy+22, W-24, 5, pct, fg=col)
            cy += 36
        else:
            cy += 4

        # ── Over summary ──
        draw_text(surf, "THIS OVER", F_TINY, TEXT3, 12, cy+4)
        ox = 95
        for b in gs.current_over:
            if b == "W":
                bc, fc, ch = RED, WHITE, "W"
            elif b == 6:
                bc, fc, ch = ACCENT, BG, "6"
            elif b == 4:
                bc, fc, ch = GOLD, BG, "4"
            elif b == 0:
                bc, fc, ch = BG4, TEXT3, "·"
            else:
                bc, fc, ch = BG4, BLUE, str(b)
            pygame.draw.rect(surf, bc, (ox, cy, 22, 22), border_radius=4)
            draw_text(surf, ch, F_MONO, fc, ox+11, cy+3, align="center")
            ox += 28
        cy += 30

        # ── Commentary log ──
        pygame.draw.line(surf, BORDER, (0, cy), (W, cy), 1)
        draw_text(surf, "COMMENTARY", F_TINY, TEXT3, 12, cy+4)
        log_y = cy + 22
        max_logs = 6
        visible  = gs.log[-max_logs:] if len(gs.log) >= max_logs else gs.log

        for over_tag, result, comment in reversed(visible):
            if log_y > H - 175:
                break
            row_h = 34
            draw_rect(surf, BG3, (8, log_y, W-16, row_h), radius=6)

            if result == "W":
                dc, dt = RED,   "W"
            elif result == 6:
                dc, dt = ACCENT,"6"
            elif result == 4:
                dc, dt = GOLD,  "4"
            elif result == 0:
                dc, dt = BG4,   "·"
            else:
                dc, dt = BG4, str(result)

            pygame.draw.rect(surf, dc, (14, log_y+5, 24, 24), border_radius=5)
            draw_text(surf, dt, F_MONO, WHITE if result != 0 else TEXT3,
                      26, log_y+8, align="center")
            draw_text(surf, comment, F_SMALL, TEXT2, 46, log_y+9, max_w=W-110)
            draw_text(surf, over_tag, F_MONO_S, TEXT3, W-18, log_y+10, align="right")
            log_y += row_h + 3

        # ── Divider above controls ──
        pygame.draw.line(surf, BORDER, (0, H-160), (W, H-160), 1)
        hint = "Choose your shot" if self.gs.mode == "ball" else "Choose strategy"
        draw_text(surf, hint.upper(), F_TINY, TEXT3, 12, H-152)

        for btn in self.buttons:
            btn.draw(surf)

        self.toast.draw(surf)


# ──────────────────────────────────────────────
#  SCREEN 4 — INNINGS BREAK
# ──────────────────────────────────────────────
class BreakScreen(Screen):
    def __init__(self, gs):
        super().__init__(gs)
        gs.target  = gs.bat1.score + 1
        gs.innings = 2
        gs.bat2    = Team(gs.bat2.code)  # fresh bat2
        gs.current_over = []

        self.buttons = [
            Button((W//2-120, 560, 240, 54), "▶  BEGIN THE CHASE", F_MED,
                   bg=GOLD, fg=BG, hover_bg=GOLD,
                   active_bg=GOLD, active_fg=BG,
                   border_col=GOLD, radius=30, tag="go")
        ]

    def on_button(self, btn):
        if btn.tag == "go":
            self.next = "match"

    def draw(self, surf):
        surf.fill(BG)
        gradient_rect(surf, BG2, BG, (0, 0, W, 100))
        pygame.draw.line(surf, GOLD, (0, 0), (W, 0), 3)
        draw_text_mid(surf, "⚔  INNINGS BREAK", F_XL, GOLD, 35)
        pygame.draw.line(surf, BORDER, (0, 90), (W, 90), 1)

        bat1 = self.gs.bat1
        bat2 = self.gs.bat2

        draw_text_mid(surf, bat1.name + "  innings", F_SMALL, TEXT3, 145)
        draw_text_mid(surf, bat1.fmt_score(), F_XXL, TEXT, 175)
        draw_text_mid(surf, f"({bat1.fmt_overs()} ov)  CRR {bat1.crr:.2f}", F_MED, TEXT2, 225)

        pygame.draw.line(surf, BORDER, (60, 268), (W-60, 268), 1)

        draw_text_mid(surf, f"{bat2.name}  need", F_MED, TEXT2, 295)
        draw_text_mid(surf, str(self.gs.target), F_SCORE, ACCENT, 330)
        draw_text_mid(surf, f"runs to win  in  {MAX_OVERS} overs", F_MED, TEXT2, 395)

        for btn in self.buttons:
            btn.draw(surf)


# ──────────────────────────────────────────────
#  SCREEN 5 — RESULT
# ──────────────────────────────────────────────
class ResultScreen(Screen):
    def __init__(self, gs):
        super().__init__(gs)
        bat1, bat2 = gs.bat1, gs.bat2
        self._won2   = bat2.score >= gs.target
        self._winner = bat2 if self._won2 else bat1
        self._loser  = bat1 if self._won2 else bat2

        if self._won2:
            margin = f"by {MAX_WICKETS - bat2.wickets} wickets"
        else:
            margin = f"by {gs.target - bat2.score - 1} runs"

        self._margin      = margin
        self._player_won  = self._winner.code == gs.player_team

        self.buttons = [
            Button((24, H-136, W-48, 52), "🔄  Play Again", F_MED,
                   bg=ACCENT, fg=BG, hover_bg=ACCENT2,
                   active_bg=ACCENT2, active_fg=BG,
                   border_col=ACCENT2, radius=12, tag="again"),
            Button((24, H-76, W-48, 46), "🏠  Main Menu", F_MED,
                   bg=BG3, fg=TEXT2,
                   radius=12, tag="menu"),
        ]

    def on_button(self, btn):
        if btn.tag == "again":
            self.gs.__init__()
            self.next = "menu"
        elif btn.tag == "menu":
            self.gs.__init__()
            self.next = "menu"

    def draw(self, surf):
        surf.fill(BG)
        gs   = self.gs
        col  = ACCENT if self._player_won else RED
        icon = "🏆" if self._player_won else "💔"

        gradient_rect(surf, BG2, BG, (0, 0, W, 130))
        pygame.draw.line(surf, col, (0, 0), (W, 0), 3)

        draw_text_mid(surf, icon, F_SCORE, col, 38)
        draw_text_mid(surf, f"{self._winner.name.upper()}  WIN!", F_XL, col, 90)
        draw_text_mid(surf, self._margin, F_MED, TEXT2, 120)

        pygame.draw.line(surf, BORDER, (0, 148), (W, 148), 1)

        # Scorecard
        draw_rect(surf, BG3, (20, 160, W-40, 140), radius=12, border_color=BORDER)
        draw_text(surf, "SCORECARD", F_TINY, TEXT3, 36, 172)
        pygame.draw.line(surf, BORDER, (36, 188), (W-36, 188), 1)

        for i, t in enumerate([gs.bat1, gs.bat2]):
            ry       = 196 + i * 46
            is_win   = (t == self._winner)
            tc       = ACCENT if is_win else TEXT2
            prefix   = "🏏  " if is_win else "      "
            bold_f   = F_MED if is_win else F_SMALL
            draw_text(surf, f"{prefix}{t.name}", bold_f, tc, 34, ry)
            draw_text(surf, t.fmt_score(), F_MONO, tc, W-30, ry, align="right")
            draw_text(surf, f"({t.fmt_overs()} ov)", F_MONO_S, TEXT3, W-30, ry+18, align="right")

        draw_text_mid(surf, VENUES[gs.venue], F_SMALL, TEXT3, 325)

        for btn in self.buttons:
            btn.draw(surf)


# ──────────────────────────────────────────────
#  APP LOOP
# ──────────────────────────────────────────────
def build_screen(name: str, gs: GameState) -> Screen:
    return {
        "menu":   MenuScreen,
        "toss":   TossScreen,
        "match":  MatchScreen,
        "break":  BreakScreen,
        "result": ResultScreen,
    }[name](gs)


def main():
    gs      = GameState()
    current = build_screen("menu", gs)

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # ESC to quit from anywhere
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            current.handle(event)

        current.update(dt)
        current.draw(screen)
        pygame.display.flip()

        # Screen transition
        if current.next:
            nxt     = current.next
            current = build_screen(nxt, gs)


if __name__ == "__main__":
    main()