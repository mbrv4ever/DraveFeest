# -*- coding: utf-8 -*-
# DraveFeest - Kerst: bouw je eigen kerstdorp. Rustig spel zonder tijd.
# Zet huisjes, bomen, lantaarns en meer neer. Sterren uit de andere spellen maken nieuwe dingen vrij.
# Met dag/avond/nacht (of de echte tijd), sneeuw spuiten, en een kerkklok die het kwartier slaat.
# Copyright (C) 2026 Dravenlock (Roger & Claudio). Vrije software onder de GNU GPL v3.0.
import datetime
import math
import random

import pygame

from basis import Scene, tekst, gloed, mix, stijl_van, retro_klein, omlijn, LIJN

W, H = 1280, 720
HORIZON = 300
BALK = 120                         # onderbalk met de onderdelen
VELD_ONDER = H - BALK

# soort: (naam, sterren nodig, breedte, hoogte)
ONDERDELEN = [
    ("huis_rood", "Huisje", 0, 120, 120),
    ("huis_wit", "Wit huisje", 0, 110, 115),
    ("boom", "Kerstboom", 0, 70, 120),
    ("den", "Dennetje", 0, 44, 70),
    ("lantaarn", "Lantaarn", 0, 24, 110),
    ("hek", "Hekje", 0, 90, 30),
    ("sneeuwpop", "Sneeuwpop", 0, 46, 66),
    ("bank", "Bankje", 0, 64, 32),
    ("kerk", "Kerk", 1, 150, 230),
    ("huis_groot", "Groot huis", 2, 170, 150),
    ("vijver", "Schaatsvijver", 3, 200, 60),
    ("kraam", "Kerstkraam", 4, 100, 100),
    ("molen", "Molen", 5, 120, 210),
    ("koor", "Koortje", 6, 80, 54),
]
INFO = {o[0]: o for o in ONDERDELEN}
STANDEN = ["echt", "dag", "avond", "nacht"]
STAND_NAAM = {"echt": "Echte tijd", "dag": "Dag", "avond": "Avond", "nacht": "Nacht"}


def schaal_voor(y):
    """Verder weg (hoger) = kleiner."""
    return 0.55 + 0.6 * max(0.0, min(1.0, (y - HORIZON) / (VELD_ONDER - HORIZON)))


