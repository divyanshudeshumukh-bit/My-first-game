"""
╔══════════════════════════════════════════════════════╗
║   🏏  CRICKET SIMULATOR  v5.0  —  pygame edition     ║
║   8 Teams · 8 Venues · In-match mode toggle          ║
╚══════════════════════════════════════════════════════╝
Install:  pip install pygame
Run:      python cricket_v5.py
ESC:      back to menu / quit from menu
"""

import pygame, random, sys, math

# ─────────────────────────────────────────────
#  WINDOW & CLOCK
# ─────────────────────────────────────────────
pygame.init()
W, H   = 500, 860
FPS    = 60
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Cricket Simulator")
clock  = pygame.time.Clock()

# ─────────────────────────────────────────────
#  PALETTE
# ─────────────────────────────────────────────
def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

BG      = hx("060f1e"); BG2  = hx("0c1e35"); BG3  = hx("102845")
BG4     = hx("1b3a5c"); BG5  = hx("22486e")
ACCENT  = hx("00e676"); ACC2 = hx("00c853")
GOLD    = hx("ffd740"); GOLD2= hx("ffab00")
RED     = hx("ff5252"); RED2 = hx("d32f2f")
BLUE    = hx("82b1ff"); PURP = hx("ce93d8")
TEXT    = hx("e8f0fe"); TX2  = hx("90aac8"); TX3 = hx("3f607f")
BORDER  = hx("1a3a5a"); WHITE= (255,255,255); BLACK=(0,0,0)

def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))

# ─────────────────────────────────────────────
#  FONTS
# ─────────────────────────────────────────────
def _sf(size, bold=False):
    for n in ["DejaVu Sans","Arial","Helvetica","FreeSans"]:
        try: return pygame.font.SysFont(n, size, bold=bold)
        except: pass
    return pygame.font.Font(None, size+4)

def _mf(size, bold=False):
    for n in ["DejaVu Sans Mono","Courier New","Courier","FreeMono"]:
        try: return pygame.font.SysFont(n, size, bold=bold)
        except: pass
    return pygame.font.Font(None, size+4)

F_XS   = _sf(11); F_SM = _sf(13); F_MED= _sf(15,True); F_LG = _sf(20,True)
F_XL   = _sf(26,True); F_XXL= _sf(36,True); F_SC = _sf(50,True)
F_MONO = _mf(12,True); F_MOS= _mf(10)

# ─────────────────────────────────────────────
#  DRAW HELPERS
# ─────────────────────────────────────────────
def rr(surf, color, rect, r=8, alpha=None):
    rc = pygame.Rect(rect)
    if alpha is not None:
        s = pygame.Surface((rc.w, rc.h), pygame.SRCALPHA)
        pygame.draw.rect(s, (*color, alpha), (0,0,rc.w,rc.h), border_radius=r)
        surf.blit(s, rc.topleft)
    else:
        pygame.draw.rect(surf, color, rc, border_radius=r)

def rb(surf, color, rect, w=1, r=8):
    pygame.draw.rect(surf, color, pygame.Rect(rect), width=w, border_radius=r)

def txt(surf, t, f, color, x, y, align="left", mw=None):
    s = str(t)
    if mw:
        while f.size(s)[0] > mw and len(s) > 2: s = s[:-1]
        if len(s) < len(str(t)): s = s[:-1]+"…"
    img = f.render(s, True, color)
    rc  = img.get_rect()
    rc.top = int(y)
    if   align=="center": rc.centerx=int(x)
    elif align=="right":  rc.right  =int(x)
    else:                 rc.left   =int(x)
    surf.blit(img, rc)
    return img.get_width()

