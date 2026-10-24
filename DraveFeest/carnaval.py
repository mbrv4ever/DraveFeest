# -*- coding: utf-8 -*-
# DraveFeest - Carnaval: de polonaise! Loop over het plein en haal verklede mensen op.
# Iedereen danst achter je aan in een lange rij. Bots je tegen de rand of je eigen rij, dan valt de rij uit elkaar.
# Copyright (C) 2026 Dravenlock (Roger & Claudio). Vrije software onder de GNU GPL v3.0.
import math
import random

import pygame

from basis import HDSpel, SPELER_TOETSEN

W, H = 1280, 720
VAK = 40
KOL, RIJ = W // VAK, (H - 80) // VAK          # 32 x 16 vakjes
BOVEN = 80
PAKKEN = [("piraat", (40, 40, 50), (220, 40, 40)), ("clown", (255, 210, 40), (60, 160, 255)),
          ("prinses", (255, 140, 200), (255, 220, 80)), ("kikker", (90, 200, 90), (60, 140, 60)),
          ("cowboy", (170, 110, 60), (230, 200, 140)), ("boer", (60, 90, 200), (220, 40, 40)),
          ("ridder", (180, 185, 200), (120, 120, 140)), ("bij", (255, 210, 40), (40, 40, 40))]
RICHTING = {"links": (-1, 0), "rechts": (1, 0), "op": (0, -1), "neer": (0, 1)}


