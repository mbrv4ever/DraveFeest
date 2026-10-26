# -*- coding: utf-8 -*-
# DraveFeest - Valentijn: Cupido. Zweef op je wolkje en schiet met je boog op de hartjes.
# Twee keer achter elkaar dezelfde kleur = een paartje (bonus). Niet op de gebroken grijze hartjes schieten!
# Copyright (C) 2026 Dravenlock (Roger & Claudio). Vrije software onder de GNU GPL v3.0.
import math
import random

import pygame

from basis import HDSpel, tekst, SPELER_TOETSEN, mix

W, H = 1280, 720
WOLK_Y = 640
SOORTEN = [("rood", (235, 50, 80), 1, 0.42), ("roze", (255, 130, 180), 1, 0.36), ("paars", (170, 90, 230), 1, 0.12),
           ("goud", (255, 205, 50), 5, 0.04), ("grijs", (130, 130, 145), -2, 0.06)]


def hart(s, x, y, r, kleur, gebroken=False):
    pygame.draw.circle(s, kleur, (int(x - r * 0.5), int(y - r * 0.2)), int(r * 0.55))
    pygame.draw.circle(s, kleur, (int(x + r * 0.5), int(y - r * 0.2)), int(r * 0.55))
    pygame.draw.polygon(s, kleur, [(x - r * 1.03, y), (x + r * 1.03, y), (x, y + r * 1.05)])
    pygame.draw.circle(s, (255, 255, 255), (int(x - r * 0.55), int(y - r * 0.35)), max(2, int(r * 0.16)))
    if gebroken:
        pygame.draw.lines(s, (60, 60, 70), False, [(x, y - r * 0.5), (x - r * 0.2, y - r * 0.1), (x + r * 0.15, y + r * 0.25),
                                                   (x - r * 0.05, y + r * 0.7)], max(2, int(r * 0.12)))