class Kerst(Scene):
    res = (W, H)
    pixel = False
    naam = "kerst"

    def __init__(self, spel):
        super().__init__(spel)
        self.dingen = [dict(d) for d in spel.opslag.d.get("kerstdorp", []) if d.get("soort") in INFO]
        self.stand = spel.opslag.d.get("kerst_stand", "echt")
        self.sneeuw = float(spel.opslag.d.get("kerst_sneeuw", 0.3))
        self.vast = None        # wat je aan de muis hebt: dict(soort, nieuw/index)
        self.muispos = (W / 2, H / 2)
        self.t = 0.0
        self.vlokken = []
        self.spuiten = False
        self.sterren = spel.opslag.totaal_sterren()
        self.melding, self.melding_t = "", 0.0
        self.laatste_slag = None
        self.slagen = []        # tijden waarop de klok slaat
        self.uitleg = not self.dingen
        self.oude_sterren = spel.opslag.sterren("kerst")
        rnd = random.Random(3)
        self.hemel = [(rnd.randrange(W), rnd.randrange(HORIZON)) for _ in range(140)]
        self.heuvels = [(x, rnd.randint(20, 60)) for x in range(-40, W + 80, 80)]
        self._gl = {}

    # ---- hulp
    def _gloed(self, r, kl, k=1.0):
        key = (r, kl, k)
        if key not in self._gl:
            self._gl[key] = gloed(r, kl, k)
        return self._gl[key]

    def tijd_stand(self):
        if self.stand != "echt":
            return self.stand
        u = datetime.datetime.now().hour
        return "dag" if 7 <= u < 17 else "avond" if 17 <= u < 23 else "nacht"

    def meld(self, t):
        self.melding, self.melding_t = t, 3.0

    def bewaar(self):
        o = self.spel.opslag
        o.d["kerstdorp"] = self.dingen
        o.d["kerst_stand"] = self.stand
        o.d["kerst_sneeuw"] = round(self.sneeuw, 2)
        o.bewaar()

    def _beoordeel(self):
        n = len(self.dingen)
        soorten = {d["soort"] for d in self.dingen}
        st = 0
        if n >= 8:
            st = 1
        if n >= 16 and "kerk" in soorten and ("boom" in soorten or "den" in soorten):
            st = 2
        if n >= 25 and len(soorten) >= 7:
            st = 3
        return st

    def weg(self):
        self.bewaar()
        st = self._beoordeel()
        if st > self.oude_sterren:
            self.spel.uitslag("kerst", "Je kerstdorp", len(self.dingen), st,
                              ["Je dorp heeft nu %d onderdelen." % len(self.dingen), "Wat een mooi dorp!"])
        else:
            self.spel.naar_dorp()

    def bij_afsluiten(self):
        self.bewaar()

    # ---- invoer
    def toets(self, ev):
        if self.uitleg:
            self.uitleg = False
            return
        if ev.key == pygame.K_ESCAPE:
            if self.vast:
                self.vast = None
            else:
                self.weg()
        elif ev.key == pygame.K_n:
            self.stand = STANDEN[(STANDEN.index(self.stand) + 1) % len(STANDEN)]
            self.meld("Licht: " + STAND_NAAM[self.stand])
        elif ev.key == pygame.K_s:
            self.spuiten = True
        elif ev.key == pygame.K_d and self.sneeuw > 0:
            self.sneeuw = max(0.0, self.sneeuw - 0.25)
            self.meld("Sneeuw weggehaald")
        elif ev.key == pygame.K_k:
            self._sla(3)
        elif ev.key in (pygame.K_F1, pygame.K_h):
            self.uitleg = True

    def los(self, ev):
        if ev.key == pygame.K_s:
            self.spuiten = False

    def muis(self, ev, pos):
        self.muispos = pos
        if self.uitleg and ev.type == pygame.MOUSEBUTTONDOWN:
            self.uitleg = False
            return
        if ev.type != pygame.MOUSEBUTTONDOWN:
            return
        x, y = pos
        if ev.button == 1:
            if y >= VELD_ONDER:
                o = self._onderdeel_op(x)
                if o:
                    if o[2] > self.sterren:
                        self.spel.geluid.speel("fout")
                        self.meld("%s: verdien eerst %d sterren in de andere spellen (je hebt er %d)."
                                  % (o[1], o[2], self.sterren))
                    else:
                        self.vast = dict(soort=o[0], nieuw=True)
                return
            if self.vast:
                if y < HORIZON - 10:
                    self.meld("Zet het iets lager neer, op de sneeuw.")
                    return
                d = dict(soort=self.vast["soort"], x=int(x), y=int(y))
                self.dingen.append(d)
                self.spel.geluid.speel("plaats")
                if self.vast["nieuw"] and not (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                    self.vast = None
                elif not self.vast["nieuw"]:
                    self.vast = None
                self.bewaar()
            else:
                i = self._ding_op(x, y)
                if i is not None:
                    d = self.dingen.pop(i)
                    self.vast = dict(soort=d["soort"], nieuw=False)
                    self.spel.geluid.speel("weg")
        elif ev.button == 3:
            if self.vast:
                self.vast = None
            else:
                i = self._ding_op(x, y)
                if i is not None:
                    self.dingen.pop(i)
                    self.spel.geluid.speel("weg")
                    self.bewaar()

    def _onderdeel_op(self, x):
        i = int((x - 10) // 90)
        return ONDERDELEN[i] if 0 <= i < len(ONDERDELEN) else None

    def _ding_op(self, x, y):
        beste = None
        for i, d in enumerate(self.dingen):
            o = INFO[d["soort"]]
            f = schaal_voor(d["y"])
            bw, bh = o[3] * f, o[4] * f
            if d["x"] - bw / 2 <= x <= d["x"] + bw / 2 and d["y"] - bh <= y <= d["y"] + 6:
                if beste is None or d["y"] > self.dingen[beste]["y"]:
                    beste = i
        return beste

    # ---- kerkklok (kwart = 1 slag, half = 2, heel uur = aantal uren; alleen overdag)
    def _sla(self, n):
        nu = self.t
        self.slagen = [nu + k * 1.6 for k in range(n)]

    def _klok(self):
        if not any(d["soort"] == "kerk" for d in self.dingen):
            return
        nu = datetime.datetime.now()
        if not (7 <= nu.hour < 22):
            return
        sleutel = (nu.hour, nu.minute)
        if nu.minute % 15 or sleutel == self.laatste_slag:
            return
        self.laatste_slag = sleutel
        if nu.minute == 0:
            self._sla(nu.hour % 12 or 12)
        elif nu.minute == 30:
            self._sla(2)
        else:
            self._sla(1)

    # ---- bijwerken
    def update(self, dt):
        self.t += dt
        self.melding_t = max(0, self.melding_t - dt)
        self._klok()
        while self.slagen and self.slagen[0] <= self.t:
            self.slagen.pop(0)
            self.spel.geluid.speel("klok")
        if self.spuiten:
            for _ in range(6):
                self.vlokken.append([random.uniform(0, W), -5, random.uniform(80, 160), random.uniform(0, 6)])
            self.sneeuw = min(1.0, self.sneeuw + dt * 0.12)
        elif random.random() < 0.5:
            self.vlokken.append([random.uniform(0, W), -5, random.uniform(25, 60), random.uniform(0, 6)])
        for v in self.vlokken:
            v[1] += v[2] * dt
            v[0] += math.sin(self.t * 1.3 + v[3]) * 20 * dt
        self.vlokken = [v for v in self.vlokken if v[1] < VELD_ONDER][-900:]

    # ---- tekenen
    def teken(self, s):
        stand = self.tijd_stand()
        stijl = stijl_van(self.spel)
        if stijl == "kleurrijk":
            lucht = {"dag": ((70, 150, 255), (190, 230, 255)), "avond": ((60, 30, 140), (230, 100, 170)),
                     "nacht": ((20, 14, 70), (70, 40, 130))}[stand]
        else:
            lucht = {"dag": ((120, 160, 210), (215, 228, 240)), "avond": ((22, 26, 70), (120, 80, 120)),
                     "nacht": ((4, 6, 20), (22, 26, 56))}[stand]
        for y in range(0, HORIZON, 4):
            pygame.draw.rect(s, mix(lucht[0], lucht[1], y / HORIZON), (0, y, W, 4))
        if stand != "dag":
            for i, (x, y) in enumerate(self.hemel):
                if (i + int(self.t)) % 13:
                    s.set_at((x, y), (230, 230, 255))
            pygame.draw.circle(s, (240, 240, 220), (1100, 80), 30)
        else:
            pygame.draw.circle(s, (255, 240, 200), (1100, 80), 34)
        # heuvels + sneeuwveld
        heuvel = mix((150, 165, 185), (235, 240, 248), self.sneeuw) if stand == "dag" else mix((40, 46, 76), (90, 100, 135), self.sneeuw)
        pts = [(-50, HORIZON + 20)] + [(x, HORIZON - h) for x, h in self.heuvels] + [(W + 50, HORIZON + 20)]
        pygame.draw.polygon(s, tuple(int(c * 0.85) for c in heuvel), pts)
        boven = mix((170, 180, 190), (245, 248, 252), self.sneeuw) if stand == "dag" else mix((50, 56, 86), (120, 130, 165), self.sneeuw)
        if stijl == "kleurrijk":
            heuvel = mix((150, 220, 160), (240, 248, 255), self.sneeuw) if stand == "dag" else mix((120, 70, 170), (170, 150, 220), self.sneeuw)
            pygame.draw.polygon(s, heuvel, pts)
            boven = mix((170, 230, 170), (235, 245, 255), self.sneeuw) if stand == "dag" else mix((110, 80, 170), (165, 150, 220), self.sneeuw)
        onder = tuple(max(0, c - 25) for c in boven)
        for y in range(HORIZON, VELD_ONDER, 4):
            pygame.draw.rect(s, mix(boven, onder, (y - HORIZON) / (VELD_ONDER - HORIZON)), (0, y, W, 4))
        if stijl == "retro":   # vaste kleuren uit het retropalet: geen strepen door verloopjes
            lu, hv, gr = {"dag": ((41, 173, 255), (255, 241, 232), (194, 195, 199)),
                          "avond": ((29, 43, 83), (95, 87, 79), (131, 118, 156)),
                          "nacht": ((0, 0, 0), (29, 43, 83), (95, 87, 79))}[stand]
            s.fill(lu, (0, 0, W, HORIZON))
            if stand != "dag":
                for i, (x, y) in enumerate(self.hemel):
                    if (i + int(self.t)) % 13 and i % 2:
                        s.fill((255, 241, 232), (x - x % 4, y - y % 4, 4, 4))
                pygame.draw.circle(s, (255, 241, 232), (1100, 80), 30)
            else:
                pygame.draw.circle(s, (255, 236, 39), (1100, 80), 34)
            pygame.draw.polygon(s, hv, pts)
            s.fill(gr, (0, HORIZON, W, VELD_ONDER - HORIZON))
        if stijl == "kleurrijk":
            pygame.draw.lines(s, LIJN, False, pts[1:-1], 5)
        # alles op volgorde van voor naar achter
        gloeien = []
        if stijl == "kleurrijk":
            laag = pygame.Surface((W, VELD_ONDER), pygame.SRCALPHA)
            for d in sorted(self.dingen, key=lambda d: d["y"]):
                self._teken_ding(laag, d["soort"], d["x"], d["y"], schaal_voor(d["y"]), stand, gloeien)
            s.blit(omlijn(laag, 3), (0, 0))
        else:
            for d in sorted(self.dingen, key=lambda d: d["y"]):
                self._teken_ding(s, d["soort"], d["x"], d["y"], schaal_voor(d["y"]), stand, gloeien)
        if self.vast and self.muispos[1] < VELD_ONDER:
            spook = pygame.Surface((W, H), pygame.SRCALPHA)
            self._teken_ding(spook, self.vast["soort"], self.muispos[0], self.muispos[1], schaal_voor(self.muispos[1]), stand, [])
            spook.set_alpha(170)
            s.blit(spook, (0, 0))
        if stand != "dag" and stijl != "retro":
            donker = pygame.Surface((W, VELD_ONDER), pygame.SRCALPHA)
            donker.fill((0, 0, 20, 70 if stand == "avond" else 120))
            s.blit(donker, (0, 0))
            if stijl != "retro":
                for x, y, r, kl in gloeien:
                    s.blit(self._gloed(r, kl), (x - r, y - r), special_flags=pygame.BLEND_ADD)
        for v in self.vlokken:
            pygame.draw.circle(s, (255, 255, 255), (int(v[0]), int(v[1])), 2 if v[2] < 80 else 3)
        if stijl == "retro":   # de wereld in grove pixels; de onderbalk blijft scherp en leesbaar
            veld = s.subsurface((0, 0, W, VELD_ONDER)).copy()
            klein = retro_klein(veld, 4, 0.0)
            s.blit(pygame.transform.scale(klein, (W, VELD_ONDER)), (0, 0))
        self._balk(s, stand)
        if self.uitleg:
            self._uitleg(s)

    def _balk(self, s, stand):
        pygame.draw.rect(s, (16, 18, 28), (0, VELD_ONDER, W, BALK))
        pygame.draw.line(s, (255, 179, 71), (0, VELD_ONDER), (W, VELD_ONDER), 2)
        for i, o in enumerate(ONDERDELEN):
            x = 10 + i * 90
            open_ = o[2] <= self.sterren
            vak = pygame.Rect(x, VELD_ONDER + 8, 84, 104)
            hover = vak.collidepoint(self.muispos)
            pygame.draw.rect(s, (40, 44, 62) if hover and open_ else (28, 30, 44), vak, border_radius=10)
            if self.vast and self.vast["soort"] == o[0]:
                pygame.draw.rect(s, (255, 179, 71), vak, 3, border_radius=10)
            mini = pygame.Surface((84, 80), pygame.SRCALPHA)
            f = min(70 / o[3], 66 / o[4])
            self._teken_ding(mini, o[0], 42, 74, f, "dag", [])
            if not open_:
                mini.set_alpha(60)
            s.blit(mini, (x, VELD_ONDER + 8))
            tekst(s, o[1], (x + 42, VELD_ONDER + 88), 14, (230, 230, 240) if open_ else (120, 120, 135), midden=True)
            if not open_:
                tekst(s, "%d ster%s" % (o[2], "" if o[2] == 1 else "ren"), (x + 42, VELD_ONDER + 40), 15,
                      (255, 205, 60), midden=True, vet=True)
        # bovenbalk
        pygame.draw.rect(s, (0, 0, 0), (0, 0, W, 44))
        tekst(s, "Je kerstdorp", (16, 6), 26, (255, 179, 71), vet=True)
        tekst(s, "Onderdelen: %d   ·   Sterren: %d   ·   Licht: %s" % (len(self.dingen), self.sterren,
                                                                          STAND_NAAM[self.stand] + (
                                                                              " (%s)" % stand if self.stand == "echt" else "")),
              (W // 2, 10), 20, (230, 230, 240), midden=True)
        tekst(s, "F1 = uitleg   Esc = terug", (W - 16, 10), 20, (150, 150, 170), rechts=True)
        if self.melding_t > 0:
            tekst(s, self.melding, (W // 2, 60), 26, (255, 230, 150), midden=True, vet=True)

    def _uitleg(self, s):
        dek = pygame.Surface((W, H), pygame.SRCALPHA)
        dek.fill((0, 0, 0, 200))
        s.blit(dek, (0, 0))
        regels = [("Bouw je eigen kerstdorp", 46, (255, 179, 71)), ("", 10, None),
                  ("Klik onderaan op een onderdeel en klik dan in de sneeuw om het neer te zetten.", 26, None),
                  ("Shift ingedrukt houden = meer van hetzelfde neerzetten.", 26, None),
                  ("Klik op iets in je dorp om het te verplaatsen. Rechtsklik = weghalen.", 26, None),
                  ("", 10, None),
                  ("N = licht: echte tijd, dag, avond of nacht.  Bij nacht gaan de huisjes uit,", 26, None),
                  ("alleen de lantaarns blijven branden.", 26, None),
                  ("Houd S ingedrukt = sneeuw spuiten.   D = sneeuw weghalen.", 26, None),
                  ("Staat er een kerk? Dan slaat de klok overdag het kwartier (1), het halfuur (2)", 26, None),
                  ("en het hele uur.   K = de klok proberen.", 26, None), ("", 10, None),
                  ("Sterren uit Sint-Maarten en Sinterklaas maken nieuwe onderdelen vrij.", 26, (255, 205, 60)),
                  ("Je dorp wordt vanzelf bewaard.", 26, (90, 217, 136)), ("", 10, None),
                  ("Klik of druk op een toets om te beginnen", 26, (255, 255, 255))]
        y = 90
        for t, g, k in regels:
            if t:
                tekst(s, t, (W // 2, y), g, k or (230, 230, 240), midden=True, vet=g > 40)
            y += g + 10

    # ---- de onderdelen zelf
    def _teken_ding(self, s, soort, x, y, f, stand, gloeien):
        sneeuw = self.sneeuw
        wit = (245, 248, 252)
        licht_aan = stand in ("avond", "dag")      # 's nachts gaan de huisjes uit
        raam = (255, 214, 120) if stand == "avond" else (150, 190, 220) if stand == "dag" else (36, 40, 58)

        def R(dx, dy, w, h):
            return pygame.Rect(int(x + dx * f), int(y + dy * f), max(1, int(w * f)), max(1, int(h * f)))

        def P(pts):
            return [(x + a * f, y + b * f) for a, b in pts]

        def raampje(dx, dy, w=18, h=20):
            pygame.draw.rect(s, raam, R(dx, dy, w, h), border_radius=max(1, int(3 * f)))
            pygame.draw.line(s, (60, 40, 30), (x + (dx + w / 2) * f, y + dy * f), (x + (dx + w / 2) * f, y + (dy + h) * f),
                             max(1, int(2 * f)))
            if stand == "avond" and licht_aan:
                gloeien.append((int(x + (dx + w / 2) * f), int(y + (dy + h / 2) * f), int(40 * f), (90, 70, 30)))

        def dak_sneeuw(pts):
            if sneeuw > 0.1:
                dik = 3 + 8 * sneeuw
                pygame.draw.lines(s, wit, False, P(pts), max(2, int(dik * f)))

        if soort in ("huis_rood", "huis_wit", "huis_groot"):
            b = {"huis_rood": 120, "huis_wit": 110, "huis_groot": 170}[soort]
            h = {"huis_rood": 75, "huis_wit": 70, "huis_groot": 95}[soort]
            muur = {"huis_rood": (170, 60, 50), "huis_wit": (235, 228, 214), "huis_groot": (120, 90, 70)}[soort]
            dak = {"huis_rood": (80, 40, 40), "huis_wit": (60, 70, 90), "huis_groot": (70, 45, 40)}[soort]
            pygame.draw.rect(s, muur, R(-b / 2, -h, b, h))
            nok = 45 if soort != "huis_groot" else 55
            pygame.draw.polygon(s, dak, P([(-b / 2 - 8, -h), (0, -h - nok), (b / 2 + 8, -h)]))
            dak_sneeuw([(-b / 2 - 8, -h), (0, -h - nok), (b / 2 + 8, -h)])
            pygame.draw.rect(s, (70, 45, 30), R(-11, -38, 22, 38))
            raampje(-b / 2 + 12, -h + 14)
            raampje(b / 2 - 30, -h + 14)
            if soort == "huis_groot":
                raampje(-9, -h - 30, 18, 18)
                raampje(-b / 2 + 12, -h + 46, 18, 18)
                raampje(b / 2 - 30, -h + 46, 18, 18)
            pygame.draw.rect(s, (90, 60, 50), R(b / 4, -h - nok + 8, 14, 26))
        elif soort == "kerk":
            pygame.draw.rect(s, (236, 228, 212), R(-75, -95, 110, 95))
            pygame.draw.polygon(s, (70, 60, 70), P([(-82, -95), (-20, -140), (42, -95)]))
            dak_sneeuw([(-82, -95), (-20, -140), (42, -95)])
            pygame.draw.rect(s, (226, 218, 202), R(35, -170, 42, 170))
            pygame.draw.polygon(s, (70, 60, 70), P([(30, -170), (56, -230), (82, -170)]))
            dak_sneeuw([(30, -170), (56, -230), (82, -170)])
            pygame.draw.line(s, (220, 190, 80), (x + 56 * f, y - 230 * f), (x + 56 * f, y - 245 * f), max(1, int(3 * f)))
            # klok met de echte tijd
            nu = datetime.datetime.now()
            cx, cy, r = x + 56 * f, y - 140 * f, 15 * f
            pygame.draw.circle(s, (250, 248, 235), (int(cx), int(cy)), int(r))
            pygame.draw.circle(s, (60, 50, 40), (int(cx), int(cy)), int(r), max(1, int(2 * f)))
            for hand, lengte, dikte in (((nu.hour % 12) / 12 + nu.minute / 720, 0.55, 3), (nu.minute / 60, 0.85, 2)):
                a = hand * 2 * math.pi - math.pi / 2
                pygame.draw.line(s, (40, 30, 30), (cx, cy), (cx + math.cos(a) * r * lengte, cy + math.sin(a) * r * lengte),
                                 max(1, int(dikte * f)))
            pygame.draw.rect(s, (90, 60, 40), R(-30, -50, 26, 50), border_top_left_radius=int(13 * f),
                             border_top_right_radius=int(13 * f))
            for dx in (-65, 5):
                pygame.draw.rect(s, raam, R(dx, -80, 16, 34), border_top_left_radius=int(8 * f), border_top_right_radius=int(8 * f))
                if stand == "avond":
                    gloeien.append((int(x + (dx + 8) * f), int(y - 63 * f), int(50 * f), (90, 70, 40)))
            pygame.draw.rect(s, raam, R(48, -110, 16, 30), border_top_left_radius=int(8 * f), border_top_right_radius=int(8 * f))
        elif soort in ("boom", "den"):
            groot = soort == "boom"
            hgt = 120 if groot else 70
            bb = 70 if groot else 44
            pygame.draw.rect(s, (100, 65, 40), R(-5, -14, 10, 14))
            for k in range(3):
                t = k / 3
                pygame.draw.polygon(s, (30, 110 + k * 15, 60), P([(-bb / 2 * (1 - t * 0.5), -14 - hgt * t * 0.8),
                                                                 (0, -14 - hgt * (t * 0.8 + 0.4)),
                                                                 (bb / 2 * (1 - t * 0.5), -14 - hgt * t * 0.8)]))
                if sneeuw > 0.2:
                    pygame.draw.line(s, wit, (x - bb / 2 * (1 - t * 0.5) * f * 0.6, y + (-14 - hgt * t * 0.8 - hgt * 0.08) * f),
                                     (x + bb / 2 * (1 - t * 0.5) * f * 0.6, y + (-14 - hgt * t * 0.8 - hgt * 0.08) * f),
                                     max(1, int(3 * sneeuw * f)))
            if groot:
                kleuren = [(255, 60, 60), (255, 220, 60), (80, 200, 255), (120, 255, 120)]
                for k in range(9):
                    a = k * 1.7
                    hy = -24 - (k / 9) * 90
                    hx = math.sin(a) * (30 - (k / 9) * 24)
                    kl = kleuren[(k + int(self.t * 2)) % 4]
                    pygame.draw.circle(s, kl, (int(x + hx * f), int(y + hy * f)), max(2, int(4 * f)))
                    if stand != "dag":
                        gloeien.append((int(x + hx * f), int(y + hy * f), int(16 * f), tuple(c // 3 for c in kl)))
                pygame.draw.polygon(s, (255, 220, 60), P([(0, -140), (5, -128), (-5, -128)]))
        elif soort == "lantaarn":
            pygame.draw.rect(s, (30, 30, 36), R(-3, -100, 6, 100))
            pygame.draw.rect(s, (30, 30, 36), R(-12, -112, 24, 16), border_radius=max(1, int(3 * f)))
            pygame.draw.rect(s, (255, 230, 150), R(-9, -109, 18, 10), border_radius=max(1, int(2 * f)))
            if stand != "dag":
                gloeien.append((int(x), int(y - 104 * f), int(110 * f), (110, 95, 55)))
            if sneeuw > 0.2:
                pygame.draw.rect(s, wit, R(-13, -116, 26, 4 + 3 * sneeuw))
        elif soort == "hek":
            for k in range(6):
                pygame.draw.rect(s, (110, 75, 50), R(-45 + k * 17, -30, 6, 30))
                if sneeuw > 0.2:
                    pygame.draw.rect(s, wit, R(-46 + k * 17, -33, 8, 4))
            pygame.draw.rect(s, (130, 90, 60), R(-45, -22, 90, 5))
            pygame.draw.rect(s, (130, 90, 60), R(-45, -10, 90, 5))
        elif soort == "sneeuwpop":
            pygame.draw.circle(s, wit, (int(x), int(y - 18 * f)), int(20 * f))
            pygame.draw.circle(s, wit, (int(x), int(y - 46 * f)), int(14 * f))
            pygame.draw.rect(s, (30, 30, 34), R(-10, -70, 20, 10))
            pygame.draw.rect(s, (30, 30, 34), R(-14, -61, 28, 3))
            pygame.draw.polygon(s, (255, 140, 30), P([(0, -48), (12, -45), (0, -43)]))
            pygame.draw.rect(s, (200, 40, 40), R(-12, -36, 24, 5))
            for dy in (-24, -14):
                pygame.draw.circle(s, (30, 30, 34), (int(x), int(y + dy * f)), max(1, int(2 * f)))
        elif soort == "bank":
            pygame.draw.rect(s, (120, 80, 50), R(-30, -20, 60, 6))
            pygame.draw.rect(s, (120, 80, 50), R(-30, -32, 60, 5))
            for dx in (-26, 22):
                pygame.draw.rect(s, (40, 40, 44), R(dx, -20, 4, 20))
            if sneeuw > 0.2:
                pygame.draw.rect(s, wit, R(-30, -23, 60, 3 + 3 * sneeuw))
        elif soort == "vijver":
            pygame.draw.ellipse(s, (170, 210, 235), R(-100, -40, 200, 46))
            pygame.draw.ellipse(s, (210, 235, 250), R(-80, -32, 110, 22))
            for k, kl in enumerate(((200, 40, 50), (40, 90, 200))):
                a = self.t * 0.8 + k * math.pi
                sx, sy = math.cos(a) * 60, -18 + math.sin(a) * 10
                pygame.draw.rect(s, kl, R(sx - 5, sy - 26, 10, 18), border_radius=max(1, int(3 * f)))
                pygame.draw.circle(s, (240, 205, 175), (int(x + sx * f), int(y + (sy - 31) * f)), max(2, int(5 * f)))
                pygame.draw.line(s, (60, 60, 70), (x + (sx - 6) * f, y + sy * f), (x + (sx + 6) * f, y + sy * f), max(1, int(2 * f)))
        elif soort == "kraam":
            pygame.draw.rect(s, (130, 85, 50), R(-46, -55, 92, 55))
            for k in range(6):
                pygame.draw.polygon(s, (200, 40, 40) if k % 2 == 0 else (245, 245, 245),
                                    P([(-50 + k * 16.7, -60), (-50 + (k + 1) * 16.7, -60), (-50 + (k + 0.5) * 16.7, -48)]))
            pygame.draw.polygon(s, (90, 50, 30), P([(-54, -60), (0, -100), (54, -60)]))
            dak_sneeuw([(-54, -60), (0, -100), (54, -60)])
            pygame.draw.rect(s, (255, 214, 120) if stand != "nacht" else (60, 55, 50), R(-36, -40, 72, 16))
            for dx in (-28, -10, 8, 24):
                pygame.draw.circle(s, (200, 140, 60), (int(x + dx * f), int(y - 44 * f)), max(2, int(5 * f)))
            if stand == "avond":
                gloeien.append((int(x), int(y - 40 * f), int(60 * f), (100, 80, 40)))
        elif soort == "molen":
            pygame.draw.polygon(s, (110, 90, 80), P([(-34, 0), (-20, -140), (20, -140), (34, 0)]))
            pygame.draw.polygon(s, (60, 50, 50), P([(-26, -140), (0, -170), (26, -140)]))
            dak_sneeuw([(-26, -140), (0, -170), (26, -140)])
            pygame.draw.rect(s, (70, 45, 30), R(-9, -30, 18, 30))
            raampje(-8, -100, 16, 16)
            a0 = self.t * 0.6
            for k in range(4):
                a = a0 + k * math.pi / 2
                ex, ey = math.cos(a) * 62, -130 + math.sin(a) * 62
                pygame.draw.line(s, (60, 45, 35), (x, y - 130 * f), (x + ex * f, y + ey * f), max(1, int(4 * f)))
                px, py = -math.sin(a) * 12, math.cos(a) * 12
                pygame.draw.polygon(s, (235, 230, 215), P([(math.cos(a) * 18, -130 + math.sin(a) * 18),
                                                          (ex, ey), (ex + px, ey + py),
                                                          (math.cos(a) * 18 + px, -130 + math.sin(a) * 18 + py)]))
            pygame.draw.circle(s, (40, 30, 30), (int(x), int(y - 130 * f)), max(2, int(5 * f)))
        elif soort == "koor":
            for k, kl in enumerate(((180, 30, 40), (30, 80, 160), (40, 130, 70))):
                dx = -26 + k * 26
                bob = math.sin(self.t * 3 + k) * 2
                pygame.draw.rect(s, kl, R(dx - 9, -32 + bob, 18, 32), border_radius=max(1, int(5 * f)))
                pygame.draw.circle(s, (240, 205, 175), (int(x + dx * f), int(y + (-40 + bob) * f)), max(2, int(8 * f)))
                pygame.draw.circle(s, (40, 30, 30), (int(x + dx * f), int(y + (-37 + bob) * f)), max(1, int(2 * f)))
                pygame.draw.rect(s, (250, 250, 250), R(dx - 7, -26 + bob, 14, 9))
            if int(self.t * 2) % 2:
                nx, ny = x + 34 * f, y - 58 * f
                pygame.draw.circle(s, (255, 255, 255), (int(nx), int(ny)), max(2, int(4 * f)))
                pygame.draw.line(s, (255, 255, 255), (nx + 3 * f, ny), (nx + 3 * f, ny - 14 * f), max(1, int(2 * f)))
                pygame.draw.line(s, (255, 255, 255), (nx + 3 * f, ny - 14 * f), (nx + 9 * f, ny - 10 * f), max(1, int(2 * f)))