class Carnaval(HDSpel):
    naam = "carnaval"
    titel = "Carnaval"
    speeltijd = 75

    def __init__(self, spel):
        super().__init__(spel)
        starts = [(8, 8)] if self.n == 1 else [(22, 4), (9, 11)]
        self.rijen = []
        for i, (x, y) in enumerate(starts):
            r = (1, 0) if i == 0 else (-1, 0) if self.n == 2 else (1, 0)
            if self.n == 2 and i == 0:
                r = (-1, 0)
            if self.n == 2 and i == 1:
                r = (1, 0)
            self.rijen.append(dict(kop=[(x, y)], pakken=[], richting=r, volgende=r, wacht=0.0, botsen=0.0,
                                   opgehaald=0, langste=1))
        self.dansers = []          # [x, y, pak]
        self.losse = []            # weglopende dansers na een botsing [x, y, vx, vy, pak, t]
        self.confetti = []
        self.tik = 0.2
        for _ in range(4):
            self._nieuwe_danser()
        rnd = random.Random(4)
        self.tegels = [[rnd.random() < 0.12 for _ in range(KOL)] for _ in range(RIJ)]
        self.slingers = [(x, rnd.choice([(255, 80, 90), (255, 210, 60), (90, 200, 255), (140, 230, 120)])) for x in range(0, W, 40)]

    def _bezet(self):
        b = set()
        for r in self.rijen:
            b.update(r["kop"])
        b.update((d[0], d[1]) for d in self.dansers)
        return b

    def _nieuwe_danser(self):
        bezet = self._bezet()
        for _ in range(60):
            x, y = random.randrange(1, KOL - 1), random.randrange(1, RIJ - 1)
            if (x, y) not in bezet and all(abs(x - r["kop"][0][0]) + abs(y - r["kop"][0][1]) > 3 for r in self.rijen):
                self.dansers.append([x, y, random.randrange(len(PAKKEN))])
                return

    def spel_toets(self, ev):
        for i, r in enumerate(self.rijen):
            k = SPELER_TOETSEN[i]
            for naam in ("links", "rechts", "op", "neer"):
                if ev.key == k[naam]:
                    d = RICHTING[naam]
                    if (d[0] + r["richting"][0], d[1] + r["richting"][1]) != (0, 0):   # niet omkeren
                        r["volgende"] = d

    def spel_update(self, dt):
        for c in self.confetti:
            c[0] += c[2] * dt
            c[1] += c[3] * dt
            c[3] += 200 * dt
            c[5] -= dt
        self.confetti = [c for c in self.confetti if c[5] > 0]
        for l in self.losse:
            l[0] += l[2] * dt
            l[1] += l[3] * dt
            l[5] -= dt
        self.losse = [l for l in self.losse if l[5] > 0]
        if self.klaar_t is not None:
            return
        verstreken = self.speeltijd - self.tijd
        self.tik = max(0.11, 0.2 - verstreken * 0.0012)
        for i, r in enumerate(self.rijen):
            r["botsen"] = max(0, r["botsen"] - dt)
            r["wacht"] -= dt
            if r["wacht"] > 0:
                continue
            r["wacht"] = self.tik
            r["richting"] = r["volgende"]
            kx, ky = r["kop"][0]
            nx, ny = kx + r["richting"][0], ky + r["richting"][1]
            # tegen de rand: keer om (de kop draait), en de rij valt uit elkaar
            muur = not (0 <= nx < KOL and 0 <= ny < RIJ)
            eigen = (nx, ny) in r["kop"][1:-1]
            ander = any((nx, ny) in o["kop"] for j, o in enumerate(self.rijen) if j != i)
            if (muur or eigen or ander) and r["botsen"] <= 0:
                self._botsing(r, "rand" if muur else "rij")
                if muur:
                    r["richting"] = r["volgende"] = (-r["richting"][0], -r["richting"][1])
                    nx, ny = kx + r["richting"][0], ky + r["richting"][1]
            if not (0 <= nx < KOL and 0 <= ny < RIJ):
                continue
            r["kop"].insert(0, (nx, ny))
            gepakt = None
            for d in self.dansers:
                if (d[0], d[1]) == (nx, ny):
                    gepakt = d
                    break
            if gepakt:
                self.dansers.remove(gepakt)
                r["pakken"].insert(0, gepakt[2])
                r["opgehaald"] += 1
                r["langste"] = max(r["langste"], len(r["kop"]))
                if len(self.dansers) < 6:
                    self._nieuwe_danser()
                if random.random() < 0.3 and len(self.dansers) < 6:
                    self._nieuwe_danser()
                self.spel.geluid.noot(523 + 40 * (len(r["kop"]) % 8), 0.08)
                if len(r["kop"]) % 5 == 0:
                    self.zweef(nx * VAK + VAK / 2, BOVEN + ny * VAK - 30, "Alaaf! Rij van %d" % len(r["kop"]), (255, 220, 90), 1.0)
                    self._knal(nx * VAK + VAK / 2, BOVEN + ny * VAK)
            else:
                r["kop"].pop()
        while len(self.dansers) < 3:
            self._nieuwe_danser()

    def _botsing(self, r, wat):
        r["botsen"] = 1.0
        hoeveel = len(r["pakken"]) // 2
        for _ in range(hoeveel):
            pos = r["kop"].pop()
            pak = r["pakken"].pop()
            a = random.uniform(0, 2 * math.pi)
            self.losse.append([pos[0] * VAK + VAK / 2, BOVEN + pos[1] * VAK + VAK / 2, math.cos(a) * 140, math.sin(a) * 140,
                               pak, 1.2])
        self.spel.geluid.speel("fout")
        kx, ky = r["kop"][0]
        self.zweef(kx * VAK, BOVEN + ky * VAK - 20, "Oei! De rij valt uit elkaar" if hoeveel else "Oei!", (255, 160, 140), 1.1)

    def _knal(self, x, y):
        for _ in range(40):
            a = random.uniform(0, 2 * math.pi)
            v = random.uniform(80, 300)
            self.confetti.append([x, y, math.cos(a) * v, math.sin(a) * v - 100,
                                  random.choice([(255, 80, 90), (255, 210, 60), (90, 200, 255), (140, 230, 120), (255, 140, 220)]),
                                  random.uniform(0.7, 1.3)])

    def punten(self):
        return sum(r["opgehaald"] + len(r["kop"]) - 1 for r in self.rijen)

    def einde(self):
        p = self.punten()
        drempel = [25, 50, 80] if self.n == 1 else [40, 80, 120]
        sterren = sum(1 for d in drempel if p >= d)
        regels = ["%d punten" % p,
                  "Opgehaald: %d   ·   Langste rij: %d" % (sum(r["opgehaald"] for r in self.rijen),
                                                             max(r["langste"] for r in self.rijen))]
        if self.n == 2:
            regels.append("Speler 1: %d   ·   Speler 2: %d" % tuple(r["opgehaald"] + len(r["kop"]) - 1 for r in self.rijen))
        self.spel.uitslag("carnaval", "Alaaf!", p, sterren, regels)

    # ---- tekenen
    def achter(self, s):
        steen = self.k((150, 120, 110)) if self.stijl != "retro" else (171, 82, 54)
        steen2 = self.k((170, 140, 125)) if self.stijl != "retro" else (95, 87, 79)
        s.fill(steen, (0, BOVEN, W, H - BOVEN))
        for y in range(RIJ):
            for x in range(KOL):
                if (x + y) % 2 == 0 or self.tegels[y][x]:
                    s.fill(steen2, (x * VAK + 1, BOVEN + y * VAK + 1, VAK - 2, VAK - 2))
        s.fill(self.k((60, 30, 90)) if self.stijl != "retro" else (29, 43, 83), (0, 0, W, BOVEN))
        for x, kl in self.slingers:
            yy = 62 + math.sin(x / 90 + self.t) * 4
            pygame.draw.polygon(s, self.k(kl), [(x, yy), (x + 30, yy), (x + 15, yy + 18)])

    def _poppetje(self, s, cx, cy, pak, rij_i=None, kop=False, stap=0.0):
        naam, kleur, accent = PAKKEN[pak] if pak is not None else ("prins", (230, 30, 40), (255, 220, 60))
        bob = math.sin(self.t * 10 + stap) * 3
        cy += bob
        pygame.draw.circle(s, self.k(kleur), (int(cx), int(cy + 6)), 15)
        pygame.draw.circle(s, (245, 210, 180), (int(cx), int(cy - 10)), 11)
        if naam == "piraat":
            pygame.draw.polygon(s, (30, 30, 30), [(cx - 14, cy - 15), (cx + 14, cy - 15), (cx, cy - 30)])
            pygame.draw.circle(s, (30, 30, 30), (int(cx + 4), int(cy - 11)), 3)
        elif naam == "clown":
            pygame.draw.circle(s, (240, 40, 40), (int(cx), int(cy - 8)), 4)
            pygame.draw.circle(s, self.k(accent), (int(cx - 9), int(cy - 20)), 6)
            pygame.draw.circle(s, self.k(accent), (int(cx + 9), int(cy - 20)), 6)
        elif naam == "prinses":
            pygame.draw.polygon(s, self.k(accent), [(cx - 8, cy - 18), (cx - 4, cy - 28), (cx, cy - 20), (cx + 4, cy - 28), (cx + 8, cy - 18)])
        elif naam == "kikker":
            pygame.draw.circle(s, self.k(kleur), (int(cx - 6), int(cy - 21)), 5)
            pygame.draw.circle(s, self.k(kleur), (int(cx + 6), int(cy - 21)), 5)
        elif naam == "cowboy":
            pygame.draw.ellipse(s, self.k(kleur), (cx - 16, cy - 22, 32, 8))
            pygame.draw.rect(s, self.k(kleur), (cx - 8, cy - 30, 16, 10), border_radius=3)
        elif naam == "boer":
            pygame.draw.rect(s, (230, 230, 230), (cx - 9, cy - 22, 18, 6))
        elif naam == "ridder":
            pygame.draw.rect(s, self.k(kleur), (cx - 11, cy - 22, 22, 14), border_radius=4)
        elif naam == "bij":
            for k in range(2):
                pygame.draw.line(s, (30, 30, 30), (cx - 12, cy + 2 + k * 8), (cx + 12, cy + 2 + k * 8), 3)
            pygame.draw.ellipse(s, (240, 240, 255), (cx + 8, cy - 8, 14, 10))
        elif naam == "prins":   # de kop van de rij: Prins Carnaval met steek en veer
            pygame.draw.ellipse(s, self.k(kleur), (cx - 15, cy - 26, 30, 12))
            pygame.draw.line(s, self.k(accent), (cx + 4, cy - 24), (cx + 14, cy - 38), 4)
            pygame.draw.rect(s, [(255, 255, 255), (90, 200, 255)][rij_i or 0], (cx - 12, cy + 12, 24, 6))
        pygame.draw.circle(s, (40, 30, 30), (int(cx - 4), int(cy - 11)), 2)
        pygame.draw.circle(s, (40, 30, 30), (int(cx + 4), int(cy - 11)), 2)

    def voor(self, s):
        for x, y, pak in self.dansers:
            cx, cy = x * VAK + VAK / 2, BOVEN + y * VAK + VAK / 2
            sprong = abs(math.sin(self.t * 4 + x)) * 6
            self._poppetje(s, cx, cy - sprong, pak, stap=x)
        for i, r in enumerate(self.rijen):
            if r["botsen"] > 0 and int(self.t * 12) % 2:
                continue
            # handjes op de schouders: een lijntje tussen iedereen
            pts = [(x * VAK + VAK / 2, BOVEN + y * VAK + VAK / 2) for x, y in r["kop"]]
            if len(pts) > 1:
                pygame.draw.lines(s, self.k((255, 230, 150)), False, pts, 4)
            for k in range(len(r["kop"]) - 1, -1, -1):
                x, y = pts[k]
                if k == 0:
                    self._poppetje(s, x, y, None, rij_i=i, kop=True, stap=0)
                else:
                    self._poppetje(s, x, y, r["pakken"][k - 1], stap=k * 0.8)
        for x, y, vx, vy, pak, t in self.losse:
            self._poppetje(s, x, y, pak, stap=t * 5)

    def effect(self, s):
        for x, y, vx, vy, kl, leven in self.confetti:
            pygame.draw.rect(s, kl, (x, y, 7, 4))
        for i, r in enumerate(self.rijen):
            x, y = r["kop"][0]
            if self.n == 2:
                from basis import tekst
                tekst(s, "1" if i == 0 else "2", (x * VAK + VAK // 2, BOVEN + y * VAK - 42), 22, (255, 255, 255), midden=True, vet=True)

    def balk(self):
        lengte = " + ".join(str(len(r["kop"])) for r in self.rijen)
        return ("Carnaval", "Punten: %d   ·   Rij: %s" % (self.punten(), lengte), "Tijd: %d" % max(0, math.ceil(self.tijd)))

    def uitleg_regels(self):
        r = ["Carnaval: de polonaise!",
             "Jij bent Prins Carnaval. Stuur met de pijltjes over het plein.",
             "Loop langs verklede mensen: ze dansen achter je aan in de rij.",
             "Pas op: bots je tegen de rand of tegen je eigen rij,",
             "dan valt de helft van de rij uit elkaar.",
             "Punten = iedereen die je ophaalde + hoe lang je rij aan het eind is."]
        if self.n == 2:
            r.append("Speler 2: W A S D.  Bots ook niet tegen elkaars rij!")
        return r