class Valentijn(HDSpel):
    naam = "valentijn"
    titel = "Valentijn"
    speeltijd = 60

    def __init__(self, spel):
        super().__init__(spel)
        start = [W // 2] if self.n == 1 else [W // 2 + 200, W // 2 - 200]
        self.cupidos = [dict(x=float(x), r=1, herlaad=0.0, vorige=None, punten=0) for x in start]
        self.harten = []        # dict(x, y, vx, vy, soort, kleur, waarde, r, fase)
        self.pijlen = []        # [x, y, speler]
        self.splinters = []
        self.punten = 0
        self.paartjes = 0
        self.raak = 0
        self.wacht = 0.5
        rnd = random.Random(2)
        self.wolken = [[rnd.uniform(0, W), rnd.uniform(90, 480), rnd.uniform(70, 140), rnd.uniform(8, 25)] for _ in range(9)]

    def spel_toets(self, ev):
        for i, c in enumerate(self.cupidos):
            if ev.key in (SPELER_TOETSEN[i]["actie"], SPELER_TOETSEN[i]["op"]) and c["herlaad"] <= 0:
                self.pijlen.append([c["x"] + 6, WOLK_Y - 130, i])
                c["herlaad"] = 0.32
                self.spel.geluid.speel("stap")

    def _nieuw_hart(self):
        k = random.random()
        som = 0
        for naam, kleur, waarde, kans in SOORTEN:
            som += kans
            if k <= som:
                break
        links = random.random() < 0.5
        r = random.uniform(24, 36) if naam != "goud" else 22
        snel = random.uniform(110, 190) * (1.6 if naam == "goud" else 1) * (1 + (self.speeltijd - self.tijd) / 90)
        self.harten.append(dict(x=-40 if links else W + 40, y=random.uniform(110, 460), vx=snel if links else -snel,
                                vy=0.0, soort=naam, kleur=kleur, waarde=waarde, r=r, fase=random.uniform(0, 6)))

    def spel_update(self, dt):
        toetsen = pygame.key.get_pressed()
        for i, c in enumerate(self.cupidos):
            c["herlaad"] = max(0, c["herlaad"] - dt)
            if self.klaar_t is None:
                k = SPELER_TOETSEN[i]
                d = (1 if toetsen[k["rechts"]] else 0) - (1 if toetsen[k["links"]] else 0)
                if d:
                    c["x"] = max(70, min(W - 70, c["x"] + d * 420 * dt))
                    c["r"] = d
        if self.klaar_t is None:
            self.wacht -= dt
            if self.wacht <= 0:
                self.wacht = random.uniform(0.45, 0.95) / (1 + (self.speeltijd - self.tijd) / 80)
                self._nieuw_hart()
        for h in self.harten:
            h["x"] += h["vx"] * dt
            h["fase"] += dt * 3
            h["y"] += math.sin(h["fase"]) * 40 * dt
        self.harten = [h for h in self.harten if -80 < h["x"] < W + 80]
        for p in self.pijlen:
            p[1] -= 900 * dt
        for p in list(self.pijlen):
            for h in list(self.harten):
                if abs(p[0] - h["x"]) < h["r"] + 6 and abs(p[1] - h["y"]) < h["r"] + 10:
                    self._raak(p, h)
                    break
        self.pijlen = [p for p in self.pijlen if p[1] > 40 and not (len(p) > 3)]
        for sp in self.splinters:
            sp[0] += sp[2] * dt
            sp[1] += sp[3] * dt
            sp[3] += 600 * dt
            sp[5] -= dt
        self.splinters = [sp for sp in self.splinters if sp[5] > 0]
        for w in self.wolken:
            w[0] = (w[0] + w[3] * dt) % (W + 300)

    def _raak(self, p, h):
        p.append("weg")
        self.harten.remove(h)
        c = self.cupidos[p[2]]
        pt = h["waarde"]
        tekstje, kl = ("+%d" % pt, (255, 255, 255)) if pt > 0 else ("Au! %d" % pt, (200, 200, 210))
        if h["soort"] == "goud":
            tekstje, kl = "Gouden hart! +5", (255, 220, 80)
            self.spel.geluid.speel("ster")
        elif pt < 0:
            self.spel.geluid.speel("fout")
            c["vorige"] = None
        else:
            if c["vorige"] == h["soort"]:
                pt += 2
                self.paartjes += 1
                tekstje, kl = "Paartje! +3", (255, 160, 210)
                c["vorige"] = None
                self.spel.geluid.speel("goed")
            else:
                c["vorige"] = h["soort"]
                self.spel.geluid.speel("snoep")
            self.raak += 1
        self.punten += pt
        c["punten"] += pt
        self.zweef(h["x"], h["y"] - 40, tekstje, kl, 0.9)
        for _ in range(14):
            a = random.uniform(0, 2 * math.pi)
            v = random.uniform(80, 260)
            self.splinters.append([h["x"], h["y"], math.cos(a) * v, math.sin(a) * v - 120, h["kleur"], random.uniform(0.5, 0.9)])

    def einde(self):
        drempel = [30, 60, 90] if self.n == 1 else [45, 85, 125]
        sterren = sum(1 for d in drempel if self.punten >= d)
        regels = ["%d punten  ·  %d hartjes geraakt" % (self.punten, self.raak), "%d paartjes gemaakt" % self.paartjes]
        if self.n == 2:
            regels.append("Speler 1: %d   ·   Speler 2: %d" % (self.cupidos[0]["punten"], self.cupidos[1]["punten"]))
        self.spel.uitslag("valentijn", "Fijne Valentijn!", self.punten, sterren, regels)

    # ---- tekenen
    def achter(self, s):
        if self.stijl == "retro":
            s.fill((255, 119, 168))
        else:
            for y in range(0, H, 4):
                pygame.draw.rect(s, mix(self.k((255, 170, 200)), self.k((255, 225, 235)), y / H), (0, y, W, 4))
        for x, y, b, _ in self.wolken:
            xx = x - 150
            for dx, dy, r in ((0, 0, b * 0.5), (b * 0.45, -b * 0.18, b * 0.42), (-b * 0.45, b * 0.05, b * 0.36)):
                pygame.draw.circle(s, (255, 255, 255) if self.stijl != "retro" else (255, 241, 232),
                                   (int(xx + dx), int(y + dy)), int(r))

    def voor(self, s):
        for h in self.harten:
            hart(s, h["x"], h["y"], h["r"], self.k(h["kleur"]), h["soort"] == "grijs")
            if h["soort"] == "goud":
                for k in range(4):
                    a = self.t * 3 + k * math.pi / 2
                    pygame.draw.circle(s, (255, 255, 200), (int(h["x"] + math.cos(a) * 40), int(h["y"] + math.sin(a) * 40)), 4)
        for x, y, i in self.pijlen:
            pygame.draw.line(s, self.k((150, 100, 60)), (x, y), (x, y + 46), 4)
            pygame.draw.polygon(s, self.k((200, 200, 210)), [(x, y - 12), (x - 7, y + 2), (x + 7, y + 2)])
            pygame.draw.polygon(s, self.k((235, 60, 90)), [(x, y + 36), (x - 9, y + 50), (x, y + 44), (x + 9, y + 50)])
        for i, c in enumerate(self.cupidos):
            self._cupido(s, c["x"], WOLK_Y, i, c)

    def _cupido(self, s, x, y, i, c):
        # wolkje
        for dx, dy, r in ((-50, 0, 34), (0, -12, 44), (50, 0, 34), (-20, 14, 30), (24, 14, 30)):
            pygame.draw.circle(s, (255, 255, 255), (int(x + dx), int(y + dy)), r)
        huid = (250, 215, 190)
        bob = math.sin(self.t * 3 + i) * 4
        # vleugeltjes
        for z in (-1, 1):
            pygame.draw.ellipse(s, (255, 255, 255), (x + z * 22 - 22 + z * 6, y - 120 + bob, 44, 28))
        pygame.draw.ellipse(s, huid, (x - 22, y - 96 + bob, 44, 56))
        pygame.draw.rect(s, self.k([(255, 130, 180), (140, 200, 255)][i]), (x - 22, y - 62 + bob, 44, 20), border_radius=8)
        pygame.draw.circle(s, huid, (int(x), int(y - 118 + bob)), 24)
        pygame.draw.circle(s, self.k((255, 210, 90)), (int(x - 8), int(y - 138 + bob)), 12)
        pygame.draw.circle(s, self.k((255, 210, 90)), (int(x + 10), int(y - 140 + bob)), 11)
        pygame.draw.circle(s, (40, 30, 30), (int(x + 7), int(y - 120 + bob)), 3)
        pygame.draw.circle(s, (40, 30, 30), (int(x - 7), int(y - 120 + bob)), 3)
        pygame.draw.arc(s, (200, 80, 90), (x - 8, y - 114 + bob, 16, 10), math.pi, 2 * math.pi, 2)
        # boog
        pygame.draw.arc(s, self.k((160, 100, 50)), (x - 4, y - 150 + bob, 40, 80), -math.pi / 2, math.pi / 2, 5)
        pygame.draw.line(s, (240, 240, 240), (x + 16, y - 150 + bob), (x + 16, y - 70 + bob), 2)
        if c["herlaad"] <= 0:
            pygame.draw.line(s, self.k((150, 100, 60)), (x + 6, y - 150 + bob), (x + 6, y - 104 + bob), 4)

    def effect(self, s):
        for x, y, vx, vy, kl, leven in self.splinters:
            hart(s, x, y, 6, self.k(kl))
        for i, c in enumerate(self.cupidos):
            if c["vorige"]:
                kleur = next(k for n, k, _, _ in SOORTEN if n == c["vorige"])
                tekst(s, "zoek een", (int(c["x"]), WOLK_Y + 36), 20, (120, 40, 80), midden=True, vet=True, schaduw=False)
                hart(s, c["x"] + 58, WOLK_Y + 50, 10, self.k(kleur))

    def balk(self):
        return ("Valentijn", "Punten: %d" % self.punten, "Tijd: %d" % max(0, math.ceil(self.tijd)))

    def uitleg_regels(self):
        r = ["Valentijn: Cupido",
             "Zweef op je wolkje met pijl links en rechts.",
             "Schiet met spatie (of pijl omhoog) een pijl op de hartjes.",
             "Twee keer achter elkaar dezelfde kleur = een paartje: +3!",
             "Gouden hart = 5 punten.  Gebroken grijs hart: niet raken (-2)!"]
        if self.n == 2:
            r.append("Speler 2: A en D = zweven, E of W = schieten")
        return r
