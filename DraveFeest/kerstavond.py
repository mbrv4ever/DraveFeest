# -*- coding: utf-8 -*-
# DraveFeest - Kerstavond: cadeautjes vangen met je slee.
# De kerstman vliegt over en laat cadeautjes vallen. Vang ze met je slee! Maar pas op voor de kolen.
# Copyright (C) 2026 Dravenlock (Roger & Claudio). Vrije software onder de GNU GPL v3.0.
import math
import random

import pygame

from basis import HDSpel, tekst, teken_kind, SPELER_TOETSEN, mix

W, H = 1280, 720
GROND = 640
SLEE_Y = GROND - 6            # onderkant van de slee
SLEE_B = 150                  # breedte van de slee
LINT = [(250, 220, 70), (255, 255, 255), (90, 200, 120), (230, 60, 70)]
PAPIER = [(220, 40, 50), (40, 120, 220), (60, 170, 90), (170, 70, 190), (240, 150, 40)]


class Kerstavond(HDSpel):
    naam = "kerstavond"
    titel = "Kerstavond"
    speeltijd = 60
    retro_licht = 0.0

    def __init__(self, spel):
        super().__init__(spel)
        start = [W // 2] if self.n == 1 else [W // 2 + 240, W // 2 - 240]
        self.sleeen = [dict(x=float(x), v=0.0, r=1, stap=0.0, schrik=0.0, punten=0, gevangen=0, wieb=0.0)
                       for x in start]
        self.vallend = []
        self.punten = 0
        self.kerstman = dict(x=-200.0, v=210.0, fase=0.0)
        self.drop_t = 0.6
        self.sneeuw = [[random.uniform(0, W), random.uniform(0, H), random.uniform(20, 60), random.uniform(1, 3)]
                       for _ in range(160)]
        self.sterren = [(random.randrange(W), random.randrange(GROND - 300)) for _ in range(70)]
        self.huizen = [(x, 120 + (x * 29) % 90) for x in range(-30, W + 80, 170)]
        self.spetters = []
        self.combo = [0, 0]

    # ---- cadeautjes en kolen
    def _laat_vallen(self):
        km = self.kerstman
        r = random.random()
        verloop = (self.speeltijd - self.tijd) / self.speeltijd       # 0 → 1 tijdens het spel
        if r < 0.08:
            soort = "ster"
        elif r < 0.30 + 0.12 * verloop:
            soort = "kool"
        else:
            soort = "cadeau"
        self.vallend.append(dict(
            soort=soort, x=km["x"] + random.uniform(-30, 30), y=150.0, vx=km["v"] * 0.25 + random.uniform(-40, 40),
            vy=random.uniform(40, 90), draai=random.uniform(0, 6.28), draaiv=random.uniform(-3, 3),
            papier=random.choice(PAPIER), lint=random.choice(LINT), b=random.choice((34, 40, 46))))

    # ---- invoer
    def spel_toets(self, ev):
        for i, sl in enumerate(self.sleeen):
            if ev.key == SPELER_TOETSEN[i]["actie"] and sl["schrik"] <= 0:
                sl["wieb"] = 0.25           # klein sprongetje met de slee
                self.spel.geluid.speel("stap")

    # ---- bijwerken
    def spel_update(self, dt):
        toetsen = pygame.key.get_pressed()
        for i, sl in enumerate(self.sleeen):
            k = SPELER_TOETSEN[i]
            sl["schrik"] = max(0.0, sl["schrik"] - dt)
            sl["wieb"] = max(0.0, sl["wieb"] - dt)
            d = 0
            if self.klaar_t is None and sl["schrik"] <= 0:
                d = (1 if toetsen[k["rechts"]] else 0) - (1 if toetsen[k["links"]] else 0)
            # een slee glijdt: versnellen en uitglijden op de sneeuw
            sl["v"] += d * 1900 * dt
            sl["v"] *= (0.86 if d == 0 else 0.93) ** (dt * 60)
            sl["v"] = max(-520, min(520, sl["v"]))
            sl["x"] += sl["v"] * dt
            if sl["x"] < SLEE_B / 2 + 10 or sl["x"] > W - SLEE_B / 2 - 10:
                sl["x"] = max(SLEE_B / 2 + 10, min(W - SLEE_B / 2 - 10, sl["x"]))
                sl["v"] *= -0.3
            if abs(sl["v"]) > 30:
                sl["r"] = 1 if sl["v"] > 0 else -1
                sl["stap"] += dt * 10
        # de kerstman vliegt heen en weer
        km = self.kerstman
        km["fase"] += dt
        km["x"] += km["v"] * dt
        if km["x"] > W + 220 and km["v"] > 0 or km["x"] < -220 and km["v"] < 0:
            km["v"] = -km["v"] * random.uniform(0.95, 1.15)
            km["v"] = max(-340, min(340, km["v"]))
        self.drop_t -= dt
        if self.drop_t <= 0 and -60 < km["x"] < W + 60 and self.klaar_t is None:
            self._laat_vallen()
            tempo = 0.85 - 0.35 * (self.speeltijd - self.tijd) / self.speeltijd
            self.drop_t = random.uniform(tempo * 0.6, tempo * 1.2) / (1.4 if self.n == 2 else 1.0)
        # vallen
        for c in self.vallend:
            c["vy"] += 330 * dt
            c["x"] += c["vx"] * dt
            c["y"] += c["vy"] * dt
            c["draai"] += c["draaiv"] * dt
            c["vx"] *= 0.99
            if c["x"] < 30 or c["x"] > W - 30:
                c["vx"] *= -1
                c["x"] = max(30, min(W - 30, c["x"]))
            if c["y"] > SLEE_Y - 60 and not c.get("weg"):
                for i, sl in enumerate(self.sleeen):
                    if abs(c["x"] - sl["x"]) < SLEE_B / 2 + 8 and c["y"] < SLEE_Y - 10:
                        self._vang(c, i)
                        break
            if c["y"] > GROND + 20 and not c.get("weg"):
                c["weg"] = True
                if c["soort"] != "kool":
                    for _ in range(8):
                        a = random.uniform(math.pi, math.tau)
                        self.spetters.append([c["x"], GROND, math.cos(a) * 120, math.sin(a) * 160, 0.6, (240, 245, 255)])
        self.vallend = [c for c in self.vallend if not c.get("weg")]
        for f in self.spetters:
            f[0] += f[2] * dt
            f[1] += f[3] * dt
            f[3] += 400 * dt
            f[4] -= dt
        self.spetters = [f for f in self.spetters if f[4] > 0]
        for sn in self.sneeuw:
            sn[1] += sn[2] * dt
            sn[0] += math.sin(self.t + sn[1] * 0.01) * 12 * dt
            if sn[1] > H:
                sn[1] = -5
                sn[0] = random.uniform(0, W)

    def _vang(self, c, i):
        sl = self.sleeen[i]
        c["weg"] = True
        if c["soort"] == "kool":
            sl["schrik"] = 1.0
            sl["v"] *= 0.2
            sl["punten"] = max(0, sl["punten"] - 2)
            self.punten = max(0, self.punten - 2)
            self.combo[i] = 0
            self.zweef(sl["x"], SLEE_Y - 130, "Kolen! -2", (200, 200, 200), 1.0)
            self.spel.geluid.speel("stap")
            for _ in range(10):
                a = random.uniform(math.pi, math.tau)
                self.spetters.append([c["x"], c["y"], math.cos(a) * 160, math.sin(a) * 200, 0.5, (60, 60, 66)])
            return
        self.combo[i] += 1
        extra = 1 if self.combo[i] >= 5 else 0
        sl["gevangen"] += 1
        if c["soort"] == "ster":
            n = 5 + extra
            self.zweef(c["x"], c["y"] - 50, "Kerstster! +%d" % n, (255, 220, 80), 1.0)
            self.spel.geluid.speel("ster")
        else:
            n = 1 + extra
            self.zweef(c["x"], c["y"] - 50, ("Cadeautje! +%d" % n) if not extra else ("Reeks! +%d" % n),
                       (255, 255, 255) if not extra else (150, 230, 255), 0.9)
            self.spel.geluid.speel("snoep")
        sl["punten"] += n
        self.punten += n
        for _ in range(12):
            a = random.random() * math.tau
            self.spetters.append([c["x"], c["y"], math.cos(a) * 170, math.sin(a) * 170 - 60, 0.6,
                                  (255, 220, 80) if c["soort"] == "ster" else c["lint"]])

    def einde(self):
        drempel = [20, 40, 60] if self.n == 1 else [30, 55, 80]
        sterren = sum(1 for d in drempel if self.punten >= d)
        gevangen = sum(s["gevangen"] for s in self.sleeen)
        regels = ["%d cadeautjes gevangen!" % gevangen, "%d punten" % self.punten]
        if self.n == 2:
            regels.append("Speler 1: %d   ·   Speler 2: %d" % (self.sleeen[0]["punten"], self.sleeen[1]["punten"]))
        self.spel.uitslag("kerstavond", "Fijne kerst!", self.punten, sterren, regels)

    # ---- tekenen
    def achter(self, s):
        if self.stijl == "retro":
            s.fill((0, 0, 40), (0, 0, W, GROND))
        else:
            for y in range(0, GROND, 4):
                pygame.draw.rect(s, mix(self.k((10, 18, 50)), self.k((40, 60, 110)), y / GROND), (0, y, W, 4))
        for x, y in self.sterren:
            s.set_at((x, y), (230, 235, 255))
        pygame.draw.circle(s, self.k((245, 245, 225)), (170, 110), 52)
        pygame.draw.circle(s, self.k((10, 18, 50)) if self.stijl != "retro" else (0, 0, 40), (192, 98), 46)
        # huisjes met warme ramen en sneeuw op het dak
        for x, h in self.huizen:
            muur = self.k((70, 50, 60)) if self.stijl != "retro" else (85, 0, 0)
            pygame.draw.rect(s, muur, (x, GROND - h, 140, h))
            pygame.draw.polygon(s, self.k((120, 40, 40)), [(x - 12, GROND - h), (x + 70, GROND - h - 60), (x + 152, GROND - h)])
            pygame.draw.polygon(s, (245, 248, 255), [(x - 12, GROND - h), (x + 70, GROND - h - 60), (x + 152, GROND - h),
                                                     (x + 140, GROND - h + 8), (x + 70, GROND - h - 48), (x, GROND - h + 8)])
            for rx in (x + 20, x + 90):
                pygame.draw.rect(s, self.k((255, 210, 110)), (rx, GROND - h + 30, 30, 32))
                pygame.draw.line(s, muur, (rx + 15, GROND - h + 30), (rx + 15, GROND - h + 61), 3)
            for k in range(7):     # lichtjes langs de dakgoot
                c = [(255, 70, 70), (255, 220, 70), (90, 200, 255), (120, 255, 140)][(k + int(self.t * 3) + x) % 4]
                pygame.draw.circle(s, c, (x + 8 + k * 21, GROND - h + 12), 4)
        # kerstboom
        bx = W - 150
        for i, (b, y) in enumerate(((180, GROND - 60), (140, GROND - 130), (100, GROND - 195))):
            pygame.draw.polygon(s, self.k((30, 110, 60)), [(bx - b // 2, y), (bx + b // 2, y), (bx, y - 90)])
        pygame.draw.rect(s, self.k((90, 60, 30)), (bx - 12, GROND - 60, 24, 60))
        ster_y = GROND - 290 + math.sin(self.t * 3) * 2
        self._ster(s, bx, ster_y, 18, (255, 220, 80))
        # de kerstman met zijn slee en rendier
        km = self.kerstman
        kx, ky = int(km["x"]), int(110 + math.sin(km["fase"] * 2) * 14)
        r = 1 if km["v"] > 0 else -1
        rx = kx + r * 120
        pygame.draw.ellipse(s, self.k((140, 90, 50)), (rx - 34, ky - 14, 68, 32))
        pygame.draw.circle(s, self.k((140, 90, 50)), (rx + r * 36, ky - 14), 14)
        pygame.draw.circle(s, (255, 40, 40), (rx + r * 48, ky - 14), 6)
        for p in (-20, 20):
            pygame.draw.line(s, self.k((110, 70, 40)), (rx + p, ky + 14), (rx + p + math.sin(self.t * 12 + p) * 8, ky + 36), 5)
        pygame.draw.line(s, self.k((200, 170, 90)), (kx + r * 40, ky), (rx - r * 30, ky), 3)
        pygame.draw.polygon(s, self.k((200, 30, 40)), [(kx - 60, ky - 10), (kx + 60, ky - 10), (kx + 50, ky + 26), (kx - 50, ky + 26)])
        pygame.draw.line(s, self.k((230, 190, 60)), (kx - 66, ky + 32), (kx + 66, ky + 32), 5)
        pygame.draw.rect(s, self.k((200, 30, 40)), (kx - 18, ky - 46, 36, 40), border_radius=10)
        pygame.draw.circle(s, (250, 220, 190), (kx, ky - 56), 14)
        pygame.draw.circle(s, (255, 255, 255), (kx, ky - 46), 12)
        pygame.draw.polygon(s, self.k((200, 30, 40)), [(kx - 14, ky - 64), (kx + 14, ky - 64), (kx + r * 22, ky - 84)])
        pygame.draw.circle(s, (255, 255, 255), (kx + r * 22, ky - 84), 5)
        pygame.draw.rect(s, self.k((60, 120, 210)), (kx - r * 44 - 14, ky - 34, 28, 26))
        pygame.draw.rect(s, self.k((60, 170, 90)), (kx - r * 22 - 10, ky - 30, 20, 22))

    def _ster(self, s, x, y, r, kleur):
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.45
            pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
        pygame.draw.polygon(s, self.k(kleur), pts)

    def _ding(self, s, c):
        x, y = int(c["x"]), int(c["y"])
        if c["soort"] == "ster":
            self._ster(s, x, y, 22, (255, 220, 80))
            return
        if c["soort"] == "kool":
            pygame.draw.circle(s, (34, 34, 38), (x, y), 16)
            pygame.draw.circle(s, (60, 60, 66), (x - 5, y - 5), 6)
            pygame.draw.circle(s, (24, 24, 28), (x + 6, y + 4), 7)
            return
        b = c["b"]
        dooos = pygame.Surface((b + 10, b + 18), pygame.SRCALPHA)
        pygame.draw.rect(dooos, self.k(c["papier"]), (5, 13, b, b), border_radius=4)
        pygame.draw.rect(dooos, c["lint"], (5 + b // 2 - 4, 13, 8, b))
        pygame.draw.rect(dooos, c["lint"], (5, 13 + b // 2 - 4, b, 8))
        pygame.draw.circle(dooos, c["lint"], (5 + b // 2 - 8, 9), 7, 3)
        pygame.draw.circle(dooos, c["lint"], (5 + b // 2 + 8, 9), 7, 3)
        dooos = pygame.transform.rotate(dooos, math.degrees(c["draai"]) % 360 * 0.15 - 25)
        s.blit(dooos, dooos.get_rect(center=(x, y)))

    def voor(self, s):
        pygame.draw.rect(s, self.k((235, 242, 255)), (0, GROND, W, H - GROND))
        pygame.draw.rect(s, self.k((210, 222, 245)), (0, GROND, W, 8))
        for c in self.vallend:
            self._ding(s, c)
        for i, sl in enumerate(self.sleeen):
            beef = math.sin(self.t * 40) * 4 if sl["schrik"] > 0 else 0
            hop = -18 * math.sin(math.pi * (sl["wieb"] / 0.25)) if sl["wieb"] > 0 else 0
            x, y = int(sl["x"] + beef), int(SLEE_Y + hop)
            hout = self.k([(170, 40, 40), (40, 90, 170)][i])
            # kind op de slee, verkleed als elf en als sneeuwpop
            jas = [(40, 150, 70), (240, 240, 245)][i]
            muts = [(200, 30, 40), (30, 30, 40)][i]
            teken_kind(s, x - sl["r"] * 30, y - 34, 0.8, self.k(jas), self.k(muts), sl["r"], sl["stap"], lijn=False)
            pygame.draw.rect(s, hout, (x - SLEE_B // 2, y - 40, SLEE_B, 30), border_radius=8)
            pygame.draw.rect(s, mix(hout, (255, 255, 255), 0.25), (x - SLEE_B // 2 + 6, y - 36, SLEE_B - 12, 8), border_radius=4)
            pygame.draw.line(s, self.k((200, 170, 80)), (x - SLEE_B // 2, y - 2), (x + SLEE_B // 2, y - 2), 5)
            voor_x = x + sl["r"] * SLEE_B // 2
            pygame.draw.arc(s, self.k((200, 170, 80)), (voor_x - 16, y - 34, 32, 34),
                            -math.pi / 2 if sl["r"] > 0 else math.pi / 2, math.pi / 2 if sl["r"] > 0 else 3 * math.pi / 2, 5)
            for px in (x - 40, x + 40):
                pygame.draw.line(s, self.k((200, 170, 80)), (px, y - 10), (px, y - 2), 4)
        for f in self.spetters:
            pygame.draw.circle(s, f[5], (int(f[0]), int(f[1])), 4)
        for sn in self.sneeuw:
            pygame.draw.circle(s, (255, 255, 255), (int(sn[0]), int(sn[1])), int(sn[3]))

    def effect(self, s):
        for i, sl in enumerate(self.sleeen):
            if sl["schrik"] > 0:
                tekst(s, "Bah!", (int(sl["x"]), SLEE_Y - 190), 34, (220, 220, 230), midden=True, vet=True)
            elif self.combo[i] >= 5:
                tekst(s, "Reeks x%d" % self.combo[i], (int(sl["x"]), SLEE_Y + 30), 30, (20, 60, 140), midden=True, vet=True)

    def balk(self):
        return ("Kerstavond", "Punten: %d" % self.punten, "Tijd: %d" % max(0, math.ceil(self.tijd)))

    def uitleg_regels(self):
        r = ["Kerstavond: cadeautjes vangen",
             "De kerstman vliegt over en laat cadeautjes vallen.",
             "Rij met je slee (pijltjes links en rechts) en vang ze op: +1",
             "Een gouden kerstster levert +5 op.",
             "Pas op voor de kolen: -2, en je slee staat even stil.",
             "Vang er 5 achter elkaar zonder kolen: elk cadeautje +1 extra.",
             "Je slee glijdt door op de sneeuw: rem op tijd!"]
        if self.n == 2:
            r.append("Speler 2 (links): A en D = rijden")
        return r
