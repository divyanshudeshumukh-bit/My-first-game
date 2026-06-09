"""
Cricket Simulator v7.0
======================
All 13 features added on top of the complete v6.6 codebase.
Requires Python 3.8+ and pygame 2.x

NEW FEATURES:
  F1  – Tournament System (T20 WC, Champions Trophy, Tri-Series, Bilateral)
  F2  – Ball-by-Ball mode with live scoreboard
  F3  – Manual player control (openers, next batter, bowler choice)
  F4  – Field settings (Defensive / Balanced / Attacking) with visual mini-map
  F5  – Post-match hub (scorecard, PoM, Play Again / Return Home)
  F6  – Realistic bowling types validated by bowler role
  F7  – Per-over simulation-mode prompt (Ball-by-Ball vs Full Over)
  F8  – Powerplay system with visual indicator
  F9  – Advanced animations (coin-flip, bat swing, trajectory, fireworks)
  F10 – Extended randomised commentary pool
  F11 – Enhanced match AI (powerplay aggression, chase strategy, etc.)
  F12 – Full statistics (SR, Economy, Fifties, Tons, 5-fers, Orange/Purple Cap)
  F13 – Code quality (modular classes, comments, 60 FPS)
"""

import pygame, random, sys, math, copy
pygame.init()

# ─────────────────────────────────────────────────────────────
#  WINDOW
# ─────────────────────────────────────────────────────────────
W, H  = 500, 880
FPS   = 60
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Cricket Simulator v7.0")
clock  = pygame.time.Clock()

# ─────────────────────────────────────────────────────────────
#  PALETTE
# ─────────────────────────────────────────────────────────────
def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

BG   = hx("060c18"); BG2 = hx("091528"); BG3 = hx("0d2040")
BG4  = hx("142c52"); BG5 = hx("1b3866")
ACG  = hx("00e676"); AC2 = hx("00c853"); AC3 = hx("69f0ae")
GLD  = hx("ffd740"); GL2 = hx("ffab00"); GL3 = hx("fff59d")
RED  = hx("ff5252"); RD2 = hx("b71c1c"); RD3 = hx("ff8a80")
BLU  = hx("448aff"); BL2 = hx("82b1ff"); BL3 = hx("bbdefb")
PRP  = hx("ce93d8"); CYN = hx("4dd0e1"); ORG = hx("ff9800")
TXT  = hx("f0f4ff"); TX2 = hx("8ba8c8"); TX3 = hx("3a5570")
BDR  = hx("162e48"); WH  = (255,255,255); BK  = (0,0,0)
BAT_T= hx("001508"); BOW_T= hx("180400")

def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))

# ─────────────────────────────────────────────────────────────
#  FONTS
# ─────────────────────────────────────────────────────────────
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
F_XL=_sf(26,True); F_XXL=_sf(38,True); F_SC=_sf(52,True)
F_MO=_mf(12,True); F_MOS=_mf(10)

# ─────────────────────────────────────────────────────────────
#  DRAW PRIMITIVES
# ─────────────────────────────────────────────────────────────
def rr(surf,col,rect,r=10,alpha=None):
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

def circ_a(surf,col,cx,cy,radius,alpha=200):
    if radius<1: return
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

