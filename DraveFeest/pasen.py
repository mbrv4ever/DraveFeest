# -*- coding: utf-8 -*-
# DraveFeest - Pasen: eieren zoeken in de tuin. Kijk achter struiken, bloemen en meer.
# De paashaas huppelt soms langs en verstopt stiekem een nieuw ei. Er is ook een gouden ei!
# Copyright (C) 2026 Dravenlock (Roger & Claudio). Vrije software onder de GNU GPL v3.0.
import math
import random

import pygame

from basis import HDSpel, tekst, teken_kind, SPELER_TOETSEN, mix

W, H = 1280, 720
GROND = 600
SOORTEN = ["struik", "bloemen", "tulpen", "gieter", "kruiwagen", "boomstronk", "vogelhuisje", "struik", "bloemen",
           "pot"]
EI_KLEUREN = [(255, 120, 150), (120, 200, 255), (255, 220, 90), (150, 230, 130), (200, 140, 255), (255, 160, 90)]


class Pasen(HDSpel):
    naam = "pasen"
    titel = "Pasen"
    speeltijd = 75

    def __init__(self, spel):
        super().__init__(spel)
        rnd = random.Random()
        self.plekken = []
        x = 260
        for i in range(20):
            self.plekken.append(dict(x=x, soort=rnd.choice(SOORTEN), ei=None, gezocht=False, schud=0.0, wiebel=rnd.random() * 9))
            x += rnd.randint(150, 220)
        self.lengte = x + 200
        for p in rnd.sample(self.plekken, 12):
            p["ei"] = rnd.choice(EI_KLEUREN)
        rnd.choice([p for p in self.plekken if p["ei"]])["ei"] = "goud"
        self.kids = [dict(x=120.0 - i * 60, r=1, stap=0.0, zoekt=0.0, plek=None) for i in range(self.n)]
        self.eieren = 0
        self.punten = 0
        self.gouden = False
        self.cam = 0.0
        self.vliegend = []          # eieren die uit de struik springen [x, y, vx, vy, kleur, t]
        self.haas = None            # dict(x, doel, richting, t)
        self.haas_wacht = rnd.uniform(9, 13)
        self.wolken = [(rnd.randint(0, self.lengte), rnd.randint(70, 220), rnd.randint(60, 120)) for _ in range(12)]
        self.vlinders = [[rnd.uniform(0, self.lengte), rnd.uniform(200, 450), rnd.random() * 6] for _ in range(8)]

    # ---- invoer
    def spel_toets(self, ev):
        for i, kid in enumerate(self.kids):
            k = SPELER_TOETSEN[i]
            if ev.key in (k["op"], k["actie"]) and kid["zoekt"] <= 0:
                p = self._plek_bij(kid["x"])
                if p and not p["gezocht"]:
                    kid["zoekt"] = 0.5
                    kid["plek"] = p
                    p["schud"] = 0.5
                    self.spel.geluid.speel("stap")
                elif p:
                    self.zweef(p["x"] - self.cam, GROND - 170, "Hier heb je al gekeken", (220, 220, 230), 0.8)

    def _plek_bij(self, x):
        beste = None
        for p in self.plekken:
            if abs(p["x"] - x) < 60 and (beste is None or abs(p["x"] - x) < abs(beste["x"] - x)):
                beste = p
        return beste

    def _gevonden(self, p):
        p["gezocht"] = True
        if p["ei"]:
            goud = p["ei"] == "goud"
            kleur = (255, 205, 40) if goud else p["ei"]
            self.vliegend.append([p["x"], GROND - 60, random.uniform(-60, 60), -520, kleur, 0.0, goud])
            n = 5 if goud else 1
            self.eieren += 1
            self.punten += n
            if goud:
                self.gouden = True
                self.zweef(p["x"] - self.cam, GROND - 200, "GOUDEN EI! +5", (255, 220, 60), 1.4)
                self.spel.geluid.speel("ster")
            else:
                self.zweef(p["x"] - self.cam, GROND - 200, "Een ei! +1", (255, 255, 255), 0.9)
                self.spel.geluid.speel("snoep")
            p["ei"] = None
        else:
            self.zweef(p["x"] - self.cam, GROND - 200, "Hier niet...", (200, 200, 210), 0.8)
            self.spel.geluid.speel("plof")

    # ---- bijwerken
    def spel_update(self, dt):
        toetsen = pygame.key.get_pressed()
        for i, kid in enumerate(self.kids):
            if kid["zoekt"] > 0:
                kid["zoekt"] -= dt
                if kid["zoekt"] <= 0 and kid["plek"]:
                    self._gevonden(kid["plek"])
                    kid["plek"] = None
                continue
            if self.klaar_t is not None:
                continue
            k = SPELER_TOETSEN[i]
            d = (1 if toetsen[k["rechts"]] else 0) - (1 if toetsen[k["links"]] else 0)
            if d:
                kid["x"] = max(60, min(self.lengte - 60, kid["x"] + d * 300 * dt))
                kid["r"] = d
                kid["stap"] += dt * 10
        doel = sum(k["x"] for k in self.kids) / self.n - W * 0.45
        self.cam += (max(0, min(self.lengte - W, doel)) - self.cam) * min(1, dt * 4)
        for p in self.plekken:
            p["schud"] = max(0, p["schud"] - dt)
        for e in self.vliegend:
            e[5] += dt
            e[0] += e[2] * dt
            e[1] += e[3] * dt
            e[3] += 1300 * dt
        self.vliegend = [e for e in self.vliegend if e[5] < 0.8]
        # de paashaas
        if self.haas is None and self.klaar_t is None:
            self.haas_wacht -= dt
            if self.haas_wacht <= 0:
                kandidaten = [p for p in self.plekken if p["gezocht"] and not p["ei"]]
                if kandidaten:
                    doel = random.choice(kandidaten)
                    start = self.cam - 80 if random.random() < 0.5 else self.cam + W + 80
                    self.haas = dict(x=start, doel=doel, r=1 if doel["x"] > start else -1, t=0.0, terug=False)
                self.haas_wacht = random.uniform(7, 11)
        elif self.haas:
            hs = self.haas
            hs["t"] += dt
            hs["x"] += hs["r"] * 330 * dt
            if not hs["terug"] and (hs["x"] - hs["doel"]["x"]) * hs["r"] >= 0:
                hs["doel"]["ei"] = random.choice(EI_KLEUREN)
                hs["doel"]["gezocht"] = False
                hs["doel"]["schud"] = 0.4
                hs["terug"] = True
                self.zweef(hs["doel"]["x"] - self.cam, GROND - 230, "De paashaas verstopte een ei!", (255, 230, 150), 1.4)
            if hs["terug"] and (hs["x"] < self.cam - 150 or hs["x"] > self.cam + W + 150):
                self.haas = None
        for v in self.vlinders:
            v[0] += math.sin(self.t * 0.7 + v[2]) * 40 * dt
            v[1] += math.cos(self.t * 1.3 + v[2]) * 30 * dt

    def einde(self):
        drempel = [8, 14, 20] if self.n == 1 else [12, 20, 28]
        sterren = sum(1 for d in drempel if self.punten >= d)
        regels = ["Je vond %d eieren: %d punten!" % (self.eieren, self.punten)]
        regels.append("Met het gouden ei!" if self.gouden else "Het gouden ei bleef verstopt...")
        self.spel.uitslag("pasen", "Vrolijk Pasen!", self.punten, sterren, regels)

    # ---- tekenen
    def achter(self, s):
        if self.stijl == "retro":   # effen retroblauw, anders wordt een verloop grijs
            s.fill((41, 173, 255), (0, 0, W, GROND))
        for y in (range(0, GROND, 4) if self.stijl != "retro" else ()):
            pygame.draw.rect(s, mix(self.k((110, 180, 245)), self.k((205, 235, 255)), y / GROND), (0, y, W, 4))
        pygame.draw.circle(s, self.k((255, 230, 120)), (1120, 100), 50)
        for x, y, b in self.wolken:
            xx = (x - self.cam * 0.2) % (self.lengte) - 100
            if -200 < xx < W + 200:
                for dx, dy, r in ((0, 0, b * 0.5), (b * 0.45, -b * 0.15, b * 0.4), (-b * 0.45, b * 0.05, b * 0.35)):
                    pygame.draw.circle(s, (255, 255, 255), (int(xx + dx), int(y + dy)), int(r))
        # heuvels ver weg
        pts = [(-10, GROND - 60)]
        for i in range(0, 40):
            xx = i * 120 - (self.cam * 0.35) % 120
            pts.append((xx, GROND - 110 - 40 * math.sin(i * 1.3)))
        pts.append((W + 10, GROND - 60))
        pygame.draw.polygon(s, self.k((140, 200, 120)), pts + [(W + 10, GROND), (-10, GROND)])

    def voor(self, s):
        # gras en hek
        pygame.draw.rect(s, self.k((100, 175, 80)), (0, GROND - 20, W, H - GROND + 20))
        for x in range(-int(self.cam) % 60 - 60, W + 60, 60):
            pygame.draw.rect(s, self.k((240, 235, 220)), (x, GROND - 120, 14, 100))
            pygame.draw.polygon(s, self.k((240, 235, 220)), [(x, GROND - 120), (x + 7, GROND - 132), (x + 14, GROND - 120)])
        pygame.draw.rect(s, self.k((240, 235, 220)), (0, GROND - 100, W, 10))
        pygame.draw.rect(s, self.k((240, 235, 220)), (0, GROND - 55, W, 10))
        for p in self.plekken:
            x = p["x"] - self.cam
            if -150 < x < W + 150:
                self._teken_plek(s, p, x)
        if self.haas:
            self._teken_haas(s, self.haas["x"] - self.cam, GROND + 10, self.haas["r"])
        for i, kid in enumerate(self.kids):
            x = kid["x"] - self.cam
            bukt = 10 if kid["zoekt"] > 0 else 0
            teken_kind(s, x, GROND + 80 - i * 14 + bukt, 0.85, self.k([(70, 110, 200), (220, 120, 50)][i]),
                       self.k([(200, 40, 50), (40, 160, 90)][i]), kid["r"], kid["stap"], lijn=False)
            # mandje
            mx = x + 30 * kid["r"]
            pygame.draw.ellipse(s, self.k((170, 120, 60)), (mx - 22, GROND + 0 - i * 14, 44, 30))
            pygame.draw.arc(s, self.k((140, 95, 45)), (mx - 18, GROND - 26 - i * 14, 36, 40), 0, math.pi, 4)
        for x, y, vx, vy, kl, t, goud in self.vliegend:
            self._ei(s, x - self.cam, y, kl, 1.2)

    def effect(self, s):
        for v in self.vlinders:
            x = v[0] - self.cam
            if -20 < x < W + 20:
                vl = abs(math.sin(self.t * 12 + v[2])) * 12
                pygame.draw.ellipse(s, self.k((255, 170, 220)), (x - 14, v[1] - vl / 2, 14, vl + 2))
                pygame.draw.ellipse(s, self.k((255, 170, 220)), (x, v[1] - vl / 2, 14, vl + 2))
        for i, kid in enumerate(self.kids):
            p = self._plek_bij(kid["x"])
            if p and not p["gezocht"] and kid["zoekt"] <= 0 and self.klaar_t is None:
                tekst(s, "Pijl omhoog = kijken" if i == 0 else "W = kijken", (int(p["x"] - self.cam), GROND - 190 - i * 34),
                      24, (255, 255, 255), midden=True, vet=True)

    def _ei(self, s, x, y, kleur, f=1.0):
        w, h = 26 * f, 34 * f
        pygame.draw.ellipse(s, kleur, (x - w / 2, y - h / 2, w, h))
        pygame.draw.line(s, (255, 255, 255), (x - w / 2 + 3, y), (x + w / 2 - 3, y), 3)
        pygame.draw.circle(s, (255, 255, 255), (int(x - 4 * f), int(y - 8 * f)), max(2, int(3 * f)))

    def _teken_plek(self, s, p, x):
        sch = math.sin(self.t * 40) * 6 if p["schud"] > 0 else 0
        # een verstopt ei wiebelt heel soms een beetje: een kleine hint
        if p["ei"] and not p["gezocht"] and (self.t + p["wiebel"]) % 9 < 0.35:
            sch = math.sin(self.t * 30) * 3
        x += sch
        g = GROND + 10
        soort = p["soort"]
        if soort == "struik":
            for dx, dy, r in ((-40, -30, 42), (30, -34, 40), (0, -62, 46)):
                pygame.draw.circle(s, self.k((50, 140, 60)), (int(x + dx), int(g + dy)), r)
            for dx, dy in ((-20, -60), (24, -40), (-44, -30)):
                pygame.draw.circle(s, self.k((80, 170, 80)), (int(x + dx), int(g + dy)), 12)
        elif soort == "bloemen":
            pygame.draw.ellipse(s, self.k((60, 150, 60)), (x - 60, g - 40, 120, 50))
            for k in range(7):
                bx, by = x - 48 + k * 16, g - 46 - (k % 3) * 12
                kl = self.k([(255, 120, 150), (255, 230, 90), (200, 140, 255), (255, 255, 255)][k % 4])
                for a in range(5):
                    pygame.draw.circle(s, kl, (int(bx + math.cos(a * 1.256) * 7), int(by + math.sin(a * 1.256) * 7)), 6)
                pygame.draw.circle(s, self.k((255, 200, 60)), (int(bx), int(by)), 4)
        elif soort == "tulpen":
            for k in range(5):
                bx = x - 44 + k * 22
                pygame.draw.line(s, self.k((60, 150, 60)), (bx, g), (bx, g - 70 - (k % 2) * 14), 5)
                pygame.draw.ellipse(s, self.k([(230, 50, 70), (255, 190, 40), (240, 120, 200)][k % 3]),
                                    (bx - 11, g - 96 - (k % 2) * 14, 22, 30))
            pygame.draw.ellipse(s, self.k((90, 160, 70)), (x - 60, g - 26, 120, 34))
        elif soort == "gieter":
            pygame.draw.rect(s, self.k((90, 160, 200)), (x - 34, g - 70, 64, 64), border_radius=10)
            pygame.draw.line(s, self.k((90, 160, 200)), (x + 26, g - 50), (x + 64, g - 86), 9)
            pygame.draw.arc(s, self.k((70, 130, 170)), (x - 30, g - 104, 56, 60), 0, math.pi, 8)
        elif soort == "kruiwagen":
            pygame.draw.polygon(s, self.k((200, 70, 60)), [(x - 66, g - 76), (x + 50, g - 76), (x + 30, g - 30), (x - 50, g - 30)])
            pygame.draw.circle(s, self.k((50, 50, 60)), (int(x + 34), int(g - 18)), 18)
            pygame.draw.line(s, self.k((120, 80, 50)), (x - 60, g - 50), (x - 100, g - 30), 7)
        elif soort == "boomstronk":
            pygame.draw.rect(s, self.k((130, 90, 55)), (x - 40, g - 76, 80, 76), border_radius=8)
            pygame.draw.ellipse(s, self.k((200, 160, 110)), (x - 40, g - 90, 80, 30))
            pygame.draw.ellipse(s, self.k((160, 120, 80)), (x - 22, g - 82, 44, 14), 3)
        elif soort == "vogelhuisje":
            pygame.draw.rect(s, self.k((120, 85, 55)), (x - 6, g - 130, 12, 130))
            pygame.draw.rect(s, self.k((240, 200, 120)), (x - 36, g - 190, 72, 64), border_radius=6)
            pygame.draw.polygon(s, self.k((200, 70, 60)), [(x - 46, g - 186), (x, g - 226), (x + 46, g - 186)])
            pygame.draw.circle(s, (60, 40, 30), (int(x), int(g - 160)), 12)
        elif soort == "pot":
            pygame.draw.polygon(s, self.k((210, 110, 60)), [(x - 40, g - 70), (x + 40, g - 70), (x + 30, g), (x - 30, g)])
            pygame.draw.rect(s, self.k((230, 130, 70)), (x - 46, g - 80, 92, 16), border_radius=5)
            for k in range(3):
                pygame.draw.circle(s, self.k((60, 150, 60)), (int(x - 20 + k * 20), int(g - 96)), 18)
        if p["gezocht"]:
            pygame.draw.circle(s, (255, 255, 255), (int(x), int(g - 130)), 6)   # al bekeken: wit stipje

    def _teken_haas(self, s, x, y, r):
        sp = abs(math.sin(self.t * 12)) * 30
        y -= sp
        bruin = self.k((200, 170, 140))
        pygame.draw.ellipse(s, bruin, (x - 36, y - 60, 72, 56))
        pygame.draw.circle(s, bruin, (int(x + 34 * r), int(y - 70)), 24)
        for dx in (-8, 8):
            pygame.draw.ellipse(s, bruin, (x + 34 * r + dx - 7, y - 130, 14, 50))
            pygame.draw.ellipse(s, self.k((250, 190, 200)), (x + 34 * r + dx - 3, y - 122, 6, 34))
        pygame.draw.circle(s, (255, 255, 255), (int(x - 34 * r), int(y - 44)), 13)
        pygame.draw.circle(s, (30, 30, 30), (int(x + 42 * r), int(y - 74)), 4)
        pygame.draw.circle(s, self.k((250, 140, 160)), (int(x + 56 * r), int(y - 66)), 4)
        if not self.haas["terug"]:
            self._ei(s, x + 20 * r, y - 30, self.k((255, 140, 200)), 0.8)

    def balk(self):
        return ("Pasen", "Eieren: %d  (%d punten)" % (self.eieren, self.punten), "Tijd: %d" % max(0, math.ceil(self.tijd)))

    def uitleg_regels(self):
        r = ["Pasen: eieren zoeken",
             "Loop door de tuin. Bij een struik, bloemen of iets anders:",
             "druk op pijl omhoog om te kijken of er een ei ligt.",
             "Tip: een plek met een ei wiebelt heel soms een klein beetje!",
             "Ergens ligt een GOUDEN EI: dat is 5 punten waard.",
             "De paashaas huppelt soms langs en verstopt een nieuw ei."]
        if self.n == 2:
            r.append("Speler 2: A en D = lopen, W = kijken")
        return r
