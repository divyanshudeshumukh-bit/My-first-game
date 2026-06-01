"""
╔══════════════════════════════════════════════════════════╗
║   🏏  CRICKET SIMULATOR  v6.0  —  Full Upgrade          ║
║   Carousel · 20 Venues · Batting/Bowling modes           ║
║   Glassmorphism UI · Animations · Realistic engine       ║
╚══════════════════════════════════════════════════════════╝
Install:  pip install pygame
Run:      python cricket_v6.py
"""

import pygame, random, sys, math
pygame.init()

# ───────────────────────────────────────────────────────────
#  WINDOW
# ───────────────────────────────────────────────────────────
W, H   = 480, 860
FPS    = 60
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Cricket Simulator v6")
clock  = pygame.time.Clock()

# ───────────────────────────────────────────────────────────
#  PALETTE
# ───────────────────────────────────────────────────────────
def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

BG      = hx("070e1c"); BG2 = hx("0b1a2e"); BG3 = hx("0f2540")
BG4     = hx("163050"); BG5 = hx("1e3f65")
ACCENT  = hx("00e676"); ACC2= hx("00c853"); ACC3= hx("b9f6ca")
GOLD    = hx("ffd740"); GLD2= hx("ffab00"); GLD3= hx("fff9c4")
RED     = hx("ff5252"); RED2= hx("b71c1c")
BLUE    = hx("448aff"); BL2 = hx("82b1ff")
PURP    = hx("ce93d8"); CYN = hx("4dd0e1")
TEXT    = hx("eef2ff"); TX2 = hx("90aac8"); TX3 = hx("3d5a7a")
BORDER  = hx("1a3a5a"); WHT = (255,255,255); BLK = (0,0,0)

# Batting / Bowling theme colors
BAT_THEME  = hx("003720")   # dark green tint for batting bg
BOWL_THEME = hx("1a0a00")   # dark red tint for bowling bg

def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))

def with_a(col, a):
    return (*col, int(a))

# ───────────────────────────────────────────────────────────
#  FONTS
# ───────────────────────────────────────────────────────────
_fc = {}
def _sf(sz, bold=False):
    k=(sz,bold)
    if k not in _fc:
        for n in ["DejaVu Sans","Arial","Helvetica","FreeSans"]:
            try: _fc[k]=pygame.font.SysFont(n,sz,bold=bold); break
            except: pass
        else: _fc[k]=pygame.font.Font(None,sz+4)
    return _fc[k]

def _mf(sz, bold=False):
    k=("m",sz,bold)
    if k not in _fc:
        for n in ["DejaVu Sans Mono","Courier New","Courier"]:
            try: _fc[k]=pygame.font.SysFont(n,sz,bold=bold); break
            except: pass
        else: _fc[k]=pygame.font.Font(None,sz+4)
    return _fc[k]

F_XS=_sf(11); F_SM=_sf(13); F_MD=_sf(15,True); F_LG=_sf(20,True)
F_XL=_sf(26,True); F_XXL=_sf(38,True); F_SC=_sf(52,True); F_BIG=_sf(64,True)
F_MO=_mf(12,True); F_MOS=_mf(10)

# ───────────────────────────────────────────────────────────
#  DRAW HELPERS
# ───────────────────────────────────────────────────────────
def rr(surf, col, rect, r=10, alpha=None):
    rc=pygame.Rect(rect)
    if rc.w<1 or rc.h<1: return
    if alpha is not None:
        s=pygame.Surface((rc.w,rc.h),pygame.SRCALPHA)
        pygame.draw.rect(s,(*col,int(alpha)),(0,0,rc.w,rc.h),border_radius=r)
        surf.blit(s,rc.topleft)
    else:
        pygame.draw.rect(surf,col,rc,border_radius=r)

def rb(surf,col,rect,w=1,r=10):
    pygame.draw.rect(surf,col,pygame.Rect(rect),width=w,border_radius=r)

def circle_a(surf, col, cx, cy, radius, alpha=200):
    s=pygame.Surface((radius*2,radius*2),pygame.SRCALPHA)
    pygame.draw.circle(s,(*col,int(alpha)),(radius,radius),radius)
    surf.blit(s,(cx-radius,cy-radius))

def txt(surf,t,f,col,x,y,align="left",mw=None):
    s=str(t)
    if mw:
        while f.size(s)[0]>mw and len(s)>2: s=s[:-1]
        if len(s)<len(str(t)): s=s[:-1]+"…"
    img=f.render(s,True,col)
    rc=img.get_rect(); rc.top=int(y)
    if   align=="center": rc.centerx=int(x)
    elif align=="right":  rc.right=int(x)
    else:                 rc.left=int(x)
    surf.blit(img,rc); return img.get_width()