def glow_line(surf,col,y,w=3,a=200):
    s=pygame.Surface((W,w+8),pygame.SRCALPHA)
    for i in range(w+8):
        al=int(a*math.exp(-0.5*((i-(w+8)//2)/2.0)**2))
        pygame.draw.line(s,(*col,al),(0,i),(W,i))
    surf.blit(s,(0,y-(w+8)//2))

def glass(surf,rect,col=BG3,border=BDR,alpha=215,r=14):
    rr(surf,col,rect,r,alpha=alpha)
    rb(surf,(*border,90),rect,1,r)

def shadow(surf,rect,r=14,sp=8,a=70):
    sr=(rect[0]-sp//2,rect[1]+sp//2,rect[2]+sp,rect[3]+sp//2)
    rr(surf,BK,sr,r+2,alpha=a)

def glow_rect(surf,col,rect,r=14,spread=6,a=80):
    sr=(rect[0]-spread,rect[1]-spread,rect[2]+spread*2,rect[3]+spread*2)
    rr(surf,col,sr,r+spread,alpha=a)

# ─────────────────────────────────────────────────────────────
#  SCREEN TRANSITION
# ─────────────────────────────────────────────────────────────
class Transition:
    def __init__(self, kind="fade", duration=0.25):
        self.kind=kind; self.dur=duration
        self.t=0.0; self.done=False; self._out=True

    def start_out(self): self.t=0.0; self._out=True; self.done=False
    def start_in(self):  self.t=0.0; self._out=False; self.done=False

    def update(self, dt):
        self.t=min(self.dur, self.t+dt)
        if self.t>=self.dur: self.done=True

    def draw(self, surf):
        p=self.t/max(self.dur,0.001)
        if self.kind=="fade":
            a=int(255*p) if self._out else int(255*(1-p))
            ov=pygame.Surface((W,H),pygame.SRCALPHA)
            ov.fill((0,0,0,a)); surf.blit(ov,(0,0))

# ─────────────────────────────────────────────────────────────
#  BACKGROUND PARTICLES
# ─────────────────────────────────────────────────────────────
class BgParticles:
    def __init__(self, n=20):
        self.pts=[]
        for _ in range(n):
            self.pts.append({
                "x":random.uniform(0,W), "y":random.uniform(0,H),
                "vy":random.uniform(-18,-6), "vx":random.uniform(-4,4),
                "r":random.uniform(1,3), "a":random.uniform(20,60),
                "col":random.choice([BLU,ACG,GLD,PRP]),
            })

    def update(self, dt):
        for p in self.pts:
            p["x"]+=p["vx"]*dt; p["y"]+=p["vy"]*dt
            if p["y"]<-10: p["y"]=H+5; p["x"]=random.uniform(0,W)

    def draw(self, surf):
        for p in self.pts:
            circ_a(surf,p["col"],int(p["x"]),int(p["y"]),int(p["r"]),int(p["a"]))

# ─────────────────────────────────────────────────────────────
#  BUTTON
# ─────────────────────────────────────────────────────────────
class Button:
    def __init__(self, rect, text, f=None,
                 bg=BG4, fg=TXT, hov=BG5,
                 abg=ACG, afg=BK,
                 bc=BDR, rad=12, tag=None, dis=False,
                 glow_col=None):
        self.rect=pygame.Rect(rect); self.text=text; self.f=f or F_MD
        self.bg=bg; self.fg=fg; self.hov=hov; self.abg=abg; self.afg=afg
        self.bc=bc; self.rad=rad; self.tag=tag; self.dis=dis
        self.glow_col=glow_col
        self.sel=False; self.hovered=False; self.pressed=False
        self._a=0.0; self._spring=0.0

    def update(self, dt):
        if self.dis: self._a=0.0; return
        tgt=1.0 if (self.hovered or self.sel) else 0.0
        self._a+=(tgt-self._a)*min(1.0,dt*16)
        self._spring*=(1-dt*18)

    def handle(self, ev):
        if self.dis: return False
        if ev.type==pygame.MOUSEMOTION:
            self.hovered=self.rect.collidepoint(ev.pos)
        if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
            if self.rect.collidepoint(ev.pos): self.pressed=True; self._spring=1.0
        if ev.type==pygame.MOUSEBUTTONUP and ev.button==1:
            if self.pressed and self.rect.collidepoint(ev.pos):
                self.pressed=False; return True
            self.pressed=False
        return False

    def draw(self, surf):
        t=self._a; sp=self._spring*2
        if self.dis:
            bgc=lerp(self.bg,BG,0.65); fgc=TX3; bcc=BDR
        elif self.sel:
            bgc=self.abg; fgc=self.afg; bcc=lerp(self.abg,WH,0.35)
        else:
            bgc=lerp(self.bg,self.hov,t); fgc=lerp(self.fg,WH,t*0.25)
            bcc=lerp(self.bc,TX2,t*0.6)

        if (self.sel or self._a>0.5) and self.glow_col:
            glow_rect(surf,self.glow_col or self.abg,self.rect,self.rad,6,int(60*self._a))
        elif self.sel and not self.glow_col:
            glow_rect(surf,self.abg,self.rect,self.rad,6,50)

        rc=self.rect.inflate(-int(sp*2),-int(sp)) if sp>0.1 else self.rect
        rr(surf,bgc,rc,self.rad)
        rb(surf,bcc,rc,1,self.rad)
        if self.sel: rr(surf,self.abg,rc,self.rad,alpha=22)

        lines=self.text.split("\n"); lh=self.f.get_height()
        tot=lh*len(lines)+2*(len(lines)-1); sy=rc.centery-tot//2
        for line in lines:
            img=self.f.render(line,True,fgc)
            surf.blit(img,(rc.centerx-img.get_width()//2,sy)); sy+=lh+2

# ─────────────────────────────────────────────────────────────
#  TOAST
# ─────────────────────────────────────────────────────────────
class Toast:
    def __init__(self): self.text=""; self.col=ACG; self.timer=0.0; self.dur=0.8; self.on=False
    def show(self,t,c=ACG,d=0.8): self.text=t; self.col=c; self.timer=0.0; self.dur=d; self.on=True
    def update(self,dt):
        if self.on:
            self.timer+=dt
            if self.timer>=self.dur: self.on=False
    def draw(self,surf):
        if not self.on: return
        t=self.timer/self.dur; a=int(255*(1-t)*min(1.0,(1-t)*4))
        sc=1.0+0.22*math.sin(t*math.pi)
        img0=F_SC.render(self.text,True,self.col); w0,h0=img0.get_size()
        nw,nh=max(1,int(w0*sc)),max(1,int(h0*sc))
        imgs=pygame.transform.smoothscale(img0,(nw,nh)); imgs.set_alpha(a)
        surf.blit(imgs,(W//2-nw//2,H//2-170-nh//2))

# ─────────────────────────────────────────────────────────────
#  PARTICLES  (F9 – extended for fireworks & trajectories)
# ─────────────────────────────────────────────────────────────
class Particles:
    def __init__(self): self.parts=[]

    def emit(self,x,y,col,n=12,speed=120):
        for _ in range(n):
            a=random.uniform(0,math.pi*2); sp=random.uniform(40,speed)
            self.parts.append([float(x),float(y),math.cos(a)*sp,math.sin(a)*sp,
                               random.uniform(0.4,1.0),col,random.randint(3,7)])

    # F9 – fireworks burst (upward fountain then gravity)
    def emit_firework(self,x,y,col,n=30):
        for _ in range(n):
            a=random.uniform(-math.pi,0); sp=random.uniform(60,200)
            life=random.uniform(0.8,1.8); sz=random.randint(2,5)
            self.parts.append([float(x),float(y),math.cos(a)*sp,math.sin(a)*sp,life,col,sz])

    # F9 – ball trajectory arc (visual only, fades quickly)
    def emit_trajectory(self,sx,sy,kind="drive"):
        col={"six":ACG,"four":GLD,"yorker":RED,"bouncer":PRP}.get(kind,BLU)
        n=18
        if kind=="six":
            for i in range(n):
                t=i/n; x=sx+t*(W//2-sx); y=sy-int(120*math.sin(t*math.pi))+int(t*60)
                self.parts.append([float(x),float(y),0,0,0.5-t*0.3,col,3])
        elif kind=="four":
            for i in range(n):
                t=i/n; x=sx+t*(W-20-sx); y=sy+int(t*30)
                self.parts.append([float(x),float(y),0,0,0.6-t*0.4,col,3])
        elif kind=="bouncer":
            for i in range(n):
                t=i/n; x=sx+t*(W//2-sx); y=sy+int(80*math.sin(t*math.pi*2)*0.4)
                self.parts.append([float(x),float(y),0,0,0.5,col,2])

    def update(self,dt):
        keep=[]
        for p in self.parts:
            p[0]+=p[2]*dt; p[1]+=p[3]*dt; p[3]+=220*dt; p[4]-=dt
            if p[4]>0: keep.append(p)
        self.parts=keep

    def draw(self,surf):
        for p in self.parts:
            a=int(255*max(0,p[4])); r=p[6]
            circ_a(surf,p[5],int(p[0]),int(p[1]),r,a)

# ─────────────────────────────────────────────────────────────
#  CAROUSEL
# ─────────────────────────────────────────────────────────────
class Carousel:
    CW=210; CH=124; GAP=18; SPD=11.0
    def __init__(self,items,idx=0,y=0,draw_fn=None):
        self.items=items; self.idx=idx; self._x=float(idx)
        self.y=y; self.draw_fn=draw_fn; self._ds=None; self._dx=0.0
        ax=W//2-self.CW//2-52
        self.bl=Button((ax,y+38,38,48),"<",F_LG,bg=BG4,fg=TX2,hov=BG5,abg=ACG,afg=BK,rad=8)
        self.br=Button((W//2+self.CW//2+14,y+38,38,48),">",F_LG,bg=BG4,fg=TX2,hov=BG5,abg=ACG,afg=BK,rad=8)

    def handle(self,ev):
        if self.bl.handle(ev): self.idx=(self.idx-1)%len(self.items); return True
        if self.br.handle(ev): self.idx=(self.idx+1)%len(self.items); return True
        if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
            _,yp=ev.pos
            if abs(yp-self.y-62)<72: self._ds=ev.pos[0]; self._dx=0.0
        if ev.type==pygame.MOUSEMOTION and self._ds is not None:
            self._dx=self._ds-ev.pos[0]
        if ev.type==pygame.MOUSEBUTTONUP and ev.button==1 and self._ds is not None:
            if self._dx>38:   self.idx=(self.idx+1)%len(self.items)
            elif self._dx<-38: self.idx=(self.idx-1)%len(self.items)
            self._ds=None; self._dx=0.0; return True
        return False

    def update(self,dt):
        self.bl.update(dt); self.br.update(dt)
        diff=self.idx-self._x; n=len(self.items)
        if diff>n/2:  diff-=n
        elif diff<-n/2: diff+=n
        self._x+=diff*min(1.0,self.SPD*dt)

    def draw(self,surf):
        cw=self.CW; ch=self.CH; cx=W//2; n=len(self.items)
        for offset in [-2,-1,0,1,2]:
            ii=(int(round(self._x))+offset)%n
            fo=offset-(self._x-round(self._x))
            px=cx+int(fo*(cw+self.GAP))-cw//2; py=self.y
            al=255 if offset==0 else 120; sc=1.0 if offset==0 else 0.83
            sw,sh=int(cw*sc),int(ch*sc); sx=px+(cw-sw)//2; sy=py+(ch-sh)//2
            item=self.items[ii]; sel=(ii==self.idx)
            if self.draw_fn: self.draw_fn(surf,item,(sx,sy,sw,sh),sel,al)
            else: rr(surf,BG3,(sx,sy,sw,sh),12,alpha=al)
        self.bl.draw(surf); self.br.draw(surf)

    @property
    def selected(self): return self.items[self.idx]

# ─────────────────────────────────────────────────────────────
#  CONFIRM DIALOG
# ─────────────────────────────────────────────────────────────
class ConfirmDialog:
    def __init__(self,msg,yes_cb,no_cb=None):
        self.msg=msg; self.yes_cb=yes_cb; self.no_cb=no_cb
        dw,dh=360,184; dx=W//2-dw//2; dy=H//2-dh//2
        self.rect=(dx,dy,dw,dh); self._al=0.0
        self.by=Button((dx+24,dy+124,144,48),"  YES",F_MD,bg=RED,fg=WH,hov=RD2,abg=RD2,afg=WH,rad=12)
        self.bn=Button((dx+192,dy+124,144,48),"  NO", F_MD,bg=BG4,fg=TX2,hov=BG5,abg=BG5,afg=TX2,rad=12)

    def handle(self,ev):
        if self.by.handle(ev): self.yes_cb(); return True
        if self.bn.handle(ev):
            if self.no_cb: self.no_cb()
            return True
        return False

    def update(self,dt):
        self._al=min(1.0,self._al+dt*8); self.by.update(dt); self.bn.update(dt)

    def draw(self,surf):
        ov=pygame.Surface((W,H),pygame.SRCALPHA)
        ov.fill((0,0,0,int(200*self._al))); surf.blit(ov,(0,0))
        dx,dy,dw,dh=self.rect; shadow(surf,self.rect,20,12,100)
        rr(surf,BG3,(dx,dy,dw,dh),20); rb(surf,BDR,(dx,dy,dw,dh),1,20)
        glow_line(surf,ACG,dy,2,60)
        for i,l in enumerate(self.msg.split("\n")):
            txtm(surf,l,F_MD,TXT,dy+26+i*30)
        self.by.draw(surf); self.bn.draw(surf)

# ─────────────────────────────────────────────────────────────
#  GAME DATA — teams
# ─────────────────────────────────────────────────────────────
MAX_WICKETS=10
FORMATS={"T20":{"overs":20,"name":"T20"},"ODI":{"overs":50,"name":"ODI"}}

TEAMS=[
    {"code":"IND","name":"India",       "abbr":"IND","col":hx("ff9800"),"dark":hx("bf360c")},
    {"code":"AUS","name":"Australia",   "abbr":"AUS","col":hx("ffeb3b"),"dark":hx("f57f17")},
    {"code":"ENG","name":"England",     "abbr":"ENG","col":hx("5c9bff"),"dark":hx("0d47a1")},
    {"code":"SL", "name":"Sri Lanka",   "abbr":"SL", "col":hx("4dd0e1"),"dark":hx("006064")},
    {"code":"PAK","name":"Pakistan",    "abbr":"PAK","col":hx("69f0ae"),"dark":hx("1b5e20")},
    {"code":"NZ", "name":"New Zealand", "abbr":"NZ", "col":hx("ef9a9a"),"dark":hx("b71c1c")},
    {"code":"SA", "name":"S. Africa",   "abbr":"SA", "col":hx("a5d6a7"),"dark":hx("1b5e20")},
    {"code":"WI", "name":"West Indies", "abbr":"WI", "col":hx("ce93d8"),"dark":hx("4a148c")},
]

# ─────────────────────────────────────────────────────────────
#  T20 SQUADS
# ─────────────────────────────────────────────────────────────
T20_SQUADS={
"IND":[
    {"name":"Shreyas Iyer",         "role":"Batsman",       "bat":85,"bowl":15,"field":80,"rating":84},
    {"name":"Tilak Varma",          "role":"Batsman",       "bat":82,"bowl":10,"field":78,"rating":80},
    {"name":"Sanju Samson",         "role":"Wicket Keeper", "bat":82,"bowl":0, "field":84,"rating":82},
    {"name":"Ishan Kishan",         "role":"Wicket Keeper", "bat":78,"bowl":0, "field":82,"rating":76},
    {"name":"Abhishek Sharma",      "role":"Opener",        "bat":80,"bowl":30,"field":78,"rating":78},
    {"name":"Vaibhav Sooryavanshi", "role":"Opener",        "bat":76,"bowl":0, "field":76,"rating":74},
    {"name":"Axar Patel",           "role":"All-Rounder",   "bat":65,"bowl":84,"field":80,"rating":78},
    {"name":"Washington Sundar",    "role":"All-Rounder",   "bat":60,"bowl":80,"field":76,"rating":75},
    {"name":"Shivam Dube",          "role":"All-Rounder",   "bat":74,"bowl":68,"field":75,"rating":72},
    {"name":"Nitish Kumar Reddy",   "role":"All-Rounder",   "bat":70,"bowl":72,"field":74,"rating":72},
    {"name":"Jasprit Bumrah",       "role":"Fast Bowler",   "bat":20,"bowl":96,"field":75,"rating":93},
    {"name":"Mohammed Siraj",       "role":"Fast Bowler",   "bat":18,"bowl":84,"field":74,"rating":80},
    {"name":"Arshdeep Singh",       "role":"Fast Bowler",   "bat":15,"bowl":80,"field":72,"rating":76},
    {"name":"Ravi Bishnoi",         "role":"Spinner",       "bat":22,"bowl":82,"field":70,"rating":78},
    {"name":"Varun Chakaravarthy",  "role":"Spinner",       "bat":18,"bowl":84,"field":68,"rating":79},
],
"AUS":[
    {"name":"Josh Inglis",          "role":"Wicket Keeper", "bat":78,"bowl":0, "field":84,"rating":78},
    {"name":"Mitchell Marsh",       "role":"All-Rounder",   "bat":76,"bowl":72,"field":78,"rating":76},
    {"name":"Alex Carey",           "role":"Wicket Keeper", "bat":74,"bowl":0, "field":86,"rating":76},
    {"name":"Travis Head",          "role":"Opener",        "bat":88,"bowl":40,"field":80,"rating":86},
    {"name":"Sam Konstas",          "role":"Opener",        "bat":80,"bowl":0, "field":78,"rating":78},
    {"name":"Tim David",            "role":"Batsman",       "bat":82,"bowl":20,"field":78,"rating":80},
    {"name":"Glenn Maxwell",        "role":"All-Rounder",   "bat":82,"bowl":70,"field":84,"rating":82},
    {"name":"Marcus Stoinis",       "role":"All-Rounder",   "bat":78,"bowl":68,"field":78,"rating":76},
    {"name":"Cameron Green",        "role":"All-Rounder",   "bat":78,"bowl":74,"field":80,"rating":78},
    {"name":"Aaron Hardie",         "role":"All-Rounder",   "bat":72,"bowl":68,"field":74,"rating":70},
    {"name":"Josh Hazlewood",       "role":"Fast Bowler",   "bat":20,"bowl":88,"field":73,"rating":85},
    {"name":"Adam Zampa",           "role":"Spinner",       "bat":25,"bowl":85,"field":70,"rating":81},
    {"name":"Nathan Ellis",         "role":"Fast Bowler",   "bat":18,"bowl":78,"field":70,"rating":74},
    {"name":"Xavier Bartlett",      "role":"Fast Bowler",   "bat":16,"bowl":76,"field":68,"rating":72},
    {"name":"Matthew Kuhnemann",    "role":"Spinner",       "bat":22,"bowl":76,"field":68,"rating":72},
],
"ENG":[
    {"name":"Harry Brook",          "role":"Batsman",       "bat":88,"bowl":30,"field":82,"rating":86},
    {"name":"Jos Buttler",          "role":"Wicket Keeper", "bat":88,"bowl":0, "field":86,"rating":88},
    {"name":"Phil Salt",            "role":"Wicket Keeper", "bat":80,"bowl":0, "field":80,"rating":78},
    {"name":"Ben Duckett",          "role":"Opener",        "bat":82,"bowl":20,"field":78,"rating":80},
    {"name":"Zak Crawley",          "role":"Opener",        "bat":83,"bowl":10,"field":78,"rating":80},
    {"name":"Sam Curran",           "role":"All-Rounder",   "bat":70,"bowl":78,"field":78,"rating":76},
    {"name":"Liam Livingstone",     "role":"All-Rounder",   "bat":78,"bowl":72,"field":78,"rating":78},
    {"name":"Will Jacks",           "role":"All-Rounder",   "bat":74,"bowl":74,"field":76,"rating":74},
    {"name":"Jacob Bethell",        "role":"All-Rounder",   "bat":72,"bowl":70,"field":74,"rating":72},
    {"name":"Jofra Archer",         "role":"Fast Bowler",   "bat":30,"bowl":88,"field":74,"rating":84},
    {"name":"Mark Wood",            "role":"Fast Bowler",   "bat":22,"bowl":84,"field":72,"rating":78},
    {"name":"Adil Rashid",          "role":"Spinner",       "bat":40,"bowl":84,"field":72,"rating":80},
    {"name":"Gus Atkinson",         "role":"Fast Bowler",   "bat":28,"bowl":80,"field":72,"rating":76},
    {"name":"Brydon Carse",         "role":"Fast Bowler",   "bat":24,"bowl":78,"field":70,"rating":74},
    {"name":"Rehan Ahmed",          "role":"Spinner",       "bat":20,"bowl":80,"field":68,"rating":76},
],
"SL":[
    {"name":"Charith Asalanka",     "role":"Batsman",       "bat":80,"bowl":30,"field":78,"rating":78},
    {"name":"Kusal Mendis",         "role":"Wicket Keeper", "bat":82,"bowl":0, "field":82,"rating":80},
    {"name":"Kusal Perera",         "role":"Wicket Keeper", "bat":76,"bowl":0, "field":80,"rating":74},
    {"name":"Pathum Nissanka",      "role":"Opener",        "bat":82,"bowl":15,"field":78,"rating":80},
    {"name":"Nuwanidu Fernando",    "role":"Opener",        "bat":76,"bowl":10,"field":76,"rating":74},
    {"name":"Kamindu Mendis",       "role":"Batsman",       "bat":78,"bowl":20,"field":76,"rating":76},
    {"name":"Wanindu Hasaranga",    "role":"All-Rounder",   "bat":64,"bowl":88,"field":76,"rating":82},
    {"name":"Dunith Wellalage",     "role":"All-Rounder",   "bat":58,"bowl":82,"field":74,"rating":76},
    {"name":"Dasun Shanaka",        "role":"All-Rounder",   "bat":72,"bowl":65,"field":76,"rating":72},
    {"name":"Chamika Karunaratne",  "role":"All-Rounder",   "bat":62,"bowl":74,"field":72,"rating":68},
    {"name":"Maheesh Theekshana",   "role":"Spinner",       "bat":28,"bowl":86,"field":72,"rating":80},
    {"name":"Matheesha Pathirana",  "role":"Fast Bowler",   "bat":14,"bowl":85,"field":70,"rating":80},
    {"name":"Dushmantha Chameera",  "role":"Fast Bowler",   "bat":22,"bowl":82,"field":72,"rating":76},
    {"name":"Nuwan Thushara",       "role":"Fast Bowler",   "bat":16,"bowl":78,"field":68,"rating":72},
    {"name":"Binura Fernando",      "role":"Fast Bowler",   "bat":14,"bowl":76,"field":68,"rating":70},
],
"PAK":[
    {"name":"Salman Ali Agha",      "role":"All-Rounder",   "bat":72,"bowl":74,"field":76,"rating":74},
    {"name":"Babar Azam",           "role":"Batsman",       "bat":93,"bowl":20,"field":86,"rating":91},
    {"name":"Mohammad Rizwan",      "role":"Wicket Keeper", "bat":86,"bowl":0, "field":84,"rating":86},
    {"name":"Fakhar Zaman",         "role":"Opener",        "bat":84,"bowl":15,"field":78,"rating":82},
    {"name":"Saim Ayub",            "role":"Opener",        "bat":80,"bowl":15,"field":78,"rating":78},
    {"name":"Abdullah Shafique",    "role":"Batsman",       "bat":78,"bowl":10,"field":76,"rating":76},
    {"name":"Shadab Khan",          "role":"All-Rounder",   "bat":68,"bowl":84,"field":78,"rating":80},
    {"name":"Iftikhar Ahmed",       "role":"All-Rounder",   "bat":74,"bowl":62,"field":72,"rating":72},
    {"name":"Mohammad Nawaz",       "role":"All-Rounder",   "bat":64,"bowl":80,"field":76,"rating":76},
    {"name":"Faheem Ashraf",        "role":"All-Rounder",   "bat":60,"bowl":74,"field":72,"rating":68},
    {"name":"Shaheen Shah Afridi",  "role":"Fast Bowler",   "bat":22,"bowl":91,"field":74,"rating":88},
    {"name":"Haris Rauf",           "role":"Fast Bowler",   "bat":20,"bowl":84,"field":72,"rating":80},
    {"name":"Naseem Shah",          "role":"Fast Bowler",   "bat":18,"bowl":86,"field":72,"rating":82},
    {"name":"Abrar Ahmed",          "role":"Spinner",       "bat":18,"bowl":82,"field":68,"rating":76},
    {"name":"Usama Mir",            "role":"Spinner",       "bat":20,"bowl":80,"field":68,"rating":74},
],
"NZ":[
    {"name":"Mitchell Santner",     "role":"All-Rounder",   "bat":64,"bowl":82,"field":76,"rating":78},
    {"name":"Tom Latham",           "role":"Wicket Keeper", "bat":82,"bowl":0, "field":84,"rating":82},
    {"name":"Devon Conway",         "role":"Wicket Keeper", "bat":86,"bowl":0, "field":80,"rating":84},
    {"name":"Kane Williamson",      "role":"Batsman",       "bat":93,"bowl":40,"field":84,"rating":91},
    {"name":"Finn Allen",           "role":"Opener",        "bat":82,"bowl":10,"field":76,"rating":80},
    {"name":"Glenn Phillips",       "role":"Batsman",       "bat":80,"bowl":62,"field":80,"rating":80},
    {"name":"Rachin Ravindra",      "role":"All-Rounder",   "bat":78,"bowl":70,"field":78,"rating":78},
    {"name":"Daryl Mitchell",       "role":"All-Rounder",   "bat":80,"bowl":68,"field":78,"rating":78},
    {"name":"James Neesham",        "role":"All-Rounder",   "bat":68,"bowl":72,"field":74,"rating":70},
    {"name":"Michael Bracewell",    "role":"All-Rounder",   "bat":70,"bowl":72,"field":72,"rating":70},
    {"name":"Matt Henry",           "role":"Fast Bowler",   "bat":20,"bowl":82,"field":70,"rating":76},
    {"name":"Lockie Ferguson",      "role":"Fast Bowler",   "bat":18,"bowl":84,"field":70,"rating":78},
    {"name":"Ish Sodhi",            "role":"Spinner",       "bat":28,"bowl":82,"field":68,"rating":76},
    {"name":"Adam Milne",           "role":"Fast Bowler",   "bat":16,"bowl":80,"field":68,"rating":74},
    {"name":"Kyle Jamieson",        "role":"Fast Bowler",   "bat":40,"bowl":82,"field":72,"rating":76},
],
"SA":[
    {"name":"Aiden Markram",        "role":"All-Rounder",   "bat":82,"bowl":65,"field":80,"rating":82},
    {"name":"Keshav Maharaj",       "role":"Spinner",       "bat":32,"bowl":84,"field":70,"rating":78},
    {"name":"Quinton de Kock",      "role":"Wicket Keeper", "bat":88,"bowl":0, "field":86,"rating":88},
    {"name":"Tristan Stubbs",       "role":"Batsman",       "bat":80,"bowl":10,"field":78,"rating":78},
    {"name":"David Miller",         "role":"Batsman",       "bat":86,"bowl":10,"field":80,"rating":84},
    {"name":"Reeza Hendricks",      "role":"Opener",        "bat":80,"bowl":10,"field":76,"rating":78},
    {"name":"Dewald Brevis",        "role":"Batsman",       "bat":78,"bowl":15,"field":76,"rating":76},
    {"name":"Marco Jansen",         "role":"All-Rounder",   "bat":62,"bowl":84,"field":74,"rating":78},
    {"name":"George Linde",         "role":"All-Rounder",   "bat":58,"bowl":78,"field":72,"rating":72},
    {"name":"Corbin Bosch",         "role":"All-Rounder",   "bat":60,"bowl":76,"field":72,"rating":70},
    {"name":"Kagiso Rabada",        "role":"Fast Bowler",   "bat":30,"bowl":92,"field":76,"rating":89},
    {"name":"Anrich Nortje",        "role":"Fast Bowler",   "bat":20,"bowl":87,"field":72,"rating":81},
    {"name":"Lungi Ngidi",          "role":"Fast Bowler",   "bat":18,"bowl":84,"field":70,"rating":78},
    {"name":"Kwena Maphaka",        "role":"Fast Bowler",   "bat":14,"bowl":80,"field":68,"rating":74},
    {"name":"Tabraiz Shamsi",       "role":"Spinner",       "bat":18,"bowl":85,"field":68,"rating":79},
],
"WI":[
    {"name":"Rovman Powell",        "role":"Batsman",       "bat":80,"bowl":30,"field":76,"rating":78},
    {"name":"Shai Hope",            "role":"Wicket Keeper", "bat":82,"bowl":0, "field":82,"rating":80},
    {"name":"Nicholas Pooran",      "role":"Wicket Keeper", "bat":86,"bowl":0, "field":82,"rating":84},
    {"name":"Brandon King",         "role":"Opener",        "bat":80,"bowl":10,"field":76,"rating":78},
    {"name":"Shimron Hetmyer",      "role":"Batsman",       "bat":82,"bowl":10,"field":74,"rating":80},
    {"name":"Sherfane Rutherford",  "role":"Batsman",       "bat":78,"bowl":20,"field":74,"rating":76},
    {"name":"Jason Holder",         "role":"All-Rounder",   "bat":68,"bowl":84,"field":78,"rating":80},
    {"name":"Andre Russell",        "role":"All-Rounder",   "bat":84,"bowl":78,"field":76,"rating":86},
    {"name":"Kyle Mayers",          "role":"All-Rounder",   "bat":78,"bowl":68,"field":76,"rating":76},
    {"name":"Romario Shepherd",     "role":"All-Rounder",   "bat":66,"bowl":76,"field":72,"rating":70},
    {"name":"Alzarri Joseph",       "role":"Fast Bowler",   "bat":22,"bowl":85,"field":72,"rating":79},
    {"name":"Akeal Hosein",         "role":"Spinner",       "bat":28,"bowl":80,"field":68,"rating":74},
    {"name":"Gudakesh Motie",       "role":"Spinner",       "bat":20,"bowl":79,"field":68,"rating":73},
    {"name":"Obed McCoy",           "role":"Fast Bowler",   "bat":16,"bowl":78,"field":68,"rating":72},
    {"name":"Oshane Thomas",        "role":"Fast Bowler",   "bat":14,"bowl":80,"field":66,"rating":74},
],
}

# ─────────────────────────────────────────────────────────────
#  ODI SQUADS
# ─────────────────────────────────────────────────────────────
ODI_SQUADS={
"IND":[
    {"name":"Rohit Sharma",         "role":"Opener",        "bat":92,"bowl":20,"field":80,"rating":90},
    {"name":"Shubman Gill",         "role":"Opener",        "bat":87,"bowl":15,"field":82,"rating":86},
    {"name":"Virat Kohli",          "role":"Batsman",       "bat":95,"bowl":18,"field":88,"rating":93},
    {"name":"Shreyas Iyer",         "role":"Batsman",       "bat":84,"bowl":15,"field":80,"rating":83},
    {"name":"KL Rahul",             "role":"Wicket Keeper", "bat":83,"bowl":0, "field":85,"rating":83},
    {"name":"Hardik Pandya",        "role":"All-Rounder",   "bat":80,"bowl":75,"field":84,"rating":82},
    {"name":"Ravindra Jadeja",      "role":"All-Rounder",   "bat":74,"bowl":85,"field":90,"rating":84},
    {"name":"Washington Sundar",    "role":"All-Rounder",   "bat":60,"bowl":80,"field":76,"rating":75},
    {"name":"Axar Patel",           "role":"Spinner",       "bat":65,"bowl":82,"field":80,"rating":78},
    {"name":"Jasprit Bumrah",       "role":"Fast Bowler",   "bat":20,"bowl":96,"field":75,"rating":93},
    {"name":"Mohammed Shami",       "role":"Fast Bowler",   "bat":18,"bowl":90,"field":72,"rating":87},
    {"name":"Mohammed Siraj",       "role":"Fast Bowler",   "bat":18,"bowl":84,"field":74,"rating":80},
    {"name":"Kuldeep Yadav",        "role":"Spinner",       "bat":22,"bowl":86,"field":72,"rating":80},
    {"name":"Shardul Thakur",       "role":"All-Rounder",   "bat":58,"bowl":76,"field":76,"rating":72},
    {"name":"Ishan Kishan",         "role":"Wicket Keeper", "bat":80,"bowl":0, "field":82,"rating":78},
],
"AUS":[
    {"name":"David Warner",         "role":"Opener",        "bat":90,"bowl":15,"field":82,"rating":88},
    {"name":"Travis Head",          "role":"Opener",        "bat":86,"bowl":38,"field":80,"rating":84},
    {"name":"Steve Smith",          "role":"Batsman",       "bat":95,"bowl":60,"field":82,"rating":93},
    {"name":"Marnus Labuschagne",   "role":"Batsman",       "bat":88,"bowl":55,"field":80,"rating":86},
    {"name":"Alex Carey",           "role":"Wicket Keeper", "bat":74,"bowl":0, "field":86,"rating":76},
    {"name":"Mitchell Marsh",       "role":"All-Rounder",   "bat":76,"bowl":72,"field":78,"rating":76},
    {"name":"Glenn Maxwell",        "role":"All-Rounder",   "bat":82,"bowl":70,"field":84,"rating":82},
    {"name":"Cameron Green",        "role":"All-Rounder",   "bat":78,"bowl":74,"field":80,"rating":78},
    {"name":"Pat Cummins",          "role":"Fast Bowler",   "bat":36,"bowl":93,"field":76,"rating":90},
    {"name":"Mitchell Starc",       "role":"Fast Bowler",   "bat":28,"bowl":90,"field":74,"rating":87},
    {"name":"Josh Hazlewood",       "role":"Fast Bowler",   "bat":20,"bowl":88,"field":73,"rating":85},
    {"name":"Adam Zampa",           "role":"Spinner",       "bat":25,"bowl":83,"field":70,"rating":79},
    {"name":"Marcus Stoinis",       "role":"All-Rounder",   "bat":78,"bowl":68,"field":78,"rating":76},
    {"name":"Matthew Wade",         "role":"Wicket Keeper", "bat":70,"bowl":0, "field":80,"rating":72},
    {"name":"Sean Abbott",          "role":"Fast Bowler",   "bat":22,"bowl":76,"field":72,"rating":72},
],
"ENG":[
    {"name":"Ben Duckett",          "role":"Opener",        "bat":83,"bowl":20,"field":78,"rating":81},
    {"name":"Zak Crawley",          "role":"Opener",        "bat":83,"bowl":10,"field":78,"rating":80},
    {"name":"Joe Root",             "role":"Batsman",       "bat":94,"bowl":62,"field":85,"rating":92},
    {"name":"Harry Brook",          "role":"Batsman",       "bat":88,"bowl":30,"field":82,"rating":86},
    {"name":"Jos Buttler",          "role":"Wicket Keeper", "bat":88,"bowl":0, "field":86,"rating":88},
    {"name":"Ben Stokes",           "role":"All-Rounder",   "bat":84,"bowl":78,"field":86,"rating":86},
    {"name":"Liam Livingstone",     "role":"All-Rounder",   "bat":78,"bowl":72,"field":78,"rating":78},
    {"name":"Sam Curran",           "role":"All-Rounder",   "bat":70,"bowl":78,"field":78,"rating":76},
    {"name":"Adil Rashid",          "role":"Spinner",       "bat":40,"bowl":84,"field":72,"rating":80},
    {"name":"Jofra Archer",         "role":"Fast Bowler",   "bat":30,"bowl":88,"field":74,"rating":84},
    {"name":"Gus Atkinson",         "role":"Fast Bowler",   "bat":28,"bowl":82,"field":72,"rating":78},
    {"name":"Mark Wood",            "role":"Fast Bowler",   "bat":22,"bowl":84,"field":72,"rating":78},
    {"name":"Chris Woakes",         "role":"All-Rounder",   "bat":62,"bowl":82,"field":76,"rating":78},
    {"name":"Will Jacks",           "role":"All-Rounder",   "bat":74,"bowl":74,"field":76,"rating":74},
    {"name":"Brydon Carse",         "role":"Fast Bowler",   "bat":24,"bowl":78,"field":70,"rating":74},
],
"SL":[
    {"name":"Pathum Nissanka",      "role":"Opener",        "bat":83,"bowl":15,"field":78,"rating":81},
    {"name":"Dimuth Karunaratne",   "role":"Opener",        "bat":84,"bowl":30,"field":78,"rating":82},
    {"name":"Kusal Mendis",         "role":"Wicket Keeper", "bat":82,"bowl":0, "field":82,"rating":80},
    {"name":"Charith Asalanka",     "role":"Batsman",       "bat":80,"bowl":30,"field":78,"rating":78},
    {"name":"Angelo Mathews",       "role":"All-Rounder",   "bat":80,"bowl":68,"field":78,"rating":80},
    {"name":"Kamindu Mendis",       "role":"Batsman",       "bat":78,"bowl":20,"field":76,"rating":76},
    {"name":"Wanindu Hasaranga",    "role":"All-Rounder",   "bat":62,"bowl":88,"field":76,"rating":82},
    {"name":"Dunith Wellalage",     "role":"All-Rounder",   "bat":58,"bowl":82,"field":74,"rating":76},
    {"name":"Maheesh Theekshana",   "role":"Spinner",       "bat":28,"bowl":85,"field":72,"rating":79},
    {"name":"Dushmantha Chameera",  "role":"Fast Bowler",   "bat":22,"bowl":83,"field":72,"rating":77},
    {"name":"Matheesha Pathirana",  "role":"Fast Bowler",   "bat":14,"bowl":84,"field":70,"rating":79},
    {"name":"Lahiru Kumara",        "role":"Fast Bowler",   "bat":16,"bowl":80,"field":70,"rating":74},
    {"name":"Nuwan Pradeep",        "role":"Fast Bowler",   "bat":18,"bowl":80,"field":68,"rating":74},
    {"name":"Dasun Shanaka",        "role":"All-Rounder",   "bat":72,"bowl":65,"field":76,"rating":72},
    {"name":"Kusal Perera",         "role":"Wicket Keeper", "bat":76,"bowl":0, "field":80,"rating":74},
],
"PAK":[
    {"name":"Babar Azam",           "role":"Batsman",       "bat":93,"bowl":20,"field":86,"rating":91},
    {"name":"Mohammad Rizwan",      "role":"Wicket Keeper", "bat":86,"bowl":0, "field":84,"rating":86},
    {"name":"Fakhar Zaman",         "role":"Opener",        "bat":84,"bowl":15,"field":78,"rating":82},
    {"name":"Imam-ul-Haq",          "role":"Opener",        "bat":82,"bowl":10,"field":76,"rating":80},
    {"name":"Saud Shakeel",         "role":"Batsman",       "bat":80,"bowl":20,"field":76,"rating":78},
    {"name":"Abdullah Shafique",    "role":"Batsman",       "bat":78,"bowl":10,"field":76,"rating":76},
    {"name":"Shadab Khan",          "role":"All-Rounder",   "bat":68,"bowl":84,"field":78,"rating":80},
    {"name":"Mohammad Nawaz",       "role":"All-Rounder",   "bat":64,"bowl":80,"field":76,"rating":76},
    {"name":"Shaheen Shah Afridi",  "role":"Fast Bowler",   "bat":22,"bowl":91,"field":74,"rating":88},
    {"name":"Haris Rauf",           "role":"Fast Bowler",   "bat":20,"bowl":84,"field":72,"rating":80},
    {"name":"Naseem Shah",          "role":"Fast Bowler",   "bat":18,"bowl":86,"field":72,"rating":82},
    {"name":"Abrar Ahmed",          "role":"Spinner",       "bat":18,"bowl":82,"field":68,"rating":76},
    {"name":"Usama Mir",            "role":"Spinner",       "bat":20,"bowl":80,"field":68,"rating":74},
    {"name":"Iftikhar Ahmed",       "role":"All-Rounder",   "bat":74,"bowl":62,"field":72,"rating":72},
    {"name":"Hasan Ali",            "role":"Fast Bowler",   "bat":22,"bowl":78,"field":70,"rating":72},
],
"NZ":[
    {"name":"Devon Conway",         "role":"Wicket Keeper", "bat":86,"bowl":0, "field":80,"rating":84},
    {"name":"Will Young",           "role":"Opener",        "bat":79,"bowl":20,"field":76,"rating":77},
    {"name":"Kane Williamson",      "role":"Batsman",       "bat":93,"bowl":40,"field":84,"rating":91},
    {"name":"Tom Latham",           "role":"Wicket Keeper", "bat":82,"bowl":0, "field":84,"rating":82},
    {"name":"Daryl Mitchell",       "role":"All-Rounder",   "bat":80,"bowl":68,"field":78,"rating":78},
    {"name":"Glenn Phillips",       "role":"Batsman",       "bat":80,"bowl":62,"field":80,"rating":80},
    {"name":"Mitchell Santner",     "role":"All-Rounder",   "bat":64,"bowl":82,"field":76,"rating":78},
    {"name":"Tim Southee",          "role":"Fast Bowler",   "bat":34,"bowl":86,"field":74,"rating":82},
    {"name":"Trent Boult",          "role":"Fast Bowler",   "bat":22,"bowl":88,"field":72,"rating":84},
    {"name":"Lockie Ferguson",      "role":"Fast Bowler",   "bat":18,"bowl":84,"field":70,"rating":78},
    {"name":"Ish Sodhi",            "role":"Spinner",       "bat":28,"bowl":82,"field":68,"rating":76},
    {"name":"Kyle Jamieson",        "role":"Fast Bowler",   "bat":40,"bowl":82,"field":72,"rating":76},
    {"name":"Mark Chapman",         "role":"Batsman",       "bat":76,"bowl":20,"field":74,"rating":74},
    {"name":"Rachin Ravindra",      "role":"All-Rounder",   "bat":78,"bowl":70,"field":78,"rating":78},
    {"name":"Matt Henry",           "role":"Fast Bowler",   "bat":20,"bowl":82,"field":70,"rating":76},
],
"SA":[
    {"name":"Quinton de Kock",      "role":"Wicket Keeper", "bat":88,"bowl":0, "field":86,"rating":88},
    {"name":"Reeza Hendricks",      "role":"Opener",        "bat":80,"bowl":10,"field":76,"rating":78},
    {"name":"Temba Bavuma",         "role":"Batsman",       "bat":80,"bowl":20,"field":80,"rating":80},
    {"name":"Rassie van der Dussen","role":"Batsman",       "bat":82,"bowl":20,"field":78,"rating":80},
    {"name":"David Miller",         "role":"Batsman",       "bat":84,"bowl":10,"field":80,"rating":82},
    {"name":"Aiden Markram",        "role":"All-Rounder",   "bat":82,"bowl":65,"field":80,"rating":82},
    {"name":"Marco Jansen",         "role":"All-Rounder",   "bat":62,"bowl":84,"field":74,"rating":78},
    {"name":"Andile Phehlukwayo",   "role":"All-Rounder",   "bat":60,"bowl":76,"field":72,"rating":70},
    {"name":"Kagiso Rabada",        "role":"Fast Bowler",   "bat":30,"bowl":92,"field":76,"rating":89},
    {"name":"Anrich Nortje",        "role":"Fast Bowler",   "bat":20,"bowl":87,"field":72,"rating":81},
    {"name":"Lungi Ngidi",          "role":"Fast Bowler",   "bat":18,"bowl":84,"field":70,"rating":78},
    {"name":"Tabraiz Shamsi",       "role":"Spinner",       "bat":18,"bowl":85,"field":68,"rating":79},
    {"name":"Keshav Maharaj",       "role":"Spinner",       "bat":32,"bowl":84,"field":70,"rating":78},
    {"name":"Ryan Rickelton",       "role":"Batsman",       "bat":76,"bowl":10,"field":74,"rating":74},
    {"name":"Gerald Coetzee",       "role":"Fast Bowler",   "bat":20,"bowl":80,"field":70,"rating":74},
],
"WI":[
    {"name":"Shai Hope",            "role":"Wicket Keeper", "bat":83,"bowl":0, "field":82,"rating":81},
    {"name":"Brandon King",         "role":"Opener",        "bat":80,"bowl":10,"field":76,"rating":78},
    {"name":"Kyle Mayers",          "role":"All-Rounder",   "bat":78,"bowl":68,"field":76,"rating":76},
    {"name":"Nicholas Pooran",      "role":"Wicket Keeper", "bat":84,"bowl":0, "field":82,"rating":82},
    {"name":"Rovman Powell",        "role":"Batsman",       "bat":80,"bowl":30,"field":76,"rating":78},
    {"name":"Jason Holder",         "role":"All-Rounder",   "bat":68,"bowl":86,"field":78,"rating":82},
    {"name":"Andre Russell",        "role":"All-Rounder",   "bat":82,"bowl":76,"field":76,"rating":84},
    {"name":"Roston Chase",         "role":"All-Rounder",   "bat":72,"bowl":78,"field":74,"rating":74},
    {"name":"Alzarri Joseph",       "role":"Fast Bowler",   "bat":22,"bowl":85,"field":72,"rating":79},
    {"name":"Kemar Roach",          "role":"Fast Bowler",   "bat":18,"bowl":82,"field":70,"rating":76},
    {"name":"Gudakesh Motie",       "role":"Spinner",       "bat":20,"bowl":79,"field":68,"rating":73},
    {"name":"Akeal Hosein",         "role":"Spinner",       "bat":28,"bowl":80,"field":68,"rating":74},
    {"name":"Shimron Hetmyer",      "role":"Batsman",       "bat":80,"bowl":10,"field":74,"rating":78},
    {"name":"Alick Athanaze",       "role":"Batsman",       "bat":76,"bowl":15,"field":74,"rating":74},
    {"name":"Romario Shepherd",     "role":"All-Rounder",   "bat":66,"bowl":74,"field":72,"rating":70},
],
}

def get_squad(team_code, fmt_key):
    return T20_SQUADS[team_code] if fmt_key=="T20" else ODI_SQUADS[team_code]

# ─────────────────────────────────────────────────────────────
#  VENUES (50)
# ─────────────────────────────────────────────────────────────
VENUES=[
    {"name":"Wankhede",     "city":"Mumbai",       "country":"India",      "bf":1.15,"pf":1.05,"sf":0.90,"bnd":1.10,"dew":0.8},
    {"name":"Eden Gardens", "city":"Kolkata",      "country":"India",      "bf":1.10,"pf":1.00,"sf":0.95,"bnd":1.05,"dew":0.6},
    {"name":"Narendra Modi","city":"Ahmedabad",    "country":"India",      "bf":1.05,"pf":1.05,"sf":0.92,"bnd":1.00,"dew":0.5},
    {"name":"Chinnaswamy",  "city":"Bangalore",    "country":"India",      "bf":1.20,"pf":0.95,"sf":1.00,"bnd":1.15,"dew":0.7},
    {"name":"Arun Jaitley", "city":"Delhi",        "country":"India",      "bf":1.08,"pf":1.02,"sf":0.95,"bnd":1.05,"dew":0.4},
    {"name":"Chepauk",      "city":"Chennai",      "country":"India",      "bf":0.95,"pf":0.90,"sf":1.15,"bnd":0.95,"dew":0.9},
    {"name":"Rajiv Gandhi", "city":"Hyderabad",    "country":"India",      "bf":1.12,"pf":1.00,"sf":0.95,"bnd":1.08,"dew":0.8},
    {"name":"PCA Mohali",   "city":"Mohali",       "country":"India",      "bf":1.05,"pf":1.05,"sf":0.92,"bnd":1.00,"dew":0.5},
    {"name":"Green Park",   "city":"Kanpur",       "country":"India",      "bf":0.90,"pf":0.92,"sf":1.12,"bnd":0.92,"dew":0.6},
    {"name":"Ekana Stadium","city":"Lucknow",      "country":"India",      "bf":1.08,"pf":1.02,"sf":0.95,"bnd":1.05,"dew":0.6},
    {"name":"JSCA Ranchi",  "city":"Ranchi",       "country":"India",      "bf":0.98,"pf":1.00,"sf":1.00,"bnd":0.98,"dew":0.5},
    {"name":"Holkar Indore","city":"Indore",       "country":"India",      "bf":1.18,"pf":1.00,"sf":0.88,"bnd":1.12,"dew":0.4},
    {"name":"VCA Nagpur",   "city":"Nagpur",       "country":"India",      "bf":1.00,"pf":0.95,"sf":1.08,"bnd":1.00,"dew":0.5},
    {"name":"Barabati",     "city":"Cuttack",      "country":"India",      "bf":1.05,"pf":0.98,"sf":1.00,"bnd":1.05,"dew":0.7},
    {"name":"MCG",          "city":"Melbourne",    "country":"Australia",  "bf":1.00,"pf":1.08,"sf":0.90,"bnd":0.95,"dew":0.2},
    {"name":"SCG",          "city":"Sydney",       "country":"Australia",  "bf":1.08,"pf":1.02,"sf":0.95,"bnd":1.00,"dew":0.2},
    {"name":"Adelaide Oval","city":"Adelaide",     "country":"Australia",  "bf":1.10,"pf":1.05,"sf":0.92,"bnd":1.05,"dew":0.1},
    {"name":"Perth Stadium","city":"Perth",        "country":"Australia",  "bf":0.95,"pf":1.15,"sf":0.85,"bnd":0.95,"dew":0.1},
    {"name":"Gabba",        "city":"Brisbane",     "country":"Australia",  "bf":0.98,"pf":1.12,"sf":0.88,"bnd":0.98,"dew":0.2},
    {"name":"Manuka Oval",  "city":"Canberra",     "country":"Australia",  "bf":1.05,"pf":1.00,"sf":0.95,"bnd":1.00,"dew":0.1},
    {"name":"Bellerive",    "city":"Hobart",       "country":"Australia",  "bf":0.96,"pf":1.08,"sf":0.90,"bnd":0.94,"dew":0.2},
    {"name":"Lord's",       "city":"London",       "country":"England",    "bf":0.92,"pf":1.05,"sf":1.10,"bnd":0.90,"dew":0.3},
    {"name":"The Oval",     "city":"London",       "country":"England",    "bf":1.00,"pf":1.02,"sf":1.05,"bnd":0.98,"dew":0.3},
    {"name":"Headingley",   "city":"Leeds",        "country":"England",    "bf":0.98,"pf":1.08,"sf":1.00,"bnd":0.96,"dew":0.4},
    {"name":"Old Trafford", "city":"Manchester",   "country":"England",    "bf":0.95,"pf":1.05,"sf":1.08,"bnd":0.93,"dew":0.5},
    {"name":"Trent Bridge", "city":"Nottingham",   "country":"England",    "bf":1.05,"pf":1.00,"sf":1.00,"bnd":1.02,"dew":0.3},
    {"name":"Edgbaston",    "city":"Birmingham",   "country":"England",    "bf":1.02,"pf":1.03,"sf":1.02,"bnd":1.00,"dew":0.3},
    {"name":"Wanderers",    "city":"Johannesburg", "country":"S.Africa",   "bf":1.15,"pf":1.10,"sf":0.88,"bnd":1.10,"dew":0.2},
    {"name":"Newlands",     "city":"Cape Town",    "country":"S.Africa",   "bf":1.02,"pf":1.05,"sf":0.98,"bnd":1.00,"dew":0.3},
    {"name":"Centurion",    "city":"Pretoria",     "country":"S.Africa",   "bf":1.08,"pf":1.08,"sf":0.90,"bnd":1.05,"dew":0.2},
    {"name":"Kingsmead",    "city":"Durban",       "country":"S.Africa",   "bf":1.05,"pf":1.05,"sf":0.92,"bnd":1.02,"dew":0.4},
    {"name":"Gaddafi",      "city":"Lahore",       "country":"Pakistan",   "bf":0.95,"pf":0.95,"sf":1.10,"bnd":0.93,"dew":0.6},
    {"name":"Nat. Stadium", "city":"Karachi",      "country":"Pakistan",   "bf":0.92,"pf":0.92,"sf":1.15,"bnd":0.90,"dew":0.7},
    {"name":"Rawalpindi",   "city":"Rawalpindi",   "country":"Pakistan",   "bf":1.00,"pf":1.00,"sf":1.00,"bnd":0.97,"dew":0.5},
    {"name":"Eden Park",    "city":"Auckland",     "country":"New Zealand","bf":1.10,"pf":1.02,"sf":0.95,"bnd":1.08,"dew":0.3},
    {"name":"Basin Reserve","city":"Wellington",   "country":"New Zealand","bf":0.92,"pf":1.12,"sf":0.90,"bnd":0.90,"dew":0.4},
    {"name":"Hagley Oval",  "city":"Christchurch", "country":"New Zealand","bf":0.98,"pf":1.05,"sf":0.95,"bnd":0.96,"dew":0.3},
    {"name":"Seddon Park",  "city":"Hamilton",     "country":"New Zealand","bf":1.02,"pf":1.02,"sf":0.98,"bnd":1.00,"dew":0.3},
    {"name":"Kensington",   "city":"Bridgetown",   "country":"W.Indies",   "bf":1.05,"pf":1.05,"sf":0.95,"bnd":1.02,"dew":0.5},
    {"name":"Sabina Park",  "city":"Kingston",     "country":"W.Indies",   "bf":1.00,"pf":1.08,"sf":0.90,"bnd":0.98,"dew":0.5},
    {"name":"Providence",   "city":"Guyana",       "country":"W.Indies",   "bf":1.08,"pf":1.00,"sf":0.95,"bnd":1.05,"dew":0.6},
    {"name":"Premadasa",    "city":"Colombo",      "country":"Sri Lanka",  "bf":1.05,"pf":0.95,"sf":1.10,"bnd":1.05,"dew":0.9},
    {"name":"Galle",        "city":"Galle",        "country":"Sri Lanka",  "bf":0.88,"pf":0.85,"sf":1.20,"bnd":0.88,"dew":0.8},
    {"name":"Pallekele",    "city":"Kandy",        "country":"Sri Lanka",  "bf":0.95,"pf":0.92,"sf":1.12,"bnd":0.95,"dew":0.7},
    {"name":"Shere Bangla", "city":"Dhaka",        "country":"Bangladesh", "bf":0.95,"pf":0.90,"sf":1.15,"bnd":0.93,"dew":0.9},
    {"name":"Zahur Ahmed",  "city":"Chittagong",   "country":"Bangladesh", "bf":0.92,"pf":0.88,"sf":1.18,"bnd":0.90,"dew":0.9},
    {"name":"Harare SC",    "city":"Harare",       "country":"Zimbabwe",   "bf":1.00,"pf":0.98,"sf":1.02,"bnd":0.98,"dew":0.3},
    {"name":"Dubai Int.",   "city":"Dubai",        "country":"UAE",        "bf":0.98,"pf":0.95,"sf":1.08,"bnd":0.96,"dew":0.1},
    {"name":"Abu Dhabi",    "city":"Abu Dhabi",    "country":"UAE",        "bf":0.96,"pf":0.95,"sf":1.05,"bnd":0.94,"dew":0.1},
    {"name":"SuperSport",   "city":"Centurion",    "country":"S.Africa",   "bf":1.06,"pf":1.06,"sf":0.92,"bnd":1.04,"dew":0.2},
]

# ─────────────────────────────────────────────────────────────
#  F10 – EXTENDED COMMENTARY POOL
# ─────────────────────────────────────────────────────────────
COMMENTARY_POOL = {
    "dot": [
        "Dot ball! Excellent line and length.",
        "Plays and misses — the bowler celebrates!",
        "Tight line, batter defends solidly.",
        "Probing delivery, no run.",
        "Beat the outside edge! Keeper takes it.",
        "Blocked firmly back down the pitch.",
        "Seam movement beats the bat — close call!",
        "Defended watchfully. Building pressure.",
    ],
    "one": [
        "Nudged into the gap for a single.",
        "Worked away to fine leg — one run.",
        "Flicked off the hips, quick single.",
        "Tapped to cover, they steal a single.",
        "Pushed to mid-off, smart running.",
        "Turned to backward square — one.",
        "Steered to third man for a single.",
    ],
    "two": [
        "Driven into the outfield — two runs!",
        "Well timed past point, good running!",
        "Flicked hard to mid-wicket, two more.",
        "Threaded through covers — two!",
        "Pushed hard, they come back for two.",
        "Fine placement earns two.",
    ],
    "four": [
        "FOUR! Pierces the gap at covers brilliantly!",
        "FOUR! Crashes through mid-off — nothing can stop that!",
        "FOUR! Upper cut sails over point!",
        "FOUR! That's a magnificent drive!",
        "FOUR! Raced away to the boundary, all along the ground!",
        "FOUR! Pulled hard — phenomenal placement!",
        "FOUR! Edged but flies wide of the keeper for four!",
        "FOUR! Flicked off the pads — pure timing!",
        "FOUR! Through extra cover, absolutely stunning!",
        "FOUR! The ball smashed the boundary rope!",
    ],
    "six": [
        "SIX! Launched into the stands — that's massive!",
        "SIX! Deposited over long-on! Breathtaking!",
        "SIX! Maximum! Goes all the way!",
        "SIX! Flat-batted over mid-wicket — incredible power!",
        "SIX! Swept powerfully over fine leg!",
        "SIX! That disappeared into the crowd!",
        "SIX! Over extra cover — what a shot!",
        "SIX! The crowd goes absolutely wild!",
        "SIX! Reverse swept for a maximum — audacious!",
        "SIX! Distance on that one — wow!",
    ],
    "wicket": [
        "WICKET! Clean bowled — the stumps are shattered!",
        "WICKET! Caught at slip — excellent reflexes!",
        "WICKET! Plumb LBW — that's stone dead!",
        "WICKET! Caught behind — feathered edge!",
        "WICKET! Run out! Direct hit from point!",
        "WICKET! Skied it and the fielder takes it easily.",
        "WICKET! Top-edged and safely pouched at fine leg!",
        "WICKET! Stumped! Miles out of the crease!",
        "WICKET! That's a huge blow — key batter gone!",
        "WICKET! Miscued completely — caught at mid-on!",
    ],
}

WICKET_COMM={
    "yorker":"Yorker! BOWLED! Middle stump flying!",
    "good_length":"Good length, edged and CAUGHT behind!",
    "bouncer":"Bouncer! Top edge — CAUGHT at fine leg!",
    "full_toss":"Full toss — skied and CAUGHT!",
    "slower":"Slower ball — STUMPED, miles out!",
    "wide_half":"Width offered — CAUGHT at covers!",
    "off_spin":"Off spin — bat-pad CATCH to short leg!",
    "leg_spin":"Leg spin — clean BOWLED through the gate!",
    "doosra":"Doosra! Edged and CAUGHT at slip!",
    "googly":"Googly — LBW, trapped on the crease!",
    "carrom":"Carrom ball — STUMPED!",
    "flighted":"Flighted — top-edged and CAUGHT!",
}
DELIVERY_COMM={
    "yorker":     ["Yorker! Dug out for {}.","Toe-crusher, {}!","Full yorker squeezed for {}."],
    "good_length":["Good length, driven for {}.","Textbook line, worked for {}.","On the money, {}."],
    "bouncer":    ["Short ball! Pulled for {}!","Bouncer — {}!","Rises sharply, {}!"],
    "full_toss":  ["Full toss — smashed for {}!","Free gift! {}!","Beamer dispatched for {}!"],
    "slower":     ["Slower ball — {} only.","Deceived in flight, {}.","Change of pace, {}."],
    "wide_half":  ["Width! Driven for {}!","Half-volley punished for {}!","Full and wide, {}."],
    "off_spin":   ["Off spin, worked for {}.","Turned away to leg for {}.","Flighted off spinner — {}."],
    "leg_spin":   ["Leg spin, swept for {}!","Wrong footed the batter — {}.","Googly-ish — {}."],
    "doosra":     ["Doosra, punched for {}.","Deceptive turn — {}.","Doosra beats the outside edge — {}."],
    "googly":     ["Googly! Plays off the wrong line — {}.","Wrist-spin magic — {}.","Googly — {}."],
    "carrom":     ["Carrom ball, fended for {}.","Skid through — {}.","Carrom ball — {}."],
    "flighted":   ["Flighted delivery, driven for {}!","Tossed up — {}.","Flight and guile — {}."],
}

# ─────────────────────────────────────────────────────────────
#  F6 – BOWLING TYPE VALIDATION
# ─────────────────────────────────────────────────────────────
FAST_DELIVERIES = ["Yorker","Good Length","Bouncer","Slower Ball","Full Toss","Balanced","Attacking","Yorker Focus","Defensive"]
SPIN_DELIVERIES = ["Off Spin","Leg Spin","Doosra","Googly","Carrom Ball","Flighted Ball","Spin Attack","Defensive"]
ALL_DELIVERIES  = FAST_DELIVERIES + [d for d in SPIN_DELIVERIES if d not in FAST_DELIVERIES]

def is_spinner(player):
    return player["role"]=="Spinner" or (player["role"]=="All-Rounder" and player["bowl"]>=60 and player.get("spin",False))

def get_allowed_deliveries(player):
    """F6: Return only deliveries valid for a bowler's role."""
    role=player["role"]
    if role=="Spinner": return SPIN_DELIVERIES
    if role=="Fast Bowler": return FAST_DELIVERIES
    # All-Rounders get fast deliveries by default; could be customised
    return FAST_DELIVERIES

def _delivery_to_internal(d):
    """Map display names to internal delivery keys."""
    m={"Off Spin":"off_spin","Leg Spin":"leg_spin","Doosra":"doosra","Googly":"googly",
       "Carrom Ball":"carrom","Flighted Ball":"flighted","Spin Attack":"slower",
       "Yorker":"yorker","Good Length":"good_length","Bouncer":"bouncer",
       "Slower Ball":"slower","Full Toss":"full_toss","Balanced":"good_length",
       "Attacking":"bouncer","Yorker Focus":"yorker","Defensive":"good_length"}
    return m.get(d,"good_length")

# ─────────────────────────────────────────────────────────────
#  DELIVERY ENGINE  (F6, F8 integrated)
# ─────────────────────────────────────────────────────────────
def _sim_ball(bat_style,bowl_style,venue,bat_team,fmt_overs,innings,target,over_num,batter_r=80,bowler_r=80):
    bf=venue["bf"]; pressure=1.0
    # F8 – Powerplay factor
    pp_overs=6 if fmt_overs==20 else 10
    is_pp=(over_num<pp_overs)
    is_death=(over_num>=fmt_overs-4)
    pp_bf=1.20 if is_pp else 1.0   # More batting-friendly in powerplay

    if innings==2 and target>0 and bat_team.total_balls>0:
        need=target-bat_team.score; rem=fmt_overs*6-bat_team.total_balls
        if rem>0:
            rrr=need*6/rem
            if rrr>14: pressure=1.35
            elif rrr>10: pressure=1.15
            elif rrr<5: pressure=0.80
    confidence=1.0-bat_team.wickets*0.07
    bfac=batter_r/80.0; wfac=bowler_r/80.0

    # Internal delivery key
    delivery_key=_delivery_to_internal(bowl_style)

    dmap={
        "yorker":       {"yorker":0.60,"good_length":0.15,"bouncer":0.05,"full_toss":0.10,"slower":0.06,"wide_half":0.04},
        "good_length":  {"good_length":0.45,"yorker":0.15,"bouncer":0.15,"slower":0.15,"full_toss":0.05,"wide_half":0.05},
        "bouncer":      {"bouncer":0.55,"good_length":0.20,"yorker":0.10,"full_toss":0.05,"slower":0.05,"wide_half":0.05},
        "slower":       {"slower":0.55,"good_length":0.20,"wide_half":0.10,"yorker":0.08,"bouncer":0.04,"full_toss":0.03},
        "full_toss":    {"full_toss":0.50,"good_length":0.20,"yorker":0.10,"wide_half":0.15,"bouncer":0.03,"slower":0.02},
        "off_spin":     {"off_spin":0.50,"leg_spin":0.10,"flighted":0.20,"slower":0.15,"good_length":0.05},
        "leg_spin":     {"leg_spin":0.50,"googly":0.15,"flighted":0.20,"off_spin":0.10,"slower":0.05},
        "doosra":       {"doosra":0.55,"off_spin":0.20,"flighted":0.15,"slower":0.10},
        "googly":       {"googly":0.60,"leg_spin":0.20,"flighted":0.15,"slower":0.05},
        "carrom":       {"carrom":0.55,"off_spin":0.20,"leg_spin":0.15,"flighted":0.10},
        "flighted":     {"flighted":0.55,"off_spin":0.20,"leg_spin":0.15,"slower":0.10},
        "wide_half":    {"wide_half":0.50,"good_length":0.30,"full_toss":0.20},
    }
    probs=dmap.get(delivery_key,dmap["good_length"])
    delivery=random.choices(list(probs.keys()),weights=list(probs.values()))[0]

    bst={
        "Defensive":       ([0.38,0.32,0.12,0.05,0.06,0.00,0.07],0.04),
        "Normal":          ([0.18,0.24,0.16,0.10,0.15,0.06,0.11],0.12),
        "Aggressive":      ([0.08,0.12,0.10,0.08,0.22,0.22,0.18],0.22),
        "Ultra Aggressive":([0.05,0.07,0.08,0.07,0.20,0.34,0.19],0.30),
    }
    rw,wkt_base=bst.get(bat_style,bst["Normal"]); rw=list(rw); wkt_boost=0.0

    if delivery in("yorker",):     rw=[r*1.3 if i<2 else r*0.5 for i,r in enumerate(rw)]; wkt_boost=0.06
    elif delivery=="bouncer":      rw[5]*=2.0; wkt_boost=0.04
    elif delivery=="full_toss":    rw=[r*0.4 if i<3 else r*1.8 for i,r in enumerate(rw)]; wkt_boost=-0.04
    elif delivery in("slower","flighted","carrom"): rw[0]*=1.4; rw[4]*=0.5; rw[5]*=0.3; wkt_boost=0.05
    elif delivery=="wide_half":    rw=[r*0.3 if i<3 else r*2.0 for i,r in enumerate(rw)]; wkt_boost=-0.05
    elif delivery in("off_spin","leg_spin","doosra","googly"): rw[0]*=1.3; rw[4]*=0.7; wkt_boost=0.06

    # F8 – Powerplay: more boundaries
    if is_pp:
        rw[4]*=1.3*pp_bf; rw[5]*=1.2*pp_bf
        wkt_boost-=0.01  # slightly safer to bat in PP

    if is_death and delivery=="yorker": wkt_boost+=0.04

    venue_rw=[rw[0],rw[1]*bf,rw[2]*bf,rw[3]*bf,rw[4]*bf*venue["bnd"],rw[5]*bf*venue["bnd"],rw[6] if len(rw)>6 else 0.11]
    final_rw=[max(0,r*pressure*confidence*bfac/wfac) for r in venue_rw]
    wkt_chance=max(0.02,min(0.55,wkt_base+wkt_boost+(0.02 if is_death else 0)))
    sr=sum(final_rw[:6]); final_rw[6]=wkt_chance*sr/max(0.01,1.0-wkt_chance)
    total=sum(final_rw)
    if total<=0: final_rw=[1.0]*7; total=7.0
    result=random.choices([0,1,2,3,4,6,"W"],weights=[r/total for r in final_rw])[0]
    rl={0:"a dot",1:"one",2:"two",3:"three",4:"FOUR",6:"SIX"}

    # F10 – richer commentary
    if result=="W":
        comm=WICKET_COMM.get(delivery,random.choice(COMMENTARY_POOL["wicket"]))
    elif result==4:
        comm=random.choice(COMMENTARY_POOL["four"])
    elif result==6:
        comm=random.choice(COMMENTARY_POOL["six"])
    elif result==0:
        tmpl=random.choice(DELIVERY_COMM.get(delivery,["Played for {}."]))
        comm=tmpl.format(rl[0]) if "{}" in tmpl else tmpl
    else:
        tmpl=random.choice(DELIVERY_COMM.get(delivery,["Played for {}."]))
        comm=tmpl.format(rl.get(result,str(result))) if "{}" in tmpl else tmpl
    return result,delivery,comm

# ─────────────────────────────────────────────────────────────
#  F11 – ENHANCED AI CONTROLLER
# ─────────────────────────────────────────────────────────────
class AI:
    def __init__(self,difficulty="Medium"):
        self.difficulty=difficulty; self._last=None; self._rep=0

    def bat_style(self,score,wickets,target,bl_rem,fmt_overs):
        if self.difficulty=="Easy":
            return random.choices(["Defensive","Normal","Aggressive","Ultra Aggressive"],weights=[0.30,0.40,0.20,0.10])[0]
        # F11 – powerplay aggression
        pp_overs=6 if fmt_overs==20 else 10
        balls_done=fmt_overs*6-bl_rem
        in_pp=(balls_done//6)<pp_overs

        need=target-score if target>0 else 0
        rrr=(need*6/bl_rem) if bl_rem>0 else 0

        if self.difficulty=="Medium":
            if in_pp and target==0: return "Aggressive"   # F11: attack in PP
            if target==0:
                return "Defensive" if wickets>=7 else ("Aggressive" if bl_rem<12 else "Normal")
            return ("Ultra Aggressive" if rrr>14 else "Aggressive" if rrr>10 else "Normal" if rrr>7 else "Defensive")

        # Hard/Expert
        if in_pp and target==0: return "Aggressive" if wickets<3 else "Normal"
        if target==0:
            if wickets>=8: return "Defensive"
            if bl_rem<=12: return "Ultra Aggressive"
            if bl_rem<=24: return "Aggressive"
            return "Normal"
        # F11: chase logic
        if rrr>16 or (bl_rem<=6 and need>0): return "Ultra Aggressive"
        if rrr>12: return "Aggressive"
        if rrr>8:  return "Normal"
        return "Defensive" if (wickets>=7 or rrr<4) else "Normal"

    def bowl_style(self,over,fmt_overs,wickets,score,target,bowler=None):
        pp_overs=6 if fmt_overs==20 else 10
        death=over>=fmt_overs-4; pp=over<pp_overs
        mid=pp_overs<=over<fmt_overs-4

        # F11: role-aware AI bowling
        if bowler:
            role=bowler.get("role","Fast Bowler")
            if role=="Spinner":
                base=["Off Spin","Leg Spin","Flighted Ball","Doosra"]
                if mid: return random.choice(base+["Carrom Ball"])
                return random.choice(base)
            elif role=="Fast Bowler":
                if death: return random.choice(["Yorker","Yorker","Good Length"])
                if pp: return random.choice(["Good Length","Bouncer","Good Length"])
                return random.choice(["Good Length","Slower Ball","Bouncer"])

        if self.difficulty=="Easy":
            return random.choice(["Good Length","Bouncer","Slower Ball","Full Toss"])
        if self.difficulty=="Medium":
            if death: return random.choice(["Yorker","Yorker","Good Length"])
            if pp:    return random.choice(["Good Length","Bouncer","Good Length"])
            if mid:   return random.choice(["Good Length","Slower Ball","Spin Attack"])
            return random.choice(["Good Length","Slower Ball","Bouncer"])

        # Hard/Expert
        ch=(["Yorker","Yorker Focus","Yorker","Good Length"] if death else
            ["Good Length","Bouncer","Good Length","Balanced"] if pp else
            ["Slower Ball","Good Length","Attacking"] if wickets>=6 else
            ["Good Length","Slower Ball","Bouncer","Balanced","Spin Attack"])
        if self.difficulty=="Expert" and self._last and self._rep>=2:
            ch=[c for c in ch if c!=self._last] or ch
        chosen=random.choice(ch)
        self._rep=(self._rep+1) if chosen==self._last else 0; self._last=chosen
        return chosen

# ─────────────────────────────────────────────────────────────
#  SQUAD HELPERS
# ─────────────────────────────────────────────────────────────
def auto_select_xi(squad):
    by_r=sorted(squad,key=lambda p:-p["rating"]); xi=[]; wk=False; bc=0
    for p in by_r:
        if p["role"]=="Wicket Keeper" and not wk: xi.append(p); wk=True
    ib=lambda p: p["role"] in("Fast Bowler","Spinner") or (p["role"]=="All-Rounder" and p["bowl"]>=65)
    for p in by_r:
        if p in xi: continue
        if bc<4 and ib(p): xi.append(p); bc+=1
        if len(xi)==11: break
    for p in by_r:
        if len(xi)==11: break
        if p not in xi: xi.append(p)
    return xi[:11]

def validate_xi(xi):
    if len(xi)!=11: return False,"Select exactly 11 players"
    if not any(p["role"]=="Wicket Keeper" for p in xi): return False,"Need 1 Wicket Keeper"
    bc=sum(1 for p in xi if p["role"] in("Fast Bowler","Spinner") or (p["role"]=="All-Rounder" and p["bowl"]>=60))
    if bc<4: return False,"Need 4 bowling options"
    return True,"Valid XI"

def avg_r(xi,attr): return sum(p.get(attr,50) for p in xi)/max(1,len(xi))

# ─────────────────────────────────────────────────────────────
#  F12 – PLAYER STATS TRACKER
# ─────────────────────────────────────────────────────────────
class PlayerStats:
    """Tracks individual player stats across a tournament or match."""
    def __init__(self,name,team):
        self.name=name; self.team=team
        # Batting
        self.runs=0; self.balls_faced=0; self.fours=0; self.sixes=0
        self.fifties=0; self.hundreds=0; self.innings=0; self.not_outs=0
        # Bowling
        self.wickets=0; self.runs_conceded=0; self.balls_bowled=0
        self.five_fers=0; self.maidens=0
        # Fielding
        self.catches=0; self.run_outs=0

    @property
    def strike_rate(self):
        return (self.runs*100/self.balls_faced) if self.balls_faced>0 else 0.0
    @property
    def average(self):
        dism=self.innings-self.not_outs
        return (self.runs/dism) if dism>0 else float(self.runs)
    @property
    def economy(self):
        ovs=self.balls_bowled/6.0
        return (self.runs_conceded/ovs) if ovs>0 else 0.0

    def add_runs(self,r):
        if r==4: self.fours+=1
        elif r==6: self.sixes+=1
        self.runs+=r; self.balls_faced+=1

    def add_wicket(self,runs_this_over=0):
        self.wickets+=1; self.runs_conceded+=runs_this_over; self.balls_bowled+=1

# ─────────────────────────────────────────────────────────────
#  F12 – TOURNAMENT STATS AGGREGATOR
# ─────────────────────────────────────────────────────────────
class TournamentStats:
    def __init__(self):
        self.players={}  # name -> PlayerStats

    def get(self,name,team):
        if name not in self.players:
            self.players[name]=PlayerStats(name,team)
        return self.players[name]

    def orange_cap(self):
        """Top run scorer."""
        if not self.players: return None
        return max(self.players.values(),key=lambda p:p.runs)

    def purple_cap(self):
        """Top wicket taker."""
        if not self.players: return None
        return max(self.players.values(),key=lambda p:p.wickets)

    def leading_batters(self,n=5):
        return sorted(self.players.values(),key=lambda p:-p.runs)[:n]

    def leading_bowlers(self,n=5):
        return sorted(self.players.values(),key=lambda p:-p.wickets)[:n]

# ─────────────────────────────────────────────────────────────
#  F1 – TOURNAMENT ENGINE
# ─────────────────────────────────────────────────────────────
class TournamentMatch:
    """Stores the result of a single tournament match."""
    def __init__(self,team1,team2,venue,match_num=0,label=""):
        self.team1=team1; self.team2=team2; self.venue=venue
        self.match_num=match_num; self.label=label
        self.played=False; self.winner=None; self.loser=None
        self.score1=0; self.wkts1=0; self.overs1="0.0"
        self.score2=0; self.wkts2=0; self.overs2="0.0"
        self.margin=""

    def simulate(self,fmt_key="T20",difficulty="Medium"):
        """Auto-simulate a tournament match (both teams as AI)."""
        fmt_overs=FORMATS[fmt_key]["overs"]
        xi1=auto_select_xi(get_squad(self.team1,fmt_key))
        xi2=auto_select_xi(get_squad(self.team2,fmt_key))
        ai=AI(difficulty)
        # Innings 1
        bt1=_sim_innings_auto(self.team1,xi1,self.team2,xi2,
                               self.venue,fmt_overs,fmt_key,ai,1,0)
        target=bt1["score"]+1
        # Innings 2
        bt2=_sim_innings_auto(self.team2,xi2,self.team1,xi1,
                               self.venue,fmt_overs,fmt_key,ai,2,target)
        self.score1=bt1["score"]; self.wkts1=bt1["wickets"]; self.overs1=bt1["overs"]
        self.score2=bt2["score"]; self.wkts2=bt2["wickets"]; self.overs2=bt2["overs"]
        if bt2["score"]>=target:
            self.winner=self.team2; self.loser=self.team1
            self.margin=f"by {10-bt2['wickets']} wkts"
        else:
            self.winner=self.team1; self.loser=self.team2
            self.margin=f"by {target-bt2['score']-1} runs"
        self.played=True

def _sim_innings_auto(bat_code,bat_xi,bowl_code,bowl_xi,venue,fmt_overs,fmt_key,ai,innings,target):
    """Fully simulate an innings automatically (for tournament AI matches)."""
    score=0; wickets=0; total_balls=0; boundaries=0; sixes=0
    ov=0
    while ov<fmt_overs and wickets<MAX_WICKETS:
        if innings==2 and score>=target and target>0: break
        bl_rem=(fmt_overs-ov)*6
        bat_sty=ai.bat_style(score,wickets,target,bl_rem,fmt_overs)
        bowl_sty=ai.bowl_style(ov,fmt_overs,wickets,score,target)
        br=int(avg_r(bat_xi,"bat")); wlr=int(avg_r(bowl_xi,"bowl"))
        for b in range(6):
            if wickets>=MAX_WICKETS or ov>=fmt_overs: break
            if innings==2 and score>=target and target>0: break
            res,_,_=_sim_ball(bat_sty,bowl_sty,venue,
                               type('B',(),{"score":score,"wickets":wickets,"total_balls":total_balls})(),
                               fmt_overs,innings,target,ov,br,wlr)
            if res=="W": wickets+=1
            else:
                score+=res; total_balls+=1
                if res==4: boundaries+=1
                elif res==6: sixes+=1
        ov+=1
    ov_str=f"{ov}.{total_balls%6}" if total_balls%6 else f"{ov}.0"
    return {"score":score,"wickets":wickets,"overs":ov_str,"boundaries":boundaries,"sixes":sixes}

class TournamentGroup:
    """Single round-robin group."""
    def __init__(self,name,teams):
        self.name=name; self.teams=teams
        # Points table: team_code -> {p,w,l,nrr,rf,ra,balls_f,balls_a}
        self.table={t:{"p":0,"w":0,"l":0,"nrr":0.0,
                       "rf":0,"ra":0,"bf":0,"ba":0} for t in teams}
        self.matches=[]
        # Generate all pairings
        codes=teams
        for i in range(len(codes)):
            for j in range(i+1,len(codes)):
                v=random.choice(VENUES)
                m=TournamentMatch(codes[i],codes[j],v,len(self.matches)+1)
                self.matches.append(m)

    def simulate_all(self,fmt_key="T20",difficulty="Medium",player_team=None):
        """Simulate all matches except those involving player_team."""
        for m in self.matches:
            if player_team and (m.team1==player_team or m.team2==player_team):
                continue  # Will be played manually
            if not m.played:
                m.simulate(fmt_key,difficulty)
                self._update_table(m,fmt_key)

    def _update_table(self,m,fmt_key):
        if not m.played: return
        fmt_overs=FORMATS[fmt_key]["overs"]
        t1=self.table[m.team1]; t2=self.table[m.team2]
        # NRR update
        def _overs_to_float(s):
            try:
                parts=str(s).split("."); ov=int(parts[0]); b=int(parts[1]) if len(parts)>1 else 0
                return ov+b/6.0
            except: return float(fmt_overs)
        ov1=_overs_to_float(m.overs1) or fmt_overs
        ov2=_overs_to_float(m.overs2) or fmt_overs
        t1["rf"]+=m.score1; t1["bf"]+=int(ov1*6)
        t1["ra"]+=m.score2; t1["ba"]+=int(ov2*6)
        t2["rf"]+=m.score2; t2["bf"]+=int(ov2*6)
        t2["ra"]+=m.score1; t2["ba"]+=int(ov1*6)
        if m.winner==m.team1:
            t1["p"]+=2; t1["w"]+=1; t2["l"]+=1
        else:
            t2["p"]+=2; t2["w"]+=1; t1["l"]+=1
        # Recalculate NRR
        for code in [m.team1,m.team2]:
            t=self.table[code]
            rr_f=t["rf"]/(t["bf"]/6.0) if t["bf"]>0 else 0
            rr_a=t["ra"]/(t["ba"]/6.0) if t["ba"]>0 else 0
            t["nrr"]=rr_f-rr_a

    def standings(self):
        codes=list(self.table.keys())
        return sorted(codes,key=lambda c:(-self.table[c]["p"],-self.table[c]["nrr"]))

class Tournament:
    """
    F1: Supports T20 World Cup, Champions Trophy, Tri-Series, Bilateral Series.
    """
    TYPES=["T20 World Cup","Champions Trophy","Tri-Series","Bilateral Series"]

    def __init__(self,t_type="T20 World Cup",fmt_key="T20",
                 player_team="IND",difficulty="Medium"):
        self.t_type=t_type; self.fmt_key=fmt_key
        self.player_team=player_team; self.difficulty=difficulty
        self.stats=TournamentStats()
        self.stage="group"   # group / semis / final / done
        self.champion=None
        self.rounds=[]       # list of TournamentGroup or list of TournamentMatch
        self.current_match=None   # match being played manually
        self.schedule=[]
        self._setup()

    def _setup(self):
        codes=[t["code"] for t in TEAMS]
        if self.t_type=="T20 World Cup":
            random.shuffle(codes)
            g1=TournamentGroup("Group A",codes[:4])
            g2=TournamentGroup("Group B",codes[4:])
            self.groups=[g1,g2]; self.rounds=[g1,g2]
        elif self.t_type=="Champions Trophy":
            random.shuffle(codes)
            g1=TournamentGroup("Group A",codes[:4])
            g2=TournamentGroup("Group B",codes[4:])
            self.groups=[g1,g2]; self.rounds=[g1,g2]
        elif self.t_type=="Tri-Series":
            opp_teams=[c for c in codes if c!=self.player_team]
            tri_teams=[self.player_team]+random.sample(opp_teams,2)
            self.groups=[TournamentGroup("League",tri_teams)]
            self.rounds=self.groups
        elif self.t_type=="Bilateral Series":
            opp=[c for c in codes if c!=self.player_team][0]
            self.bilateral_opp=opp; self.groups=[]
            self.bilateral_matches=[
                TournamentMatch(self.player_team,opp,random.choice(VENUES),i+1,f"Match {i+1}")
                for i in range(3)  # default 3-match series
            ]
            self.rounds=self.bilateral_matches

    def simulate_group_stage(self):
        for grp in self.groups:
            grp.simulate_all(self.fmt_key,self.difficulty,self.player_team)

    def get_semis_teams(self):
        if self.t_type in("T20 World Cup","Champions Trophy") and len(self.groups)==2:
            g1=self.groups[0]; g2=self.groups[1]
            s1=g1.standings(); s2=g2.standings()
            if len(s1)>=2 and len(s2)>=2:
                return [(s1[0],s2[1]),(s2[0],s1[1])]
        return []

    def pending_player_matches(self):
        """Return matches involving the player that are not yet played."""
        result=[]
        for grp in getattr(self,"groups",[]):
            for m in grp.matches:
                if (m.team1==self.player_team or m.team2==self.player_team) and not m.played:
                    result.append(m)
        for m in getattr(self,"bilateral_matches",[]):
            if not m.played: result.append(m)
        return result

# ─────────────────────────────────────────────────────────────
#  F4 – FIELD SETTINGS
# ─────────────────────────────────────────────────────────────
FIELD_PRESETS={
    "Defensive":{
        "label":"Defensive",
        "description":"Deep fielders protect the boundary",
        "boundary_mod":0.85,  # harder to hit boundaries
        "single_mod":1.15,    # easier to rotate strike
        "catch_mod":0.75,     # fewer close catchers
        "positions":[(0.5,0.1),(0.1,0.5),(0.9,0.5),(0.5,0.9),
                     (0.15,0.2),(0.85,0.2),(0.2,0.8),(0.8,0.8),
                     (0.5,0.6),(0.3,0.55),(0.7,0.55)],
        "col":BLU,
    },
    "Balanced":{
        "label":"Balanced",
        "description":"Standard ODI/T20 field",
        "boundary_mod":1.0,
        "single_mod":1.0,
        "catch_mod":1.0,
        "positions":[(0.5,0.12),(0.2,0.3),(0.8,0.3),(0.15,0.55),
                     (0.85,0.55),(0.5,0.82),(0.25,0.72),(0.75,0.72),
                     (0.5,0.45),(0.35,0.35),(0.65,0.35)],
        "col":ACG,
    },
    "Attacking":{
        "label":"Attacking",
        "description":"Slips, gully, short leg set",
        "boundary_mod":1.15,
        "single_mod":0.85,
        "catch_mod":1.40,
        "positions":[(0.62,0.22),(0.72,0.26),(0.68,0.18),  # slips
                     (0.5,0.12),(0.3,0.38),(0.42,0.3),     # short leg, silly pt
                     (0.15,0.55),(0.5,0.82),(0.25,0.72),
                     (0.75,0.72),(0.85,0.55)],
        "col":RED,
    },
}

def draw_field_map(surf, preset_name, x, y, w, h):
    """F4: Draw a small oval cricket field with fielder dots."""
    preset=FIELD_PRESETS.get(preset_name,FIELD_PRESETS["Balanced"])
    cx=x+w//2; cy=y+h//2; rx=w//2-4; ry=h//2-4
    # Outfield
    pygame.draw.ellipse(surf,lerp(BG3,hx("1a3a1a"),0.5),(x+2,y+2,w-4,h-4))
    pygame.draw.ellipse(surf,hx("2a4a2a"),(x+2,y+2,w-4,h-4),1)
    # 30-yard circle
    cr=int(min(rx,ry)*0.60)
    pygame.draw.ellipse(surf,lerp(hx("2a4a2a"),hx("3a6a3a"),0.5),(cx-cr,cy-cr,cr*2,cr*2),1)
    # Pitch
    ph=int(h*0.35); pw=6
    pygame.draw.rect(surf,hx("c2a06a"),(cx-pw//2,cy-ph//2,pw,ph))
    # Fielder dots
    col=preset["col"]
    for fx,fy in preset["positions"]:
        dx=x+int(fx*(w-8))+4; dy=y+int(fy*(h-8))+4
        circ_a(surf,col,dx,dy,5,220)
        pygame.draw.circle(surf,WH,(dx,dy),5,1)
    # Batters at crease
    circ_a(surf,GLD,cx,cy+6,5,255)
    circ_a(surf,GLD,cx-8,cy+6,5,200)

# ─────────────────────────────────────────────────────────────
#  BATTING TEAM STATE  (F3, F8 integrated)
# ─────────────────────────────────────────────────────────────
class BattingTeam:
    def __init__(self,code,xi):
        d=next(t for t in TEAMS if t["code"]==code)
        self.code=code; self.name=d["name"]; self.abbr=d["abbr"]
        self.col=d["col"]; self.dark=d["dark"]; self.xi=xi
        self.score=0; self.wickets=0; self.overs=0; self.balls=0
        self.boundaries=0; self.sixes=0; self.dots=0; self.over_scores=[]
        # F3: manual player tracking
        self.batter1_idx=0; self.batter2_idx=1
        self.batter1_runs=0; self.batter2_runs=0
        self.batter1_balls=0; self.batter2_balls=0
        self.bowler_overs={}   # player name -> overs bowled
        # F8: powerplay tracking
        self.pp_runs=0; self.pp_wickets=0
        self._in_pp=False

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
    def innings_over(self,fmt_overs): return self.wickets>=MAX_WICKETS or self.overs>=fmt_overs

    def current_batters(self):
        xi=self.xi; n=len(xi)
        b1=xi[min(self.batter1_idx,n-1)]["name"] if n>0 else "—"
        b2=xi[min(self.batter2_idx,n-1)]["name"] if n>1 else "—"
        return b1,b2

# ─────────────────────────────────────────────────────────────
#  GAME STATE  (F1–F12)
# ─────────────────────────────────────────────────────────────
class GS:
    def __init__(self):
        self.player_team="IND"; self.opp_team="AUS"
        self.venue=VENUES[0]; self.toss_call="Head"
        self.fmt_key="T20"; self.difficulty="Medium"
        self.player_xi=[]; self.opp_xi=[]
        self.bat1=None; self.bat2=None
        self.innings=1; self.target=0
        self.log=[]; self.current_over=[]; self.over_summary=[]
        self.game_over=False; self.player_bats=True
        self.momentum=50.0; self.ai=AI("Medium")
        # F7: simulation mode
        self.sim_mode="full_over"   # "ball_by_ball" or "full_over"
        # F4: field settings
        self.field_setting="Balanced"
        # F3: manual selections
        self.manual_mode=True
        self.next_batter_idx=2
        self.current_bowler_name=""
        # F1: tournament reference
        self.tournament=None
        self.tournament_match=None
        # F12: match stats
        self.match_stats=TournamentStats()
        # F5: player of match
        self.pom=None

    @property
    def fmt_overs(self): return FORMATS[self.fmt_key]["overs"]
    @property
    def batting(self): return self.bat1 if self.innings==1 else self.bat2
    def chase_won(self): return self.innings==2 and self.bat2.score>=self.target
    def innings_done(self): return self.batting.innings_over(self.fmt_overs)

    def play_over(self,bat_style,bowl_style,field_mod=None):
        bat=self.batting; over_num=bat.overs
        br=int(avg_r(bat.xi,"bat"))
        wlr=int(avg_r(self.bat2.xi if self.innings==1 else self.bat1.xi,"bowl"))
        # F4: field modifier
        if field_mod:
            br=int(br*field_mod.get("boundary_mod",1.0))
        balls=[]; runs=0; wkts=0; self.current_over=[]
        pp_overs=6 if self.fmt_overs==20 else 10
        for _ in range(6):
            if bat.innings_over(self.fmt_overs): break
            res,delv,comm=_sim_ball(bat_style,bowl_style,self.venue,bat,self.fmt_overs,
                                     self.innings,self.target,over_num,br,wlr)
            if res=="W":
                bat.wickets+=1; wkts+=1; self.momentum=max(0,self.momentum-22)
                if over_num<pp_overs: bat.pp_wickets+=1
            else:
                bat.score+=res; runs+=res
                if over_num<pp_overs: bat.pp_runs+=res
                if res==0:   bat.dots+=1;       self.momentum=max(0,self.momentum-6)
                elif res==4: bat.boundaries+=1; self.momentum=min(100,self.momentum+16)
                elif res==6: bat.sixes+=1;      self.momentum=min(100,self.momentum+26)
                else:        self.momentum=min(100,self.momentum+res*3)
            self.current_over.append(res); bat.advance_ball()
            self.log.append((bat.fmt_overs(),res,delv,comm)); balls.append((res,delv,comm))
            if self.chase_won(): break
        bat.over_scores.append((runs,wkts)); self.current_over=[]; return balls,runs,wkts

    def calculate_pom(self):
        """F5: Determine Player of the Match based on contributions."""
        b1=self.bat1; b2=self.bat2
        if b1 and b2:
            winner_team=b2 if (b2.score>=self.target) else b1
            xi=winner_team.xi
            # Best batter by estimated contribution
            best=max(xi,key=lambda p:(p["bat"]*0.6+p["bowl"]*0.4))
            self.pom={"name":best["name"],"team":winner_team.name,"role":best["role"]}

# ─────────────────────────────────────────────────────────────
#  CAROUSEL CARD RENDERERS
# ─────────────────────────────────────────────────────────────
def draw_team_card(surf,team,rect,sel,alpha=255):
    x,y,w,h=rect; shadow(surf,(x,y,w,h),14,6,50)
    glass(surf,(x,y,w,h),col=lerp(team["dark"],BG3,0.4) if sel else BG3,
          border=team["col"] if sel else BDR,alpha=min(255,alpha),r=14)
    if sel:
        rb(surf,(*team["col"],200),(x,y,w,h),2,14)
        glow_rect(surf,team["col"],(x,y,w,h),14,8,int(50*alpha/255))
    rr(surf,team["col"],(x+12,y+7,w-24,4),3,alpha=min(240,alpha))
    txt(surf,team["abbr"],F_XL,(*team["col"],min(255,alpha)),x+w//2,y+18,align="center")
    txt(surf,team["name"],F_SM,(*TXT,min(255,alpha)),x+w//2,y+60,align="center")
    if sel: rr(surf,team["col"],(x+w//2-20,y+h-14,40,6),3,alpha=200)

def draw_venue_card(surf,venue,rect,sel,alpha=255):
    x,y,w,h=rect; shadow(surf,(x,y,w,h),14,6,50)
    glass(surf,(x,y,w,h),col=lerp(BG4,BG3,0.5) if sel else BG3,
          border=GLD if sel else BDR,alpha=min(255,alpha),r=14)
    if sel:
        rb(surf,(*GLD,190),(x,y,w,h),2,14)
        glow_rect(surf,GLD,(x,y,w,h),14,7,int(40*alpha/255))
    rr(surf,GLD,(x+12,y+7,w-24,4),3,alpha=min(200,alpha))
    txt(surf,venue["name"],F_MD,(*TXT,min(255,alpha)),x+w//2,y+18,align="center")
    txt(surf,venue["city"],F_SM,(*TX2,min(200,alpha)),x+w//2,y+48,align="center")
    txt(surf,venue["country"],F_XS,(*TX3,min(180,alpha)),x+w//2,y+68,align="center")
    if sel:
        bc=ACG if venue["bf"]>=1.0 else RED
        txt(surf,f"BAT {venue['bf']:.2f}",F_XS,(*bc,min(200,alpha)),x+16,y+h-20)
        pc=BLU if venue["pf"]>=1.0 else ORG
        txt(surf,f"PACE {venue['pf']:.2f}",F_XS,(*pc,min(200,alpha)),x+w-16,y+h-20,align="right")

# ─────────────────────────────────────────────────────────────
#  BASE SCREEN
# ─────────────────────────────────────────────────────────────
class Screen:
    def __init__(self,gs):
        self.gs=gs; self.next=None; self.buttons=[]; self.toast=Toast()
        self._dlg=None; self._trans=Transition("fade",0.22)
        self._trans_in=True; self._trans.start_in()
        self._bg_parts=BgParticles(15)

    def handle(self,ev):
        if self._dlg:
            if self._dlg.handle(ev): self._dlg=None; return
        for b in self.buttons:
            if b.handle(ev): self.on_button(b)

    def on_button(self,b): pass

    def update(self,dt):
        self._trans.update(dt); self._bg_parts.update(dt)
        if self._dlg: self._dlg.update(dt); return
        for b in self.buttons: b.update(dt)
        self.toast.update(dt)

    def draw(self,surf):
        surf.fill(BG)
        self._bg_parts.draw(surf)
        for b in self.buttons: b.draw(surf)
        if self._dlg: self._dlg.draw(surf)
        self.toast.draw(surf)
        if not self._trans.done: self._trans.draw(surf)

    def _hdr(self,surf,title,sub="",ac=ACG,y_off=0):
        grad(surf,BG2,BG,(0,0,W,104)); glow_line(surf,ac,0,4)
        txtm(surf,title,F_XL,TXT,24+y_off)
        if sub: txtm(surf,sub,F_SM,TX2,58+y_off)
        pygame.draw.line(surf,BDR,(0,100),(W,100),1)

    def _sec(self,surf,lbl,y):
        txt(surf,f"◆  {lbl}",F_XS,TX3,20,y)
        pygame.draw.line(surf,BDR,(20,y+14),(W-20,y+14),1)

    def _confirm_exit(self):
        def yes(): pygame.quit(); sys.exit()
        self._dlg=ConfirmDialog("Exit Cricket Simulator?",yes,lambda:None)

    def _confirm_menu(self):
        def yes(): self.gs.__init__(); self.next="menu"
        self._dlg=ConfirmDialog("Return to Main Menu?\nProgress will be lost.",yes,lambda:None)

# ═══════════════════════════════════════════════════════════════
#  MENU SCREEN
# ═══════════════════════════════════════════════════════════════
class MenuScreen(Screen):
    def __init__(self,gs):
        super().__init__(gs)
        mi=next((i for i,t in enumerate(TEAMS) if t["code"]==gs.player_team),0)
        oi=next((i for i,t in enumerate(TEAMS) if t["code"]==gs.opp_team),1)
        vi=next((i for i,v in enumerate(VENUES) if v["name"]==gs.venue["name"]),0)

        self._mc=Carousel(TEAMS, mi, y=148, draw_fn=draw_team_card)
        self._oc=Carousel(TEAMS, oi, y=300, draw_fn=draw_team_card)
        self._vc=Carousel(VENUES,vi, y=452, draw_fn=draw_venue_card)

        self._toss=0 if gs.toss_call=="Head" else 1
        self._fmt=0 if gs.fmt_key=="T20" else 1
        self._diff=["Easy","Medium","Hard","Expert"].index(gs.difficulty)
        self._t=0.0
        P=20; hw=(W-P*2-12)//2

        self._toss_btns=[
            Button((P,604,hw,44),"☀  HEAD",F_MD,abg=GLD,afg=BK,bc=BDR,rad=22,tag=("ts",0)),
            Button((P+hw+12,604,hw,44),"☾  TAIL",F_MD,abg=PRP,afg=BK,bc=BDR,rad=22,tag=("ts",1)),
        ]; self._toss_btns[self._toss].sel=True

        fw=(W-P*2-12)//2
        self._fmt_btns=[
            Button((P,660,fw,40),"T20",F_MD,abg=ACG,afg=BK,rad=12,tag=("fmt",0)),
            Button((P+fw+12,660,fw,40),"ODI",F_MD,abg=BLU,afg=BK,rad=12,tag=("fmt",1)),
        ]; self._fmt_btns[self._fmt].sel=True

        dw=(W-P*2-36)//4; dcols=[ACG,GLD,ORG,RED]
        self._diff_btns=[
            Button((P+i*(dw+12),712,dw,40),["Easy","Medium","Hard","Expert"][i],
                   F_XS,abg=dcols[i],afg=BK,rad=10,tag=("diff",i))
            for i in range(4)
        ]; self._diff_btns[self._diff].sel=True

        sb_w=int(W*0.68); sb_x=(W-sb_w)//2
        self._start_btn=Button(
            (sb_x,770,sb_w,46),"▶   START MATCH",F_LG,
            bg=AC2,fg=BK,hov=ACG,abg=ACG,afg=BK,bc=ACG,rad=16,tag="go",glow_col=ACG
        )
        # F1 – Tournament button
        tb_w=int(W*0.68); tb_x=(W-tb_w)//2
        self._tour_btn=Button(
            (tb_x,820,tb_w,38),"🏆  TOURNAMENT",F_MD,
            bg=BG4,fg=GLD,hov=BG5,abg=GLD,afg=BK,bc=GLD,rad=14,tag="tour"
        )
        self._exit_btn=Button((P,862,W-P*2,14),"EXIT",F_XS,
                              bg=BG4,fg=TX3,hov=BG5,abg=RED,afg=WH,bc=BDR,rad=8,tag="exit")

        self.buttons=(self._toss_btns+self._fmt_btns+self._diff_btns
                      +[self._start_btn,self._tour_btn,self._exit_btn])

    def _fmt_label(self):
        return f"Using {'T20' if self._fmt==0 else 'ODI'} Squad"

    def handle(self,ev):
        if self._dlg:
            if self._dlg.handle(ev): self._dlg=None; return
        mc=self._mc.handle(ev); oc=self._oc.handle(ev); self._vc.handle(ev)
        if mc and self._mc.idx==self._oc.idx: self._oc.idx=(self._oc.idx+1)%len(TEAMS)
        if oc and self._oc.idx==self._mc.idx: self._mc.idx=(self._mc.idx-1)%len(TEAMS)
        for b in self.buttons:
            if b.handle(ev): self.on_button(b)

    def on_button(self,b):
        if isinstance(b.tag,tuple):
            k,i=b.tag
            if k=="ts": self._toss=i; [setattr(tb,"sel",j==i) for j,tb in enumerate(self._toss_btns)]
            elif k=="fmt":
                self._fmt=i; [setattr(fb,"sel",j==i) for j,fb in enumerate(self._fmt_btns)]
            elif k=="diff": self._diff=i; [setattr(db,"sel",j==i) for j,db in enumerate(self._diff_btns)]
        elif b.tag=="go":
            mt=self._mc.selected; ot=self._oc.selected
            if mt["code"]==ot["code"]: self.toast.show("Pick different teams!",RED,1.2); return
            gs=self.gs
            gs.player_team=mt["code"]; gs.opp_team=ot["code"]
            gs.venue=self._vc.selected
            gs.toss_call=["Head","Tail"][self._toss]
            gs.fmt_key=["T20","ODI"][self._fmt]
            gs.difficulty=["Easy","Medium","Hard","Expert"][self._diff]
            gs.ai=AI(gs.difficulty); self.next="squad"
        elif b.tag=="tour":
            self.next="tournament"
        elif b.tag=="exit": self._confirm_exit()

    def update(self,dt):
        super().update(dt); self._t+=dt
        self._mc.update(dt); self._oc.update(dt); self._vc.update(dt)

    def draw(self,surf):
        surf.fill(BG); t=self._t
        c1=lerp(BG2,lerp(BG3,hx("081a08"),abs(math.sin(t*0.3))),0.5)
        grad(surf,c1,BG,(0,0,W,104)); glow_line(surf,ACG,0,4)
        txtm(surf,"CRICKET SIMULATOR",F_XL,TXT,22)
        txtm(surf,"Squad & Tournament Edition  v7.0",F_XS,TX3,56)
        pygame.draw.line(surf,BDR,(0,100),(W,100),1)

        self._bg_parts.draw(surf)
        fl=self._fmt_label(); fc=ACG if self._fmt==0 else BLU
        fw2=F_XS.size(fl)[0]+18; rr(surf,lerp(fc,BG,0.8),(W//2-fw2//2,84,fw2,18),9)
        txtm(surf,fl,F_XS,fc,86)

        self._sec(surf,"YOUR TEAM",132)
        self._mc.draw(surf)
        self._sec(surf,"OPPOSITION",284)
        self._oc.draw(surf)
        self._sec(surf,"VENUE",436)
        self._vc.draw(surf)

        rr(surf,BG2,(0,588,W,286),0,alpha=180)
        pygame.draw.line(surf,BDR,(0,588),(W,588),1)
        self._sec(surf,"TOSS CALL",590)
        self._sec(surf,"FORMAT",645)
        self._sec(surf,"DIFFICULTY",697)
        for b in self.buttons: b.draw(surf)

        glow_line(surf,ACG,768,2,40)
        if self._dlg: self._dlg.draw(surf)
        self.toast.draw(surf)
        if not self._trans.done: self._trans.draw(surf)

# ═══════════════════════════════════════════════════════════════
#  F1 – TOURNAMENT SETUP SCREEN
# ═══════════════════════════════════════════════════════════════
class TournamentSetupScreen(Screen):
    TYPES=["T20 World Cup","Champions Trophy","Tri-Series","Bilateral Series"]
    TYPE_COLS=[ACG,GLD,PRP,ORG]

    def __init__(self,gs):
        super().__init__(gs)
        self._sel_type=0; self._sel_team=0; self._sel_fmt=0; self._sel_diff=0
        P=16; G=8; bw=(W-P*2-G*3)//4; tw=(W-P*2-G)//2
        self._type_btns=[
            Button((P+i*(bw+G),128,bw,52),t.replace(" ","\n"),F_XS,
                   abg=self.TYPE_COLS[i],afg=BK,rad=10,tag=("type",i))
            for i,t in enumerate(self.TYPES)
        ]; self._type_btns[0].sel=True
        self._team_btns=[
            Button((P+i*(tw+G),230,tw,44),TEAMS[i]["abbr"],F_MD,
                   abg=TEAMS[i]["col"],afg=BK,rad=10,tag=("team",i))
            for i in range(min(len(TEAMS),8))
        ]
        # Only 2 rows of 4
        for i,b in enumerate(self._team_btns):
            row=i//4; col=i%4; bw2=(W-P*2-G*3)//4
            b.rect=pygame.Rect(P+col*(bw2+G),230+row*54,bw2,44)
        self._team_btns[0].sel=True
        self._fmt_btns=[
            Button((P,360,tw,40),"T20",F_MD,abg=ACG,afg=BK,rad=12,tag=("fmt",0)),
            Button((P+tw+G,360,tw,40),"ODI",F_MD,abg=BLU,afg=BK,rad=12,tag=("fmt",1)),
        ]; self._fmt_btns[0].sel=True
        dw=(W-P*2-G*3)//4; dcols=[ACG,GLD,ORG,RED]
        self._diff_btns=[
            Button((P+i*(dw+G),412,dw,40),["Easy","Med","Hard","Expert"][i],
                   F_XS,abg=dcols[i],afg=BK,rad=10,tag=("diff",i))
            for i in range(4)
        ]; self._diff_btns[1].sel=True; self._sel_diff=1
        sw=(W-P*2-G)//2
        self._start_btn=Button((P,474,W-P*2,56),"🏆  START TOURNAMENT",F_LG,
                               bg=GLD,fg=BK,hov=GL2,abg=GL2,afg=BK,bc=GLD,rad=16,tag="go",glow_col=GLD)
        self._back_btn=Button((P,544,W-P*2,38),"← BACK",F_SM,
                              bg=BG4,fg=TX2,rad=12,tag="back")
        self.buttons=(self._type_btns+self._team_btns+self._fmt_btns+
                      self._diff_btns+[self._start_btn,self._back_btn])

    def on_button(self,b):
        if isinstance(b.tag,tuple):
            k,i=b.tag
            if k=="type": self._sel_type=i; [setattr(x,"sel",j==i) for j,x in enumerate(self._type_btns)]
            elif k=="team": self._sel_team=i; [setattr(x,"sel",j==i) for j,x in enumerate(self._team_btns)]
            elif k=="fmt": self._sel_fmt=i; [setattr(x,"sel",j==i) for j,x in enumerate(self._fmt_btns)]
            elif k=="diff": self._sel_diff=i; [setattr(x,"sel",j==i) for j,x in enumerate(self._diff_btns)]
        elif b.tag=="go":
            gs=self.gs
            t_type=self.TYPES[self._sel_type]
            team_code=TEAMS[self._sel_team]["code"]
            fmt_key=["T20","ODI"][self._sel_fmt]
            diff=["Easy","Medium","Hard","Expert"][self._sel_diff]
            gs.player_team=team_code
            gs.fmt_key=fmt_key; gs.difficulty=diff
            tour=Tournament(t_type,fmt_key,team_code,diff)
            gs.tournament=tour
            self.next="tournament_hub"
        elif b.tag=="back": self.next="menu"

    def draw(self,surf):
        surf.fill(BG); self._bg_parts.draw(surf)
        grad(surf,lerp(GLD,BG,0.88),BG,(0,0,W,104)); glow_line(surf,GLD,0,4)
        txtm(surf,"TOURNAMENT MODE",F_XL,GLD,22); txtm(surf,"Select format & team",F_SM,TX2,58)
        pygame.draw.line(surf,BDR,(0,100),(W,100),1)
        self._sec(surf,"TOURNAMENT TYPE",110)
        self._sec(surf,"YOUR TEAM",212)
        self._sec(surf,"FORMAT",344); self._sec(surf,"DIFFICULTY",396)
        for b in self.buttons: b.draw(surf)
        if self._dlg: self._dlg.draw(surf)
        self.toast.draw(surf)
        if not self._trans.done: self._trans.draw(surf)

# ═══════════════════════════════════════════════════════════════
#  F1 – TOURNAMENT HUB SCREEN
# ═══════════════════════════════════════════════════════════════
class TournamentHubScreen(Screen):
    def __init__(self,gs):
        super().__init__(gs)
        self._tab=0   # 0=fixtures 1=standings 2=stats
        P=14; G=8; tw=(W-P*2-G*2)//3
        self._tab_btns=[
            Button((P+i*(tw+G),104,tw,36),["FIXTURES","STANDINGS","STATS"][i],F_XS,
                   abg=ACG,afg=BK,rad=10,tag=("tab",i))
            for i in range(3)
        ]; self._tab_btns[0].sel=True
        self._scroll=0.0
        tour=gs.tournament
        # Simulate all non-player group matches
        if tour:
            tour.simulate_group_stage()
        self._play_btn=Button((14,H-68,W-28,52),"▶  PLAY NEXT MATCH",F_LG,
                              bg=ACG,fg=BK,hov=AC2,abg=AC2,afg=BK,rad=14,tag="play",glow_col=ACG)
        self._menu_btn=Button((W-80,8,68,28),"MENU",F_XS,bg=BG4,fg=TX2,hov=BG5,abg=RED,afg=WH,rad=8,tag="menu")
        self.buttons=self._tab_btns+[self._play_btn,self._menu_btn]
        self._t=0.0

    def handle(self,ev):
        if self._dlg:
            if self._dlg.handle(ev): self._dlg=None; return
        for b in self.buttons:
            if b.handle(ev): self.on_button(b)
        if ev.type==pygame.MOUSEWHEEL: self._scroll=max(0,self._scroll-ev.y*22)
        if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE: self._confirm_menu()

    def on_button(self,b):
        if isinstance(b.tag,tuple) and b.tag[0]=="tab":
            i=b.tag[1]; self._tab=i
            [setattr(x,"sel",j==i) for j,x in enumerate(self._tab_btns)]
        elif b.tag=="play":
            gs=self.gs; tour=gs.tournament
            if not tour: return
            pending=tour.pending_player_matches()
            if not pending:
                self.toast.show("All matches played!",GLD,1.5); return
            m=pending[0]; gs.tournament_match=m
            # Set up match
            gs.player_team=m.team1 if m.team1==tour.player_team else m.team2
            gs.opp_team=m.team2 if m.team1==tour.player_team else m.team1
            gs.venue=m.venue; gs.fmt_key=tour.fmt_key
            gs.difficulty=tour.difficulty
            gs.ai=AI(tour.difficulty)
            self.next="squad"
        elif b.tag=="menu": self._confirm_menu()

    def update(self,dt):
        super().update(dt); self._t+=dt

    def draw(self,surf):
        surf.fill(BG); gs=self.gs; tour=gs.tournament
        self._bg_parts.draw(surf)
        grad(surf,lerp(GLD,BG,0.88),BG,(0,0,W,104)); glow_line(surf,GLD,0,4)
        tn=tour.t_type if tour else "Tournament"
        txtm(surf,tn,F_LG,GLD,22); txtm(surf,f"{tour.fmt_key} · {tour.difficulty}",F_XS,TX2,56)
        pygame.draw.line(surf,BDR,(0,100),(W,100),1)
        for b in self._tab_btns: b.draw(surf)
        self._menu_btn.draw(surf)
        pygame.draw.line(surf,BDR,(0,144),(W,144),1)

        cy=150-int(self._scroll); tab=self._tab
        if tab==0:  cy=self._draw_fixtures(surf,tour,cy)
        elif tab==1: cy=self._draw_standings(surf,tour,cy)
        elif tab==2: cy=self._draw_stats(surf,tour,cy)

        pygame.draw.line(surf,BDR,(0,H-76),(W,H-76),1)
        self._play_btn.draw(surf)
        if self._dlg: self._dlg.draw(surf)
        self.toast.draw(surf)
        if not self._trans.done: self._trans.draw(surf)

    def _draw_fixtures(self,surf,tour,cy):
        if not tour: return cy
        all_matches=[]
        for grp in getattr(tour,"groups",[]):
            for m in grp.matches: all_matches.append((grp.name,m))
        for m in getattr(tour,"bilateral_matches",[]):
            all_matches.append(("Series",m))
        for grp_name,m in all_matches:
            if cy<H-82:
                rr(surf,BG3,(12,cy,W-24,56),10)
                t1=next((t for t in TEAMS if t["code"]==m.team1),TEAMS[0])
                t2=next((t for t in TEAMS if t["code"]==m.team2),TEAMS[0])
                txt(surf,f"{grp_name} ·  {m.label}",F_XS,TX3,20,cy+4)
                if m.played:
                    txt(surf,f"{t1['abbr']}  {m.score1}/{m.wkts1} ({m.overs1})",F_SM,t1["col"],20,cy+24)
                    txt(surf,f"{t2['abbr']}  {m.score2}/{m.wkts2} ({m.overs2})",F_SM,t2["col"],W//2+8,cy+24)
                    wc=next((t for t in TEAMS if t["code"]==m.winner),None)
                    if wc: txt(surf,f"✓ {wc['abbr']} {m.margin}",F_XS,ACG,W-14,cy+4,align="right")
                else:
                    txt(surf,f"{t1['abbr']}  vs  {t2['abbr']}",F_MD,TX2,W//2,cy+26,align="center")
                    txt(surf,m.venue["name"],F_XS,TX3,W-14,cy+4,align="right")
                cy+=64
        return cy

    def _draw_standings(self,surf,tour,cy):
        if not tour: return cy
        for grp in getattr(tour,"groups",[]):
            if cy>=H-82: break
            rr(surf,BG3,(12,cy,W-24,24),8)
            txt(surf,grp.name,F_XS,GLD,W//2,cy+6,align="center"); cy+=30
            hdr=["#","TEAM","P","W","L","NRR"]
            hw=[20,120,30,30,30,54]
            for ci,h in enumerate(hdr):
                x=16+sum(hw[:ci])+4
                txt(surf,h,F_XS,TX3,x,cy)
            cy+=18
            for rank,code in enumerate(grp.standings()):
                if cy>=H-82: break
                t=next(tt for tt in TEAMS if tt["code"]==code)
                row=grp.table[code]
                bg=lerp(BG3,t["dark"],0.3) if code==tour.player_team else BG4
                rr(surf,bg,(12,cy,W-24,28),6)
                vals=[str(rank+1),code,str(row["p"]),str(row["w"]),str(row["l"]),f"{row['nrr']:+.2f}"]
                for ci,v in enumerate(vals):
                    x=16+sum(hw[:ci])+4
                    fc=t["col"] if ci==1 else (ACG if row["nrr"]>=0 else RED) if ci==5 else TXT
                    txt(surf,v,F_XS,fc,x,cy+8)
                cy+=30
            cy+=10
        return cy

    def _draw_stats(self,surf,tour,cy):
        if not tour: return cy
        stats=tour.stats
        bat=stats.leading_batters(5); bowl=stats.leading_bowlers(5)
        txt(surf,"LEADING RUN SCORERS",F_SM,GLD,W//2,cy,align="center"); cy+=28
        if not bat:
            txt(surf,"No data yet",F_XS,TX3,W//2,cy,align="center"); cy+=24
        for i,p in enumerate(bat):
            rr(surf,BG3,(12,cy,W-24,28),6)
            txt(surf,f"{i+1}. {p.name}",F_SM,TXT,20,cy+6)
            txt(surf,f"{p.runs} ({p.innings} inn)",F_XS,ACG,W-14,cy+8,align="right"); cy+=32
        cy+=8
        txt(surf,"LEADING WICKET TAKERS",F_SM,RED,W//2,cy,align="center"); cy+=28
        if not bowl:
            txt(surf,"No data yet",F_XS,TX3,W//2,cy,align="center"); cy+=24
        for i,p in enumerate(bowl):
            rr(surf,BG3,(12,cy,W-24,28),6)
            txt(surf,f"{i+1}. {p.name}",F_SM,TXT,20,cy+6)
            txt(surf,f"{p.wickets} wkts",F_XS,RED,W-14,cy+8,align="right"); cy+=32
        oc=stats.orange_cap(); pc=stats.purple_cap()
        cy+=8
        if oc:
            rr(surf,lerp(ORG,BG,0.7),(12,cy,W-24,34),10)
            txt(surf,f"🟠 Orange Cap: {oc.name}  {oc.runs} runs",F_SM,ORG,W//2,cy+8,align="center"); cy+=40
        if pc:
            rr(surf,lerp(PRP,BG,0.7),(12,cy,W-24,34),10)
            txt(surf,f"🟣 Purple Cap: {pc.name}  {pc.wickets} wkts",F_SM,PRP,W//2,cy+8,align="center")
        return cy

# ═══════════════════════════════════════════════════════════════
#  SQUAD SELECTION SCREEN
# ═══════════════════════════════════════════════════════════════
class SquadScreen(Screen):
    ROLE_COLS={"Opener":BLU,"Batsman":ACG,"Wicket Keeper":GLD,
               "All-Rounder":PRP,"Fast Bowler":RED,"Spinner":CYN}

    def __init__(self,gs):
        super().__init__(gs)
        self.squad=get_squad(gs.player_team,gs.fmt_key)
        self.selected=[False]*len(self.squad)
        best=auto_select_xi(self.squad)
        for i,p in enumerate(self.squad):
            if p in best: self.selected[i]=True
        self._scroll=0.0
        P=16
        self.buttons=[
            Button((P,H-68,W-P*2,52),"CONFIRM XI  ▶",F_LG,
                   bg=ACG,fg=BK,hov=AC2,abg=AC2,afg=BK,bc=AC2,rad=14,tag="confirm",glow_col=ACG)
        ]

    def handle(self,ev):
        if self._dlg:
            if self._dlg.handle(ev): self._dlg=None; return
        for b in self.buttons:
            if b.handle(ev): self.on_button(b)
        if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
            _,y=ev.pos
            if 108<y<H-82:
                row=int((y-108+int(self._scroll))//54)
                if 0<=row<len(self.squad): self.selected[row]=not self.selected[row]
        if ev.type==pygame.MOUSEWHEEL:
            self._scroll=max(0.0,min(self._scroll-ev.y*24,len(self.squad)*54-(H-200)))
        if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE: self._confirm_menu()

    def on_button(self,b):
        if b.tag=="confirm":
            xi=[p for i,p in enumerate(self.squad) if self.selected[i]]
            ok,msg=validate_xi(xi)
            if not ok: self.toast.show(msg,RED,1.5); return
            gs=self.gs; gs.player_xi=xi
            gs.opp_xi=auto_select_xi(get_squad(gs.opp_team,gs.fmt_key))
            self.next="toss"

    def draw(self,surf):
        surf.fill(BG); gs=self.gs
        self._bg_parts.draw(surf)
        grad(surf,BG2,BG,(0,0,W,104)); glow_line(surf,ACG,0,4)
        txtm(surf,"SELECT YOUR XI",F_XL,TXT,22)
        fc=ACG if gs.fmt_key=="T20" else BLU
        badge=f"Format: {gs.fmt_key}  ·  Using {gs.fmt_key} Squad"
        bw=F_XS.size(badge)[0]+20; rr(surf,lerp(fc,BG,0.75),(W//2-bw//2,54,bw,20),10)
        txtm(surf,badge,F_XS,fc,57)
        pygame.draw.line(surf,BDR,(0,100),(W,100),1)
        cnt=sum(self.selected)
        xi=[p for i,p in enumerate(self.squad) if self.selected[i]]
        ok,msg=validate_xi(xi) if cnt==11 else (False,"Select 11")
        sc=ACG if ok else (GLD if cnt<11 else RED)
        mark="✓" if ok else f"  {msg}"
        txtm(surf,f"Selected: {cnt}/11  {mark}",F_SM,sc,76)
        row_h=54; item_y=108
        for i,p in enumerate(self.squad):
            ry=item_y+i*row_h-int(self._scroll)
            if ry<96 or ry>H-82: continue
            sel=self.selected[i]; rc=self.ROLE_COLS.get(p["role"],TX2)
            rr(surf,lerp(BG3,BG4,0.3) if sel else BG4,(14,ry,W-28,row_h-4),11)
            if sel:
                rb(surf,(*rc,150),(14,ry,W-28,row_h-4),2,11)
                rr(surf,rc,(14,ry,5,row_h-4),3)
            cb=ACG if sel else BG5; rr(surf,cb,(24,ry+17,20,20),5)
            if sel: txtm(surf,"✓",F_SM,BK,ry+17)
            txt(surf,p["name"],F_SM,TXT if sel else TX2,52,ry+6)
            txt(surf,p["role"],F_XS,rc,52,ry+27)
            txt(surf,f"BAT {p['bat']}",F_XS,ACG,W-160,ry+6)
            txt(surf,f"BOWL {p['bowl']}",F_XS,BLU,W-160,ry+26)
            txt(surf,f"★{p['rating']}",F_XS,GLD,W-76,ry+14)
        pygame.draw.line(surf,BDR,(0,H-76),(W,H-76),1)
        for b in self.buttons: b.draw(surf)
        if self._dlg: self._dlg.draw(surf)
        self.toast.draw(surf)
        if not self._trans.done: self._trans.draw(surf)

# ═══════════════════════════════════════════════════════════════
#  TOSS SCREEN  (F9: enhanced coin animation)
# ═══════════════════════════════════════════════════════════════
class TossScreen(Screen):
    def __init__(self,gs):
        super().__init__(gs)
        self._phase="idle"; self._ft=0.0; self._fi=0; self._done=False
        self._won=False; self._icon="☀"; self._rt=""; self._dt=""
        self._bf=""; self._bfn=""; self._t=0.0
        self._frames=["☀","◑","☾","◐"]*6  # F9: longer flip
        self._parts=Particles()
        self.buttons=[Button((W//2-124,506,248,54),"☀  FLIP THE COIN  ☾",F_LG,
                             bg=GLD,fg=BK,hov=GL2,abg=GL2,afg=BK,bc=GLD,rad=30,tag="flip",glow_col=GLD)]
        self._pb=Button((W//2-124,610,248,52),"▶  START MATCH",F_LG,
                        bg=ACG,fg=BK,hov=AC2,abg=AC2,afg=BK,bc=ACG,rad=30,tag="go",glow_col=ACG)

    def handle(self,ev):
        if self._dlg:
            if self._dlg.handle(ev): self._dlg=None; return
        for b in self.buttons:
            if b.handle(ev): self.on_button(b)
        if self._done and self._pb.handle(ev): self.on_button(self._pb)
        if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE: self._confirm_exit()

    def on_button(self,b):
        if b.tag=="flip" and not self._done: self._phase="spin"
        elif b.tag=="go": self.next="match"

    def update(self,dt):
        super().update(dt); self._pb.update(dt); self._t+=dt; self._parts.update(dt)
        if self._phase=="spin":
            self._ft+=dt
            if self._ft>=0.08: self._ft=0.0; self._fi+=1
            if self._fi>=len(self._frames): self._resolve()

    def _resolve(self):
        gs=self.gs; res=random.choice(["Head","Tail"]); won=(res==gs.toss_call)
        wc=gs.player_team if won else gs.opp_team; dec=random.choice(["bat","bowl"])
        self._won=won; self._icon="☀" if res=="Head" else "☾"
        wname=next(t["name"] for t in TEAMS if t["code"]==wc)
        self._rt="YOU WIN THE TOSS!" if won else f"{next(t['name'] for t in TEAMS if t['code']==gs.opp_team)} WIN!"
        self._dt=f"{wname} elected to {dec} first"
        bf=wc if dec=="bat" else (gs.opp_team if won else gs.player_team)
        wf=gs.opp_team if bf==gs.player_team else gs.player_team
        self._bf=bf; self._bfn=next(t["name"] for t in TEAMS if t["code"]==bf)
        gs.bat1=BattingTeam(bf,gs.player_xi if bf==gs.player_team else gs.opp_xi)
        gs.bat2=BattingTeam(wf,gs.player_xi if wf==gs.player_team else gs.opp_xi)
        gs.innings=1; gs.player_bats=(bf==gs.player_team)
        gs.next_batter_idx=2
        self._phase="result"; self._done=True
        # F9: winner celebration particles
        col=GLD if won else RED
        self._parts.emit_firework(W//2,280,col,30)

    def draw(self,surf):
        surf.fill(BG); self._bg_parts.draw(surf)
        grad(surf,lerp(GLD,BG,0.88),BG,(0,0,W,104)); glow_line(surf,GLD,0,4)
        txtm(surf,"THE TOSS",F_XL,GLD,24)
        v=self.gs.venue; txtm(surf,f"{v['name']} · {v['city']}  ·  {self.gs.fmt_key}",F_SM,TX2,58)
        pygame.draw.line(surf,BDR,(0,100),(W,100),1)
        self._parts.draw(surf); cx=W//2; cy=295
        if self._phase=="idle":
            p=1.0+0.06*math.sin(self._t*2.5); r=int(66*p)
            circ_a(surf,GLD,cx,cy,r+8,40)
            pygame.draw.circle(surf,lerp(GLD,GL2,abs(math.sin(self._t))),(cx,cy),r)
            pygame.draw.circle(surf,lerp(GLD,WH,0.3),(cx,cy),r,3)
            txtm(surf,"☀",F_XXL,BK,cy-28); txtm(surf,"HEAD",F_XS,BK,cy+14)
            txtm(surf,"Tap to flip the coin",F_SM,TX2,cy+92)
            for b in self.buttons: b.draw(surf)
        elif self._phase=="spin":
            # F9: dynamic coin flip with scale pulse
            spd=min(1.0,self._fi/(len(self._frames)*0.8))
            p=1.0+0.25*math.sin(self._t*30*spd); r=int(66*p)
            c=lerp(GLD,PRP,spd)
            circ_a(surf,c,cx,cy,r+10,60)
            pygame.draw.circle(surf,c,(cx,cy),r); pygame.draw.circle(surf,WH,(cx,cy),r,2)
            fi=min(self._fi,len(self._frames)-1)
            scl=abs(math.cos(self._fi*0.8))   # squish for realism
            ch=self._frames[fi]; img=F_XXL.render(ch,True,BK)
            sw2=max(1,int(img.get_width()*max(0.1,scl)))
            si=pygame.transform.smoothscale(img,(sw2,img.get_height()))
            surf.blit(si,(cx-sw2//2,cy-28))
            txtm(surf,"Flipping…",F_SM,TX2,cy+92)
        else:
            rc=ACG if self._won else RED
            circ_a(surf,rc,cx,cy,88,35); pygame.draw.circle(surf,rc,(cx,cy),66,3)
            ic=GLD if self._icon=="☀" else PRP
            txtm(surf,self._icon,F_XXL,ic,cy-30)
            shadow(surf,(24,cy+92,W-48,158),18,8,80)
            glass(surf,(24,cy+92,W-48,158),col=BG3,border=rc,alpha=235,r=18)
            rb(surf,(*rc,170),(24,cy+92,W-48,158),2,18)
            txtm(surf,self._rt,F_MD,rc,cy+108); txtm(surf,self._dt,F_SM,TX2,cy+136)
            wfn=next(t["name"] for t in TEAMS if t["code"]!=self._bf
                     and t["code"] in(self.gs.player_team,self.gs.opp_team))
            txtm(surf,f"BAT: {self._bfn}   BOWL: {wfn}",F_XS,TX3,cy+164)
            txtm(surf,f"{FORMATS[self.gs.fmt_key]['name']} · {self.gs.fmt_overs} overs · AI: {self.gs.difficulty}",
                 F_XS,TX3,cy+186)
            self._pb.draw(surf)
        if self._dlg: self._dlg.draw(surf)
        if not self._trans.done: self._trans.draw(surf)

# ═══════════════════════════════════════════════════════════════
#  F7 – SIMULATION MODE PROMPT SCREEN
# ═══════════════════════════════════════════════════════════════
class SimModeScreen(Screen):
    """Shown before each over to let the player choose ball-by-ball or full simulation."""
    def __init__(self,gs):
        super().__init__(gs)
        bat=gs.batting
        self._over_num=bat.overs
        self._is_pp=(bat.overs<(6 if gs.fmt_overs==20 else 10))
        P=30; bw=W-P*2
        self._bbb_btn=Button((P,350,bw,72),"BALL BY BALL\nWatch every delivery",F_MD,
                             bg=BG4,fg=TXT,hov=BG5,abg=BLU,afg=WH,rad=16,tag="bbb",glow_col=BLU)
        self._full_btn=Button((P,438,bw,72),"SIMULATE FULL OVER\nInstant result",F_MD,
                              bg=BG4,fg=TXT,hov=BG5,abg=ACG,afg=BK,rad=16,tag="full",glow_col=ACG)
        # F3: bowler choice (shown when player is bowling)
        self._bowler_btn=None
        if not gs.player_bats:
            self._bowler_btn=Button((P,H-84,bw,52),"SELECT BOWLER ▼",F_MD,
                                    bg=BG4,fg=GLD,hov=BG5,abg=GLD,afg=BK,rad=12,tag="bowler")
        btns=[self._bbb_btn,self._full_btn]
        if self._bowler_btn: btns.append(self._bowler_btn)
        self.buttons=btns
        self._t=0.0

    def on_button(self,b):
        gs=self.gs
        if b.tag=="bbb":
            gs.sim_mode="ball_by_ball"; self.next="match"
        elif b.tag=="full":
            gs.sim_mode="full_over"; self.next="match"
        elif b.tag=="bowler":
            self.next="bowler_select"

    def update(self,dt):
        super().update(dt); self._t+=dt

    def draw(self,surf):
        surf.fill(BG); gs=self.gs; bat=gs.batting
        self._bg_parts.draw(surf)
        pp_overs=6 if gs.fmt_overs==20 else 10
        pp_str=" — POWERPLAY!" if self._is_pp else ""
        grad(surf,BG2,BG,(0,0,W,104)); glow_line(surf,GLD,0,4)
        txtm(surf,f"OVER {bat.overs + 1}{pp_str}",F_XL,GLD if self._is_pp else TXT,22)
        txtm(surf,"Choose simulation mode",F_SM,TX2,58)
        pygame.draw.line(surf,BDR,(0,100),(W,100),1)
        # Score so far
        rr(surf,BG3,(16,110,W-32,80),14)
        txtm(surf,bat.fmt_score(),F_XXL,bat.col,118)
        txtm(surf,f"({bat.fmt_overs()} ov)  CRR {bat.crr:.2f}  ·  {gs.fmt_key}",F_XS,TX2,180)
        if gs.innings==2:
            need=gs.target-bat.score; rem=gs.fmt_overs*6-bat.total_balls
            rrr=(need*6/rem) if rem>0 else 0
            rrc=ACG if rrr<9 else (GLD if rrr<13 else RED)
            txtm(surf,f"Need {need} from {rem} balls  RRR {rrr:.2f}",F_SM,rrc,200)
        # F8 – Powerplay badge
        if self._is_pp:
            pw=F_MD.size("⚡ POWERPLAY ACTIVE")[0]+20
            rr(surf,lerp(GLD,BG,0.6),(W//2-pw//2,226,pw,30),12)
            txtm(surf,"⚡ POWERPLAY ACTIVE",F_MD,GLD,228)
        txtm(surf,"SELECT MODE FOR THIS OVER",F_XS,TX3,310)
        for b in self.buttons: b.draw(surf)
        if not self._trans.done: self._trans.draw(surf)

# ═══════════════════════════════════════════════════════════════
#  F3 – BOWLER SELECTION SCREEN
# ═══════════════════════════════════════════════════════════════
class BowlerSelectScreen(Screen):
    def __init__(self,gs):
        super().__init__(gs)
        # Bowlers = Fast Bowlers, Spinners, All-Rounders with bowl >= 60
        bowl_xi=gs.bat1.xi if gs.innings==1 else gs.bat2.xi
        # Actually the opposing team bowls
        if gs.player_bats:
            bowl_xi=gs.bat2.xi if gs.innings==1 else gs.bat1.xi
        else:
            bowl_xi=gs.bat1.xi if gs.innings==1 else gs.bat2.xi
        # In practice: bowling team is whoever is NOT batting
        bat=gs.batting
        bowl_team_xi=gs.opp_xi if bat.code==gs.player_team else gs.player_xi
        self.bowlers=[p for p in bowl_team_xi
                      if p["role"] in("Fast Bowler","Spinner") or
                      (p["role"]=="All-Rounder" and p["bowl"]>=60)]
        self._scroll=0.0
        self.buttons=[Button((16,H-64,W-32,48),"← BACK",F_MD,bg=BG4,fg=TX2,rad=12,tag="back")]

    def handle(self,ev):
        super().handle(ev)
        if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
            _,y=ev.pos
            if 110<y<H-72:
                row=int((y-110+int(self._scroll))//52)
                if 0<=row<len(self.bowlers):
                    p=self.bowlers[row]
                    self.gs.current_bowler_name=p["name"]
                    self.next="sim_mode"
        if ev.type==pygame.MOUSEWHEEL:
            self._scroll=max(0,min(self._scroll-ev.y*22,len(self.bowlers)*52-(H-180)))

    def on_button(self,b):
        if b.tag=="back": self.next="sim_mode"

    def draw(self,surf):
        surf.fill(BG); self._bg_parts.draw(surf)
        grad(surf,BG2,BG,(0,0,W,104)); glow_line(surf,RED,0,4)
        txtm(surf,"SELECT BOWLER",F_XL,TXT,22); txtm(surf,"Tap to select",F_SM,TX2,56)
        pygame.draw.line(surf,BDR,(0,100),(W,100),1)
        bat=self.gs.batting
        py=110-int(self._scroll)
        for p in self.bowlers:
            if py<96 or py>H-72: py+=52; continue
            role_col=RED if p["role"]=="Fast Bowler" else CYN if p["role"]=="Spinner" else PRP
            sel=(p["name"]==self.gs.current_bowler_name)
            rr(surf,lerp(BG3,BG4,0.2) if sel else BG4,(12,py,W-24,48),10)
            if sel:
                rb(surf,(*role_col,180),(12,py,W-24,48),2,10)
                rr(surf,role_col,(12,py,4,48),3)
            txt(surf,p["name"],F_SM,TXT,22,py+6)
            txt(surf,p["role"],F_XS,role_col,22,py+26)
            txt(surf,f"BOWL {p['bowl']}",F_XS,BLU,W//2,py+16)
            ovs=self.gs.batting.bowler_overs.get(p["name"],0)
            txt(surf,f"{ovs} ov",F_XS,TX3,W-16,py+16,align="right")
            py+=52
        for b in self.buttons: b.draw(surf)
        if not self._trans.done: self._trans.draw(surf)

# ═══════════════════════════════════════════════════════════════
#  F4 – FIELD SETTING SCREEN
# ═══════════════════════════════════════════════════════════════
class FieldSettingScreen(Screen):
    def __init__(self,gs):
        super().__init__(gs)
        P=16; bw=(W-P*2-24)//3
        self._field_btns=[]
        for i,(name,preset) in enumerate(FIELD_PRESETS.items()):
            col=preset["col"]
            b=Button((P+i*(bw+12),360,bw,54),name,F_SM,
                     abg=col,afg=BK,rad=12,tag=("field",name))
            b.sel=(name==gs.field_setting)
            self._field_btns.append(b)
        self._ok_btn=Button((P,H-72,W-P*2,54),"▶  CONTINUE",F_LG,
                            bg=ACG,fg=BK,hov=AC2,abg=AC2,afg=BK,rad=14,tag="ok",glow_col=ACG)
        self.buttons=self._field_btns+[self._ok_btn]
        self._t=0.0; self._sel=gs.field_setting

    def on_button(self,b):
        if isinstance(b.tag,tuple) and b.tag[0]=="field":
            self._sel=b.tag[1]; self.gs.field_setting=self._sel
            [setattr(x,"sel",x.tag==b.tag) for x in self._field_btns]
        elif b.tag=="ok": self.next="sim_mode"

    def update(self,dt):
        super().update(dt); self._t+=dt

    def draw(self,surf):
        surf.fill(BG); self._bg_parts.draw(surf)
        grad(surf,BG2,BG,(0,0,W,104)); glow_line(surf,ORG,0,4)
        txtm(surf,"FIELD PLACEMENT",F_XL,TXT,22)
        txtm(surf,"Choose your defensive strategy",F_SM,TX2,56)
        pygame.draw.line(surf,BDR,(0,100),(W,100),1)
        # Mini field map
        fm_w=220; fm_h=200
        fm_x=(W-fm_w)//2; fm_y=130
        draw_field_map(surf,self._sel,fm_x,fm_y,fm_w,fm_h)
        # Preset info
        preset=FIELD_PRESETS.get(self._sel,FIELD_PRESETS["Balanced"])
        cy=fm_y+fm_h+12
        rr(surf,BG3,(16,cy,W-32,80),12)
        txtm(surf,preset["description"],F_SM,TX2,cy+10)
        bc=ACG if preset["boundary_mod"]>=1.0 else RED
        txt(surf,f"Bdry: {preset['boundary_mod']:.0%}",F_XS,bc,30,cy+36)
        sc2=ACG if preset["single_mod"]>=1.0 else RED
        txt(surf,f"Singles: {preset['single_mod']:.0%}",F_XS,sc2,W//2-30,cy+36)
        cc=ACG if preset["catch_mod"]>=1.0 else RED
        txt(surf,f"Catches: {preset['catch_mod']:.0%}",F_XS,cc,W-30,cy+36,align="right")
        cy+=90
        txtm(surf,"SELECT FIELD",F_XS,TX3,cy+4)
        for b in self.buttons: b.draw(surf)
        if not self._trans.done: self._trans.draw(surf)

# ═══════════════════════════════════════════════════════════════
#  MATCH SCREEN  (F2, F3, F4, F6, F7, F8, F9 integrated)
# ═══════════════════════════════════════════════════════════════
class MatchScreen(Screen):
    BAT_OPTS=[
        ("Defensive",       "0-6/ov",  BLU),
        ("Normal",          "5-14/ov", ACG),
        ("Aggressive",      "10-22/ov",GLD),
        ("Ultra Aggressive","15-36/ov",RED),
    ]
    BOWL_OPTS_FAST=[
        ("Defensive",   "Tight",   BLU),
        ("Good Length", "Line",    ACG),
        ("Attacking",   "Attack",  ORG),
        ("Yorker Focus","Yorkers", RED),
        ("Slower Ball", "Slow",    PRP),
    ]
    BOWL_OPTS_SPIN=[
        ("Defensive",  "Tight",    BLU),
        ("Off Spin",   "Off Spin", ACG),
        ("Leg Spin",   "Leg Spin", GLD),
        ("Doosra",     "Doosra",   PRP),
        ("Flighted Ball","Flight", CYN),
    ]

    def __init__(self,gs):
        super().__init__(gs)
        self._over_result=[]; self._show_summary=False; self._sum_t=0.0
        self._parts=Particles(); self._sel_bat=1; self._sel_bowl=1
        self._t=0.0; self._ai_flash=0.0
        # F2: ball-by-ball state
        self._bbb_balls=[]      # remaining balls in current BBB over
        self._bbb_active=False  # True while in ball-by-ball mode
        self._bbb_current=None  # (res,delv,comm) last ball
        self._bbb_wait=False    # waiting for tap to advance
        self._bbb_bat_sty=""
        self._bbb_bowl_sty=""
        # F9: trajectory particles
        self._traj_parts=Particles()
        self._build_ctrl()

    def _build_ctrl(self):
        self.buttons=[]
        gs=self.gs; P=10; G=6
        CTRL_Y=H-126
        if gs.player_bats:
            bw=(W-P*2-G*3)//4
            for i,(lbl,sub,col) in enumerate(self.BAT_OPTS):
                x=P+i*(bw+G)
                b=Button((x,CTRL_Y+22,bw,60),f"{lbl}\n{sub}",F_XS,
                         bg=BG4,fg=TX2,hov=BG5,abg=col,afg=BK,rad=12,tag=("bat",i))
                b.sel=(i==self._sel_bat); self.buttons.append(b)
        else:
            # F6: show delivery options based on current bowler role
            bat=gs.batting
            bowl_xi=gs.opp_xi if bat.code==gs.player_team else gs.player_xi
            cur_bowler=None
            if gs.current_bowler_name:
                cur_bowler=next((p for p in bowl_xi if p["name"]==gs.current_bowler_name),None)
            opts=self.BOWL_OPTS_SPIN if (cur_bowler and cur_bowler["role"]=="Spinner") else self.BOWL_OPTS_FAST
            bw=(W-P*2-G*4)//5
            for i,(lbl,sub,col) in enumerate(opts):
                x=P+i*(bw+G)
                b=Button((x,CTRL_Y+22,bw,60),f"{lbl}\n{sub}",F_XS,
                         bg=BG4,fg=TX2,hov=BG5,abg=col,afg=BK,rad=12,tag=("bowl",i))
                b.sel=(i==self._sel_bowl); self.buttons.append(b)
        self._mb=Button((W-80,8,72,28),"MENU",F_XS,bg=BG4,fg=TX2,hov=BG5,abg=RED,afg=WH,rad=8,tag="menu")
        # F4: field setting button
        self._field_btn=Button((W-160,8,72,28),"FIELD",F_XS,bg=BG4,fg=ORG,hov=BG5,abg=ORG,afg=BK,rad=8,tag="field")

    def handle(self,ev):
        if self._dlg:
            if self._dlg.handle(ev): self._dlg=None; return
        if self._mb.handle(ev): self._confirm_menu(); return
        if self._field_btn.handle(ev): self.next="field_setting"; return
        # F2: ball-by-ball tap to advance
        if self._bbb_active and self._bbb_wait:
            if ev.type in(pygame.MOUSEBUTTONUP,pygame.KEYDOWN):
                self._bbb_wait=False
                self._advance_bbb()
                return
        if self._show_summary:
            if ev.type in(pygame.MOUSEBUTTONUP,pygame.KEYDOWN):
                self._show_summary=False
                if not self.gs.game_over and not self.next: self._check_end()
                else: self._check_end()
            return
        for b in self.buttons:
            if b.handle(ev): self.on_button(b)
        if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE: self._confirm_menu()

    def on_button(self,b):
        gs=self.gs
        if gs.game_over: return
        k=b.tag[0]
        if k in("bat","bowl"):
            if k=="bat": self._sel_bat=b.tag[1]
            else:        self._sel_bowl=b.tag[1]
            for btn in self.buttons: btn.sel=(btn.tag==b.tag)
            self._start_over()

    def _start_over(self):
        gs=self.gs
        if gs.player_bats:
            bat_sty=self.BAT_OPTS[self._sel_bat][0]
            bowl_sty=gs.ai.bowl_style(gs.batting.overs,gs.fmt_overs,gs.batting.wickets,gs.batting.score,gs.target)
        else:
            bowl_sty_name=self._get_bowl_style_name()
            bat=gs.batting; bl_rem=gs.fmt_overs*6-bat.total_balls
            bat_sty=gs.ai.bat_style(bat.score,bat.wickets,gs.target,bl_rem,gs.fmt_overs)
            bowl_sty=bowl_sty_name

        if gs.sim_mode=="ball_by_ball":
            self._bbb_bat_sty=bat_sty; self._bbb_bowl_sty=bowl_sty
            self._prepare_bbb(bat_sty,bowl_sty)
        else:
            self._play_full_over(bat_sty,bowl_sty)

    def _get_bowl_style_name(self):
        gs=self.gs
        bat=gs.batting
        bowl_xi=gs.opp_xi if bat.code==gs.player_team else gs.player_xi
        cur_bowler=next((p for p in bowl_xi if p["name"]==gs.current_bowler_name),None)
        opts=self.BOWL_OPTS_SPIN if (cur_bowler and cur_bowler["role"]=="Spinner") else self.BOWL_OPTS_FAST
        return opts[min(self._sel_bowl,len(opts)-1)][0]

    def _prepare_bbb(self,bat_sty,bowl_sty):
        """F2: Pre-generate the 6 balls then show them one by one."""
        gs=self.gs; bat=gs.batting; over_num=bat.overs
        br=int(avg_r(bat.xi,"bat"))
        wlr=int(avg_r((gs.bat2 if gs.innings==1 else gs.bat1).xi,"bowl"))
        field_mod=FIELD_PRESETS.get(gs.field_setting,{})
        balls=[]
        tmp_score=bat.score; tmp_wickets=bat.wickets
        for _ in range(6):
            if bat.innings_over(gs.fmt_overs): break
            if gs.chase_won(): break
            res,delv,comm=_sim_ball(bat_sty,bowl_sty,gs.venue,bat,gs.fmt_overs,
                                     gs.innings,gs.target,over_num,br,wlr)
            balls.append((res,delv,comm))
        self._bbb_balls=balls; self._bbb_active=True
        self._bbb_current=None; self._bbb_wait=False
        self._bbb_done_balls=[]
        self._advance_bbb()

    def _advance_bbb(self):
        """F2: Process next ball in BBB mode."""
        gs=self.gs; bat=gs.batting
        if not self._bbb_balls or bat.innings_over(gs.fmt_overs) or gs.chase_won():
            self._finish_bbb(); return
        res,delv,comm=self._bbb_balls.pop(0)
        self._bbb_current=(res,delv,comm)
        self._bbb_done_balls.append((res,delv,comm))
        # Apply to game state
        if res=="W":
            bat.wickets+=1; self.gs.momentum=max(0,self.gs.momentum-22)
        else:
            bat.score+=res
            if res==0: bat.dots+=1; self.gs.momentum=max(0,self.gs.momentum-6)
            elif res==4: bat.boundaries+=1; self.gs.momentum=min(100,self.gs.momentum+16)
            elif res==6: bat.sixes+=1; self.gs.momentum=min(100,self.gs.momentum+26)
            else: self.gs.momentum=min(100,self.gs.momentum+res*3)
        bat.advance_ball()
        gs.log.append((bat.fmt_overs(),res,delv,comm))
        # F9: ball trajectory animation
        if res==6: self._traj_parts.emit_trajectory(W//2,320,"six")
        elif res==4: self._traj_parts.emit_trajectory(W//2,320,"four")
        elif delv in("yorker","bouncer"): self._traj_parts.emit_trajectory(W//2,320,delv)
        self._bbb_wait=True
        if gs.chase_won() or bat.innings_over(gs.fmt_overs):
            self._bbb_balls=[]; self._finish_bbb()

    def _finish_bbb(self):
        gs=self.gs; bat=gs.batting
        done=self._bbb_done_balls[:]
        runs=sum(r for r,_,__ in done if isinstance(r,int))
        wkts=sum(1 for r,_,__ in done if r=="W")
        bat.over_scores.append((runs,wkts))
        self._over_result=done; self._bbb_active=False
        self._show_summary=True; self._sum_t=0.0
        if runs>=12: self._parts.emit(W//2,320,ACG,14,160)
        if wkts>=2: self._parts.emit(W//2,320,RED,12,140)
        if gs.chase_won() or gs.innings_done(): self._check_end()

    def _play_full_over(self,bat_sty,bowl_sty):
        gs=self.gs
        field_mod=FIELD_PRESETS.get(gs.field_setting,{})
        balls,runs,wkts=gs.play_over(bat_sty,bowl_sty,field_mod)
        self._over_result=balls; self._show_summary=True; self._sum_t=0.0
        if runs>=12: self._parts.emit(W//2,320,ACG,14,160)
        if wkts>=2: self._parts.emit(W//2,320,RED,12,140)
        if gs.chase_won() or gs.innings_done(): self._check_end()

    def _check_end(self):
        gs=self.gs
        if gs.chase_won(): gs.game_over=True; gs.calculate_pom(); self.next="result"
        elif gs.innings_done():
            if gs.innings==1: self.next="break"
            else: gs.game_over=True; gs.calculate_pom(); self.next="result"

    def update(self,dt):
        super().update(dt)
        self._mb.update(dt); self._field_btn.update(dt)
        self._parts.update(dt); self._traj_parts.update(dt)
        self._t+=dt; self._sum_t+=dt; self._ai_flash=(self._ai_flash+dt)%2.0

    def draw(self,surf):
        gs=self.gs; bat=gs.batting; is_bat=gs.player_bats
        tint=BAT_T if is_bat else BOW_T
        surf.fill(lerp(BG,tint,0.55))
        grad(surf,lerp(BG2,tint,0.65),lerp(BG,tint,0.55),(0,0,W,168))
        glow_line(surf,bat.col,0,4)
        self._bg_parts.draw(surf)

        # F8: Powerplay indicator
        pp_overs=6 if gs.fmt_overs==20 else 10
        in_pp=(bat.overs<pp_overs)

        txt(surf,f"{gs.venue['name']} · {gs.venue['city']}",F_XS,TX3,14,11)
        inn="1st INNINGS" if gs.innings==1 else "2nd INNINGS · CHASE"
        mode="BATTING" if is_bat else "BOWLING"; mc=ACG if is_bat else RED

        img2=F_XS.render(f"{mode} · {gs.fmt_key}",True,mc)
        pw2=img2.get_width()+14; rr(surf,lerp(mc,BG,0.82),(W-pw2-10,30,pw2,20),10)
        surf.blit(img2,(W-pw2-3,32))
        # F8: PP badge
        if in_pp:
            pp_img=F_XS.render("⚡ POWERPLAY",True,GLD)
            ppw=pp_img.get_width()+14; rr(surf,lerp(GLD,BG,0.7),(W-ppw-10,54,ppw,18),8)
            surf.blit(pp_img,(W-ppw-3,56))
        self._mb.draw(surf); self._field_btn.draw(surf)

        txt(surf,bat.name,F_SM,bat.col,14,34)
        sc_str=bat.fmt_score()
        sc_img=F_SC.render(sc_str,True,TXT); surf.blit(sc_img,(14,50))
        txt(surf,bat.fmt_overs()+" ov",F_MD,TX2,14,114)
        txt(surf,f"CRR {bat.crr:.2f}",F_MD,TX3,160,114)
        txt(surf,f"4s:{bat.boundaries}  6s:{bat.sixes}",F_XS,TX3,W-14,116,align="right")
        pygame.draw.line(surf,BDR,(0,146),(W,146),1)
        cy=150

        if gs.innings==2:
            need=gs.target-bat.score; bl=gs.fmt_overs*6-bat.total_balls
            rrr=(need*6/bl) if bl>0 else 99.99
            rrc=ACG if rrr<9 else (GLD if rrr<13 else RED)
            rr(surf,BG3,(10,cy,W-20,44),10)
            txt(surf,f"Target  {gs.target}",F_MD,GLD,20,cy+6)
            txt(surf,f"Need {need}  from  {bl}  balls",F_MD,rrc,190,cy+6,mw=W-200)
            txt(surf,f"RRR {rrr:.2f}",F_MD,rrc,W-20,cy+24,align="right")
            pct=bat.score/max(1,gs.target); bc=ACG if pct<0.85 else GLD
            rr(surf,BG4,(10,cy+38,W-20,6),3)
            rr(surf,bc,(10,cy+38,max(0,int((W-20)*pct)),6),3)
            cy+=56
        else: cy+=4

        if is_bat:
            mom=gs.momentum/100.0; mc2=lerp(RED,ACG,mom)
            txt(surf,"MOMENTUM",F_XS,TX3,14,cy+2)
            rr(surf,BG4,(104,cy+2,W-118,12),5)
            rr(surf,mc2,(104,cy+2,max(0,int((W-118)*mom)),12),5)
            cy+=20

        # Field indicator (F4)
        fp=FIELD_PRESETS.get(gs.field_setting,{})
        fc=fp.get("col",ACG) if fp else ACG
        txt(surf,f"⬡ {gs.field_setting}",F_XS,(*fc,180),14,cy+2)
        cy+=18

        ov_slots=gs.fmt_overs; slot_w=(W-28)/ov_slots; oy=cy+4
        for ov_i in range(ov_slots):
            ox2=14+int(ov_i*slot_w); ow=max(2,int(slot_w)-1)
            if ov_i<bat.overs:
                score_ov,wkt_ov=(bat.over_scores[ov_i] if ov_i<len(bat.over_scores) else (0,0))
                col=RED if wkt_ov>0 else (ACG if score_ov>=8 else BLU)
                pp_hl=GLD if ov_i<pp_overs else col  # F8 highlight PP overs
                rr(surf,pp_hl,(ox2,oy,ow,8),2)
            elif ov_i==bat.overs:
                rr(surf,GLD,(ox2,oy,ow,8),2,alpha=160)
            else:
                col_empty=lerp(BG4,GLD,0.1) if ov_i<pp_overs else BG4
                rr(surf,col_empty,(ox2,oy,ow,8),2)
        cy+=18

        pygame.draw.line(surf,BDR,(0,cy),(W,cy),1)
        txt(surf,"COMMENTARY",F_XS,TX3,14,cy+4); ly=cy+22
        dcols={"yorker":PRP,"bouncer":RED,"full_toss":GLD,"slower":CYN,"good_length":BLU,"wide_half":ACG,
               "off_spin":CYN,"leg_spin":GLD,"doosra":PRP,"googly":ORG,"carrom":BL2,"flighted":ACG}
        for entry in reversed(gs.log[-5:]):
            if ly>H-136: break
            tg,res,delv,comm=entry
            rr(surf,BG4,(10,ly,W-20,34),7)
            dc=dcols.get(delv,BG5); dw=F_XS.size(delv)[0]+10
            rr(surf,lerp(dc,BG,0.5),(14,ly+4,dw,16),4)
            txt(surf,delv,F_XS,dc,14+dw//2,ly+6,align="center")
            if res=="W":   dotc,dch=RED,"W"
            elif res==6:   dotc,dch=ACG,"6"
            elif res==4:   dotc,dch=GLD,"4"
            elif res==0:   dotc,dch=BG5,"·"
            else:          dotc,dch=BLU,str(res)
            pygame.draw.rect(surf,dotc,(W-42,ly+5,26,24),border_radius=5)
            txt(surf,dch,F_MO,WH,W-29,ly+9,align="center")
            txt(surf,comm,F_XS,TX2,14+dw+7,ly+11,mw=W-dw-58)
            ly+=37

        # Control bar
        CTRL_Y=H-126
        pygame.draw.line(surf,BDR,(0,CTRL_Y),(W,CTRL_Y),1)
        rr(surf,BG2,(0,CTRL_Y,W,126),0,alpha=230)
        hint_col=ACG if is_bat else RED
        hint="BATTING STRATEGY" if is_bat else "BOWLING PLAN"
        # F7: show sim mode
        sim_label=" [BALL BY BALL]" if gs.sim_mode=="ball_by_ball" else ""
        txt(surf,hint+sim_label,F_XS,hint_col,14,CTRL_Y+6)
        if not is_bat:
            ai_a=int(140+100*math.sin(self._ai_flash*math.pi))
            txt(surf,f"AI: {gs.difficulty}  Bowler: {gs.current_bowler_name or 'Auto'}",
                F_XS,(*TX3,ai_a),W-14,CTRL_Y+6,align="right")
        for b in self.buttons: b.draw(surf)

        # F9: trajectory
        self._traj_parts.draw(surf)
        self._parts.draw(surf)
        self.toast.draw(surf)

        # F2: Ball-by-ball overlay
        if self._bbb_active and self._bbb_wait and self._bbb_current:
            self._draw_bbb_overlay(surf)
        elif self._show_summary:
            self._draw_over_summary(surf)

        if self._dlg: self._dlg.draw(surf)
        if not self._trans.done: self._trans.draw(surf)

    def _draw_bbb_overlay(self,surf):
        """F2: Ball-by-ball delivery display."""
        gs=self.gs; bat=gs.batting
        ov=pygame.Surface((W,H),pygame.SRCALPHA)
        a=min(200,int(self._sum_t*600)); ov.fill((0,0,0,a)); surf.blit(ov,(0,0))
        shadow(surf,(20,180,W-40,300),20,12,100)
        glass(surf,(20,180,W-40,300),col=BG3,border=ACG,alpha=245,r=20)
        rb(surf,(*ACG,150),(20,180,W-40,300),2,20)
        glow_line(surf,ACG,182,2,80)

        res,delv,comm=self._bbb_current
        b_num=len(self._bbb_done_balls)
        over_num=bat.overs if bat.balls>0 else bat.overs
        ball_num=bat.balls if bat.balls>0 else 6
        txtm(surf,f"OVER {over_num}.{ball_num}",F_LG,TXT,196)
        # Bowler & batter names
        b1,b2=bat.current_batters()
        txtm(surf,f"? to {b1}",F_SM,TX2,228)

        if res=="W":   bc,fc,ch=RED,WH,"W"
        elif res==6:   bc,fc,ch=ACG,BK,"6"
        elif res==4:   bc,fc,ch=GLD,BK,"4"
        elif res==0:   bc,fc,ch=BG4,TX3,"•"
        else:          bc,fc,ch=BLU,WH,str(res)

        # Big ball result
        circ_a(surf,bc,W//2,310,36,220)
        txtm(surf,ch,F_XL,fc,298)
        txtm(surf,comm,F_MD,TXT,368,mw=W-60)

        # Running score
        txtm(surf,bat.fmt_score(),F_XL,bat.col,408)
        txtm(surf,f"({bat.fmt_overs()} ov)",F_XS,TX2,444)

        # Ball progress dots
        bx=W//2-len(self._bbb_done_balls)*19
        for j,(r,_,__) in enumerate(self._bbb_done_balls):
            if r=="W": dc=RED
            elif r==6: dc=ACG
            elif r==4: dc=GLD
            elif r==0: dc=BG4
            else: dc=BLU
            rr(surf,dc,(bx+j*38,462,30,16),5)
            rl=str(r) if r!="W" else "W"
            txt(surf,rl,F_XS,WH,bx+j*38+15,463,align="center")

        txtm(surf,"Tap to continue",F_XS,TX3,490)

    def _draw_over_summary(self,surf):
        ov=pygame.Surface((W,H),pygame.SRCALPHA)
        a=min(210,int(self._sum_t*700)); ov.fill((0,0,0,a)); surf.blit(ov,(0,0))
        shadow(surf,(28,195,W-56,370),20,12,100)
        glass(surf,(28,195,W-56,370),col=BG3,border=ACG,alpha=245,r=20)
        rb(surf,(*ACG,150),(28,195,W-56,370),2,20)
        glow_line(surf,ACG,196,2,80)
        cur_bat=self.gs.batting
        ov_num=(cur_bat.overs-1) if cur_bat.balls==0 else cur_bat.overs
        txtm(surf,f"Over {ov_num} Complete",F_MD,TXT,212)
        n=len(self._over_result); bx=W//2-n*19
        for j,(res,_,__) in enumerate(self._over_result):
            if res=="W": bc,fc,ch=RED,WH,"W"
            elif res==6: bc,fc,ch=ACG,BK,"6"
            elif res==4: bc,fc,ch=GLD,BK,"4"
            elif res==0: bc,fc,ch=BG4,TX3,"·"
            else:        bc,fc,ch=BG4,BLU,str(res)
            rr(surf,bc,(bx+j*38,248,32,32),8)
            txt(surf,ch,F_MD,fc,bx+j*38+16,252,align="center")
        or_=sum(r for r,_,__ in self._over_result if isinstance(r,int))
        wk=sum(1 for r,_,__ in self._over_result if r=="W")
        run_col=ACG if or_>=8 else (GLD if or_>=5 else TX2)
        txtm(surf,f"Runs: {or_}   Wickets: {wk}",F_LG,run_col,298)
        ly2=336
        for _,_,comm in self._over_result[-4:]:
            if ly2>522: break
            txtm(surf,comm,F_XS,TX2,ly2,mw=W-80); ly2+=24
        txtm(surf,"Tap anywhere to continue",F_XS,TX3,524)

# ═══════════════════════════════════════════════════════════════
#  INNINGS BREAK
# ═══════════════════════════════════════════════════════════════
class BreakScreen(Screen):
    def __init__(self,gs):
        super().__init__(gs)
        gs.target=gs.bat1.score+1; gs.innings=2
        gs.bat2=BattingTeam(gs.bat2.code,gs.bat2.xi)
        gs.current_over=[]; gs.momentum=50.0
        gs.player_bats=(gs.bat2.code==gs.player_team)
        gs.next_batter_idx=2; gs.sim_mode="full_over"
        self._t=0.0; self._parts=Particles()
        self._parts.emit_firework(W//2,300,GLD,22)
        self.buttons=[Button((W//2-140,H-88,280,58),"▶  BEGIN THE CHASE",F_LG,
                             bg=GLD,fg=BK,hov=GL2,abg=GL2,afg=BK,bc=GLD,rad=30,
                             tag="go",glow_col=GLD)]

    def on_button(self,b):
        if b.tag=="go": self.next="sim_mode"

    def update(self,dt):
        super().update(dt); self._t+=dt; self._parts.update(dt)

    def draw(self,surf):
        surf.fill(BG); self._bg_parts.draw(surf)
        c=lerp(BG2,lerp(GLD,BG,0.9),abs(math.sin(self._t*0.4)))
        grad(surf,c,BG,(0,0,W,104)); glow_line(surf,GLD,0,4)
        txtm(surf,"INNINGS BREAK",F_XL,GLD,24)
        pygame.draw.line(surf,BDR,(0,100),(W,100),1)
        self._parts.draw(surf)
        b1=self.gs.bat1

        shadow(surf,(18,114,W-36,116),16,8,70)
        glass(surf,(18,114,W-36,116),col=BG3,border=BDR,alpha=225,r=18)
        rb(surf,(*b1.col,170),(18,114,W-36,116),2,18)
        rr(surf,b1.col,(18,114,W-36,4),3)
        txtm(surf,b1.name+" — 1st Innings",F_SM,TX2,126)
        txtm(surf,b1.fmt_score(),F_XXL,b1.col,148)
        txtm(surf,f"({b1.fmt_overs()} ov)   CRR {b1.crr:.2f}   4s:{b1.boundaries}   6s:{b1.sixes}",F_XS,TX3,200)

        pygame.draw.line(surf,BDR,(60,240),(W-60,240),1)

        shadow(surf,(18,254,W-36,208),18,8,70)
        glass(surf,(18,254,W-36,208),col=BG3,border=ACG,alpha=225,r=18)
        rb(surf,(*ACG,170),(18,254,W-36,208),2,18)
        rr(surf,ACG,(18,254,W-36,4),3)
        b2=self.gs.bat2
        txtm(surf,b2.name+" need",F_LG,TX2,268)
        p=1.0+0.05*math.sin(self._t*3.5)
        ts=F_SC.render(str(self.gs.target),True,ACG)
        tw,th=ts.get_size(); nw,nh=max(1,int(tw*p)),max(1,int(th*p))
        ts2=pygame.transform.smoothscale(ts,(nw,nh)); surf.blit(ts2,(W//2-nw//2,298))
        txtm(surf,f"runs to win in {self.gs.fmt_overs} overs",F_MD,TX2,390)
        rrr=self.gs.target*6/(self.gs.fmt_overs*6)
        rrc=ACG if rrr<9 else (GLD if rrr<13 else RED)
        txtm(surf,f"Required Rate: {rrr:.2f}",F_SM,rrc,422)

        for b in self.buttons: b.draw(surf)
        if self._dlg: self._dlg.draw(surf)
        if not self._trans.done: self._trans.draw(surf)

# ═══════════════════════════════════════════════════════════════
#  F5 – RESULT SCREEN  (Player of Match, Return Home, Tournament Hub)
# ═══════════════════════════════════════════════════════════════
class ResultScreen(Screen):
    def __init__(self,gs):
        super().__init__(gs)
        b1,b2=gs.bat1,gs.bat2; self._t=0.0
        self._w2=b2.score>=gs.target; self._win=b2 if self._w2 else b1
        self._pw=(self._win.code==gs.player_team)
        self._mg=(f"by {MAX_WICKETS-b2.wickets} wickets" if self._w2
                  else f"by {gs.target-b2.score-1} runs")
        self._parts=Particles(); rc=ACG if self._pw else RED
        for _ in range(12): self._parts.emit_firework(random.randint(40,W-40),random.randint(60,200),rc,10)
        # F5 – buttons
        has_tour=gs.tournament is not None
        btn_y=H-156 if has_tour else H-116
        self.buttons=[
            Button((14,btn_y,W-28,48),"PLAY AGAIN",F_LG,bg=ACG,fg=BK,hov=AC2,abg=AC2,afg=BK,
                   bc=AC2,rad=14,tag="a",glow_col=ACG),
            Button((14,btn_y+58,W-28,40),"RETURN HOME",F_MD,bg=BG4,fg=TX2,rad=14,tag="home"),
        ]
        if has_tour:
            self.buttons.append(
                Button((14,btn_y+108,W-28,40),"TOURNAMENT HUB",F_MD,bg=BG4,fg=GLD,rad=14,tag="tour")
            )
        # Update tournament match result
        if gs.tournament and gs.tournament_match:
            m=gs.tournament_match
            m.played=True; m.score1=b1.score; m.wkts1=b1.wickets; m.overs1=b1.fmt_overs()
            m.score2=b2.score; m.wkts2=b2.wickets; m.overs2=b2.fmt_overs()
            m.winner=self._win.code; m.loser=(b1 if self._win==b2 else b2).code
            m.margin=self._mg
            for grp in getattr(gs.tournament,"groups",[]):
                for gm in grp.matches:
                    if gm is m or (gm.team1==m.team1 and gm.team2==m.team2 and not gm.played):
                        grp._update_table(m,gs.fmt_key); break

    def on_button(self,b):
        if b.tag=="a": self.gs.__init__(); self.next="menu"
        elif b.tag=="home": self.gs.__init__(); self.next="menu"
        elif b.tag=="tour": self.next="tournament_hub"

    def update(self,dt):
        super().update(dt); self._t+=dt; self._parts.update(dt)
        if self._t<4.0 and random.random()<0.08:
            rc=ACG if self._pw else RED
            self._parts.emit_firework(random.randint(30,W-30),random.randint(30,160),rc,6)

    def draw(self,surf):
        surf.fill(BG); gs=self.gs; rc=ACG if self._pw else RED
        self._bg_parts.draw(surf)
        c=lerp(BG2,lerp(rc,BG,0.92),abs(math.sin(self._t*0.3)))
        grad(surf,c,BG,(0,0,W,160)); glow_line(surf,rc,0,4)
        self._parts.draw(surf)

        bounce=int(7*math.sin(self._t*2.8)); cx=W//2
        circ_a(surf,rc,cx,66+bounce,60,50)
        pygame.draw.circle(surf,rc,(cx,66+bounce),58,3)
        icon="★" if self._pw else "✗"
        txtm(surf,icon,F_XXL,rc,42+bounce)

        txtm(surf,f"{self._win.name.upper()}  WIN!",F_XL,rc,94)
        txtm(surf,self._mg,F_LG,TXT,130)
        pygame.draw.line(surf,BDR,(0,162),(W,162),1)

        # F5: Scorecard
        shadow(surf,(14,168,W-28,160),18,8,70)
        glass(surf,(14,168,W-28,160),col=BG3,border=BDR,alpha=225,r=18)
        txt(surf,"SCORECARD",F_XS,TX3,30,180)
        pygame.draw.line(surf,BDR,(30,196),(W-30,196),1)
        for i,t in enumerate([gs.bat1,gs.bat2]):
            ry=204+i*58; iw=(t==self._win); tc=t.col if iw else TX2
            if iw: rr(surf,t.col,(14,ry,5,52),3)
            bf=F_MD if iw else F_SM; pr=">> " if iw else "   "
            txt(surf,f"{pr}{t.name}",bf,tc,32,ry+4)
            txt(surf,t.fmt_score(),F_MO,tc,W-28,ry+4,align="right")
            txt(surf,f"({t.fmt_overs()} ov)  CRR {t.crr:.2f}",F_MOS,TX3,W-28,ry+22,align="right")
            txt(surf,f"4s:{t.boundaries}  6s:{t.sixes}  •:{t.dots}",F_MOS,TX3,W-28,ry+38,align="right")
            if i==0: pygame.draw.line(surf,BDR,(30,ry+54),(W-30,ry+54),1)

        # F5: Player of Match
        pom=gs.pom
        if pom:
            cy=334
            rr(surf,lerp(GLD,BG,0.75),(14,cy,W-28,44),12)
            rb(surf,(*GLD,120),(14,cy,W-28,44),1,12)
            txtm(surf,f"⭐ Player of the Match: {pom['name']} ({pom['team']})",F_SM,GLD,cy+12)

        txtm(surf,f"{gs.venue['name']} · {gs.venue['city']} · {gs.fmt_key}",F_XS,TX3,384)

        for b in self.buttons: b.draw(surf)
        if self._dlg: self._dlg.draw(surf)
        if not self._trans.done: self._trans.draw(surf)

# ═══════════════════════════════════════════════════════════════
#  F9 – TROPHY CEREMONY SCREEN (post-tournament)
# ═══════════════════════════════════════════════════════════════
class TrophyScreen(Screen):
    def __init__(self,gs,champion_code):
        super().__init__(gs)
        self._champ=champion_code
        self._team=next((t for t in TEAMS if t["code"]==champion_code),TEAMS[0])
        self._t=0.0; self._parts=Particles()
        for _ in range(20):
            self._parts.emit_firework(random.randint(20,W-20),random.randint(20,200),
                                     self._team["col"],16)
        self.buttons=[Button((W//2-140,H-80,280,52),"MAIN MENU",F_LG,
                             bg=GLD,fg=BK,hov=GL2,abg=GL2,afg=BK,rad=30,tag="menu",glow_col=GLD)]

    def on_button(self,b):
        if b.tag=="menu": self.gs.__init__(); self.next="menu"

    def update(self,dt):
        super().update(dt); self._t+=dt; self._parts.update(dt)
        if self._t<6.0 and random.random()<0.12:
            self._parts.emit_firework(random.randint(20,W-20),random.randint(10,H//3),
                                     random.choice([GLD,ACG,self._team["col"],PRP]),12)

    def draw(self,surf):
        surf.fill(BG); self._bg_parts.draw(surf)
        col=self._team["col"]
        grad(surf,lerp(col,BG,0.7),BG,(0,0,W,H))
        glow_line(surf,col,0,6)
        self._parts.draw(surf)
        # Trophy
        bounce=int(8*math.sin(self._t*2.2)); cy=160+bounce
        circ_a(surf,GLD,W//2,cy,80,60)
        pygame.draw.circle(surf,GLD,(W//2,cy),78,4)
        txtm(surf,"🏆",F_SC,GLD,cy-40)

        txtm(surf,"CHAMPIONS!",F_SC,col,cy+70)
        txtm(surf,self._team["name"].upper(),F_XL,WH,cy+130)
        txtm(surf,f"Winners of the {self.gs.tournament.t_type if self.gs.tournament else 'Tournament'}",
             F_SM,TX2,cy+170)

        # Confetti (stars)
        for i in range(0,W,40):
            x=i+int(20*math.sin(self._t*2+i*0.1))
            y=100+int(30*math.cos(self._t*1.5+i*0.15))
            circ_a(surf,GLD,x,y,3,int(180*abs(math.sin(self._t+i))))

        for b in self.buttons: b.draw(surf)
        if not self._trans.done: self._trans.draw(surf)

# ─────────────────────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────────────────────
SCREENS={
    "menu":MenuScreen,
    "squad":SquadScreen,
    "toss":TossScreen,
    "match":MatchScreen,
    "break":BreakScreen,
    "result":ResultScreen,
    "tournament":TournamentSetupScreen,
    "tournament_hub":TournamentHubScreen,
    "sim_mode":SimModeScreen,
    "field_setting":FieldSettingScreen,
    "bowler_select":BowlerSelectScreen,
    "trophy":TrophyScreen,
}

def main():
    gs=GS(); cur=MenuScreen(gs)
    while True:
        dt=min(clock.tick(FPS)/1000.0, 0.05)
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit(); sys.exit()
            cur.handle(ev)
        cur.update(dt)

        # Special screen creation for TrophyScreen (needs champion arg)
        if cur.next=="trophy" and hasattr(gs,"tournament") and gs.tournament:
            champ=gs.tournament.champion or gs.player_team
            cur=TrophyScreen(gs,champ)
            continue

        if cur.next:
            nxt=cur.next
            if nxt in SCREENS:
                cur=SCREENS[nxt](gs)
            else:
                cur=MenuScreen(gs)

        cur.draw(screen)
        pygame.display.flip()

if __name__=="__main__":
    main()