# -*- coding: utf-8 -*-
# DraveFeest - Oud & Nieuw: de vuurwerkshow. Pijlen schieten omhoog; laat ze knallen als ze bij de ring zijn.
# De klok telt af naar middernacht. Om twaalf uur: grote finale!
# Copyright (C) 2026 Dravenlock (Roger & Claudio). Vrije software onder de GNU GPL v3.0.
import math
import random

import pygame

from basis import HDSpel, tekst, gloed, mix, pijl

W, H = 1280, 720
DOEL_Y = 230
BAAN_X = [320, 533, 746, 960]
KLEUREN = [(255, 80, 90), (255, 210, 60), (90, 200, 255), (140, 255, 120), (255, 120, 230), (255, 160, 60)]


class Nieuwjaar(HDSpel):
    naam = "nieuwjaar"
    titel = "Oud & Nieuw"
    speeltijd = 60
    retro_licht = 0.0

    def __init__(self, spel):
        super().__init__(spel)
        if self.n == 1:
            self.banen = [(pygame.K_LEFT, "links"), (pygame.K_DOWN, "neer"), (pygame.K_UP, "op"), (pygame.K_RIGHT, "rechts")]
            self.wie = [0, 0, 0, 0]
        else:  # speler 2 links (A en D), speler 1 rechts (pijl links en pijl rechts)
            self.banen = [(pygame.K_a, "A"), (pygame.K_d, "D"), (pygame.K_LEFT, "links"), (pygame.K_RIGHT, "rechts")]
            self.wie = [1, 1, 0, 0]
        self.pijlen = []          # [baan, y, snelheid, kleur]
        self.vonken = []          # [x, y, vx, vy, kleur, leven]
        self.knipper = [0.0] * 4
        self.punten = 0
        self.punten_speler = [0, 0]
        self.reeks = 0
        self.beste_reeks = 0
        self.raak = 0
        self.gemist = 0
        self.wacht = 1.0
        self.finale = 0.0
        rnd = random.Random(11)
        self.sterren_lucht = [(rnd.randrange(W), rnd.randrange(420)) for _ in range(130)]
        self.stad = []
        x = -20
        while x < W + 40:
            b = rnd.randint(50, 110)
            self.stad.append((x, b, rnd.randint(70, 190), [(rnd.randint(6, b - 14), rnd.randint(12, 150)) for _ in range(6)]))
            x += b - 4
        self._gl = {}

    # ---- invoer
    def spel_toets(self, ev):
        for i, (toets, _) in enumerate(self.banen):
            if ev.key == toets:
                self._knal(i)

    def _knal(self, baan):
        self.knipper[baan] = 0.15
        beste, afstand = None, 999
        for p in self.pijlen:
            if p[0] == baan and abs(p[1] - DOEL_Y) < afstand:
                beste, afstand = p, abs(p[1] - DOEL_Y)
        if beste is None or afstand > 46:
            self.reeks = 0
            self.spel.geluid.speel("fout")
            return
        self.pijlen.remove(beste)
        pt, woord = (3, "Perfect!") if afstand <= 12 else (2, "Goed!") if afstand <= 28 else (1, "Oké")
        self.reeks += 1
        self.beste_reeks = max(self.beste_reeks, self.reeks)
        extra = 1 if self.reeks >= 10 else 0
        self.punten += pt + extra
        self.punten_speler[self.wie[baan]] += pt + extra
        self.raak += 1
        self._ontplof(BAAN_X[baan], beste[1], beste[3], 70 if pt == 3 else 45)
        self.spel.geluid.noot([523, 659, 784, 1047][baan] * (2 if pt == 3 else 1), 0.12)
        self.spel.geluid.speel("plof")
        self.zweef(BAAN_X[baan], beste[1] - 70, woord, (255, 255, 255) if pt < 3 else (255, 220, 90), 0.8)

    def _ontplof(self, x, y, kleur, n):
        for _ in range(n):
            a = random.uniform(0, 2 * math.pi)
            v = random.uniform(120, 380)
            self.vonken.append([x, y, math.cos(a) * v, math.sin(a) * v, kleur if random.random() < 0.8 else (255, 255, 255),
                                random.uniform(0.8, 1.5)])

    # ---- bijwerken
    def spel_update(self, dt):
        if self.klaar_t is not None:
            # finale: om middernacht overal vuurwerk
            self.finale += dt
            if random.random() < 0.35:
                self._ontplof(random.randint(150, W - 150), random.randint(110, 330), random.choice(KLEUREN), 60)
                if random.random() < 0.5:
                    self.spel.geluid.speel("plof")
        else:
            verstreken = self.speeltijd - self.tijd
            self.wacht -= dt
            if self.wacht <= 0:
                tempo = 1.0 + verstreken / 30.0
                self.wacht = random.uniform(0.55, 1.1) / tempo
                baan = random.randrange(4)
                self.pijlen.append([baan, H + 10, random.uniform(260, 330) * (1 + verstreken / 120), random.choice(KLEUREN)])
                if verstreken > 25 and random.random() < 0.25:
                    self.pijlen.append([(baan + 2) % 4, H + 60, random.uniform(260, 330) * (1 + verstreken / 120),
                                        random.choice(KLEUREN)])
        for p in self.pijlen:
            p[1] -= p[2] * dt
        for p in [p for p in self.pijlen if p[1] < DOEL_Y - 70]:
            self.pijlen.remove(p)
            self.reeks = 0
            self.gemist += 1
            self.zweef(BAAN_X[p[0]], p[1] - 20, "pfff...", (160, 160, 180), 0.7)
        for v in self.vonken:
            v[0] += v[2] * dt
            v[1] += v[3] * dt
            v[2] *= 0.985
            v[3] = v[3] * 0.985 + 160 * dt
            v[5] -= dt
        self.vonken = [v for v in self.vonken if v[5] > 0]
        self.knipper = [max(0, k - dt) for k in self.knipper]

    def einde(self):
        drempel = [100, 200, 320]
        sterren = sum(1 for d in drempel if self.punten >= d)
        regels = ["%d punten  ·  %d pijlen geknald" % (self.punten, self.raak),
                  "Langste reeks: %d op rij" % self.beste_reeks]
        if self.n == 2:
            regels.append("Speler 1: %d   ·   Speler 2: %d" % tuple(self.punten_speler))
        self.spel.uitslag("nieuwjaar", "Gelukkig Nieuwjaar!", self.punten, sterren, regels)

    # ---- tekenen
    def _gloed(self, r, kl):
        if (r, kl) not in self._gl:
            self._gl[(r, kl)] = gloed(r, kl)
        return self._gl[(r, kl)]

    def achter(self, s):
        boven, onder = (self.k((6, 6, 26)), self.k((40, 24, 70)))
        if self.stijl == "kleurrijk":
            boven, onder = (30, 16, 90), (120, 50, 150)
        if self.stijl == "retro":
            boven, onder = (0, 0, 0), (0, 0, 0)
        for y in range(0, H, 4):
            pygame.draw.rect(s, mix(boven, onder, y / H), (0, y, W, 4))
        for i, (x, y) in enumerate(self.sterren_lucht):
            if (i + int(self.t * 2)) % 9:
                pygame.draw.circle(s, (230, 230, 255), (x, y), 2 if (self.stijl == "kleurrijk" and i % 3 == 0) else 1)

    def voor(self, s):
        # stad met verlichte ramen
        for x, b, h, ramen in self.stad:
            kl = {"kleurrijk": (70, 40, 120), "retro": (29, 43, 83)}.get(self.stijl, (20, 18, 40))
            pygame.draw.rect(s, kl, (x, H - 60 - h, b, h + 60))
            for rx, ry in ramen:
                if ry < h:
                    pygame.draw.rect(s, self.k((255, 210, 110)), (x + rx, H - 60 - h + ry, 8, 10))
        # kerktoren met klok
        tx = W // 2
        toren = {"kleurrijk": (90, 60, 140), "retro": (95, 87, 79)}.get(self.stijl, (34, 30, 52))
        pygame.draw.rect(s, toren, (tx - 40, H - 360, 80, 360))
        pygame.draw.polygon(s, toren,
                            [(tx - 48, H - 360), (tx, H - 470), (tx + 48, H - 360)])
        pygame.draw.circle(s, (250, 245, 225), (tx, H - 310), 30)
        sec = max(0, self.tijd) if self.klaar_t is None else 0
        # de laatste minuut voor twaalven: grote wijzer net voor de 12, rode secondewijzer loopt mee
        a_groot = -math.pi / 2 - (sec / 60) * (2 * math.pi / 60) * 1
        a_sec = -math.pi / 2 - (sec / 60) * 2 * math.pi
        pygame.draw.line(s, (40, 30, 30), (tx, H - 310), (tx + math.cos(-math.pi / 2 - 0.02) * 16, H - 310 + math.sin(-math.pi / 2 - 0.02) * 16), 5)
        pygame.draw.line(s, (40, 30, 30), (tx, H - 310), (tx + math.cos(a_groot) * 24, H - 310 + math.sin(a_groot) * 24), 3)
        pygame.draw.line(s, (200, 40, 40), (tx, H - 310), (tx + math.cos(a_sec) * 26, H - 310 + math.sin(a_sec) * 26), 2)
        # grond
        pygame.draw.rect(s, self.k((28, 26, 36)) if self.stijl != "kleurrijk" else (80, 70, 120), (0, H - 60, W, 60))
        # lanceerbuizen met de toets eronder
        for i, x in enumerate(BAAN_X):
            kl = (255, 255, 255) if self.knipper[i] > 0 else (190, 190, 205)
            pygame.draw.rect(s, (110, 40, 40), (x - 16, H - 110, 32, 54), border_radius=5)
            pygame.draw.rect(s, (230, 200, 60), (x - 16, H - 94, 32, 8))
            pygame.draw.rect(s, (30, 30, 40), (x - 30, H - 56, 60, 44), border_radius=10)
            toets = self.banen[i][1]
            if toets in ("links", "rechts", "op", "neer"):
                pijl(s, toets, x, H - 34, 14, kl)
            else:
                tekst(s, toets, (x, H - 52), 30, kl, midden=True, vet=True, schaduw=False)
        # pijlen (vuurpijlen)
        for baan, y, _, kl in self.pijlen:
            x = BAAN_X[baan]
            pygame.draw.polygon(s, kl, [(x, y - 30), (x - 9, y - 12), (x + 9, y - 12)])
            pygame.draw.rect(s, kl, (x - 7, y - 12, 14, 34), border_radius=3)
            pygame.draw.line(s, (200, 170, 110), (x, y + 22), (x, y + 70), 3)

    def effect(self, s):
        # doelringen
        for i, x in enumerate(BAAN_X):
            r = 30 + (6 if self.knipper[i] > 0 else 0)
            kleur = (255, 220, 120) if self.stijl != "kleurrijk" else (255, 255, 255)
            pygame.draw.circle(s, kleur, (x, DOEL_Y), r, 4)
            pygame.draw.circle(s, kleur, (x, DOEL_Y), 12, 2)
        # vonkjes en vuurstaarten
        for baan, y, _, kl in self.pijlen:
            x = BAAN_X[baan]
            for k in range(4):
                pygame.draw.circle(s, (255, 200, 90), (x + random.randint(-4, 4), int(y + 26 + k * 9 + random.randint(0, 6))), 3 - k // 2)
            if self.stijl != "retro":
                s.blit(self._gloed(40, (90, 60, 20)), (x - 40, y - 20), special_flags=pygame.BLEND_ADD)
        for x, y, vx, vy, kl, leven in self.vonken:
            r = 4 if leven > 0.6 else 3 if leven > 0.3 else 2
            pygame.draw.circle(s, kl, (int(x), int(y)), r)
        # aftellen naar middernacht
        if self.klaar_t is None and not self.uitleg and self.start_tel <= 0:
            sec = math.ceil(self.tijd)
            if sec <= 10:
                tekst(s, str(sec), (W // 2, 70), 120, (255, 255, 255), midden=True, vet=True)
            else:
                tekst(s, "23:59:%02d" % (60 - sec), (W // 2, 80), 40, (230, 230, 245), midden=True, vet=True)
        elif self.klaar_t is not None:
            tekst(s, "Gelukkig Nieuwjaar!", (W // 2, 90), 80, (255, 220, 90), midden=True, vet=True)
        if self.reeks >= 3 and self.klaar_t is None:
            tekst(s, "%d op rij!%s" % (self.reeks, "  (+1 per knal)" if self.reeks >= 10 else ""), (W // 2, H - 170), 30,
                  (255, 220, 120), midden=True, vet=True)

    def balk(self):
        return ("Oud & Nieuw", "Punten: %d" % self.punten, "Nog: %d sec" % max(0, math.ceil(self.tijd)))

    def uitleg_regels(self):
        r = ["Oud & Nieuw: de vuurwerkshow",
             "Vuurpijlen schieten omhoog. Is een pijl bij de gele ring?",
             "Druk dan op de toets onder die buis: KNAL!",
             "Precies in het midden = Perfect (3 punten).  10 op rij = extra punten.",
             "De klok telt af naar middernacht. Om twaalf uur: grote finale!"]
        if self.n == 1:
            r.append("Toetsen: pijl links, pijl omlaag, pijl omhoog, pijl rechts")
        else:
            r.append("Speler 2: A en D (links)   ·   Speler 1: pijl links en pijl rechts (rechts)")
        return r
