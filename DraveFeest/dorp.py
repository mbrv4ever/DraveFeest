# -*- coding: utf-8 -*-
# DraveFeest - het feestdagen-dorp (retro pixels). Elk huis is een feestdag met een eigen spel.
# Copyright (C) 2026 Dravenlock (Roger & Claudio). Vrije software onder de GNU GPL v3.0.
import math
import random

import pygame

from basis import (Scene, tekst, seizoen, is_avond, SPELER_TOETSEN, VERSIE, stijl_van, palet_filter, STIJL_NAAM,
                   LIJN, teken_kind, ster, gloed, mix)

W, H = 480, 270
GROND = 214          # waar de straat begint
HUIS_B, AFSTAND = 76, 104


def _huizen():
    from sintmaarten import SintMaarten
    from sinterklaas import Sinterklaas
    from kerst import Kerst
    from nieuwjaar import Nieuwjaar
    from pasen import Pasen
    from koningsdag import Koningsdag
    from valentijn import Valentijn
    from carnaval import Carnaval
    from halloween import Halloween
    return [
        dict(code="nieuwjaar", naam="Oud & Nieuw", sub="De vuurwerkshow", spel=Nieuwjaar, muur=(70, 60, 110), dak=(40, 34, 70), teken="vuurwerk"),
        dict(code="valentijn", naam="Valentijn", sub="Cupido", spel=Valentijn, muur=(200, 110, 140), dak=(130, 50, 80), teken="hart"),
        dict(code="carnaval", naam="Carnaval", sub="De polonaise", spel=Carnaval, muur=(220, 180, 60), dak=(170, 40, 50), teken="masker"),
        dict(code="pasen", naam="Pasen", sub="Eieren zoeken", spel=Pasen, muur=(160, 210, 150), dak=(90, 140, 90), teken="ei"),
        dict(code="koningsdag", naam="Koningsdag", sub="Koekhappen", spel=Koningsdag, muur=(240, 140, 50), dak=(160, 70, 20), teken="kroon"),
        dict(code="halloween", naam="Halloween", sub="Spoken vangen", spel=Halloween, muur=(70, 60, 60), dak=(40, 30, 40), teken="pompoen"),
        dict(code="sintmaarten", naam="Sint-Maarten", sub="Lampionnen-route", spel=SintMaarten, muur=(120, 90, 70),
             dak=(70, 45, 35), teken="lampion"),
        dict(code="sinterklaas", naam="Sinterklaas", sub="Pakjes door de schoorsteen", spel=Sinterklaas,
             muur=(170, 60, 60), dak=(90, 30, 35), teken="mijter"),
        dict(code="kerst", naam="Kerst", sub="Bouw je kerstdorp", spel=Kerst, muur=(60, 110, 80), dak=(150, 40, 40),
             teken="boom"),
    ]


def teken_poppetje(s, x, y, kleur, stap, richting, winter):
    """Klein pixelpoppetje (12 hoog), x/y = voeten midden."""
    huid, haar, broek = (240, 200, 170), (80, 50, 30), (40, 40, 60)
    b = 1 if stap % 2 else 0
    pygame.draw.rect(s, broek, (x - 3, y - 4, 2, 4 - b))
    pygame.draw.rect(s, broek, (x + 1, y - 4, 2, 3 + b))
    pygame.draw.rect(s, kleur, (x - 4, y - 10, 8, 6))
    pygame.draw.rect(s, huid, (x - 3, y - 15, 6, 5))
    pygame.draw.rect(s, haar, (x - 3, y - 16, 6, 2))
    oog = x + (1 if richting > 0 else -2)
    s.set_at((oog, y - 13), (20, 20, 20))
    if winter:
        pygame.draw.rect(s, (220, 40, 40), (x - 4, y - 11, 8, 2))
        pygame.draw.rect(s, (220, 40, 40), (x - 3, y - 18, 6, 3))
        s.set_at((x, y - 19), (255, 255, 255))