def txtm(surf, t, f, color, y, mw=None):
    return txt(surf, t, f, color, W//2, y, align="center", mw=mw)

def pill(surf, t, f, fg, bg, cx, y, px=8, py=3, r=20):
    img = f.render(t, True, fg)
    tw,th = img.get_size()
    rx = cx-(tw+px*2)//2
    rr(surf, bg, (rx,y,tw+px*2,th+py*2), r)
    surf.blit(img, (rx+px, y+py))

def prog(surf, x, y, w, h, pct, fg=ACCENT, bg=BG4, r=4):
    rr(surf, bg, (x,y,w,h), r)
    fw = max(0, int(w*min(1.0,max(0.0,pct))))
    if fw > 0: rr(surf, fg, (x,y,fw,h), r)

def grad(surf, tc, bc, rect):
    rc = pygame.Rect(rect)
    for i in range(rc.h):
        t = i/max(rc.h-1,1)
        pygame.draw.line(surf, lerp(tc,bc,t), (rc.left,rc.top+i),(rc.right,rc.top+i))

def glow_line(surf, color, y, w=3, a=160):
    s = pygame.Surface((W, w+4), pygame.SRCALPHA)
    for i in range(w+4):
        al = int(a*math.exp(-0.5*((i-(w+4)//2)/1.5)**2))
        pygame.draw.line(s, (*color, al), (0,i),(W,i))
    surf.blit(s, (0, y-(w+4)//2))

# ─────────────────────────────────────────────
#  BUTTON
# ─────────────────────────────────────────────
class Button:
    def __init__(self, rect, text, f=None,
                 bg=BG3, fg=TEXT, hov=BG4,
                 abg=ACCENT, afg=BG,
                 bc=BORDER, rad=10, tag=None, dis=False):
        self.rect=pygame.Rect(rect); self.text=text; self.f=f or F_MED
        self.bg=bg; self.fg=fg; self.hov=hov; self.abg=abg; self.afg=afg
        self.bc=bc; self.rad=rad; self.tag=tag; self.dis=dis
        self.sel=False; self.hovered=False; self.pressed=False; self._a=0.0

    def update(self, dt):
        if self.dis: self._a=0.0; return
        tgt = 1.0 if (self.hovered or self.sel) else 0.0
        self._a += (tgt-self._a)*min(1.0,dt*12)

    def handle(self, ev):
        if self.dis: return False
        if ev.type==pygame.MOUSEMOTION:
            self.hovered=self.rect.collidepoint(ev.pos)
        if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
            if self.rect.collidepoint(ev.pos): self.pressed=True
        if ev.type==pygame.MOUSEBUTTONUP and ev.button==1:
            if self.pressed and self.rect.collidepoint(ev.pos):
                self.pressed=False; return True
            self.pressed=False
        return False

    def draw(self, surf):
        t = self._a
        if self.dis:
            bg_c=lerp(self.bg,BG,0.5); fg_c=TX3; bc_c=BORDER
        elif self.sel:
            bg_c=self.abg; fg_c=self.afg; bc_c=lerp(self.abg,WHITE,0.3)
        else:
            bg_c=lerp(self.bg,self.hov,t); fg_c=lerp(self.fg,WHITE,t*0.2)
            bc_c=lerp(self.bc,TX3,t*0.5)
        rc = self.rect.inflate(-4,-2) if self.pressed else self.rect
        rr(surf,bg_c,rc,self.rad)
        rb(surf,bc_c,rc,1,self.rad)
        if self.sel and not self.dis: rr(surf,self.abg,rc,self.rad,alpha=30)
        lines=self.text.split("\n")
        lh=self.f.get_height(); tot=lh*len(lines)+2*(len(lines)-1)
        sy=rc.centery-tot//2
        for line in lines:
            img=self.f.render(line,True,fg_c)
            surf.blit(img,(rc.centerx-img.get_width()//2,sy)); sy+=lh+2

# ─────────────────────────────────────────────
#  TOAST
# ─────────────────────────────────────────────
class Toast:
    def __init__(self): self.text=""; self.color=ACCENT; self.timer=0.0; self.dur=0.75; self.active=False
    def show(self,t,c=ACCENT,d=0.75): self.text=t; self.color=c; self.timer=0.0; self.dur=d; self.active=True
    def update(self,dt):
        if self.active:
            self.timer+=dt
            if self.timer>=self.dur: self.active=False
    def draw(self,surf):
        if not self.active: return
        t=self.timer/self.dur; a=int(255*(1-t)*min(1.0,(1-t)*4))
        sc=1.0+0.2*math.sin(t*math.pi)
        img0=F_SC.render(self.text,True,self.color)
        w0,h0=img0.get_size(); nw,nh=max(1,int(w0*sc)),max(1,int(h0*sc))
        imgs=pygame.transform.smoothscale(img0,(nw,nh)); imgs.set_alpha(a)
        surf.blit(imgs,(W//2-nw//2, H//2-140-nh//2))

# ─────────────────────────────────────────────
#  GAME DATA
# ─────────────────────────────────────────────
MAX_OVERS=5; MAX_WICKETS=10

TEAMS={
    "IND":{"name":"India",       "abbr":"IND","color":hx("ff9800")},
    "AUS":{"name":"Australia",   "abbr":"AUS","color":hx("ffeb3b")},
    "ENG":{"name":"England",     "abbr":"ENG","color":hx("5c9bff")},
    "SL": {"name":"Sri Lanka",   "abbr":"SL", "color":hx("4dd0e1")},
    "PAK":{"name":"Pakistan",    "abbr":"PAK","color":hx("69f0ae")},
    "NZ": {"name":"New Zealand", "abbr":"NZ", "color":hx("ef9a9a")},
    "SA": {"name":"S. Africa",   "abbr":"SA", "color":hx("a5d6a7")},
    "WI": {"name":"West Indies", "abbr":"WI", "color":hx("ce93d8")},
}
TEAM_LIST=list(TEAMS.keys())

VENUES={
    "Wankhede":     "Mumbai  ·  Wankhede Stadium",
    "MCG":          "Melbourne  ·  MCG",
    "Lords":        "London  ·  Lord's Cricket Ground",
    "Eden Gardens": "Kolkata  ·  Eden Gardens",
    "Newlands":     "Cape Town  ·  Newlands",
    "Headingley":   "Leeds  ·  Headingley",
    "Gaddafi":      "Lahore  ·  Gaddafi Stadium",
    "SCG":          "Sydney  ·  SCG",
}
VENUE_LIST=list(VENUES.keys())

SHOTS={0:[0,0,0,1,"W"],1:[0,1,1,1,2],2:[1,2,2,2,3],3:[2,3,3,4,3],4:[3,4,4,6,4],6:[4,6,6,6,"W"]}

COMM={
    0:  ["Dot ball. Tight line and length.","Defended back to the bowler.","Played and missed!"],
    1:  ["Quick single to mid-on!","Pushed into the gap — one run.","Clipped off the pads!"],
    2:  ["Driven into covers — two runs!","Two through the gap at point!"],
    3:  ["Three! Deep cover fumbles at the rope!"],
    4:  ["FOUR! Beautifully timed through covers!","FOUR! Whipped through mid-wicket!","FOUR! No stopping that!"],
    6:  ["SIX! Cleared the ropes!","MAXIMUM! Into the upper tier!","SIX! Slog sweep into the stands!"],
    "W":["OUT! Bowled — middle stump flying!","WICKET! Caught behind!","OUT! LBW — plumb in front!",
         "WICKET! Caught in the deep!","OUT! Stumped — miles out!"],
}

OVER_RNG={"Defensive":(3,7,0.08),"Balanced":(5,11,0.18),"Aggressive":(9,18,0.38)}

# ─────────────────────────────────────────────
#  TEAM STATE
# ─────────────────────────────────────────────
class Team:
    def __init__(self,code):
        self.code=code; self.name=TEAMS[code]["name"]; self.abbr=TEAMS[code]["abbr"]
        self.color=TEAMS[code]["color"]; self.score=0; self.wickets=0; self.overs=0; self.balls=0
    @property
    def total_balls(self): return self.overs*6+self.balls
    @property
    def crr(self): return (self.score*6/self.total_balls) if self.total_balls>0 else 0.0
    def fmt_overs(self): return f"{self.overs}.{self.balls}"
    def fmt_score(self): return f"{self.score}/{self.wickets}"
    def advance_ball(self):
        self.balls+=1
        if self.balls==6: self.overs+=1; self.balls=0; return True
        return False
    def innings_over(self): return self.wickets>=MAX_WICKETS or self.overs>=MAX_OVERS

# ─────────────────────────────────────────────
#  GAME STATE
# ─────────────────────────────────────────────
class GS:
    def __init__(self):
        self.player_team="IND"; self.opp_team="AUS"; self.venue="Wankhede"
        self.toss_call="Head"; self.mode="ball"
        self.bat1=None; self.bat2=None; self.innings=1; self.target=0
        self.log=[]; self.current_over=[]; self.game_over=False
    @property
    def batting(self): return self.bat1 if self.innings==1 else self.bat2
    def play_ball(self,shot):
        bat=self.batting; res=random.choice(SHOTS[shot])
        key="W" if res=="W" else res; cmt=random.choice(COMM[key]); tag=bat.fmt_overs()
        if res=="W": bat.wickets+=1
        else: bat.score+=res
        self.current_over.append(res); done=bat.advance_ball()
        if done: self.current_over=[]
        self.log.append((tag,res,cmt)); return res,cmt,done
    def play_over(self,style):
        bat=self.batting; mn,mx,wc=OVER_RNG[style]; runs=0; wkts=0
        for _ in range(6):
            tag=bat.fmt_overs()
            if random.random()<wc and bat.wickets+wkts<MAX_WICKETS:
                wkts+=1; self.log.append((tag,"W",random.choice(COMM["W"]))); self.current_over.append("W")
            else:
                r=max(0,random.randint(mn,mx)//6); bat.score+=r; runs+=r
                self.log.append((tag,r,random.choice(COMM[min(r,6)]))); self.current_over.append(r)
            bat.advance_ball()
        bat.wickets+=wkts; self.current_over=[]; return runs,wkts
    def innings_done(self): return self.batting.innings_over()
    def chase_won(self): return self.innings==2 and self.bat2.score>=self.target

# ─────────────────────────────────────────────
#  BASE SCREEN
# ─────────────────────────────────────────────
class Screen:
    def __init__(self,gs):
        self.gs=gs; self.next=None; self.buttons=[]; self.toast=Toast()
    def handle(self,ev):
        for b in self.buttons:
            if b.handle(ev): self.on_button(b)
    def on_button(self,b): pass
    def update(self,dt):
        for b in self.buttons: b.update(dt)
        self.toast.update(dt)
    def draw(self,surf):
        surf.fill(BG)
        for b in self.buttons: b.draw(surf)
        self.toast.draw(surf)
    def _hdr(self,surf,title,sub="",ac=ACCENT):
        grad(surf,BG2,BG,(0,0,W,100)); glow_line(surf,ac,0,3)
        txtm(surf,title,F_XL,TEXT,28)
        if sub: txtm(surf,sub,F_SM,TX3,58)
        pygame.draw.line(surf,BORDER,(0,96),(W,96),1)
    def _sec(self,surf,label,y):
        txt(surf,f"◆  {label}",F_XS,TX3,18,y)
    def _foot(self,surf,t):
        pygame.draw.line(surf,BORDER,(0,H-34),(W,H-34),1); txtm(surf,t,F_XS,TX3,H-20)

# ═══════════════════════════════════════════
#  MENU SCREEN
# ═══════════════════════════════════════════
class MenuScreen(Screen):
    def __init__(self,gs):
        super().__init__(gs)
        self._my  = TEAM_LIST.index(gs.player_team)
        self._opp = TEAM_LIST.index(gs.opp_team)
        self._ven = VENUE_LIST.index(gs.venue)
        self._tos = 0 if gs.toss_call=="Head" else 1
        self._mod = 0 if gs.mode=="ball" else 1
        self._mb=[]; self._ob=[]; self._vb=[]; self._tb=[]; self._xb=[]
        self._build()

    def _build(self):
        self.buttons=[]; P=14; G=6
        cols=4; bw=(W-P*2-(cols-1)*G)//cols; bh=44
        # MY TEAM
        y0=118
        for idx in range(8):
            r,c=divmod(idx,cols); code=TEAM_LIST[idx]
            tc=TEAMS[code]["color"]
            x=P+c*(bw+G); y=y0+r*(bh+G)
            b=Button((x,y,bw,bh), f"{TEAMS[code]['abbr']}\n{TEAMS[code]['name']}",
                     F_XS, bg=BG3,fg=TX2,hov=BG4,abg=tc,afg=BG,rad=10,tag=("mt",idx))
            b.sel=(idx==self._my); self._mb.append(b); self.buttons.append(b)
        # OPP TEAM
        y1=y0+2*(bh+G)+42
        for idx in range(8):
            r,c=divmod(idx,cols); code=TEAM_LIST[idx]
            tc=TEAMS[code]["color"]
            x=P+c*(bw+G); y=y1+r*(bh+G)
            b=Button((x,y,bw,bh), f"{TEAMS[code]['abbr']}\n{TEAMS[code]['name']}",
                     F_XS, bg=BG3,fg=TX2,hov=BG4,abg=tc,afg=BG,rad=10,tag=("ot",idx))
            b.sel=(idx==self._opp); self._ob.append(b); self.buttons.append(b)
        # VENUE (2 rows x 4)
        yv=y1+2*(bh+G)+42
        vw=(W-P*2-(cols-1)*G)//cols; vh=34
        for i,v in enumerate(VENUE_LIST):
            r,c=divmod(i,cols); x=P+c*(vw+G); y=yv+r*(vh+G)
            b=Button((x,y,vw,vh),v,F_XS,abg=GOLD,afg=BG,rad=8,tag=("vn",i))
            b.sel=(i==self._ven); self._vb.append(b); self.buttons.append(b)
        # TOSS
        yt=yv+2*(vh+G)+42; hw=(W-P*2-G)//2
        for i,(lbl,col) in enumerate([("☀  HEAD",GOLD),("☾  TAIL",PURP)]):
            x=P+i*(hw+G)
            b=Button((x,yt,hw,46),lbl,F_MED,abg=col,afg=BG,rad=30,tag=("ts",i))
            b.sel=(i==self._tos); self._tb.append(b); self.buttons.append(b)
        # MODE
        ym=yt+46+36
        for i,(lbl,col) in enumerate([("⚾  Ball-by-Ball",BLUE),("🏃  Over Mode",ACCENT)]):
            x=P+i*(hw+G)
            b=Button((x,ym,hw,50),lbl,F_MED,abg=col,afg=BG,rad=10,tag=("md",i))
            b.sel=(i==self._mod); self._xb.append(b); self.buttons.append(b)
        # START
        ys=ym+50+20
        b=Button((P,ys,W-P*2,56),"▶   FLIP THE COIN",F_XL,
                 bg=ACCENT,fg=BG,hov=ACC2,abg=ACC2,afg=BG,bc=ACC2,rad=14,tag=("go",0))
        self.buttons.append(b)
        self._ys=ys

    def _resel(self,kind):
        for b in self.buttons:
            if b.tag and b.tag[0]==kind:
                i=b.tag[1]
                if   kind=="mt": b.sel=(i==self._my)
                elif kind=="ot": b.sel=(i==self._opp)
                elif kind=="vn": b.sel=(i==self._ven)
                elif kind=="ts": b.sel=(i==self._tos)
                elif kind=="md": b.sel=(i==self._mod)
        # disable mirror entries
        for b in self._mb: b.dis=(b.tag[1]==self._opp)
        for b in self._ob: b.dis=(b.tag[1]==self._my)

    def on_button(self,btn):
        k,i=btn.tag
        if k=="mt":
            if i==self._opp: self.toast.show("Already opposition!",RED,1.0); return
            self._my=i; self._resel("mt")
        elif k=="ot":
            if i==self._my: self.toast.show("Already your team!",RED,1.0); return
            self._opp=i; self._resel("ot")
        elif k=="vn": self._ven=i; self._resel("vn")
        elif k=="ts": self._tos=i; self._resel("ts")
        elif k=="md": self._mod=i; self._resel("md")
        elif k=="go":
            self.gs.player_team=TEAM_LIST[self._my]; self.gs.opp_team=TEAM_LIST[self._opp]
            self.gs.venue=VENUE_LIST[self._ven]; self.gs.toss_call=["Head","Tail"][self._tos]
            self.gs.mode=["ball","over"][self._mod]; self.next="toss"

    def update(self,dt):
        super().update(dt)
        for b in self._mb: b.dis=(b.tag[1]==self._opp)
        for b in self._ob: b.dis=(b.tag[1]==self._my)

    def draw(self,surf):
        surf.fill(BG); grad(surf,BG2,BG,(0,0,W,100)); glow_line(surf,ACCENT,0,3)
        txtm(surf,"CRICKET SIMULATOR",F_XL,TEXT,22)
        txtm(surf,"T20 MATCH ENGINE  —  SELECT PREFERENCES",F_XS,TX3,52)
        pygame.draw.line(surf,BORDER,(0,96),(W,96),1)

        P=14; G=6; cols=4; bh=44; bw=(W-P*2-(cols-1)*G)//cols
        vh=34; vw=(W-P*2-(cols-1)*G)//cols
        y0=118; y1=y0+2*(bh+G)+42; yv=y1+2*(bh+G)+42; yt=yv+2*(vh+G)+42; ym=yt+46+36

        self._sec(surf,"YOUR TEAM",     y0-16)
        self._sec(surf,"OPPOSITION",    y1-16)
        self._sec(surf,"VENUE",         yv-16)
        self._sec(surf,"TOSS CALL",     yt-18)
        self._sec(surf,"GAME MODE",     ym-18)

        if self._my==self._opp:
            txtm(surf,"⚠ Both teams are the same! Pick different teams.",F_XS,RED,self._ys-14)

        for b in self.buttons: b.draw(surf)
        self.toast.draw(surf)
        self._foot(surf,"ESC to quit")

# ═══════════════════════════════════════════
#  TOSS SCREEN
# ═══════════════════════════════════════════
class TossScreen(Screen):
    def __init__(self,gs):
        super().__init__(gs)
        self._phase="idle"; self._ft=0.0; self._fi=0; self._done=False
        self._won=False; self._icon="☀"; self._rtxt=""; self._dtxt=""
        self._bf=""; self._wf=""; self._t=0.0
        self._frames=["☀","◑","☾","◐","☀","◑","☾","◐","☀","◑","☾"]
        self.buttons=[
            Button((W//2-120,500,240,52),"☀  FLIP THE COIN  ☾",F_MED,
                   bg=GOLD,fg=BG,hov=GOLD2,abg=GOLD2,afg=BG,bc=GOLD,rad=30,tag="flip")
        ]
        self._pb=Button((W//2-120,598,240,50),"▶  START MATCH",F_MED,
                        bg=ACCENT,fg=BG,hov=ACC2,abg=ACC2,afg=BG,bc=ACCENT,rad=30,tag="go")

    def handle(self,ev):
        for b in self.buttons:
            if b.handle(ev): self.on_button(b)
        if self._done and self._pb.handle(ev): self.on_button(self._pb)

    def on_button(self,b):
        if b.tag=="flip" and not self._done: self._phase="spin"
        elif b.tag=="go": self.next="match"

    def update(self,dt):
        super().update(dt); self._pb.update(dt); self._t+=dt
        if self._phase=="spin":
            self._ft+=dt
            if self._ft>=0.11:
                self._ft=0.0; self._fi+=1
                if self._fi>=len(self._frames):
                    self._phase="result"; self._done=True; self._resolve()

    def _resolve(self):
        gs=self.gs; res=random.choice(["Head","Tail"]); won=(res==gs.toss_call)
        wc=gs.player_team if won else gs.opp_team
        dec=random.choice(["bat","bowl"])
        self._won=won; self._icon="☀" if res=="Head" else "☾"
        self._rtxt="YOU WIN THE TOSS!" if won else f"{TEAMS[gs.opp_team]['name'].upper()} WIN!"
        self._dtxt=f"{TEAMS[wc]['name']} elected to {dec} first"
        bf = wc if dec=="bat" else (gs.opp_team if won else gs.player_team)
        wf = gs.opp_team if bf==gs.player_team else gs.player_team
        self._bf=bf; self._wf=wf
        gs.bat1=Team(bf); gs.bat2=Team(wf); gs.innings=1

    def draw(self,surf):
        surf.fill(BG); self._hdr(surf,"THE TOSS",VENUES[self.gs.venue],GOLD)
        cx=W//2; cy=290
        if self._phase=="idle":
            pygame.draw.circle(surf,GOLD,(cx,cy),64); pygame.draw.circle(surf,lerp(GOLD,WHITE,0.25),(cx,cy),64,3)
            txtm(surf,"☀",F_XXL,BG,cy-26); txtm(surf,"HEAD",F_XS,BG,cy+14)
            txtm(surf,"Click button to flip the coin",F_SM,TX2,cy+90)
            for b in self.buttons: b.draw(surf)
        elif self._phase=="spin":
            p=1.0+0.15*math.sin(self._t*22); r=int(64*p)
            c=lerp(GOLD,PURP,(math.sin(self._t*9)+1)/2)
            pygame.draw.circle(surf,c,(cx,cy),r); pygame.draw.circle(surf,WHITE,(cx,cy),r,2)
            fi=min(self._fi,len(self._frames)-1); txtm(surf,self._frames[fi],F_XXL,BG,cy-26)
            txtm(surf,"Flipping…",F_SM,TX2,cy+90)
        else:
            rc=ACCENT if self._won else RED
            rr(surf,rc,(cx-68,cy-68,136,136),68,alpha=30)
            pygame.draw.circle(surf,rc,(cx,cy),64,3)
            txtm(surf,self._icon,F_XXL,rc,cy-26)
            rr(surf,BG3,(24,cy+90,W-48,150),14); rb(surf,BORDER,(24,cy+90,W-48,150),1,14)
            txtm(surf,self._rtxt,F_MED,rc,cy+106)
            txtm(surf,self._dtxt,F_SM,TX2,cy+136)
            txtm(surf,f"Bat: {TEAMS[self._bf]['name']}   Bowl: {TEAMS[self._wf]['name']}",F_SM,TX3,cy+162)
            self._pb.draw(surf)

# ═══════════════════════════════════════════
#  MATCH SCREEN
# ═══════════════════════════════════════════
class MatchScreen(Screen):
    def __init__(self,gs):
        super().__init__(gs)
        self._sb=self._shot_btns(); self._ob=self._over_btns()
        self._toggle=self._mode_toggle()

    def _shot_btns(self):
        shots=[(0,"•"),(1,"1"),(2,"2"),(3,"3"),(4,"4"),(6,"6")]
        P=12; bw=(W-P*2-5*6)//6; by=H-134; cl={4:(GOLD,BG),6:(ACCENT,BG)}
        bs=[]
        for i,(v,l) in enumerate(shots):
            x=P+i*(bw+6); abg,afg=cl.get(v,(ACCENT,BG))
            bs.append(Button((x,by,bw,58),l,F_XL,bg=BG3,fg=TEXT,abg=abg,afg=afg,rad=10,tag=("s",v)))
        return bs

    def _over_btns(self):
        data=[("Defensive","🛡\nDefensive\n3-7",BLUE),("Balanced","⚖\nBalanced\n5-11",GOLD),
              ("Aggressive","🔥\nAggressive\n9-18",ACCENT)]
        bw=(W-32-16)//3; by=H-152; bs=[]
        for i,(k,l,c) in enumerate(data):
            x=16+i*(bw+8)
            bs.append(Button((x,by,bw,86),l,F_XS,bg=BG3,fg=TX2,abg=c,afg=BG,rad=12,tag=("o",k)))
        return bs

    def _mode_toggle(self):
        bs=[]
        for i,(v,l) in enumerate([("ball","B·B"),("over","OVR")]):
            b=Button((W-82+i*38,8,34,22),l,F_XS,bg=BG4,fg=TX3,abg=BLUE,afg=BG,rad=6,tag=("mt",v))
            b.sel=(self.gs.mode==v); bs.append(b)
        return bs

    @property
    def _play_btns(self): return self._sb if self.gs.mode=="ball" else self._ob

    def handle(self,ev):
        for b in self._toggle:
            if b.handle(ev):
                self.gs.mode=b.tag[1]
                for tb in self._toggle: tb.sel=(tb.tag[1]==self.gs.mode)
                return
        for b in self._play_btns:
            if b.handle(ev): self.on_button(b)

    def on_button(self,btn):
        gs=self.gs
        if gs.game_over: return
        k=btn.tag[0]
        if k=="s":
            res,_,__=gs.play_ball(btn.tag[1])
            if res=="W": self.toast.show("OUT!",RED,0.8)
            elif res==6: self.toast.show("SIX!",ACCENT,0.7)
            elif res==4: self.toast.show("FOUR!",GOLD,0.7)
        elif k=="o":
            r,w=gs.play_over(btn.tag[1])
            self.toast.show(f"+{r}"+(" 💀"*min(w,2)),ACCENT,0.8)
        self._chk()

    def _chk(self):
        gs=self.gs
        if gs.chase_won(): gs.game_over=True; self.next="result"; return
        if gs.innings_done():
            if gs.innings==1: self.next="break"
            else: gs.game_over=True; self.next="result"

    def update(self,dt):
        self.toast.update(dt)
        for b in self._toggle+self._play_btns: b.update(dt)

    def draw(self,surf):
        surf.fill(BG); gs=self.gs; bat=gs.batting
        grad(surf,BG2,BG,(0,0,W,152)); glow_line(surf,bat.color,0,3)

        # scoreboard
        txt(surf,VENUES[gs.venue],F_XS,TX3,12,10)
        inn="1st INNINGS" if gs.innings==1 else "2nd INNINGS · CHASE"
        pill(surf,inn,F_XS,ACCENT,BG4,W-70,7,px=8,py=3)
        for b in self._toggle: b.draw(surf)
        txt(surf,bat.name,F_SM,bat.color,12,32)
        txt(surf,bat.fmt_score(),F_SC,TEXT,12,48)
        txt(surf,f"({bat.fmt_overs()} ov)",F_MED,TX2,12,108)
        txt(surf,f"CRR {bat.crr:.2f}",F_SM,TX3,140,112)
        pygame.draw.line(surf,BORDER,(0,148),(W,148),1)

        cy=152
        if gs.innings==2:
            need=gs.target-bat.score; bl=MAX_OVERS*6-bat.total_balls
            rrr=(need*6/bl) if bl>0 else 99.99
            rc=ACCENT if rrr<9 else (GOLD if rrr<13 else RED)
            txt(surf,f"Target: {gs.target}",F_SM,GOLD,12,cy+2)
            txt(surf,f"Need {need}  |  RRR {rrr:.2f}",F_SM,rc,160,cy+2)
            bc=ACCENT if bat.score/max(1,gs.target)<0.85 else GOLD
            prog(surf,12,cy+22,W-24,5,bat.score/max(1,gs.target),fg=bc)
            cy+=32
        else: cy+=4

        # this over
        txt(surf,"THIS OVER",F_XS,TX3,12,cy+4); ox=94
        for b in gs.current_over:
            if b=="W": bc,fc,ch=RED,WHITE,"W"
            elif b==6: bc,fc,ch=ACCENT,BG,"6"
            elif b==4: bc,fc,ch=GOLD,BG,"4"
            elif b==0: bc,fc,ch=BG4,TX3,"·"
            else: bc,fc,ch=BG4,BLUE,str(b)
            pygame.draw.rect(surf,bc,(ox,cy,24,22),border_radius=4)
            txt(surf,ch,F_MONO,fc,ox+12,cy+3,align="center"); ox+=30
        cy+=32

        # commentary
        pygame.draw.line(surf,BORDER,(0,cy),(W,cy),1)
        txt(surf,"COMMENTARY",F_XS,TX3,12,cy+4); ly=cy+22; ml=6
        for tag,res,cmt in reversed(gs.log[-ml:]):
            if ly>H-178: break
            rr(surf,BG3,(8,ly,W-16,34),6)
            if res=="W": dc,dt_="W",RED
            elif res==6: dc,dt_="6",ACCENT
            elif res==4: dc,dt_="4",GOLD
            elif res==0: dc,dt_="·",BG4
            else: dc,dt_=str(res),BG4
            pygame.draw.rect(surf,dt_,(14,ly+5,24,24),border_radius=5)
            txt(surf,dc,F_MONO,WHITE if res!=0 else TX3,26,ly+8,align="center")
            txt(surf,cmt,F_SM,TX2,46,ly+9,mw=W-108)
            txt(surf,tag,F_MOS,TX3,W-18,ly+11,align="right")
            ly+=37

        pygame.draw.line(surf,BORDER,(0,H-162),(W,H-162),1)
        hl="CHOOSE YOUR SHOT" if gs.mode=="ball" else "CHOOSE STRATEGY"
        txt(surf,hl,F_XS,TX3,12,H-153)
        for b in self._play_btns: b.draw(surf)
        self.toast.draw(surf)

# ═══════════════════════════════════════════
#  INNINGS BREAK
# ═══════════════════════════════════════════
class BreakScreen(Screen):
    def __init__(self,gs):
        super().__init__(gs)
        gs.target=gs.bat1.score+1; gs.innings=2
        gs.bat2=Team(gs.bat2.code); gs.current_over=[]
        self._t=0.0
        self.buttons=[Button((W//2-130,570,260,54),"▶  BEGIN THE CHASE",F_MED,
                              bg=GOLD,fg=BG,hov=GOLD2,abg=GOLD2,afg=BG,bc=GOLD,rad=30,tag="go")]
    def on_button(self,b):
        if b.tag=="go": self.next="match"
    def update(self,dt): super().update(dt); self._t+=dt
    def draw(self,surf):
        surf.fill(BG); self._hdr(surf,"INNINGS BREAK",ac=GOLD)
        b1=self.gs.bat1; b2=self.gs.bat2
        rr(surf,BG3,(20,112,W-40,100),12); rb(surf,BORDER,(20,112,W-40,100),1,12)
        txtm(surf,b1.name+" innings",F_SM,TX3,122)
        txtm(surf,b1.fmt_score(),F_XXL,b1.color,144)
        txtm(surf,f"({b1.fmt_overs()} ov)  CRR {b1.crr:.2f}",F_MED,TX2,186)
        pygame.draw.line(surf,BORDER,(60,222),(W-60,222),1)
        rr(surf,BG3,(20,234,W-40,178),12); rb(surf,ACCENT,(20,234,W-40,178),1,12)
        txtm(surf,b2.name+" need",F_MED,TX2,252)
        p=1.0+0.04*math.sin(self._t*3.5)
        ts=F_SC.render(str(self.gs.target),True,ACCENT); tw,th=ts.get_size()
        nw,nh=max(1,int(tw*p)),max(1,int(th*p))
        ts2=pygame.transform.smoothscale(ts,(nw,nh)); surf.blit(ts2,(W//2-nw//2,286))
        txtm(surf,f"runs to win in {MAX_OVERS} overs",F_MED,TX2,358)
        bl=MAX_OVERS*6; rrr=self.gs.target*6/bl
        txtm(surf,f"Required Rate: {rrr:.2f}",F_SM,TX3,390)
        for b in self.buttons: b.draw(surf)

# ═══════════════════════════════════════════
#  RESULT SCREEN
# ═══════════════════════════════════════════
class ResultScreen(Screen):
    def __init__(self,gs):
        super().__init__(gs)
        b1,b2=gs.bat1,gs.bat2; self._t=0.0
        self._w2=b2.score>=gs.target
        self._win=b2 if self._w2 else b1
        self._pw=(self._win.code==gs.player_team)
        self._mg=f"by {MAX_WICKETS-b2.wickets} wickets" if self._w2 else f"by {gs.target-b2.score-1} runs"
        self.buttons=[
            Button((20,H-138,W-40,52),"🔄  Play Again",F_MED,bg=ACCENT,fg=BG,hov=ACC2,abg=ACC2,afg=BG,bc=ACC2,rad=12,tag="a"),
            Button((20,H-76, W-40,46),"🏠  Main Menu", F_MED,bg=BG3,fg=TX2,rad=12,tag="m"),
        ]
    def on_button(self,b):
        if b.tag in("a","m"): self.gs.__init__(); self.next="menu"
    def update(self,dt): super().update(dt); self._t+=dt
    def draw(self,surf):
        surf.fill(BG); gs=self.gs; rc=ACCENT if self._pw else RED
        grad(surf,BG2,BG,(0,0,W,140)); glow_line(surf,rc,0,3)
        bounce=int(5*math.sin(self._t*2.8))
        icon="🏆" if self._pw else "💔"
        im=F_SC.render(icon,True,rc); surf.blit(im,(W//2-im.get_width()//2,18+bounce))
        txtm(surf,f"{self._win.name.upper()}  WIN!",F_XL,rc,82)
        txtm(surf,self._mg,F_MED,TX2,114)
        pygame.draw.line(surf,BORDER,(0,148),(W,148),1)
        rr(surf,BG3,(20,160,W-40,170),12); rb(surf,BORDER,(20,160,W-40,170),1,12)
        txt(surf,"SCORECARD",F_XS,TX3,36,172)
        pygame.draw.line(surf,BORDER,(36,188),(W-36,188),1)
        for i,t in enumerate([gs.bat1,gs.bat2]):
            ry=196+i*62; iw=(t==self._win); tc=t.color if iw else TX2
            bf=F_MED if iw else F_SM; pr="🏏  " if iw else "     "
            txt(surf,f"{pr}{t.name}",bf,tc,34,ry)
            txt(surf,t.fmt_score(),F_MONO,tc,W-30,ry,align="right")
            txt(surf,f"({t.fmt_overs()} ov)  CRR {t.crr:.2f}",F_MOS,TX3,W-30,ry+20,align="right")
            if i==0: pygame.draw.line(surf,BORDER,(34,ry+54),(W-34,ry+54),1)
        txtm(surf,VENUES[gs.venue],F_SM,TX3,348)
        for b in self.buttons: b.draw(surf)

# ─────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────
SCREENS={"menu":MenuScreen,"toss":TossScreen,"match":MatchScreen,"break":BreakScreen,"result":ResultScreen}

def main():
    gs=GS(); cur=MenuScreen(gs)
    while True:
        dt=clock.tick(FPS)/1000.0
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE:
                if isinstance(cur,MenuScreen): pygame.quit(); sys.exit()
                else: gs.__init__(); cur=MenuScreen(gs); continue
            cur.handle(ev)
        cur.update(dt); cur.draw(screen); pygame.display.flip()
        if cur.next: cur=SCREENS[cur.next](gs)

if __name__=="__main__":
    main()
