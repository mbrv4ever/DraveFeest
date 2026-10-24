# -*- coding: utf-8 -*-
# DraveFeest - Koningsdag: koekhappen. De koek zwiept aan een touw; spring op het goede moment en hap!
# Drie happen = koek op. Elke nieuwe koek zwiept sneller.
# Copyright (C) 2026 Dravenlock (Roger & Claudio). Vrije software onder de GNU GPL v3.0.
import math
import random

import pygame

from basis import HDSpel, tekst, teken_kind, SPELER_TOETSEN, mix

W, H = 1280, 720
GROND = 640
OPHANG_Y = 120
TOUW = 300
VLAG_KLEUREN = [(255, 120, 30), (240, 240, 240), (30, 80, 200), (220, 30, 40)]


class Koningsdag(HDSpel):
    naam = "koningsdag"
    titel = "Koningsdag"
    speeltijd = 45

    def __init__(self, spel):
        super().__init__(spel)
        midden = [W // 2] if self.n == 1 else [W // 2 + 260, W // 2 - 260]   # speler 1 rechts, speler 2 links
        self.banen = []
        for i in range(self.n):
            self.banen.append(dict(ox=midden[i], x=float(midden[i]), r=1, stap=0.0, sprong=0.0, vy=0.0, koek=3,
                                   koeken=0, hoek=0.0, fase=random.random() * 6, snel=1.6, wijd=0.55, happen=0,
                                   punten=0, mis_t=0.0, hap_t=0.0, kruimels=[]))
        self.punten = 0
        self.vlaggen = [(x, random.choice(VLAG_KLEUREN)) for x in range(0, W + 60, 46)]

    def _koek_pos(self, b):
        a = b["wijd"] * math.sin(b["fase"])
        return (b["ox"] + math.sin(a) * TOUW, OPHANG_Y + math.cos(a) * TOUW), a

    def _mond(self, b, i):
        return (b["x"] + 6, GROND + 20 - i * 0 - b["sprong"] - 118)

    # ---- invoer
    def spel_toets(self, ev):
        for i, b in enumerate(self.banen):
            k = SPELER_TOETSEN[i]
            if ev.key in (k["op"], k["actie"]) and b["sprong"] <= 0:
                b["vy"] = 720
                b["sprong"] = 0.01
                self.spel.geluid.speel("stap")

    # ---- bijwerken
    def spel_update(self, dt):
        toetsen = pygame.key.get_pressed()
        for i, b in enumerate(self.banen):
            b["fase"] += dt * b["snel"]
            k = SPELER_TOETSEN[i]
            if self.klaar_t is None:
                d = (1 if toetsen[k["rechts"]] else 0) - (1 if toetsen[k["links"]] else 0)
                if d:
                    b["x"] = max(b["ox"] - 230, min(b["ox"] + 230, b["x"] + d * 260 * dt))
                    b["r"] = d
                    b["stap"] += dt * 10
            if b["sprong"] > 0:
                b["sprong"] += b["vy"] * dt
                b["vy"] -= 2000 * dt
                (kx, ky), _ = self._koek_pos(b)
                mx, my = self._mond(b, i)
                if b["koek"] > 0 and b["hap_t"] <= 0 and abs(mx - kx) < 42 and abs(my - (ky + 30)) < 40:
                    self._hap(b, kx, ky)
                if b["sprong"] <= 0:
                    b["sprong"] = 0
                    if b["hap_t"] <= 0 and b["mis_t"] <= 0:
                        b["mis_t"] = 0.3
            b["hap_t"] = max(0, b["hap_t"] - dt)
            b["mis_t"] = max(0, b["mis_t"] - dt)
            for c in b["kruimels"]:
                c[0] += c[2] * dt
                c[1] += c[3] * dt
                c[3] += 900 * dt
                c[4] -= dt
            b["kruimels"] = [c for c in b["kruimels"] if c[4] > 0]

    def _hap(self, b, kx, ky):
        b["koek"] -= 1
        b["happen"] += 1
        b["hap_t"] = 0.45
        pt = 1
        for _ in range(10):
            b["kruimels"].append([kx + random.uniform(-20, 20), ky + 50, random.uniform(-120, 120), random.uniform(-300, -60),
                                  random.uniform(0.5, 0.9)])
        if b["koek"] == 0:
            pt += 2
            b["koeken"] += 1
            self.zweef(kx, ky - 40, "Koek op! +3", (255, 200, 60), 1.2)
            self.spel.geluid.speel("ster")
            # nieuwe koek, sneller en wilder
            b["koek"] = 3
            b["snel"] = min(3.6, b["snel"] + 0.3)
            b["wijd"] = min(0.95, b["wijd"] + 0.06)
        else:
            self.zweef(kx, ky - 40, "Hap! +1", (255, 255, 255), 0.8)
            self.spel.geluid.speel("snoep")
        b["punten"] += pt
        self.punten += pt

    def einde(self):
        drempel = [10, 18, 26] if self.n == 1 else [16, 28, 40]
        sterren = sum(1 for d in drempel if self.punten >= d)
        koeken = sum(b["koeken"] for b in self.banen)
        happen = sum(b["happen"] for b in self.banen)
        regels = ["%d happen, %d hele koeken op!" % (happen, koeken), "%d punten" % self.punten]
        if self.n == 2:
            regels.append("Speler 1: %d   ·   Speler 2: %d" % (self.banen[0]["punten"], self.banen[1]["punten"]))
        self.spel.uitslag("koningsdag", "Leve de koning!", self.punten, sterren, regels)

    # ---- tekenen
    def achter(self, s):
        if self.stijl == "retro":   # effen retroblauw, anders wordt een verloop grijs
            s.fill((41, 173, 255), (0, 0, W, GROND))
        for y in (range(0, GROND, 4) if self.stijl != "retro" else ()):
            pygame.draw.rect(s, mix(self.k((90, 170, 250)), self.k((200, 230, 255)), y / GROND), (0, y, W, 4))
        pygame.draw.circle(s, self.k((255, 225, 100)), (110, 110), 46)
        # huizen in de straat
        x = -30
        for i in range(10):
            b = 150 + (i * 37) % 50
            h = 210 + (i * 53) % 90
            kl = self.k([(180, 90, 70), (150, 110, 90), (200, 150, 110), (130, 90, 80)][i % 4])
            pygame.draw.rect(s, kl, (x, GROND - h, b, h))
            pygame.draw.polygon(s, kl, [(x, GROND - h), (x + b // 2, GROND - h - 50), (x + b, GROND - h)])
            for rx in range(x + 18, x + b - 30, 46):
                for ry in range(GROND - h + 26, GROND - 40, 62):
                    pygame.draw.rect(s, self.k((210, 230, 250)), (rx, ry, 26, 36))
            x += b + 6

    def voor(self, s):
        pygame.draw.rect(s, self.k((150, 140, 130)), (0, GROND, W, H - GROND))
        pygame.draw.rect(s, self.k((180, 170, 160)), (0, GROND, W, 10))
        # vlaggetjeslijn
        for x, kl in self.vlaggen:
            y = 60 + math.sin(x / 140) * 16
            pygame.draw.polygon(s, self.k(kl), [(x, y), (x + 36, y), (x + 18, y + 38)])
        pygame.draw.lines(s, (80, 70, 60), False, [(x, 60 + math.sin(x / 140) * 16) for x, _ in self.vlaggen], 3)
        for i, b in enumerate(self.banen):
            ox = b["ox"]
            # houten paal-frame
            hout = self.k((150, 100, 55))
            pygame.draw.rect(s, hout, (ox - 250, OPHANG_Y - 16, 500, 18), border_radius=6)
            pygame.draw.rect(s, hout, (ox - 250, OPHANG_Y - 16, 18, GROND - OPHANG_Y + 16))
            pygame.draw.rect(s, hout, (ox + 232, OPHANG_Y - 16, 18, GROND - OPHANG_Y + 16))
            # touw + koek
            (kx, ky), a = self._koek_pos(b)
            pygame.draw.line(s, self.k((220, 200, 160)), (ox, OPHANG_Y), (kx, ky), 4)
            if b["koek"] > 0:
                hoogte = 26 * b["koek"]
                koek = pygame.Surface((70, 90), pygame.SRCALPHA)
                pygame.draw.rect(koek, self.k((160, 95, 40)), (5, 6, 60, hoogte + 6), border_radius=8)
                pygame.draw.rect(koek, self.k((200, 130, 60)), (11, 12, 48, hoogte - 6), border_radius=6)
                for c in range(4):
                    pygame.draw.circle(koek, self.k((120, 70, 30)), (20 + c * 10, 18 + (c % 2) * 10), 3)
                koek = pygame.transform.rotate(koek, math.degrees(-a))
                s.blit(koek, (kx - koek.get_width() / 2, ky - 6))
            # kind
            teken_kind(s, b["x"], GROND + 20 - b["sprong"], 1.0, self.k([(240, 130, 40), (60, 120, 220)][i]),
                       self.k([(240, 130, 40), (240, 240, 240)][i]), b["r"], b["stap"], lijn=False)
            if b["hap_t"] > 0:
                mx, my = self._mond(b, i)
                pygame.draw.circle(s, (60, 20, 20), (int(mx), int(my + 4)), 8)
            for c in b["kruimels"]:
                pygame.draw.circle(s, self.k((170, 110, 50)), (int(c[0]), int(c[1])), 5)

    def effect(self, s):
        for i, b in enumerate(self.banen):
            if b["mis_t"] > 0:
                tekst(s, "mis!", (int(b["x"]), GROND - 260), 30, (255, 150, 130), midden=True, vet=True)
            tekst(s, "Koek %d" % (b["koeken"] + 1), (b["ox"], OPHANG_Y + 8), 26, (255, 255, 255), midden=True, vet=True)

    def balk(self):
        return ("Koningsdag", "Punten: %d" % self.punten, "Tijd: %d" % max(0, math.ceil(self.tijd)))

    def uitleg_regels(self):
        r = ["Koningsdag: koekhappen",
             "De koek zwiept heen en weer aan een touw.",
             "Spring met pijl omhoog (of spatie) en hap in de koek!",
             "Met pijl links en rechts schuif je een stukje opzij.",
             "Drie happen = koek op (+3). De volgende koek zwiept sneller.",
             "Handen op je rug, hè!  ;-)"]
        if self.n == 2:
            r.append("Speler 2 (links): A en D = schuiven, W = springen")
        return r
