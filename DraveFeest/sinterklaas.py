# -*- coding: utf-8 -*-
# DraveFeest - Sinterklaas: pakjes door de schoorsteen (retro pixels).
# Sint rijdt op zijn schimmel over de daken. Laat op het goede moment een pakje vallen:
# in een schoorsteen met een schoentje = raak! Niet in een rokende schoorsteen (daar brandt de kachel).
# Copyright (C) 2026 Dravenlock (Roger & Claudio). Vrije software onder de GNU GPL v3.0.
import math
import random

import pygame

from basis import Scene, tekst, SPELER_TOETSEN, stijl_van, palet_filter, LIJN, mix, omlijn

W, H = 480, 270
PAARD_X = 110
VLIEG_Y = 96          # hoogte van de hoeven
ZWAARTE = 380


class Sinterklaas(Scene):
    naam = "sinterklaas"
    K = 1280 / W

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
        self.n = 2 if spel.twee else 1
        self.pakjes = [25] if self.n == 1 else [20, 20]
        self.totaal = sum(self.pakjes)
        self.raak = 0
        self.mis = 0
        self.au = 0
        self.wereld = 0.0
        self.snelheid = 70.0
        self.t = 0.0
        self.huizen = []
        self._volgende_x = 0
        while self._volgende_x < W + 200:
            self._nieuw_huis()
        self.vallend = []
        self.wolkjes = []
        self.meeuwen = []
        self.meeuw_wacht = 10.0
        self.sprong = 0.0       # >0 = paard springt
        self.sprong_v = 0.0
        self.knipper = 0.0
        self.teksten = []
        self.uitleg = True
        self.start_tel = 3.0
        self.einde_t = None
        rnd = random.Random(5)
        self.sterren = [(rnd.randrange(W), rnd.randrange(150)) for _ in range(60)]
        self.ver = [rnd.randint(10, 40) for _ in range(40)]

    def _nieuw_huis(self):
        b = random.choice([64, 72, 80, 96])
        dak = random.randint(150, 190)
        kans = random.random()
        soort = "schoen" if kans < 0.55 else "rook" if kans < 0.8 else "leeg"
        sx = random.randint(14, b - 22)
        self.huizen.append(dict(x=self._volgende_x, b=b, dak=dak, schoorsteen=sx, soort=soort, gevuld=False,
                                muur=random.choice([(120, 70, 60), (100, 80, 70), (90, 70, 80), (130, 90, 60)])))
        self._volgende_x += b + random.randint(0, 10)

    # ---- invoer
    def toets(self, ev):
        if self.uitleg:
            if ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                self.uitleg = False
            elif ev.key == pygame.K_ESCAPE:
                self.spel.naar_dorp()
            return
        if ev.key == pygame.K_ESCAPE:
            self.spel.naar_dorp()
            return
        if self.start_tel > 0 or self.einde_t is not None:
            return
        for i in range(self.n):
            k = SPELER_TOETSEN[i]
            if ev.key == k["actie"] or (ev.key == k["neer"]):
                self._laat_vallen(i)
            elif ev.key == k["op"] and self.sprong <= 0:
                self.sprong_v = 190
                self.sprong = 0.001
                self.spel.geluid.speel("stap")

    def _laat_vallen(self, i):
        if self.pakjes[i] <= 0:
            self.spel.geluid.speel("fout")
            return
        self.pakjes[i] -= 1
        x = PAARD_X - 6 - i * 12
        self.vallend.append(dict(x=self.wereld + x, y=VLIEG_Y - 10 - self.sprong, vx=self.snelheid, vy=0.0,
                                 kleur=random.choice([(220, 40, 50), (60, 140, 230), (250, 200, 50), (90, 190, 90)]),
                                 speler=i))
        self.spel.geluid.speel("stap")

    # ---- bijwerken
    def update(self, dt):
        self.t += dt
        if self.uitleg:
            return
        if self.start_tel > 0:
            self.start_tel -= dt
            return
        if self.einde_t is not None:
            self.einde_t -= dt
            if self.einde_t <= 0:
                self._einde()
            return
        self.snelheid = min(150, self.snelheid + dt * 1.1)
        self.wereld += self.snelheid * dt
        while self._volgende_x < self.wereld + W + 200:
            self._nieuw_huis()
        self.huizen = [h for h in self.huizen if h["x"] + h["b"] > self.wereld - 60]
        # springen
        if self.sprong > 0:
            self.sprong += self.sprong_v * dt
            self.sprong_v -= 520 * dt
            if self.sprong <= 0:
                self.sprong = 0
        # pakjes vallen
        for p in self.vallend:
            p["x"] += p["vx"] * dt
            p["vy"] += ZWAARTE * dt
            p["y"] += p["vy"] * dt
            for h in self.huizen:
                sx = h["x"] + h["schoorsteen"]
                top = h["dak"] - 22
                if sx - 1 <= p["x"] <= sx + 9 and top - 2 <= p["y"] <= top + 6 and p["vy"] > 0:
                    p["weg"] = True
                    if h["soort"] == "schoen" and not h["gevuld"]:
                        h["gevuld"] = True
                        self.raak += 1
                        self.spel.geluid.speel("goed")
                        self.teksten.append([sx + 4, top - 10, "+1", (120, 255, 140), 1.0])
                    elif h["soort"] == "rook":
                        self.au += 1
                        self.spel.geluid.speel("fout")
                        self.teksten.append([sx + 4, top - 10, "Au, heet!", (255, 120, 90), 1.2])
                    else:
                        self.mis += 1
                        self.spel.geluid.speel("plof")
                        self.teksten.append([sx + 4, top - 10, "geen schoen", (200, 200, 210), 1.0])
                    break
                if h["x"] <= p["x"] <= h["x"] + h["b"] and p["y"] >= h["dak"] - self._dakhoogte(h, p["x"]):
                    p["weg"] = True
                    self.mis += 1
                    self.spel.geluid.speel("plof")
                    break
            if p["y"] > H:
                p["weg"] = True
                self.mis += 1
        self.vallend = [p for p in self.vallend if not p.get("weg")]
        # rook
        for h in self.huizen:
            if h["soort"] == "rook" and random.random() < dt * 4:
                self.wolkjes.append([h["x"] + h["schoorsteen"] + 4, h["dak"] - 24, 0.0])
        for w in self.wolkjes:
            w[1] -= 14 * dt
            w[0] -= 6 * dt
            w[2] += dt
        self.wolkjes = [w for w in self.wolkjes if w[2] < 2.5]
        # meeuwen (springen met pijl omhoog)
        self.meeuw_wacht -= dt
        if self.meeuw_wacht <= 0:
            self.meeuw_wacht = random.uniform(6, 11)
            self.meeuwen.append([self.wereld + W + 20, VLIEG_Y - 14])
        for m in self.meeuwen:
            m[0] -= 40 * dt
            sx = m[0] - self.wereld
            if self.knipper <= 0 and PAARD_X - 20 < sx < PAARD_X + 14 and self.sprong < 14:
                verlies = min(3, sum(self.pakjes))
                for _ in range(verlies):
                    i = max(range(self.n), key=lambda j: self.pakjes[j])
                    self.pakjes[i] -= 1
                self.knipper = 1.5
                self.spel.geluid.speel("fout")
                self.teksten.append([self.wereld + PAARD_X, VLIEG_Y - 50, "-%d pakjes!" % verlies, (255, 120, 90), 1.4])
        self.meeuwen = [m for m in self.meeuwen if m[0] > self.wereld - 40]
        self.knipper = max(0, self.knipper - dt)
        for t in self.teksten:
            t[1] -= 18 * dt
            t[4] -= dt
        self.teksten = [t for t in self.teksten if t[4] > 0]
        if sum(self.pakjes) <= 0 and not self.vallend:
            self.einde_t = 1.2

    def _dakhoogte(self, h, x):
        """Puntdak: hoogste punt in het midden."""
        rel = (x - h["x"]) / h["b"]
        return int(18 * (1 - abs(rel - 0.5) * 2))

    def _einde(self):
        drempel = [8, 14, 20] if self.n == 1 else [12, 22, 32]
        sterren = sum(1 for d in drempel if self.raak >= d)
        regels = ["%d van de %d pakjes in een schoen!" % (self.raak, self.totaal)]
        if self.au:
            regels.append("%dx in een brandende kachel. Au!" % self.au)
        self.spel.uitslag("sinterklaas", "Sinterklaas", self.raak, sterren, regels)

    # ---- tekenen
    def teken(self, s):
        if self.stijl == "kleurrijk":
            self._teken_kleurrijk(s)
            return
        self._teken_pixel(s)
        if self.stijl == "retro":
            s.blit(palet_filter(s, 0.27), (0, 0))
        self._hud_pixel(s)

    def _teken_pixel(self, s):
        for y in range(0, H, 2):
            f = y / H
            pygame.draw.rect(s, (int(8 + 20 * f), int(10 + 18 * f), int(34 + 40 * f)), (0, y, W, 2))
        for i, (x, y) in enumerate(self.sterren):
            if (i + int(self.t * 2)) % 7:
                s.set_at((x, y), (220, 220, 255))
        pygame.draw.circle(s, (240, 240, 215), (410, 40), 14)
        pygame.draw.circle(s, (16, 18, 48), (416, 36), 12)
        # stad ver weg
        for i, hh in enumerate(self.ver):
            x = int(i * 24 - (self.wereld * 0.3) % 24)
            pygame.draw.rect(s, (22, 22, 46), (x, 190 - hh, 22, hh + 80))
            if (i * 7) % 3 == 0:
                s.set_at((x + 6, 200 - hh), (200, 170, 90))
        # huizen
        for h in self.huizen:
            x = int(h["x"] - self.wereld)
            if x > W or x + h["b"] < 0:
                continue
            pygame.draw.rect(s, h["muur"], (x, h["dak"], h["b"], H - h["dak"]))
            # dak
            pygame.draw.polygon(s, (90, 30, 30), [(x - 2, h["dak"]), (x + h["b"] // 2, h["dak"] - 18), (x + h["b"] + 2, h["dak"])])
            for k in range(3):
                pygame.draw.line(s, (120, 45, 40), (x + k * 6 + 4, h["dak"] - 2), (x + h["b"] // 2, h["dak"] - 16 + k * 4))
            # sneeuw op het dak
            pygame.draw.line(s, (235, 240, 250), (x - 2, h["dak"]), (x + h["b"] // 2, h["dak"] - 18), 2)
            pygame.draw.line(s, (235, 240, 250), (x + h["b"] // 2, h["dak"] - 18), (x + h["b"] + 2, h["dak"]), 2)
            # ramen
            for rx in range(x + 8, x + h["b"] - 12, 20):
                for ry in range(h["dak"] + 10, H - 10, 26):
                    pygame.draw.rect(s, (255, 210, 110) if (rx + ry) % 3 else (50, 45, 60), (rx, ry, 9, 11))
            # schoorsteen
            sx = x + h["schoorsteen"]
            top = h["dak"] - 22
            pygame.draw.rect(s, (110, 60, 50), (sx, top, 9, 22 - self._dakhoogte(h, h["x"] + h["schoorsteen"]) // 2 + 6))
            pygame.draw.rect(s, (80, 40, 35), (sx - 1, top, 11, 3))
            for k in range(3):
                pygame.draw.line(s, (90, 50, 45), (sx, top + 6 + k * 5), (sx + 8, top + 6 + k * 5))
            if h["soort"] == "schoen" and not h["gevuld"]:
                yy = top - 10 + int(math.sin(self.t * 4 + h["x"]) * 2)
                pygame.draw.rect(s, (250, 250, 250), (sx - 1, yy - 1, 12, 8))
                pygame.draw.rect(s, (60, 35, 20), (sx, yy + 2, 9, 4))   # schoentje
                pygame.draw.rect(s, (60, 35, 20), (sx, yy, 3, 3))
                pygame.draw.line(s, (255, 140, 30), (sx + 6, yy - 3), (sx + 9, yy + 1), 2)  # wortel
            elif h["gevuld"]:
                pygame.draw.rect(s, (220, 40, 50), (sx + 2, top - 6, 5, 5))
                pygame.draw.line(s, (250, 210, 60), (sx + 4, top - 6), (sx + 4, top - 2))
        for w in self.wolkjes:
            r = int(2 + w[2] * 2)
            pygame.draw.circle(s, (170, 170, 180), (int(w[0] - self.wereld), int(w[1])), r)
        # pakjes
        for p in self.vallend:
            x, y = int(p["x"] - self.wereld), int(p["y"])
            pygame.draw.rect(s, p["kleur"], (x - 3, y - 3, 7, 7))
            pygame.draw.line(s, (255, 230, 120), (x, y - 3), (x, y + 3))
            pygame.draw.line(s, (255, 230, 120), (x - 3, y), (x + 3, y))
        for m in self.meeuwen:
            x, y = int(m[0] - self.wereld), int(m[1])
            vl = 3 if int(self.t * 8) % 2 else -2
            pygame.draw.lines(s, (235, 235, 240), False, [(x - 7, y + vl), (x - 3, y), (x, y + 2), (x + 3, y), (x + 7, y + vl)], 2)
            s.set_at((x + 5, y + 1), (255, 170, 40))
        if not (self.knipper > 0 and int(self.t * 12) % 2):
            self._sint(s, PAARD_X, int(VLIEG_Y - self.sprong))
        for x, y, t, kl, _ in self.teksten:
            tekst(s, t, (int(x - self.wereld), int(y)), 16, kl, midden=True, pixel=True)

    def _hud_pixel(self, s):
        pygame.draw.rect(s, (0, 0, 0), (0, 0, W, 14))
        tekst(s, "SINTERKLAAS", (4, 2), 16, (255, 179, 71), pixel=True, schaduw=False)
        tekst(s, "In de schoen: %d" % self.raak, (W // 2, 2), 16, (255, 255, 255), midden=True, pixel=True, schaduw=False)
        pk = "Pakjes: %d" % self.pakjes[0] if self.n == 1 else "Pakjes: %d + %d" % tuple(self.pakjes)
        tekst(s, pk, (W - 4, 2), 16, (255, 255, 255), rechts=True, pixel=True, schaduw=False)
        if self.start_tel > 0 and not self.uitleg:
            tekst(s, str(math.ceil(self.start_tel)), (W // 2, 100), 64, (255, 255, 255), midden=True, pixel=True)
        if self.uitleg:
            self._uitleg(s)

    def _sint(self, s, x, y):
        """Sinterklaas op zijn schimmel. x,y = hoeven midden."""
        b = int(self.t * 10) % 2
        wit, grijs = (240, 240, 245), (190, 190, 200)
        # paard
        pygame.draw.rect(s, wit, (x - 14, y - 14, 26, 9))
        pygame.draw.rect(s, wit, (x + 10, y - 22, 6, 10))   # hals
        pygame.draw.rect(s, wit, (x + 13, y - 24, 9, 5))    # hoofd
        s.set_at((x + 19, y - 23), (30, 30, 30))
        pygame.draw.line(s, grijs, (x - 15, y - 13), (x - 19, y - 6), 2)  # staart
        for i, lx in enumerate((x - 12, x - 7, x + 4, x + 9)):
            d = (1 if (i + b) % 2 else -1) * 2
            pygame.draw.line(s, grijs, (lx, y - 5), (lx + d, y), 2)
        # zadeldeken
        pygame.draw.rect(s, (200, 30, 40), (x - 6, y - 15, 12, 6))
        # Sint
        pygame.draw.rect(s, (200, 30, 40), (x - 6, y - 30, 12, 16))       # mantel
        pygame.draw.rect(s, (250, 250, 250), (x - 1, y - 30, 2, 16))
        pygame.draw.rect(s, (240, 205, 175), (x - 3, y - 36, 7, 6))      # gezicht
        pygame.draw.rect(s, (255, 255, 255), (x - 4, y - 32, 9, 6))      # baard
        pygame.draw.polygon(s, (210, 30, 40), [(x - 4, y - 36), (x + 5, y - 36), (x + 4, y - 44), (x, y - 47), (x - 3, y - 44)])
        pygame.draw.line(s, (255, 210, 60), (x, y - 45), (x, y - 37))
        pygame.draw.line(s, (255, 210, 60), (x - 2, y - 41), (x + 2, y - 41))
        pygame.draw.line(s, (255, 210, 60), (x - 9, y - 40), (x - 9, y - 16))  # staf
        pygame.draw.arc(s, (255, 210, 60), (x - 13, y - 46, 7, 8), 0, math.pi, 1)
        # zak met pakjes
        pygame.draw.circle(s, (120, 80, 50), (x - 12, y - 20), 5)

    def _uitleg_regels(self):
        return ["SINTERKLAAS: PAKJES DOOR DE SCHOORSTEEN", "",
                  "Sint rijdt op zijn schimmel over de daken.",
                  "Druk op spatie (of pijl omlaag) om een pakje te laten vallen.",
                  "Het pakje valt schuin: laat het dus iets vooraf los!", "",
                  "Schoorsteen met een schoentje = raak!",
                  "Rokende schoorsteen = daar brandt de kachel. Au!", "",
                  "Pas op voor meeuwen: spring met pijl omhoog.", "",
                  "Speler 2: E (of S) = pakje, W = springen", "",
                  "Enter = beginnen   Esc = terug naar het dorp"]

    def _uitleg(self, s):
        pygame.draw.rect(s, (10, 10, 24), (28, 22, W - 56, H - 40))
        pygame.draw.rect(s, (255, 179, 71), (28, 22, W - 56, H - 40), 1)
        regels = self._uitleg_regels()
        y = 30
        for r in regels:
            tekst(s, r, (W // 2, y), 16, (255, 179, 71) if r.isupper() else (230, 230, 235), midden=True, pixel=True,
                  schaduw=False)
            y += 15

    # ================================================================= stijl 'kleurrijk' (cartoon, 1280 x 720)
    def _teken_kleurrijk(self, s):
        K = self.K
        SW, SH = 1280, 720
        wx = lambda x: (x - self.wereld) * K   # noqa: E731
        for y in range(0, SH, 4):
            pygame.draw.rect(s, mix((50, 30, 130), (210, 80, 160), y / SH), (0, y, SW, 4))
        for i, (x, y) in enumerate(self.sterren):
            if (i + int(self.t * 2)) % 7:
                pygame.draw.circle(s, (255, 250, 200), (int(x * K), int(y * K)), 3 if i % 3 == 0 else 2)
        pygame.draw.circle(s, LIJN, (1094, 106), 44)
        pygame.draw.circle(s, (255, 236, 140), (1094, 106), 38)
        pygame.draw.circle(s, (240, 210, 110), (1080, 96), 8)
        # stad ver weg
        for i, hh in enumerate(self.ver):
            x = (i * 24 - (self.wereld * 0.3) % 24) * K
            r = pygame.Rect(int(x), int((190 - hh) * K), int(22 * K), SH)
            pygame.draw.rect(s, (110, 60, 160), r, border_radius=10)
            pygame.draw.rect(s, LIJN, r, 4, border_radius=10)
        felle = [(40, 200, 190), (255, 200, 60), (255, 120, 100), (120, 200, 90), (90, 150, 255), (250, 140, 200)]
        for h in self.huizen:
            x = wx(h["x"])
            b = h["b"] * K
            if x > SW + 30 or x + b < -30:
                continue
            dak = h["dak"] * K
            muur = felle[int(h["x"] / 7) % len(felle)]
            romp = pygame.Rect(int(x), int(dak), int(b), SH)
            pygame.draw.rect(s, LIJN, romp.inflate(10, 10), border_radius=12)
            pygame.draw.rect(s, muur, romp, border_radius=8)
            for rx in range(int(x + 22), int(x + b - 40), 54):
                for ry in range(int(dak + 26), SH - 20, 70):
                    kl = (255, 240, 140) if (rx + ry) % 3 else (80, 60, 120)
                    pygame.draw.ellipse(s, LIJN, (rx - 4, ry - 4, 34, 40))
                    pygame.draw.ellipse(s, kl, (rx, ry, 26, 32))
            # schoorsteen (achter het dak)
            sx = wx(h["x"] + h["schoorsteen"])
            top = (h["dak"] - 22) * K
            hoog = dak - top - 4
            pygame.draw.rect(s, LIJN, (sx - 5, top - 5, 9 * K + 10, hoog + 5), border_radius=6)
            pygame.draw.rect(s, (200, 80, 60), (sx, top, 9 * K, hoog), border_radius=4)
            pygame.draw.rect(s, (150, 50, 40), (sx - 4, top, 9 * K + 8, 10))
            dakpunten = [(x - 10, dak + 4), (x + b / 2, dak - 18 * K), (x + b + 10, dak + 4)]
            pygame.draw.polygon(s, (170, 50, 70), dakpunten)
            pygame.draw.lines(s, (255, 255, 255), False, dakpunten, 12)
            pygame.draw.polygon(s, LIJN, dakpunten, 5)
            if h["soort"] == "schoen" and not h["gevuld"]:
                cy = top - 38 + math.sin(self.t * 4 + h["x"]) * 5
                cx = sx + 12
                pygame.draw.circle(s, LIJN, (int(cx), int(cy)), 24)
                pygame.draw.circle(s, (255, 255, 255), (int(cx), int(cy)), 20)
                pygame.draw.rect(s, (110, 60, 30), (cx - 13, cy - 2, 24, 10), border_radius=4)
                pygame.draw.rect(s, (110, 60, 30), (cx - 13, cy - 10, 8, 10), border_radius=3)
                pygame.draw.line(s, (255, 140, 30), (cx + 4, cy - 12), (cx + 12, cy - 2), 5)
            elif h["gevuld"]:
                self._kpakje(s, sx + 12, top - 16, 14, (230, 50, 60))
        for w in self.wolkjes:
            r = int((2 + w[2] * 2) * K)
            pygame.draw.circle(s, LIJN, (int(wx(w[0])), int(w[1] * K)), r + 3)
            pygame.draw.circle(s, (215, 215, 230), (int(wx(w[0])), int(w[1] * K)), r)
        for p in self.vallend:
            self._kpakje(s, wx(p["x"]), p["y"] * K, 11, p["kleur"])
        for m in self.meeuwen:
            x, y = wx(m[0]), m[1] * K
            vl = 9 if int(self.t * 8) % 2 else -6
            pts = [(x - 20, y + vl), (x - 8, y), (x, y + 6), (x + 8, y), (x + 20, y + vl)]
            pygame.draw.lines(s, LIJN, False, pts, 11)
            pygame.draw.lines(s, (255, 255, 255), False, pts, 6)
            pygame.draw.circle(s, (255, 170, 40), (int(x + 14), int(y + 3)), 4)
        if not (self.knipper > 0 and int(self.t * 12) % 2):
            self._ksint(s, PAARD_X * K, (VLIEG_Y - self.sprong) * K)
        for x, y, t, kl, _ in self.teksten:
            tekst(s, t, (int(wx(x)), int(y * K)), 30, kl, midden=True, vet=True)
        # balk
        pygame.draw.rect(s, (0, 0, 0), (0, 0, SW, 50))
        tekst(s, "Sinterklaas", (16, 8), 30, (255, 179, 71), vet=True)
        tekst(s, "In de schoen: %d" % self.raak, (SW // 2, 8), 30, (255, 255, 255), midden=True, vet=True)
        pk = "Pakjes: %d" % self.pakjes[0] if self.n == 1 else "Pakjes: %d + %d" % tuple(self.pakjes)
        tekst(s, pk, (SW - 16, 8), 30, (255, 255, 255), rechts=True, vet=True)
        if self.start_tel > 0 and not self.uitleg:
            tekst(s, str(math.ceil(self.start_tel)), (SW // 2, 250), 140, (255, 255, 255), midden=True, vet=True)
        if self.uitleg:
            dek = pygame.Surface((SW, SH), pygame.SRCALPHA)
            dek.fill((10, 8, 25, 225))
            s.blit(dek, (0, 0))
            y = 70
            for r in self._uitleg_regels():
                if r:
                    tekst(s, r, (SW // 2, y), 36 if r.isupper() else 28,
                          (255, 179, 71) if r.isupper() else (235, 235, 245), midden=True, vet=r.isupper())
                y += 40

    def _kpakje(self, s, x, y, r, kleur):
        pygame.draw.rect(s, LIJN, (x - r - 4, y - r - 4, 2 * r + 8, 2 * r + 8), border_radius=5)
        pygame.draw.rect(s, kleur, (x - r, y - r, 2 * r, 2 * r), border_radius=3)
        pygame.draw.line(s, (255, 230, 120), (x, y - r), (x, y + r), 4)
        pygame.draw.line(s, (255, 230, 120), (x - r, y), (x + r, y), 4)
        pygame.draw.circle(s, (255, 230, 120), (int(x - 4), int(y - r - 3)), 4)
        pygame.draw.circle(s, (255, 230, 120), (int(x + 4), int(y - r - 3)), 4)

    def _ksint(self, s, x, y):
        """Sinterklaas op zijn schimmel, cartoon. x,y = hoeven midden."""
        b = int(self.t * 10) % 2
        laag = pygame.Surface((240, 200), pygame.SRCALPHA)
        ox, oy = 120, 170   # hoeven midden binnen de laag
        wit = (250, 250, 255)
        for i, lx in enumerate((-30, -16, 14, 28)):
            d = (1 if (i + b) % 2 else -1) * 6
            pygame.draw.line(laag, (210, 210, 225), (ox + lx, oy - 18), (ox + lx + d, oy), 8)
        pygame.draw.ellipse(laag, wit, (ox - 44, oy - 50, 84, 36))
        pygame.draw.polygon(laag, wit, [(ox + 24, oy - 42), (ox + 42, oy - 76), (ox + 56, oy - 70), (ox + 40, oy - 34)])
        pygame.draw.ellipse(laag, wit, (ox + 36, oy - 84, 34, 20))
        pygame.draw.circle(laag, (30, 30, 30), (ox + 56, oy - 77), 3)
        pygame.draw.line(laag, (210, 210, 225), (ox - 42, oy - 44), (ox - 56, oy - 22), 8)
        pygame.draw.rect(laag, (220, 30, 40), (ox - 18, oy - 56, 36, 18), border_radius=6)   # zadeldeken
        pygame.draw.rect(laag, (220, 30, 40), (ox - 16, oy - 98, 34, 46), border_radius=10)  # mantel
        pygame.draw.rect(laag, (255, 255, 255), (ox - 2, oy - 98, 6, 46))
        pygame.draw.circle(laag, (240, 205, 175), (ox + 1, oy - 110), 12)
        pygame.draw.ellipse(laag, (255, 255, 255), (ox - 12, oy - 110, 26, 22))                # baard
        pygame.draw.polygon(laag, (225, 30, 40), [(ox - 12, oy - 118), (ox + 14, oy - 118), (ox + 10, oy - 140),
                                                  (ox + 1, oy - 150), (ox - 8, oy - 140)])
        pygame.draw.line(laag, (255, 210, 60), (ox + 1, oy - 146), (ox + 1, oy - 121), 4)
        pygame.draw.line(laag, (255, 210, 60), (ox - 6, oy - 134), (ox + 8, oy - 134), 4)
        pygame.draw.line(laag, (255, 210, 60), (ox - 28, oy - 140), (ox - 28, oy - 52), 5)       # staf
        pygame.draw.arc(laag, (255, 210, 60), (ox - 42, oy - 154, 22, 24), 0, math.pi, 5)
        pygame.draw.circle(laag, (140, 90, 50), (ox - 40, oy - 70), 16)                          # zak
        laag = omlijn(laag, 4)
        s.blit(laag, (x - ox, y - oy))