def teken_teken(s, soort, cx, cy, t):
    """Klein uithangbord-plaatje boven de deur."""
    if soort == "vuurwerk":
        for i in range(8):
            a = i * math.pi / 4 + t
            pygame.draw.line(s, (255, 220, 90), (cx, cy), (cx + 5 * math.cos(a), cy + 5 * math.sin(a)))
    elif soort == "hart":
        pygame.draw.circle(s, (230, 40, 70), (cx - 2, cy - 1), 3)
        pygame.draw.circle(s, (230, 40, 70), (cx + 2, cy - 1), 3)
        pygame.draw.polygon(s, (230, 40, 70), [(cx - 5, cy), (cx + 5, cy), (cx, cy + 5)])
    elif soort == "masker":
        pygame.draw.ellipse(s, (120, 40, 160), (cx - 6, cy - 3, 12, 6))
        s.set_at((cx - 3, cy), (0, 0, 0))
        s.set_at((cx + 3, cy), (0, 0, 0))
    elif soort == "ei":
        pygame.draw.ellipse(s, (250, 240, 200), (cx - 3, cy - 5, 7, 9))
        pygame.draw.line(s, (90, 160, 220), (cx - 3, cy), (cx + 3, cy))
    elif soort == "kroon":
        pygame.draw.polygon(s, (255, 200, 40), [(cx - 5, cy + 3), (cx - 5, cy - 3), (cx - 2, cy), (cx, cy - 4),
                                                (cx + 2, cy), (cx + 5, cy - 3), (cx + 5, cy + 3)])
    elif soort == "pompoen":
        pygame.draw.ellipse(s, (240, 120, 20), (cx - 5, cy - 3, 11, 8))
        pygame.draw.rect(s, (60, 120, 30), (cx, cy - 5, 2, 3))
        s.set_at((cx - 2, cy), (255, 230, 80))
        s.set_at((cx + 2, cy), (255, 230, 80))
    elif soort == "lampion":
        pygame.draw.line(s, (90, 70, 50), (cx, cy - 6), (cx, cy - 3))
        pygame.draw.ellipse(s, (255, 150, 40), (cx - 4, cy - 3, 9, 8))
        pygame.draw.ellipse(s, (255, 230, 120), (cx - 2, cy - 1, 5, 4))
    elif soort == "mijter":
        pygame.draw.polygon(s, (220, 30, 40), [(cx - 4, cy + 4), (cx + 4, cy + 4), (cx + 3, cy - 3), (cx, cy - 6),
                                               (cx - 3, cy - 3)])
        pygame.draw.line(s, (255, 210, 60), (cx, cy - 4), (cx, cy + 3))
        pygame.draw.line(s, (255, 210, 60), (cx - 2, cy), (cx + 2, cy))
    elif soort == "boom":
        pygame.draw.polygon(s, (40, 150, 70), [(cx, cy - 6), (cx - 5, cy + 3), (cx + 5, cy + 3)])
        pygame.draw.rect(s, (110, 70, 40), (cx - 1, cy + 3, 2, 2))
        s.set_at((cx, cy - 7), (255, 220, 60))