def txtm(surf,t,f,col,y,mw=None):
    return txt(surf,t,f,col,W//2,y,align="center",mw=mw)

def grad(surf,tc,bc,rect):
    rc=pygame.Rect(rect)
    if rc.h<1: return
    for i in range(rc.h):
        t=i/max(rc.h-1,1)
        pygame.draw.line(surf,lerp(tc,bc,t),(rc.left,rc.top+i),(rc.right,rc.top+i))

def glow(surf,col,y,w=3,a=180):
    s=pygame.Surface((W,w+6),pygame.SRCALPHA)
    for i in range(w+6):
        al=int(a*math.exp(-0.5*((i-(w+6)//2)/1.8)**2))
        pygame.draw.line(s,(*col,al),(0,i),(W,i))
    surf.blit(s,(0,y-(w+6)//2))

def glass_card(surf, rect, col=BG3, border=BORDER, alpha=200, radius=16):
    """Glassmorphism-style card."""
    rr(surf, col, rect, radius, alpha=alpha)
    rb(surf, (*border,120), rect, 1, radius)

def draw_shadow(surf, rect, radius=16, spread=8, alpha=80):
    """Drop shadow under a card."""
    sr=(rect[0]-spread//2, rect[1]+spread//2, rect[2]+spread, rect[3]+spread//2)
    rr(surf, BLK, sr, radius+2, alpha=alpha)

# ───────────────────────────────────────────────────────────
#  BUTTON
# ───────────────────────────────────────────────────────────
class Button:
    def __init__(self, rect, text, f=None,
                 bg=BG4, fg=TEXT, hov=BG5,
                 abg=ACCENT, afg=BLK,
                 bc=BORDER, rad=12, tag=None, dis=False):
        self.rect=pygame.Rect(rect); self.text=text; self.f=f or F_MD
        self.bg=bg; self.fg=fg; self.hov=hov; self.abg=abg; self.afg=afg
        self.bc=bc; self.rad=rad; self.tag=tag; self.dis=dis
        self.sel=False; self.hovered=False; self.pressed=False; self._a=0.0

    def update(self,dt):
        if self.dis: self._a=0.0; return
        tgt=1.0 if (self.hovered or self.sel) else 0.0
        self._a+=(tgt-self._a)*min(1.0,dt*14)

    def handle(self,ev):
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

    def draw(self,surf):
        t=self._a
        if self.dis:
            bgc=lerp(self.bg,BG,0.6); fgc=TX3; bcc=BORDER
        elif self.sel:
            bgc=self.abg; fgc=self.afg; bcc=lerp(self.abg,WHT,0.4)
        else:
            bgc=lerp(self.bg,self.hov,t); fgc=lerp(self.fg,WHT,t*0.2)
            bcc=lerp(self.bc,TX2,t*0.5)
        rc=self.rect.inflate(-4,-2) if self.pressed else self.rect
        rr(surf,bgc,rc,self.rad)
        rb(surf,bcc,rc,1,self.rad)
        if self.sel: rr(surf,self.abg,rc,self.rad,alpha=28)
        lines=self.text.split("\n"); lh=self.f.get_height()
        tot=lh*len(lines)+2*(len(lines)-1); sy=rc.centery-tot//2
        for line in lines:
            img=self.f.render(line,True,fgc)
            surf.blit(img,(rc.centerx-img.get_width()//2,sy)); sy+=lh+2

# ───────────────────────────────────────────────────────────
#  TOAST
# ───────────────────────────────────────────────────────────
class Toast:
    def __init__(self): self.text=""; self.col=ACCENT; self.timer=0.0; self.dur=0.8; self.on=False
    def show(self,t,c=ACCENT,d=0.8): self.text=t; self.col=c; self.timer=0.0; self.dur=d; self.on=True
    def update(self,dt):
        if self.on:
            self.timer+=dt
            if self.timer>=self.dur: self.on=False
    def draw(self,surf):
        if not self.on: return
        t=self.timer/self.dur; a=int(255*(1-t)*min(1.0,(1-t)*4))
        sc=1.0+0.22*math.sin(t*math.pi)
        img0=F_SC.render(self.text,True,self.col)
        w0,h0=img0.get_size(); nw,nh=max(1,int(w0*sc)),max(1,int(h0*sc))
        imgs=pygame.transform.smoothscale(img0,(nw,nh)); imgs.set_alpha(a)
        surf.blit(imgs,(W//2-nw//2,H//2-160-nh//2))

# ───────────────────────────────────────────────────────────
#  CAROUSEL
# ───────────────────────────────────────────────────────────
class Carousel:
    """Swipeable horizontal carousel for team/venue selection."""
    CARD_W = 200; CARD_H = 120; GAP = 20; ANIM_SPD = 10.0

    def __init__(self, items, current=0, y=0, draw_fn=None):
        self.items   = items
        self.idx     = current
        self._x      = float(current)   # fractional index (animated)
        self.y       = y
        self.draw_fn = draw_fn          # fn(surf, item, rect, selected)
        self._drag_start = None
        self._drag_x     = 0.0

        # Arrow buttons
        ax = W//2 - self.CARD_W//2 - 48
        self.btn_left  = Button((ax, y+35, 36, 46), "<", F_LG,
                                bg=BG4, fg=TX2, hov=BG5, abg=ACCENT, afg=BLK, rad=8)
        self.btn_right = Button((W//2+self.CARD_W//2+12, y+35, 36, 46), ">", F_LG,
                                bg=BG4, fg=TX2, hov=BG5, abg=ACCENT, afg=BLK, rad=8)

    def handle(self, ev):
        if self.btn_left.handle(ev):
            self.idx = (self.idx-1) % len(self.items); return True
        if self.btn_right.handle(ev):
            self.idx = (self.idx+1) % len(self.items); return True

        if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
            x,yp=ev.pos
            if abs(yp-self.y-60)<70: self._drag_start=x; self._drag_x=0.0
        if ev.type==pygame.MOUSEMOTION and self._drag_start is not None:
            self._drag_x=self._drag_start-ev.pos[0]
        if ev.type==pygame.MOUSEBUTTONUP and ev.button==1 and self._drag_start is not None:
            if self._drag_x > 40:  self.idx=(self.idx+1)%len(self.items)
            elif self._drag_x < -40: self.idx=(self.idx-1)%len(self.items)
            self._drag_start=None; self._drag_x=0.0; return True
        return False

    def update(self, dt):
        self.btn_left.update(dt); self.btn_right.update(dt)
        # smooth scroll
        diff = self.idx - self._x
        # wrap shortest path
        n=len(self.items)
        if diff > n/2:  diff -= n
        elif diff < -n/2: diff += n
        self._x += diff * min(1.0, self.ANIM_SPD*dt)

    def draw(self, surf):
        cw=self.CARD_W; ch=self.CARD_H; gap=self.GAP
        cx=W//2
        n=len(self.items)
        # draw 3 slots: prev, current, next
        for offset in [-1, 0, 1, -2, 2]:
            item_idx=(int(round(self._x))+offset)%n
            # pixel offset from center
            frac_off=offset-(self._x-round(self._x))
            px=cx+int(frac_off*(cw+gap))-cw//2
            py=self.y
            alpha=255 if offset==0 else 140
            scale=1.0 if offset==0 else 0.85
            sw=int(cw*scale); sh=int(ch*scale)
            sx=px+(cw-sw)//2; sy=py+(ch-sh)//2
            item=self.items[item_idx]
            sel=(item_idx==self.idx)
            if self.draw_fn:
                self.draw_fn(surf, item, (sx,sy,sw,sh), sel, alpha)
            else:
                col=lerp(BG3,BG4,0) if sel else BG3
                rr(surf,col,(sx,sy,sw,sh),12,alpha=alpha)
        self.btn_left.draw(surf)
        self.btn_right.draw(surf)

    @property
    def selected(self):
        return self.items[self.idx]

# ───────────────────────────────────────────────────────────
#  CONFIRM DIALOG
# ───────────────────────────────────────────────────────────
class ConfirmDialog:
    """Blocking modal dialog with Yes/No."""
    def __init__(self, message, yes_cb, no_cb=None):
        self.msg=message; self.yes_cb=yes_cb; self.no_cb=no_cb
        dw,dh=320,160; dx=W//2-dw//2; dy=H//2-dh//2
        self.rect=(dx,dy,dw,dh)
        self.btn_y=Button((dx+20,dy+100,130,46),"YES",F_MD,
                          bg=RED,fg=WHT,hov=RED2,abg=RED2,afg=WHT,rad=12)
        self.btn_n=Button((dx+170,dy+100,130,46),"NO",F_MD,
                          bg=BG4,fg=TX2,hov=BG5,abg=BG5,afg=TX2,rad=12)
        self._alpha=0.0

    def handle(self,ev):
        if self.btn_y.handle(ev): self.yes_cb(); return True
        if self.btn_n.handle(ev):
            if self.no_cb: self.no_cb()
            return True
        return False

    def update(self,dt):
        self._alpha=min(1.0,self._alpha+dt*6)
        self.btn_y.update(dt); self.btn_n.update(dt)

    def draw(self,surf):
        # dim overlay
        ov=pygame.Surface((W,H),pygame.SRCALPHA)
        ov.fill((0,0,0,int(180*self._alpha))); surf.blit(ov,(0,0))
        # card
        dx,dy,dw,dh=self.rect
        draw_shadow(surf,self.rect,18,10,100)
        rr(surf,BG3,(dx,dy,dw,dh),18)
        rb(surf,BORDER,(dx,dy,dw,dh),1,18)
        # message
        lines=self.msg.split("\n")
        for i,l in enumerate(lines):
            txtm(surf,l,F_MD,TEXT,dy+24+i*24)
        self.btn_y.draw(surf); self.btn_n.draw(surf)

# ───────────────────────────────────────────────────────────
#  PARTICLES
# ───────────────────────────────────────────────────────────
class Particles:
    def __init__(self): self.parts=[]
    def emit(self,x,y,col,n=12,speed=120):
        for _ in range(n):
            a=random.uniform(0,math.pi*2); sp=random.uniform(40,speed)
            self.parts.append([float(x),float(y),math.cos(a)*sp,math.sin(a)*sp,
                               random.uniform(0.5,1.0),col,random.randint(3,7)])
    def update(self,dt):
        keep=[]
        for p in self.parts:
            p[0]+=p[2]*dt; p[1]+=p[3]*dt; p[3]+=200*dt; p[4]-=dt
            if p[4]>0: keep.append(p)
        self.parts=keep
    def draw(self,surf):
        for p in self.parts:
            a=int(255*max(0,p[4])); r=p[6]
            circle_a(surf,p[5],int(p[0]),int(p[1]),r,a)

# ───────────────────────────────────────────────────────────
#  GAME DATA — 8 teams
# ───────────────────────────────────────────────────────────
MAX_OVERS=5; MAX_WICKETS=10

TEAMS=[
    {"code":"IND","name":"India",       "abbr":"IND","col":hx("ff9800"),"dark":hx("e65100")},
    {"code":"AUS","name":"Australia",   "abbr":"AUS","col":hx("ffeb3b"),"dark":hx("f57f17")},
    {"code":"ENG","name":"England",     "abbr":"ENG","col":hx("5c9bff"),"dark":hx("1565c0")},
    {"code":"SL", "name":"Sri Lanka",   "abbr":"SL", "col":hx("4dd0e1"),"dark":hx("00838f")},
    {"code":"PAK","name":"Pakistan",    "abbr":"PAK","col":hx("69f0ae"),"dark":hx("1b5e20")},
    {"code":"NZ", "name":"New Zealand", "abbr":"NZ", "col":hx("ef9a9a"),"dark":hx("b71c1c")},
    {"code":"SA", "name":"S. Africa",   "abbr":"SA", "col":hx("a5d6a7"),"dark":hx("1b5e20")},
    {"code":"WI", "name":"West Indies", "abbr":"WI", "col":hx("ce93d8"),"dark":hx("4a148c")},
]
TEAM_CODES=[t["code"] for t in TEAMS]

# ───────────────────────────────────────────────────────────
#  20 VENUES
# ───────────────────────────────────────────────────────────
VENUES=[
    {"name":"Wankhede",      "city":"Mumbai",      "country":"India",     "bf":1.15,"wf":0.90},
    {"name":"Eden Gardens",  "city":"Kolkata",     "country":"India",     "bf":1.10,"wf":0.95},
    {"name":"Narendra Modi", "city":"Ahmedabad",   "country":"India",     "bf":1.05,"wf":1.00},
    {"name":"Chinnaswamy",   "city":"Bangalore",   "country":"India",     "bf":1.20,"wf":0.85},
    {"name":"Arun Jaitley",  "city":"Delhi",       "country":"India",     "bf":1.08,"wf":0.95},
    {"name":"Chepauk",       "city":"Chennai",     "country":"India",     "bf":0.95,"wf":1.10},
    {"name":"Rajiv Gandhi",  "city":"Hyderabad",   "country":"India",     "bf":1.12,"wf":0.92},
    {"name":"PCA Stadium",   "city":"Mohali",      "country":"India",     "bf":1.05,"wf":1.00},
    {"name":"Green Park",    "city":"Kanpur",      "country":"India",     "bf":0.90,"wf":1.15},
    {"name":"MCG",           "city":"Melbourne",   "country":"Australia", "bf":1.00,"wf":1.05},
    {"name":"SCG",           "city":"Sydney",      "country":"Australia", "bf":1.08,"wf":0.95},
    {"name":"Adelaide Oval", "city":"Adelaide",    "country":"Australia", "bf":1.10,"wf":0.92},
    {"name":"Perth Stadium", "city":"Perth",       "country":"Australia", "bf":0.95,"wf":1.12},
    {"name":"Lord's",        "city":"London",      "country":"England",   "bf":0.92,"wf":1.15},
    {"name":"The Oval",      "city":"London",      "country":"England",   "bf":1.00,"wf":1.05},
    {"name":"Old Trafford",  "city":"Manchester",  "country":"England",   "bf":0.95,"wf":1.10},
    {"name":"Headingley",    "city":"Leeds",       "country":"England",   "bf":0.98,"wf":1.08},
    {"name":"Newlands",      "city":"Cape Town",   "country":"S.Africa",  "bf":1.02,"wf":1.02},
    {"name":"Wanderers",     "city":"Johannesburg","country":"S.Africa",  "bf":1.15,"wf":0.90},
    {"name":"Gaddafi",       "city":"Lahore",      "country":"Pakistan",  "bf":0.95,"wf":1.10},
]

# ───────────────────────────────────────────────────────────
#  DELIVERY TYPES & COMMENTARY
# ───────────────────────────────────────────────────────────
DELIVERY_TYPES=["yorker","good_length","bouncer","full_toss","slower","wide_half"]

DELIVERY_COMM={
    "yorker":      ["Yorker! Squeezed out for {}.",    "Full yorker — dug out!",           "Toe-crusher yorker, {}!"],
    "good_length": ["Good length, driven for {}.",     "On the money, worked away for {}.", "Textbook delivery, {}."],
    "bouncer":     ["Short ball! Pulled away for {}!", "Bouncer — {}!",                    "Rises sharply, {}!"],
    "full_toss":   ["Full toss — smashed for {}!",    "Beamer — dispatched for {}!",       "Free hit chance, {}!"],
    "slower":      ["Slower ball — {} only.",          "Deceived in flight, {}.",           "Change of pace, {}."],
    "wide_half":   ["Width on offer — driven for {}!","Half-volley — {}!",                 "Full and wide, {}!"],
}
WICKET_COMM={
    "yorker":      "Yorker! BOWLED! Middle stump flying!",
    "good_length": "Good length, edged and CAUGHT behind!",
    "bouncer":     "Bouncer! Top edge — CAUGHT at fine leg!",
    "full_toss":   "Full toss — skied and CAUGHT!",
    "slower":      "Slower ball — STUMPED, miles out!",
    "wide_half":   "Width offered — but CAUGHT at covers!",
}
WICKET_COMM_GENERIC=["OUT! Bowled — stump cartwheel!","WICKET! Caught behind!",
                     "OUT! LBW — huge appeal upheld!","WICKET! Caught brilliantly!"]

BOWL_STYLE_COMM={
    "Defensive field": "Defensive field set — tight lines.",
    "Balanced field":  "Balanced field — options open.",
    "Attacking field": "Attacking field — pressure on!",
}

# ───────────────────────────────────────────────────────────
#  TEAM STATE
# ───────────────────────────────────────────────────────────
class Team:
    def __init__(self,code):
        d=[t for t in TEAMS if t["code"]==code][0]
        self.code=code; self.name=d["name"]; self.abbr=d["abbr"]
        self.col=d["col"]; self.dark=d["dark"]
        self.score=0; self.wickets=0; self.overs=0; self.balls=0
        self.boundaries=0; self.sixes=0; self.dots=0

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

# ───────────────────────────────────────────────────────────
#  REALISTIC BALL ENGINE
# ───────────────────────────────────────────────────────────
def simulate_delivery(bat_style, bowl_style, venue, bat: Team, innings, target):
    """
    Returns (result, delivery_type, commentary, is_wd, is_nb)
    result: int or 'W'
    """
    bf=venue["bf"]; wf=venue["wf"]

    # Pressure factor
    pressure=1.0
    if innings==2 and target>0 and bat.total_balls>0:
        need=target-bat.score
        bl_rem=MAX_OVERS*6-bat.total_balls
        if bl_rem>0:
            rrr=need*6/bl_rem
            if rrr>12: pressure=1.3
            elif rrr>8: pressure=1.1
            elif rrr<5: pressure=0.85

    # Confidence (falls with wickets)
    confidence=1.0-bat.wickets*0.08

    # Delivery type probabilities by bowl style
    if bowl_style=="Yorker":
        probs={"yorker":0.60,"good_length":0.15,"bouncer":0.05,"full_toss":0.08,"slower":0.07,"wide_half":0.05}
        wkt_boost=0.10
    elif bowl_style=="Bouncer":
        probs={"bouncer":0.55,"good_length":0.20,"yorker":0.10,"full_toss":0.05,"slower":0.05,"wide_half":0.05}
        wkt_boost=0.06
    elif bowl_style=="Slower Ball":
        probs={"slower":0.55,"good_length":0.20,"wide_half":0.10,"yorker":0.08,"bouncer":0.04,"full_toss":0.03}
        wkt_boost=0.09
    elif bowl_style=="Full Toss":
        probs={"full_toss":0.50,"good_length":0.20,"yorker":0.10,"wide_half":0.15,"bouncer":0.03,"slower":0.02}
        wkt_boost=0.03
    else:  # Good Length (default/Balanced)
        probs={"good_length":0.45,"yorker":0.15,"bouncer":0.15,"slower":0.15,"full_toss":0.05,"wide_half":0.05}
        wkt_boost=0.07

    delivery=random.choices(list(probs.keys()),weights=list(probs.values()))[0]

    # Extras (small chance)
    nb=False; wd=False
    if bowl_style=="Full Toss" and random.random()<0.04: nb=True
    if bowl_style in("Bouncer","Good Length") and random.random()<0.03: wd=True

    # Batting style weights
    if bat_style=="Defensive":
        run_weights=[0.40,0.30,0.12,0.05,0.06,0.00,0.07]  # 0,1,2,3,4,6,W
        wkt_base=0.05
    elif bat_style=="Moderate":
        run_weights=[0.18,0.24,0.16,0.10,0.15,0.06,0.11]
        wkt_base=0.13
    else:  # Aggressive
        run_weights=[0.08,0.10,0.10,0.08,0.22,0.25,0.17]
        wkt_base=0.22

    # Delivery modifiers to run weights
    if delivery=="yorker":
        # harder to score big, more wickets
        run_weights=[w*1.3 if i<2 else w*0.5 for i,w in enumerate(run_weights)]
        wkt_boost+=0.04
    elif delivery=="bouncer":
        run_weights=[run_weights[0],run_weights[1],run_weights[2],
                     run_weights[3],run_weights[4],run_weights[5]*2.0,run_weights[6]]
        wkt_boost+=0.03
    elif delivery=="full_toss":
        run_weights=[w*0.5 if i<3 else w*1.8 for i,w in enumerate(run_weights)]
        wkt_boost-=0.04
    elif delivery=="slower":
        # deceives batter → more wickets, fewer big shots
        run_weights=[run_weights[0]*1.4,run_weights[1],run_weights[2],
                     run_weights[3]*0.5,run_weights[4]*0.5,run_weights[5]*0.3,run_weights[6]*1.3]
        wkt_boost+=0.03
    elif delivery=="wide_half":
        run_weights=[w*0.3 if i<3 else w*2.0 for i,w in enumerate(run_weights)]
        wkt_boost-=0.05

    # Apply venue batting factor
    run_weights=[run_weights[0],
                 run_weights[1]*bf,run_weights[2]*bf,run_weights[3]*bf,
                 run_weights[4]*bf,run_weights[5]*bf,
                 run_weights[6]*wf]

    # Pressure and confidence
    run_weights=[r*pressure*confidence for r in run_weights]
    run_weights=list(map(abs,run_weights))

    wkt_chance=wkt_base+wkt_boost
    # Sample outcome
    outcomes=[0,1,2,3,4,6,"W"]
    # Ensure wicket weight is proportional
    run_weights[6]=wkt_chance*sum(run_weights[:6])/(1-wkt_chance+1e-9)

    total=sum(run_weights)
    if total<=0: run_weights=[1]*7; total=7
    result=random.choices(outcomes,weights=[w/total for w in run_weights])[0]

    # Commentary
    run_labels={0:"a dot",1:"one",2:"two",3:"three",4:"FOUR",6:"SIX"}
    if result=="W":
        comm=WICKET_COMM.get(delivery,random.choice(WICKET_COMM_GENERIC))
    else:
        templates=DELIVERY_COMM.get(delivery,["Played for {}."])
        comm=random.choice(templates).format(run_labels.get(result,str(result)))

    return result, delivery, comm, wd, nb

# ───────────────────────────────────────────────────────────
#  GAME STATE
# ───────────────────────────────────────────────────────────
class GS:
    def __init__(self):
        self.player_team=TEAMS[0]["code"]
        self.opp_team   =TEAMS[1]["code"]
        self.venue      =VENUES[0]
        self.toss_call  ="Head"
        self.bat_first  =""        # filled after toss
        self.bowl_first =""
        self.bat1: Team =None
        self.bat2: Team =None
        self.innings    =1
        self.target     =0
        self.log        =[]        # (tag, result, delivery, comm)
        self.current_over=[]
        self.game_over  =False
        self.player_bats=True      # True if player is batting this innings
        self.momentum   =50.0      # 0-100 batting momentum bar

    @property
    def batting(self): return self.bat1 if self.innings==1 else self.bat2
    def chase_won(self): return self.innings==2 and self.bat2.score>=self.target
    def innings_done(self): return self.batting.innings_over()

    def play_delivery(self, bat_style, bowl_style):
        bat=self.batting
        tag=bat.fmt_overs()
        result,delivery,comm,wd,nb=simulate_delivery(
            bat_style, bowl_style, self.venue, bat, self.innings, self.target)

        if result=="W":
            bat.wickets+=1
            self.momentum=max(0,self.momentum-20)
        else:
            bat.score+=result
            if result==0:
                bat.dots+=1; self.momentum=max(0,self.momentum-5)
            elif result==4:
                bat.boundaries+=1; self.momentum=min(100,self.momentum+15)
            elif result==6:
                bat.sixes+=1; self.momentum=min(100,self.momentum+25)
            else:
                self.momentum=min(100,self.momentum+3*result)

        self.current_over.append(result)
        done=bat.advance_ball()
        if done: self.current_over=[]
        self.log.append((tag,result,delivery,comm))
        return result,comm,done

    def play_over_style(self, bat_style, bowl_style):
        """Play full over (over mode)."""
        runs=0; wkts=0
        for _ in range(6):
            res,comm,_=self.play_delivery(bat_style,bowl_style)
            if res=="W": wkts+=1
            elif isinstance(res,int): runs+=res
            if self.innings_done(): break
        self.current_over=[]
        return runs,wkts

# ───────────────────────────────────────────────────────────
#  BASE SCREEN
# ───────────────────────────────────────────────────────────
class Screen:
    def __init__(self,gs):
        self.gs=gs; self.next=None; self.buttons=[]; self.toast=Toast()
        self._dialog=None

    def handle(self,ev):
        if self._dialog:
            if self._dialog.handle(ev): self._dialog=None
            return
        for b in self.buttons:
            if b.handle(ev): self.on_button(b)

    def on_button(self,b): pass

    def update(self,dt):
        if self._dialog: self._dialog.update(dt); return
        for b in self.buttons: b.update(dt)
        self.toast.update(dt)

    def draw(self,surf):
        surf.fill(BG)
        for b in self.buttons: b.draw(surf)
        if self._dialog: self._dialog.draw(surf)
        self.toast.draw(surf)

    def _hdr(self,surf,title,sub="",ac=ACCENT):
        grad(surf,BG2,BG,(0,0,W,100)); glow(surf,ac,0,3)
        txtm(surf,title,F_XL,TEXT,26)
        if sub: txtm(surf,sub,F_SM,TX2,58)
        pygame.draw.line(surf,BORDER,(0,96),(W,96),1)

    def _sec(self,surf,label,y): txt(surf,f"◆  {label}",F_XS,TX3,18,y)
    def _foot(self,surf,t):
        pygame.draw.line(surf,BORDER,(0,H-34),(W,H-34),1)
        txtm(surf,t,F_XS,TX3,H-20)

    def _show_exit_dialog(self):
        def yes(): pygame.quit(); sys.exit()
        def no():  self._dialog=None
        self._dialog=ConfirmDialog("Exit Cricket Simulator?",yes,no)

    def _show_menu_dialog(self):
        def yes(): self.gs.__init__(); self.next="menu"
        def no():  self._dialog=None
        self._dialog=ConfirmDialog("Return to Main Menu?\nProgress will be lost.",yes,no)

# ───────────────────────────────────────────────────────────
#  CAROUSEL DRAW FUNCTIONS
# ───────────────────────────────────────────────────────────
def draw_team_card(surf, team, rect, sel, alpha=255):
    x,y,w,h=rect
    # shadow
    draw_shadow(surf,(x,y,w,h),14,6,60)
    # glass card
    glass_card(surf,(x,y,w,h),
               col=lerp(team["dark"],BG3,0.5) if sel else BG3,
               border=team["col"] if sel else BORDER,
               alpha=min(255,alpha),radius=14)
    if sel: rb(surf,(*team["col"],200),(x,y,w,h),2,14)
    # color accent bar
    rr(surf,team["col"],(x+12,y+8,w-24,4),3,alpha=min(255,alpha))
    # abbr big
    txt(surf,team["abbr"],F_XL,(*team["col"],min(255,alpha)),x+w//2,y+20,align="center")
    txt(surf,team["name"],F_SM,(*TEXT,min(255,alpha)),x+w//2,y+60,align="center")
    if sel:
        rr(surf,team["col"],(x+w//2-20,y+h-14,40,6),3,alpha=200)

def draw_venue_card(surf, venue, rect, sel, alpha=255):
    x,y,w,h=rect
    draw_shadow(surf,(x,y,w,h),14,6,60)
    c=lerp(BG4,BG3,0.5) if sel else BG3
    glass_card(surf,(x,y,w,h),col=c,
               border=GOLD if sel else BORDER,alpha=min(255,alpha),radius=14)
    if sel: rb(surf,(*GOLD,180),(x,y,w,h),2,14)
    rr(surf,GOLD,(x+12,y+8,w-24,4),3,alpha=min(200,alpha))
    txt(surf,venue["name"],F_MD,(*TEXT,min(255,alpha)),x+w//2,y+18,align="center")
    txt(surf,venue["city"],F_SM,(*TX2,min(200,alpha)),x+w//2,y+48,align="center")
    txt(surf,venue["country"],F_XS,(*TX3,min(180,alpha)),x+w//2,y+70,align="center")
    if sel:
        # batting/bowling factor
        bf_col=ACCENT if venue["bf"]>=1.0 else RED
        wf_col=RED if venue["wf"]>=1.05 else ACCENT
        txt(surf,f"BAT {venue['bf']:.2f}",F_XS,(*bf_col,min(200,alpha)),x+20,y+h-22)
        txt(surf,f"BOWL {venue['wf']:.2f}",F_XS,(*wf_col,min(200,alpha)),x+w-20,y+h-22,align="right")

# ═══════════════════════════════════════════════════════════
#  SCREEN 1 — MENU
# ═══════════════════════════════════════════════════════════
class MenuScreen(Screen):
    def __init__(self,gs):
        super().__init__(gs)
        mi=next((i for i,t in enumerate(TEAMS) if t["code"]==gs.player_team),0)
        oi=next((i for i,t in enumerate(TEAMS) if t["code"]==gs.opp_team),1)
        vi=next((i for i,v in enumerate(VENUES) if v["name"]==gs.venue["name"]),0)

        self._my_car  =Carousel(TEAMS,  mi,  y=152, draw_fn=draw_team_card)
        self._opp_car =Carousel(TEAMS,  oi,  y=306, draw_fn=draw_team_card)
        self._ven_car =Carousel(VENUES, vi,  y=460, draw_fn=draw_venue_card)

        self._sel_toss=0 if gs.toss_call=="Head" else 1
        P=16; hw=(W-P*2-10)//2
        self._toss_btns=[
            Button((P,608,hw,44),"☀  HEAD",F_MD,abg=GOLD,afg=BLK,bc=BORDER,rad=22,tag=("ts",0)),
            Button((P+hw+10,608,hw,44),"☾  TAIL",F_MD,abg=PURP,afg=BLK,bc=BORDER,rad=22,tag=("ts",1)),
        ]
        self._toss_btns[self._sel_toss].sel=True

        self.buttons=[
            Button((P,668,W-P*2,54),"FLIP THE COIN  ▶",F_XL,
                   bg=ACCENT,fg=BLK,hov=ACC2,abg=ACC2,afg=BLK,bc=ACC2,rad=14,tag="go"),
            Button((P,736,W-P*2,44),"EXIT GAME",F_MD,
                   bg=BG4,fg=TX2,hov=BG5,abg=RED,afg=WHT,bc=BORDER,rad=12,tag="exit"),
        ]+self._toss_btns
        self._t=0.0

    def handle(self,ev):
        if self._dialog:
            if self._dialog.handle(ev): self._dialog=None
            return
        # carousels
        my_changed=self._my_car.handle(ev)
        opp_changed=self._opp_car.handle(ev)
        self._ven_car.handle(ev)
        # prevent same team
        if my_changed and self._my_car.idx==self._opp_car.idx:
            self._opp_car.idx=(self._opp_car.idx+1)%len(TEAMS)
        if opp_changed and self._opp_car.idx==self._my_car.idx:
            self._my_car.idx=(self._my_car.idx-1)%len(TEAMS)
        # buttons
        for b in self.buttons:
            if b.handle(ev): self.on_button(b)

    def on_button(self,b):
        if b.tag==("ts",0): self._sel_toss=0; self._toss_btns[0].sel=True; self._toss_btns[1].sel=False
        elif b.tag==("ts",1): self._sel_toss=1; self._toss_btns[0].sel=False; self._toss_btns[1].sel=True
        elif b.tag=="go":
            mt=self._my_car.selected; ot=self._opp_car.selected
            if mt["code"]==ot["code"]:
                self.toast.show("Pick different teams!",RED,1.2); return
            self.gs.player_team=mt["code"]; self.gs.opp_team=ot["code"]
            self.gs.venue=self._ven_car.selected
            self.gs.toss_call=["Head","Tail"][self._sel_toss]
            self.next="toss"
        elif b.tag=="exit": self._show_exit_dialog()

    def update(self,dt):
        super().update(dt); self._t+=dt
        self._my_car.update(dt); self._opp_car.update(dt); self._ven_car.update(dt)

    def draw(self,surf):
        surf.fill(BG)
        # animated top gradient
        t=self._t
        c1=lerp(BG2,lerp(BG3,hx("0d2a10"),abs(math.sin(t*0.3))),0.5)
        grad(surf,c1,BG,(0,0,W,100)); glow(surf,ACCENT,0,3)
        txtm(surf,"CRICKET SIMULATOR",F_XL,TEXT,22)
        txtm(surf,"T20 MATCH ENGINE  v6.0",F_XS,TX3,54)
        pygame.draw.line(surf,BORDER,(0,96),(W,96),1)

        self._sec(surf,"YOUR TEAM",134)
        self._my_car.draw(surf)
        self._sec(surf,"OPPOSITION",288)
        self._opp_car.draw(surf)
        self._sec(surf,"VENUE",442)
        self._ven_car.draw(surf)
        self._sec(surf,"TOSS CALL",590)
        for b in self.buttons: b.draw(surf)
        if self._dialog: self._dialog.draw(surf)
        self.toast.draw(surf)

# ═══════════════════════════════════════════════════════════
#  SCREEN 2 — TOSS
# ═══════════════════════════════════════════════════════════
class TossScreen(Screen):
    def __init__(self,gs):
        super().__init__(gs)
        self._phase="idle"; self._ft=0.0; self._fi=0; self._done=False
        self._won=False; self._icon="☀"; self._rtxt=""; self._dtxt=""
        self._bf=""; self._bfname=""; self._t=0.0
        self._frames=["☀","◑","☾","◐","☀","◑","☾","◐","☀","◑","☾","◐"]
        self._particles=Particles()
        self.buttons=[
            Button((W//2-120,490,240,54),"☀  FLIP  ☾",F_LG,
                   bg=GOLD,fg=BLK,hov=GLD2,abg=GLD2,afg=BLK,bc=GOLD,rad=30,tag="flip")
        ]
        self._pb=Button((W//2-120,598,240,50),"▶  START MATCH",F_MD,
                        bg=ACCENT,fg=BLK,hov=ACC2,abg=ACC2,afg=BLK,bc=ACCENT,rad=30,tag="go")

    def handle(self,ev):
        if self._dialog:
            if self._dialog.handle(ev): self._dialog=None; return
        for b in self.buttons:
            if b.handle(ev): self.on_button(b)
        if self._done and self._pb.handle(ev): self.on_button(self._pb)
        if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE:
            self._show_exit_dialog()

    def on_button(self,b):
        if b.tag=="flip" and not self._done: self._phase="spin"
        elif b.tag=="go": self.next="match"

    def update(self,dt):
        super().update(dt); self._pb.update(dt); self._t+=dt
        self._particles.update(dt)
        if self._phase=="spin":
            self._ft+=dt
            if self._ft>=0.10:
                self._ft=0.0; self._fi+=1
                if self._fi>=len(self._frames): self._resolve()

    def _resolve(self):
        gs=self.gs; res=random.choice(["Head","Tail"]); won=(res==gs.toss_call)
        wc=gs.player_team if won else gs.opp_team
        dec=random.choice(["bat","bowl"])
        self._won=won; self._icon="☀" if res=="Head" else "☾"
        self._rtxt="YOU WIN THE TOSS!" if won else f"{next(t['name'] for t in TEAMS if t['code']==gs.opp_team)} WIN!"
        self._dtxt=f"{next(t['name'] for t in TEAMS if t['code']==wc)} elected to {dec} first"
        bf=wc if dec=="bat" else (gs.opp_team if won else gs.player_team)
        wf=gs.opp_team if bf==gs.player_team else gs.player_team
        self._bf=bf; self._bfname=next(t["name"] for t in TEAMS if t["code"]==bf)
        gs.bat1=Team(bf); gs.bat2=Team(wf); gs.innings=1
        gs.player_bats=(bf==gs.player_team)
        self._phase="result"; self._done=True
        self._particles.emit(W//2,300,GOLD if won else RED,16,150)

    def draw(self,surf):
        surf.fill(BG)
        c=lerp(GOLD,BG,0.88)
        grad(surf,c,BG,(0,0,W,100)); glow(surf,GOLD,0,3)
        txtm(surf,"THE TOSS",F_XL,GOLD,26)
        v=self.gs.venue; txtm(surf,f"{v['name']} · {v['city']}",F_SM,TX2,58)
        pygame.draw.line(surf,BORDER,(0,96),(W,96),1)

        self._particles.draw(surf)
        cx=W//2; cy=290
        if self._phase=="idle":
            t=self._t
            pulse=1.0+0.06*math.sin(t*2.5); r=int(64*pulse)
            pygame.draw.circle(surf,lerp(GOLD,GLD2,abs(math.sin(t))),(cx,cy),r)
            pygame.draw.circle(surf,lerp(GOLD,WHT,0.3),(cx,cy),r,3)
            txtm(surf,"☀",F_XXL,BLK,cy-26); txtm(surf,"HEAD",F_XS,BLK,cy+14)
            txtm(surf,"Tap to flip the coin",F_SM,TX2,cy+90)
            for b in self.buttons: b.draw(surf)
        elif self._phase=="spin":
            t=self._t; p=1.0+0.18*math.sin(t*28); r=int(64*p)
            c=lerp(GOLD,PURP,(math.sin(t*12)+1)/2)
            pygame.draw.circle(surf,c,(cx,cy),r)
            pygame.draw.circle(surf,WHT,(cx,cy),r,2)
            fi=min(self._fi,len(self._frames)-1)
            txtm(surf,self._frames[fi],F_XXL,BLK,cy-26)
            txtm(surf,"Flipping…",F_SM,TX2,cy+90)
        else:
            rc=ACCENT if self._won else RED
            circle_a(surf,rc,cx,cy,80,40)
            pygame.draw.circle(surf,rc,(cx,cy),64,3)
            ic_col=GOLD if self._icon=="☀" else PURP
            txtm(surf,self._icon,F_XXL,ic_col,cy-26)
            # result card
            draw_shadow(surf,(24,cy+90,W-48,148),18,8,80)
            glass_card(surf,(24,cy+90,W-48,148),col=BG3,border=rc,alpha=230,radius=16)
            rb(surf,(*rc,160),(24,cy+90,W-48,148),2,16)
            txtm(surf,self._rtxt,F_MD,rc,cy+106)
            txtm(surf,self._dtxt,F_SM,TX2,cy+136)
            bf_name=self._bfname
            wf_name=next(t["name"] for t in TEAMS if t["code"]!=self._bf and
                         (t["code"]==self.gs.player_team or t["code"]==self.gs.opp_team))
            txtm(surf,f"Bat: {bf_name}   Bowl: {wf_name}",F_XS,TX3,cy+162)
            self._pb.draw(surf)
        if self._dialog: self._dialog.draw(surf)

# ═══════════════════════════════════════════════════════════
#  SCREEN 3 — MATCH  (batting + bowling screens)
# ═══════════════════════════════════════════════════════════
class MatchScreen(Screen):
    BAT_STYLES  =["Defensive","Moderate","Aggressive"]
    BOWL_STYLES =["Yorker","Good Length","Bouncer","Slower Ball","Full Toss"]
    FIELD_STYLES=["Defensive field","Balanced field","Attacking field"]

    def __init__(self,gs):
        super().__init__(gs)
        self._bat_sel  =1   # default Moderate
        self._bowl_sel =1   # default Good Length
        self._field_sel=1
        self._build_buttons()
        self._particles=Particles()
        self._t=0.0

    def _build_buttons(self):
        self.buttons=[]
        gs=self.gs; P=12; G=8

        if gs.player_bats:
            # ── Batting controls ──
            bw=(W-P*2-G*2)//3; by=H-136
            colors=[BLUE,GOLD,RED]
            for i,s in enumerate(self.BAT_STYLES):
                x=P+i*(bw+G)
                b=Button((x,by,bw,58),s,F_SM,
                         bg=BG4,fg=TX2,hov=BG5,
                         abg=colors[i],afg=BLK,rad=12,tag=("bat",i))
                b.sel=(i==self._bat_sel)
                self.buttons.append(b)
        else:
            # ── Bowling controls ──
            bw=(W-P*2-G*4)//5; by=H-136
            colors=[ACCENT,BLUE,RED,GOLD,PURP]
            for i,s in enumerate(self.BOWL_STYLES):
                x=P+i*(bw+G)
                b=Button((x,by,bw,58),s,F_XS,
                         bg=BG4,fg=TX2,hov=BG5,
                         abg=colors[i],afg=BLK,rad=12,tag=("bowl",i))
                b.sel=(i==self._bowl_sel)
                self.buttons.append(b)

        # Menu button (small, top right)
        self._menu_btn=Button((W-74,6,66,28),"MENU",F_XS,
                              bg=BG4,fg=TX2,hov=BG5,abg=RED,afg=WHT,rad=8,tag="menu")

    def _bat_style(self):  return self.BAT_STYLES[self._bat_sel]
    def _bowl_style(self): return self.BOWL_STYLES[self._bowl_sel]

    def handle(self,ev):
        if self._dialog:
            if self._dialog.handle(ev): self._dialog=None; return
        if self._menu_btn.handle(ev): self._show_menu_dialog(); return
        for b in self.buttons:
            if b.handle(ev): self.on_button(b)
        if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE:
            self._show_menu_dialog()

    def on_button(self,b):
        gs=self.gs
        if gs.game_over: return
        k=b.tag[0]
        if k=="bat":
            self._bat_sel=b.tag[1]
            for btn in self.buttons: btn.sel=(btn.tag==b.tag)
            self._fire_ball()
        elif k=="bowl":
            self._bowl_sel=b.tag[1]
            for btn in self.buttons: btn.sel=(btn.tag==b.tag)
            self._fire_ball()
        elif k=="menu": self._show_menu_dialog()

    def _fire_ball(self):
        gs=self.gs; bs=self._bat_style(); bws=self._bowl_style()
        res,comm,_=gs.play_delivery(bs,bws)
        if res=="W":
            self.toast.show("OUT!",RED,0.9)
            self._particles.emit(W//2,350,RED,14,160)
        elif res==6:
            self.toast.show("SIX!",ACCENT,0.75)
            self._particles.emit(W//2,350,ACCENT,18,200)
        elif res==4:
            self.toast.show("FOUR!",GOLD,0.75)
            self._particles.emit(W//2,350,GOLD,12,140)
        self._check_end()

    def _check_end(self):
        gs=self.gs
        if gs.chase_won(): gs.game_over=True; self.next="result"; return
        if gs.innings_done():
            if gs.innings==1: self.next="break"
            else: gs.game_over=True; self.next="result"

    def update(self,dt):
        super().update(dt)
        self._menu_btn.update(dt); self._particles.update(dt); self._t+=dt

    def draw(self,surf):
        gs=self.gs; bat=gs.batting; is_bat=gs.player_bats

        # Theme background
        bg_tint=BAT_THEME if is_bat else BOWL_THEME
        surf.fill(lerp(BG,bg_tint,0.5))
        grad(surf,lerp(BG2,bg_tint,0.6),lerp(BG,bg_tint,0.5),(0,0,W,160))

        theme_col=ACCENT if is_bat else RED
        glow(surf,bat.col,0,3)

        # ── Scoreboard ──
        txt(surf,gs.venue["name"]+" · "+gs.venue["city"],F_XS,TX3,12,10)
        inn="1st INNINGS" if gs.innings==1 else "2nd INNINGS · CHASE"
        bmode="BATTING" if is_bat else "BOWLING"
        mode_col=ACCENT if is_bat else RED
        # pills top right
        img=F_XS.render(inn,True,ACCENT)
        pill_w=img.get_width()+16
        rr(surf,BG4,(W-pill_w-10,6,pill_w,20),10)
        surf.blit(img,(W-pill_w-2,8))
        img2=F_XS.render(bmode,True,mode_col)
        pw2=img2.get_width()+16
        rr(surf,lerp(mode_col,BG,0.8),(W-pw2-10,30,pw2,20),10)
        surf.blit(img2,(W-pw2-2,32))

        self._menu_btn.draw(surf)

        # ── Score display ──
        txt(surf,bat.name,F_SM,bat.col,12,32)
        txt(surf,bat.fmt_score(),F_SC,TEXT,12,48)
        txt(surf,f"({bat.fmt_overs()} ov)",F_MD,TX2,12,110)
        txt(surf,f"CRR {bat.crr:.2f}",F_SM,TX3,140,114)
        # boundaries/sixes mini stats
        txt(surf,f"4s:{bat.boundaries}  6s:{bat.sixes}",F_XS,TX3,W-12,114,align="right")

        pygame.draw.line(surf,BORDER,(0,148),(W,148),1)

        cy=152
        if gs.innings==2:
            need=gs.target-bat.score; bl=MAX_OVERS*6-bat.total_balls
            rrr=(need*6/bl) if bl>0 else 99.99
            rc=ACCENT if rrr<9 else (GOLD if rrr<13 else RED)
            txt(surf,f"Target {gs.target}",F_SM,GOLD,12,cy+2)
            txt(surf,f"Need {need}  |  RRR {rrr:.2f}",F_SM,rc,160,cy+2)
            pct=bat.score/max(1,gs.target); bc=ACCENT if pct<0.85 else GOLD
            rr(surf,BG4,(12,cy+22,W-24,5),3)
            rr(surf,bc,(12,cy+22,max(0,int((W-24)*pct)),5),3)
            cy+=32
        else: cy+=4

        # ── Momentum bar (batting only) ──
        if is_bat:
            mom=gs.momentum/100.0
            mc=lerp(RED,ACCENT,mom); txt(surf,"MOMENTUM",F_XS,TX3,12,cy+4)
            rr(surf,BG4,(90,cy+4,W-102,10),5)
            rr(surf,mc,(90,cy+4,max(0,int((W-102)*mom)),10),5)
            cy+=20

        # ── This over ──
        txt(surf,"THIS OVER",F_XS,TX3,12,cy+4); ox=94
        for b in gs.current_over:
            if b=="W": bc_,fc_,ch=RED,WHT,"W"
            elif b==6: bc_,fc_,ch=ACCENT,BLK,"6"
            elif b==4: bc_,fc_,ch=GOLD,BLK,"4"
            elif b==0: bc_,fc_,ch=BG4,TX3,"·"
            else: bc_,fc_,ch=BG4,BLUE,str(b)
            pygame.draw.rect(surf,bc_,(ox,cy,24,22),border_radius=4)
            txt(surf,ch,F_MO,fc_,ox+12,cy+3,align="center"); ox+=30
        cy+=32

        # ── Commentary ──
        pygame.draw.line(surf,BORDER,(0,cy),(W,cy),1)
        txt(surf,"COMMENTARY",F_XS,TX3,12,cy+4); ly=cy+22
        for entry in reversed(gs.log[-6:]):
            if ly>H-178: break
            tag_s,result,delivery,comm=entry
            rh=36
            rr(surf,BG4,(8,ly,W-16,rh),6)
            # delivery type badge
            dcols={"yorker":PURP,"bouncer":RED,"full_toss":GOLD,"slower":CYN,
                   "good_length":BLUE,"wide_half":ACCENT}
            dc=dcols.get(delivery,BG5)
            dw=F_XS.size(delivery)[0]+10
            rr(surf,lerp(dc,BG,0.5),(12,ly+4,dw,16),4)
            txt(surf,delivery,F_XS,dc,12+dw//2,ly+6,align="center")
            # result dot
            if result=="W": dotc,dotch=RED,"W"
            elif result==6: dotc,dotch=ACCENT,"6"
            elif result==4: dotc,dotch=GOLD,"4"
            elif result==0: dotc,dotch=BG5,"·"
            else: dotc,dotch=BLUE,str(result)
            pygame.draw.rect(surf,dotc,(W-40,ly+6,24,24),border_radius=5)
            txt(surf,dotch,F_MO,WHT,W-28,ly+10,align="center")
            txt(surf,comm,F_XS,TX2,12+dw+6,ly+13,mw=W-dw-60)
            ly+=rh+3

        # ── Controls ──
        pygame.draw.line(surf,BORDER,(0,H-162),(W,H-162),1)
        # Theme label
        if is_bat:
            rr(surf,lerp(ACCENT,BG,0.85),(0,H-162,W,22),0)
            txt(surf,"CHOOSE BATTING STYLE",F_XS,ACCENT,12,H-154)
        else:
            rr(surf,lerp(RED,BG,0.85),(0,H-162,W,22),0)
            txt(surf,"CHOOSE DELIVERY",F_XS,RED,12,H-154)
            # Field setting mini display
            fs=self.FIELD_STYLES[self._field_sel]
            txt(surf,f"Field: {fs}",F_XS,TX2,W-12,H-154,align="right")

        for b in self.buttons: b.draw(surf)
        self._particles.draw(surf)
        self.toast.draw(surf)
        if self._dialog: self._dialog.draw(surf)

# ═══════════════════════════════════════════════════════════
#  SCREEN 4 — INNINGS BREAK
# ═══════════════════════════════════════════════════════════
class BreakScreen(Screen):
    def __init__(self,gs):
        super().__init__(gs)
        gs.target=gs.bat1.score+1; gs.innings=2
        gs.bat2=Team(gs.bat2.code); gs.current_over=[]; gs.momentum=50.0
        # Swap player_bats
        gs.player_bats=(gs.bat2.code==gs.player_team)
        self._t=0.0; self._particles=Particles()
        self._particles.emit(W//2,300,GOLD,20,120)
        self.buttons=[
            Button((W//2-130,590,260,54),"▶  BEGIN THE CHASE",F_LG,
                   bg=GOLD,fg=BLK,hov=GLD2,abg=GLD2,afg=BLK,bc=GOLD,rad=30,tag="go")
        ]

    def on_button(self,b):
        if b.tag=="go": self.next="match"

    def update(self,dt):
        super().update(dt); self._t+=dt; self._particles.update(dt)

    def draw(self,surf):
        surf.fill(BG)
        c=lerp(BG2,lerp(GOLD,BG,0.9),abs(math.sin(self._t*0.4)))
        grad(surf,c,BG,(0,0,W,100)); glow(surf,GOLD,0,3)
        txtm(surf,"INNINGS BREAK",F_XL,GOLD,26)
        pygame.draw.line(surf,BORDER,(0,96),(W,96),1)
        self._particles.draw(surf)
        b1=self.gs.bat1

        # Card 1: 1st innings
        draw_shadow(surf,(20,112,W-40,108),14,8,80)
        glass_card(surf,(20,112,W-40,108),col=BG3,border=BORDER,alpha=220,radius=16)
        rb(surf,(*b1.col,160),(20,112,W-40,108),2,16)
        txtm(surf,b1.name+" — 1st Innings",F_SM,TX2,124)
        txtm(surf,b1.fmt_score(),F_XXL,b1.col,144)
        txtm(surf,f"({b1.fmt_overs()} ov)   CRR {b1.crr:.2f}   "
                  f"4s:{b1.boundaries}   6s:{b1.sixes}",F_XS,TX3,192)

        pygame.draw.line(surf,BORDER,(60,230),(W-60,230),1)

        # Card 2: target
        draw_shadow(surf,(20,244,W-40,190),16,8,80)
        glass_card(surf,(20,244,W-40,190),col=BG3,border=ACCENT,alpha=220,radius=16)
        rb(surf,(*ACCENT,160),(20,244,W-40,190),2,16)
        b2=self.gs.bat2
        txtm(surf,b2.name+" need",F_LG,TX2,260)
        # pulsing target
        p=1.0+0.05*math.sin(self._t*3.5)
        ts=F_SC.render(str(self.gs.target),True,ACCENT)
        tw,th=ts.get_size(); nw,nh=max(1,int(tw*p)),max(1,int(th*p))
        ts2=pygame.transform.smoothscale(ts,(nw,nh)); surf.blit(ts2,(W//2-nw//2,290))
        txtm(surf,f"runs to win in {MAX_OVERS} overs",F_MD,TX2,372)
        rrr_req=self.gs.target*6/(MAX_OVERS*6)
        rrr_col=ACCENT if rrr_req<9 else (GOLD if rrr_req<13 else RED)
        txtm(surf,f"Required Rate: {rrr_req:.2f}",F_SM,rrr_col,404)

        for b in self.buttons: b.draw(surf)

# ═══════════════════════════════════════════════════════════
#  SCREEN 5 — RESULT
# ═══════════════════════════════════════════════════════════
class ResultScreen(Screen):
    def __init__(self,gs):
        super().__init__(gs)
        b1,b2=gs.bat1,gs.bat2; self._t=0.0
        self._won2=b2.score>=gs.target
        self._win=b2 if self._won2 else b1
        self._pw=(self._win.code==gs.player_team)
        self._mg=f"by {MAX_WICKETS-b2.wickets} wickets" if self._won2 else f"by {gs.target-b2.score-1} runs"
        self._parts=Particles()
        wc=ACCENT if self._pw else RED
        for _ in range(6):
            self._parts.emit(random.randint(60,W-60),random.randint(100,300),wc,8,100)
        self.buttons=[
            Button((20,H-136,W-40,50),"PLAY AGAIN",F_LG,
                   bg=ACCENT,fg=BLK,hov=ACC2,abg=ACC2,afg=BLK,bc=ACC2,rad=12,tag="a"),
            Button((20,H-76, W-40,46),"MAIN MENU", F_MD,
                   bg=BG4, fg=TX2, rad=12, tag="m"),
        ]

    def on_button(self,b):
        if b.tag in("a","m"): self.gs.__init__(); self.next="menu"

    def update(self,dt):
        super().update(dt); self._t+=dt; self._parts.update(dt)
        if self._t<2.0 and random.random()<0.15:
            wc=ACCENT if self._pw else RED
            self._parts.emit(random.randint(40,W-40),200,wc,6,80)

    def draw(self,surf):
        surf.fill(BG); gs=self.gs; rc=ACCENT if self._pw else RED
        c=lerp(BG2,lerp(rc,BG,0.92),abs(math.sin(self._t*0.3)))
        grad(surf,c,BG,(0,0,W,150)); glow(surf,rc,0,3)
        self._parts.draw(surf)

        # Trophy
        bounce=int(6*math.sin(self._t*2.8))
        icon="W" if self._pw else "L"
        circle_a(surf,rc,W//2,62+bounce,52,60)
        pygame.draw.circle(surf,rc,(W//2,62+bounce),52,3)
        txtm(surf,icon,F_XXL,rc,40+bounce)

        txtm(surf,f"{self._win.name.upper()}  WIN!",F_XL,rc,84)
        txtm(surf,self._mg,F_MD,TX2,116)
        pygame.draw.line(surf,BORDER,(0,150),(W,150),1)

        # Scorecard glass card
        draw_shadow(surf,(16,160,W-32,178),16,8,80)
        glass_card(surf,(16,160,W-32,178),col=BG3,border=BORDER,alpha=220,radius=16)
        txt(surf,"SCORECARD",F_XS,TX3,32,172)
        pygame.draw.line(surf,BORDER,(32,188),(W-32,188),1)

        for i,t in enumerate([gs.bat1,gs.bat2]):
            ry=196+i*66; iw=(t==self._win); tc=t.col if iw else TX2
            bf=F_MD if iw else F_SM; pr=">> " if iw else "   "
            txt(surf,f"{pr}{t.name}",bf,tc,32,ry)
            txt(surf,t.fmt_score(),F_MO,tc,W-30,ry,align="right")
            txt(surf,f"({t.fmt_overs()} ov)  CRR {t.crr:.2f}  4s:{t.boundaries}  6s:{t.sixes}",
                F_MOS,TX3,W-30,ry+20,align="right")
            if i==0: pygame.draw.line(surf,BORDER,(32,ry+58),(W-32,ry+58),1)

        txtm(surf,f"{gs.venue['name']} · {gs.venue['city']} · {gs.venue['country']}",F_XS,TX3,352)
        for b in self.buttons: b.draw(surf)
        if self._dialog: self._dialog.draw(surf)

# ───────────────────────────────────────────────────────────
#  APP LOOP
# ───────────────────────────────────────────────────────────
SCREENS={"menu":MenuScreen,"toss":TossScreen,"match":MatchScreen,
         "break":BreakScreen,"result":ResultScreen}

def main():
    gs=GS(); cur=MenuScreen(gs)
    while True:
        dt=min(clock.tick(FPS)/1000.0, 0.05)
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT:
                pygame.quit(); sys.exit()
            cur.handle(ev)
        cur.update(dt); cur.draw(screen); pygame.display.flip()
        if cur.next: cur=SCREENS[cur.next](gs)

if __name__=="__main__":
    main()