class Dorp(Scene):
    naam = "dorp"
    K = 1280 / W          # schaal voor de stijl 'kleurrijk' (die tekent op 1280 x 720)

    @property
    def stijl(self):
        return stijl_van(self.spel)

    @property
    def res(self):
        return (1280, 720) if self.stijl == "kleurrijk" else (W, H)

    @property
    def pixel(self):
        return self.stijl != "kleurrijk"

    def __init__(self, spel):
        super().__init__(spel)
        self.huizen = _huizen()
        for i, h in enumerate(self.huizen):
            h["x"] = 90 + i * AFSTAND
        self.lengte = self.huizen[-1]["x"] + HUIS_B + 90
        start = next(h["x"] for h in self.huizen if h["code"] == "sintmaarten")
        self.spelers = [dict(x=start - 20.0, stap=0, r=1, t=0.0), dict(x=start - 36.0, stap=0, r=1, t=0.0)]
        self.cam = 0.0
        self.t = 0.0
        self.hulp = False
        self.esc = 0.0
        self.melding, self.melding_t = "", 0.0
        rnd = random.Random(7)
        self.vlokjes = [[rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(8, 22), rnd.uniform(0, 6)] for _ in range(90)]
        self.sterrenhemel = [(rnd.randrange(W), rnd.randrange(GROND - 60)) for _ in range(70)]
        self.bergen = [(i * 40, rnd.randint(30, 70)) for i in range(0, self.lengte // 40 + 4)]
        self.ingedrukt = set()

    def terug(self):
        self.seizoen = seizoen()
        self.avond = is_avond()
        self.ingedrukt = set()

    # ---- invoer
    def toets(self, ev):
        self.ingedrukt.add(ev.key)
        if self.hulp:
            self.hulp = False
            return
        if ev.key == pygame.K_F1 or ev.key == pygame.K_h:
            self.hulp = True
        elif ev.key == pygame.K_2:
            self.spel.opslag.d["twee"] = not self.spel.twee
            self.spel.opslag.bewaar()
            if self.spel.twee:
                self.spelers[1]["x"] = self.spelers[0]["x"] - 16
            self.meld("Tweede speler " + ("doet mee! (W A S D + E)" if self.spel.twee else "is gestopt"))
        elif ev.key == pygame.K_3:
            volg = {"mix": "retro", "retro": "kleurrijk", "kleurrijk": "mix"}
            st = volg[self.stijl]
            self.spel.opslag.d["stijl"] = st
            self.spel.opslag.bewaar()
            self.meld("Stijl: %s%s" % (STIJL_NAAM[st], " (standaard)" if st == "mix" else ""))
        elif ev.key == pygame.K_ESCAPE:
            if self.esc > 0:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            else:
                self.esc = 2.0
                self.meld("Nog een keer Esc = het spel afsluiten")
        elif ev.key in (pygame.K_UP, pygame.K_RETURN, pygame.K_SPACE, pygame.K_w, pygame.K_e):
            sp = 1 if ev.key in (pygame.K_w, pygame.K_e) and self.spel.twee else 0
            h = self.bij_huis(self.spelers[sp]["x"])
            if h:
                if h["spel"]:
                    self.spel.start(h["spel"])
                else:
                    self.spel.geluid.speel("fout")
                    self.meld("%s komt later! Dit huis wordt nog gebouwd." % h["naam"])

    def los(self, ev):
        self.ingedrukt.discard(ev.key)

    def meld(self, t):
        self.melding, self.melding_t = t, 3.0

    def bij_huis(self, x):
        for h in self.huizen:
            if abs(x - (h["x"] + HUIS_B / 2)) < 14:
                return h
        return None

    # ---- bijwerken
    def update(self, dt):
        self.t += dt
        self.esc = max(0, self.esc - dt)
        self.melding_t = max(0, self.melding_t - dt)
        toetsen = pygame.key.get_pressed()
        n = 2 if self.spel.twee else 1
        for i in range(n):
            k, p = SPELER_TOETSEN[i], self.spelers[i]
            d = (1 if toetsen[k["rechts"]] else 0) - (1 if toetsen[k["links"]] else 0)
            if d:
                p["x"] = max(10, min(self.lengte - 10, p["x"] + d * 70 * dt))
                p["r"] = d
                p["t"] += dt
                if p["t"] > 0.14:
                    p["t"] = 0
                    p["stap"] += 1
            else:
                p["stap"] = 0
        doel = (sum(self.spelers[i]["x"] for i in range(n)) / n) - W / 2
        doel = max(0, min(self.lengte - W, doel))
        self.cam += (doel - self.cam) * min(1, dt * 6)
        for v in self.vlokjes:
            v[1] += v[2] * dt
            v[0] += math.sin(self.t + v[3]) * 6 * dt
            if v[1] > H:
                v[1] = -3
                v[0] = random.uniform(0, W)

    # ---- tekenen
    def _lucht(self, s):
        if self.avond:
            boven, onder = (10, 12, 35), (35, 30, 70)
        else:
            boven, onder = {"winter": ((120, 150, 190), (200, 215, 230)), "lente": ((90, 160, 230), (190, 225, 250)),
                            "zomer": ((60, 140, 230), (170, 215, 250)), "herfst": ((110, 130, 170), (220, 190, 160))}[self.seizoen]
        for y in range(GROND):
            f = y / GROND
            pygame.draw.line(s, tuple(int(boven[i] + (onder[i] - boven[i]) * f) for i in range(3)), (0, y), (W, y))
        if self.avond:
            for i, (x, y) in enumerate(self.sterrenhemel):
                if (int(self.t * 2) + i) % 9:
                    s.set_at((x, y), (230, 230, 255))
            pygame.draw.circle(s, (240, 240, 210), (400, 34), 10)
            pygame.draw.circle(s, boven, (405, 31), 9)
        else:
            pygame.draw.circle(s, (255, 230, 140), (400, 40), 12)
        # bergen ver weg (langzamer)
        kleur = (40, 40, 70) if self.avond else {"winter": (170, 185, 205), "herfst": (150, 120, 100)}.get(self.seizoen, (110, 150, 120))
        pts = [(x - self.cam * 0.3, GROND - 30 - h) for x, h in self.bergen]
        pygame.draw.polygon(s, kleur, [(-10, GROND)] + pts + [(W + 400, GROND)])
        if self.seizoen == "winter":
            for x, h in self.bergen:
                xx = x - self.cam * 0.3
                pygame.draw.polygon(s, (240, 245, 250), [(xx - 6, GROND - 24 - h), (xx, GROND - 30 - h), (xx + 6, GROND - 24 - h)])

    def _huis(self, s, h, i):
        x = int(h["x"] - self.cam)
        if x > W + 10 or x + HUIS_B < -10:
            return
        y0 = GROND - 70
        open_ = h["spel"] is not None
        muur = h["muur"] if open_ else tuple(int(c * 0.6) for c in h["muur"])
        pygame.draw.rect(s, muur, (x, y0, HUIS_B, 70))
        # dakje (trapgevel-achtig)
        pygame.draw.polygon(s, h["dak"], [(x - 4, y0), (x + HUIS_B // 2, y0 - 34), (x + HUIS_B + 4, y0)])
        if self.seizoen == "winter":
            pygame.draw.polygon(s, (245, 248, 252), [(x - 4, y0), (x + HUIS_B // 2, y0 - 34), (x + HUIS_B + 4, y0),
                                                       (x + HUIS_B, y0 - 3), (x + HUIS_B // 2, y0 - 30), (x, y0 - 3)])
        # ramen
        licht = (255, 214, 110) if (self.avond and open_) else (120, 160, 190) if not self.avond else (40, 40, 55)
        for rx in (x + 8, x + HUIS_B - 22):
            pygame.draw.rect(s, (40, 30, 30), (rx - 1, y0 + 9, 16, 16))
            pygame.draw.rect(s, licht, (rx, y0 + 10, 14, 14))
            pygame.draw.line(s, (40, 30, 30), (rx + 7, y0 + 10), (rx + 7, y0 + 23))
            pygame.draw.line(s, (40, 30, 30), (rx, y0 + 17), (rx + 13, y0 + 17))
        # deur
        dx = x + HUIS_B // 2 - 8
        pygame.draw.rect(s, (60, 35, 25), (dx, y0 + 38, 16, 32))
        s.set_at((dx + 12, y0 + 55), (255, 210, 60))
        if not open_:
            # in aanbouw: planken en steigertje
            pygame.draw.line(s, (150, 110, 60), (dx - 2, y0 + 44), (dx + 18, y0 + 60), 3)
            pygame.draw.line(s, (150, 110, 60), (dx + 18, y0 + 44), (dx - 2, y0 + 60), 3)
            for sx in (x - 6, x + HUIS_B + 4):
                pygame.draw.line(s, (130, 130, 140), (sx, y0 - 6), (sx, GROND), 1)
            pygame.draw.line(s, (130, 130, 140), (x - 6, y0 + 20), (x + HUIS_B + 4, y0 + 20), 1)
        # uithangbord
        bx, by = x + HUIS_B // 2, y0 + 30
        pygame.draw.rect(s, (235, 225, 200), (bx - 9, by - 8, 18, 15))
        pygame.draw.rect(s, (90, 60, 40), (bx - 9, by - 8, 18, 15), 1)
        teken_teken(s, h["teken"], bx, by - 1, self.t)
        # versiering per feestdag
        if h["code"] == "sintmaarten" and open_:
            for k in range(4):
                lx = x + 6 + k * 21
                pygame.draw.line(s, (60, 50, 40), (lx, y0 - 2), (lx, y0 + 3))
                gl = 0.7 + 0.3 * math.sin(self.t * 3 + k)
                pygame.draw.ellipse(s, (int(255 * gl), int(140 * gl), 40), (lx - 3, y0 + 3, 7, 7))
        if h["code"] == "kerst" and open_:
            for k in range(12):
                c = [(255, 60, 60), (255, 220, 60), (80, 200, 255), (120, 255, 120)][(k + int(self.t * 3)) % 4]
                px = x + 2 + k * 6
                s.set_at((px, y0 + 2 + (k % 2)), c)
                s.set_at((px + 1, y0 + 2 + (k % 2)), c)
            pygame.draw.circle(s, (40, 120, 50), (dx + 8, y0 + 46), 5, 2)
            s.set_at((dx + 8, y0 + 51), (220, 30, 30))
        if h["code"] == "sinterklaas" and open_:
            pygame.draw.rect(s, (90, 80, 80), (x + HUIS_B - 18, y0 - 26, 8, 14))
            for k in range(3):
                pygame.draw.circle(s, (200, 200, 205), (x + HUIS_B - 14 + k * 3, int(y0 - 30 - k * 5 - (self.t * 8) % 5)), 2)
        # naambordje + sterren
        tekst(s, h["naam"], (x + HUIS_B // 2, y0 - 50), 16, (255, 255, 255), midden=True, pixel=True)
        if open_:
            n = self.spel.opslag.sterren(h["code"])
            for k in range(3):
                kl = (255, 205, 60) if k < n else (70, 70, 80)
                cx = x + HUIS_B // 2 - 10 + k * 10
                pygame.draw.polygon(s, kl, [(cx, y0 - 40), (cx + 2, y0 - 36), (cx + 4, y0 - 36), (cx + 2, y0 - 34),
                                            (cx + 3, y0 - 31), (cx, y0 - 33), (cx - 3, y0 - 31), (cx - 2, y0 - 34),
                                            (cx - 4, y0 - 36), (cx - 2, y0 - 36)])

    def _straat(self, s):
        kleur = (190, 195, 205) if self.seizoen == "winter" else (110, 100, 95)
        pygame.draw.rect(s, kleur, (0, GROND, W, H - GROND))
        steen = (170, 175, 185) if self.seizoen == "winter" else (90, 82, 78)
        for y in range(GROND + 4, H, 8):
            off = (y // 8) % 2 * 6 - int(self.cam) % 12
            for x in range(-12, W + 12, 12):
                pygame.draw.rect(s, steen, (x + off, y, 10, 6), 1)
        # lantaarns
        for i in range(0, self.lengte, 130):
            x = int(i + 40 - self.cam)
            if -20 < x < W + 20:
                pygame.draw.line(s, (30, 30, 35), (x, GROND), (x, GROND - 46), 2)
                pygame.draw.rect(s, (30, 30, 35), (x - 4, GROND - 52, 9, 7))
                pygame.draw.rect(s, (255, 220, 120) if self.avond else (200, 200, 180), (x - 3, GROND - 51, 7, 5))
                if self.avond and self.stijl != "retro":
                    gl = pygame.Surface((60, 60), pygame.SRCALPHA)
                    pygame.draw.circle(gl, (255, 210, 120, 40), (30, 30), 28)
                    pygame.draw.circle(gl, (255, 210, 120, 50), (30, 30), 16)
                    s.blit(gl, (x - 30, GROND - 78))

    def teken(self, s):
        if self.stijl == "kleurrijk":
            self._teken_kleurrijk(s)
            return
        self._teken_pixel(s)
        if self.stijl == "retro":
            s.blit(palet_filter(s, 0.27 if self.avond else 0.0), (0, 0))
        self._hud_pixel(s)

    def _teken_pixel(self, s):
        self._lucht(s)
        for i, h in enumerate(self.huizen):
            self._huis(s, h, i)
        self._straat(s)
        n = 2 if self.spel.twee else 1
        kleuren = [(60, 110, 200), (230, 130, 40)]
        for i in range(n - 1, -1, -1):
            p = self.spelers[i]
            teken_poppetje(s, int(p["x"] - self.cam), GROND + 22 - i * 3, kleuren[i], p["stap"], p["r"],
                           self.seizoen == "winter")
        # weer
        if self.seizoen in ("winter", "herfst", "lente"):
            kl = {"winter": (255, 255, 255), "herfst": (210, 120, 40), "lente": (255, 200, 220)}[self.seizoen]
            for v in self.vlokjes[:: (1 if self.seizoen == "winter" else 3)]:
                s.set_at((int(v[0]), int(v[1])), kl)

    def _hud_pixel(self, s):
        n = 2 if self.spel.twee else 1
        pygame.draw.rect(s, (0, 0, 0), (0, 0, W, 14))
        tekst(s, "DRAVEFEEST", (4, 2), 16, (255, 179, 71), pixel=True, schaduw=False)
        tekst(s, "F1 hulp  2 speler 2  3 stijl: %s" % STIJL_NAAM[self.stijl], (W // 2 + 16, 2), 16, (170, 170, 180), midden=True,
              pixel=True, schaduw=False)
        tekst(s, "* %d" % self.spel.opslag.totaal_sterren(), (W - 4, 2), 16, (255, 205, 60), rechts=True, pixel=True,
              schaduw=False)
        # wat is hier?
        for i in range(n):
            h = self.bij_huis(self.spelers[i]["x"])
            if h:
                regel = ("%s - %s" % (h["naam"], h["sub"])) if h["spel"] else ("%s - komt later" % h["naam"])
                y = 236 + i * 14 if n > 1 else 240
                pygame.draw.rect(s, (0, 0, 0), (W // 2 - 150, y - 2, 300, 14))
                tekst(s, regel + ("   [pijl omhoog]" if i == 0 else "   [W]") * (1 if h["spel"] else 0),
                      (W // 2, y), 16, (255, 255, 255), midden=True, pixel=True, schaduw=False)
        if self.melding_t > 0:
            pygame.draw.rect(s, (40, 30, 10), (20, 20, W - 40, 16))
            tekst(s, self.melding, (W // 2, 23), 16, (255, 220, 140), midden=True, pixel=True, schaduw=False)
        if self.hulp:
            self._hulp(s)

    def _hulp_regels(self):
        return ["WELKOM IN HET FEESTDAGEN-DORP!", "",
                  "Elk huis is een feestdag met een eigen spel.",
                  "Loop naar een deur en druk op pijl omhoog (of Enter).", "",
                  "Speler 1: pijltjes + spatie",
                  "Speler 2: W A S D + E   (druk op 2 om mee te doen)", "",
                  "F11 = schermvullend   M = muziek / geluid aan of uit",
                  "3 = stijl kiezen: Mix, Retro of Kleurrijk",
                  "Esc = terug / afsluiten", "",
                  "Verdien sterren: die maken nieuwe dingen vrij",
                  "voor je kerstdorp!", "",
                  "Druk op een toets om verder te gaan.   v" + VERSIE]

    def _hulp(self, s):
        pygame.draw.rect(s, (10, 10, 20), (30, 22, W - 60, H - 40))
        pygame.draw.rect(s, (255, 179, 71), (30, 22, W - 60, H - 40), 1)
        regels = self._hulp_regels()
        y = 30
        for r in regels:
            tekst(s, r, (W // 2, y), 16, (255, 179, 71) if r.isupper() else (230, 230, 235), midden=True, pixel=True,
                  schaduw=False)
            y += 15

    # ================================================================= stijl 'kleurrijk' (cartoon, 1280 x 720)
    def _teken_kleurrijk(self, s):
        K = self.K
        SW, SH = 1280, 720
        GY = int(GROND * K)
        if self.avond:
            boven, onder = (50, 30, 130), (210, 80, 160)
        else:
            boven, onder = {"winter": ((90, 160, 255), (205, 235, 255)), "lente": ((80, 180, 255), (200, 245, 255)),
                            "zomer": ((40, 150, 255), (150, 225, 255)), "herfst": ((90, 140, 255), (255, 200, 140))}[self.seizoen]
        for y in range(0, GY, 4):
            pygame.draw.rect(s, mix(boven, onder, y / GY), (0, y, SW, 4))
        if self.avond:
            for i, (x, y) in enumerate(self.sterrenhemel):
                if (int(self.t * 2) + i) % 9:
                    pygame.draw.circle(s, (255, 250, 200), (int(x * K), int(y * K)), 3 if i % 4 == 0 else 2)
            pygame.draw.circle(s, LIJN, (1066, 92), 46)
            pygame.draw.circle(s, (255, 236, 140), (1066, 92), 40)
            pygame.draw.circle(s, (240, 210, 110), (1052, 80), 8)
        else:
            pygame.draw.circle(s, LIJN, (1066, 100), 50)
            pygame.draw.circle(s, (255, 214, 60), (1066, 100), 44)
            for k in range(8):
                a = k * math.pi / 4 + self.t * 0.3
                pygame.draw.line(s, (255, 214, 60), (1066 + math.cos(a) * 58, 100 + math.sin(a) * 58),
                                 (1066 + math.cos(a) * 76, 100 + math.sin(a) * 76), 7)
        # heuvels
        heuvel = (110, 60, 160) if self.avond else {"winter": (235, 245, 255), "herfst": (230, 150, 80)}.get(self.seizoen, (110, 200, 110))
        pts = [(-20, GY)] + [((x - self.cam * 0.3) * K, (GROND - 30 - hh) * K) for x, hh in self.bergen] + [(SW + 800, GY)]
        pygame.draw.polygon(s, heuvel, pts)
        pygame.draw.lines(s, LIJN, False, pts[1:-1], 5)
        felle = {"nieuwjaar": (120, 110, 230), "valentijn": (255, 120, 170), "carnaval": (255, 205, 60),
                 "pasen": (150, 230, 140), "koningsdag": (255, 150, 50), "halloween": (130, 110, 150),
                 "sintmaarten": (255, 170, 90), "sinterklaas": (240, 80, 80), "kerst": (60, 190, 120)}
        for h in self.huizen:
            x = (h["x"] - self.cam) * K
            b, hh = HUIS_B * K, 70 * K
            if x > SW + 40 or x + b < -40:
                continue
            open_ = h["spel"] is not None
            muur = felle.get(h["code"], h["muur"])
            if not open_:
                muur = mix(muur, (150, 150, 160), 0.55)
            top = GY - hh
            romp = pygame.Rect(int(x), int(top), int(b), int(hh))
            pygame.draw.rect(s, LIJN, romp.inflate(10, 10), border_radius=16)
            pygame.draw.rect(s, muur, romp, border_radius=12)
            dak = [(x - 14, top + 4), (x + b / 2, top - 34 * K), (x + b + 14, top + 4)]
            pygame.draw.polygon(s, tuple(int(c * 0.65) for c in muur), dak)
            if self.seizoen == "winter":
                pygame.draw.lines(s, (255, 255, 255), False, dak, 14)
            pygame.draw.polygon(s, LIJN, dak, 6)
            raam = (255, 240, 140) if (self.avond and open_) else (170, 220, 255) if not self.avond else (70, 60, 110)
            for rx in (x + 18, x + b - 62):
                pygame.draw.ellipse(s, LIJN, (rx - 5, top + 20, 54, 50))
                pygame.draw.ellipse(s, raam, (rx, top + 25, 44, 40))
                pygame.draw.line(s, LIJN, (rx + 22, top + 25), (rx + 22, top + 64), 4)
                if self.avond and open_:
                    s.blit(self._kgloed(70, (90, 80, 20)), (rx - 48, top - 25), special_flags=pygame.BLEND_ADD)
            dx = x + b / 2 - 24
            pygame.draw.rect(s, LIJN, (dx - 5, GY - 92, 58, 97), border_top_left_radius=29, border_top_right_radius=29)
            pygame.draw.rect(s, (150, 80, 50), (dx, GY - 87, 48, 87), border_top_left_radius=24, border_top_right_radius=24)
            pygame.draw.circle(s, (255, 220, 60), (int(dx + 38), GY - 44), 5)
            if not open_:
                pygame.draw.line(s, (200, 150, 80), (dx - 6, GY - 70), (dx + 54, GY - 20), 9)
                pygame.draw.line(s, (200, 150, 80), (dx + 54, GY - 70), (dx - 6, GY - 20), 9)
            # bord met plaatje (het pixelplaatje groot en zacht)
            bx, by = x + b / 2, top + 72
            pygame.draw.circle(s, LIJN, (int(bx), int(by)), 26)
            pygame.draw.circle(s, (255, 248, 230), (int(bx), int(by)), 22)
            mini = pygame.Surface((20, 20), pygame.SRCALPHA)
            teken_teken(mini, h["teken"], 10, 10, self.t)
            s.blit(pygame.transform.smoothscale(mini, (40, 40)), (bx - 20, by - 20))
            tekst(s, h["naam"], (int(bx), int(top - 34 * K - 62)), 26, (255, 255, 255), midden=True, vet=True)
            if open_:
                n = self.spel.opslag.sterren(h["code"])
                for k in range(3):
                    ster(s, bx - 30 + k * 30, top - 34 * K - 20, 12, (255, 205, 60) if k < n else (90, 90, 110), LIJN)
        # straat
        pygame.draw.rect(s, (200, 205, 225) if self.seizoen == "winter" else (130, 115, 170), (0, GY, SW, SH - GY))
        pygame.draw.rect(s, (230, 235, 250) if self.seizoen == "winter" else (170, 155, 210), (0, GY, SW, 16))
        pygame.draw.line(s, LIJN, (0, GY), (SW, GY), 5)
        for i in range(0, self.lengte, 130):
            x = (i + 40 - self.cam) * K
            if -60 < x < SW + 60:
                pygame.draw.rect(s, LIJN, (x - 6, GY - 125, 12, 125), border_radius=5)
                pygame.draw.circle(s, LIJN, (int(x), GY - 136), 18)
                pygame.draw.circle(s, (255, 240, 150) if self.avond else (255, 255, 230), (int(x), GY - 136), 13)
                if self.avond:
                    s.blit(self._kgloed(110, (90, 80, 40)), (x - 110, GY - 246), special_flags=pygame.BLEND_ADD)
        n = 2 if self.spel.twee else 1
        for i in range(n - 1, -1, -1):
            p = self.spelers[i]
            teken_kind(s, (p["x"] - self.cam) * K, GY + 70 - i * 10, 0.62, [(70, 110, 200), (220, 120, 50)][i],
                       [(200, 40, 50), (40, 160, 90)][i], p["r"], p["stap"] * 1.2)
        if self.seizoen in ("winter", "herfst", "lente"):
            kl = {"winter": (255, 255, 255), "herfst": (255, 150, 40), "lente": (255, 190, 220)}[self.seizoen]
            for v in self.vlokjes[:: (1 if self.seizoen == "winter" else 3)]:
                if self.seizoen == "winter":
                    pygame.draw.circle(s, kl, (int(v[0] * K), int(v[1] * K)), 4)
                else:
                    pygame.draw.ellipse(s, kl, (v[0] * K, v[1] * K, 14, 7))
        # balk
        pygame.draw.rect(s, (0, 0, 0), (0, 0, SW, 44))
        tekst(s, "DraveFeest", (16, 6), 28, (255, 179, 71), vet=True)
        tekst(s, "F1 = hulp   2 = speler 2   3 = stijl: %s   M = muziek" % STIJL_NAAM[self.stijl], (SW // 2, 10), 20,
              (200, 200, 215), midden=True)
        ster(s, SW - 70, 22, 13, (255, 205, 60), None)
        tekst(s, str(self.spel.opslag.totaal_sterren()), (SW - 18, 6), 28, (255, 255, 255), rechts=True, vet=True)
        for i in range(n):
            h = self.bij_huis(self.spelers[i]["x"])
            if h:
                regel = ("%s - %s" % (h["naam"], h["sub"])) if h["spel"] else ("%s - komt later" % h["naam"])
                if h["spel"]:
                    regel += "   [pijl omhoog]" if i == 0 else "   [W]"
                y = 640 + i * 40 if n > 1 else 660
                pygame.draw.rect(s, LIJN, (SW // 2 - 330, y - 6, 660, 40), border_radius=12)
                tekst(s, regel, (SW // 2, y), 26, (255, 255, 255), midden=True, vet=True)
        if self.melding_t > 0:
            pygame.draw.rect(s, LIJN, (140, 60, SW - 280, 46), border_radius=14)
            tekst(s, self.melding, (SW // 2, 68), 26, (255, 230, 150), midden=True, vet=True)
        if self.hulp:
            dek = pygame.Surface((SW, SH), pygame.SRCALPHA)
            dek.fill((10, 8, 25, 225))
            s.blit(dek, (0, 0))
            y = 60
            for r in self._hulp_regels():
                if r:
                    tekst(s, r, (SW // 2, y), 34 if r.isupper() else 26,
                          (255, 179, 71) if r.isupper() else (235, 235, 245), midden=True, vet=r.isupper())
                y += 38

    def _kgloed(self, r, kl):
        if not hasattr(self, "_kg"):
            self._kg = {}
        if (r, kl) not in self._kg:
            self._kg[(r, kl)] = gloed(r, kl)
        return self._kg[(r, kl)]
