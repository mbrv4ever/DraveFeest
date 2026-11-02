# -*- coding: utf-8 -*-
# DraveFeest - Halloween: spoken vangen met je zaklamp.
# Houd de zaklamp op een spook tot de balk vol is: gevangen! Maar de batterij raakt op, en vleermuizen duiken op je af.
# Copyright (C) 2026 Dravenlock (Roger & Claudio). Vrije software onder de GNU GPL v3.0.
import math
import random

import pygame

from basis import HDSpel, tekst, teken_kind, SPELER_TOETSEN, mix

W, H = 1280, 720
GROND = 640
LAMP_Y = GROND - 150        # hoogte van de zaklamp in de hand
BUNDEL = 260                # halve breedte van de lichtbundel bovenin
KLEUR_LICHT = [(255, 236, 150), (170, 230, 255)]


class Halloween(HDSpel):
    naam = "halloween"
    titel = "Halloween"
    speeltijd = 60
    retro_licht = 0.0

    def __init__(self, spel):
        super().__init__(spel)
        start = [W // 2] if self.n == 1 else [W // 2 + 220, W // 2 - 220]
        self.kids = [dict(x=float(x), r=1, stap=0.0, lamp=False, batterij=1.0, leeg=False, schrik=0.0, punten=0,
                          gevangen=0) for x in start]
        self.spoken = []
        self.vleermuizen = []
        self.punten = 0
        self.nieuw_t = 0.4
        self.vleer_t = 6.0
        self.sterren = [(random.randrange(W), random.randrange(GROND - 260)) for _ in range(90)]
        self.huizen = [(x, 160 + (x * 37) % 120) for x in range(-40, W + 80, 190)]
        self.graven = [(x, (x * 13) % 3) for x in range(60, W, 150)]
        self.flarden = []

    # ---- spoken
    def _nieuw_spook(self):
        gouden = random.random() < 0.12
        kant = random.choice((-1, 1))
        self.spoken.append(dict(
            x=float(random.randrange(120, W - 120)), y=float(random.randrange(90, LAMP_Y - 200)),
            vx=random.uniform(60, 130) * kant, fase=random.random() * 6, vang=0.0,
            nodig=1.6 if gouden else 0.7, waarde=5 if gouden else 1, gouden=gouden, licht_door=None,
            leef=random.uniform(9, 14), boe=0.0))

    def _in_bundel(self, kid, x, y):
        if not kid["lamp"] or kid["leeg"] or kid["schrik"] > 0:
            return False
        hoogte = LAMP_Y - y
        if hoogte < 10:
            return False
        breed = 30 + BUNDEL * min(1.0, hoogte / (LAMP_Y - 60))
        return abs(x - kid["x"]) < breed

    # ---- invoer
    def spel_toets(self, ev):
        for i, kid in enumerate(self.kids):
            if ev.key == SPELER_TOETSEN[i]["actie"] and kid["schrik"] <= 0:
                self.spel.geluid.speel("stap")

    # ---- bijwerken
    def spel_update(self, dt):
        toetsen = pygame.key.get_pressed()
        for i, kid in enumerate(self.kids):
            k = SPELER_TOETSEN[i]
            kid["schrik"] = max(0.0, kid["schrik"] - dt)
            if self.klaar_t is None and kid["schrik"] <= 0:
                d = (1 if toetsen[k["rechts"]] else 0) - (1 if toetsen[k["links"]] else 0)
                if d:
                    kid["x"] = max(60, min(W - 60, kid["x"] + d * 330 * dt))
                    kid["r"] = d
                    kid["stap"] += dt * 12
                kid["lamp"] = bool(toetsen[k["actie"]] or toetsen[k["op"]])
            else:
                kid["lamp"] = False
            # batterij: leeg = even wachten tot hij weer een beetje vol is
            if kid["lamp"] and not kid["leeg"]:
                kid["batterij"] -= dt * 0.22
                if kid["batterij"] <= 0:
                    kid["batterij"] = 0
                    kid["leeg"] = True
                    self.zweef(kid["x"], LAMP_Y - 80, "Batterij leeg!", (255, 170, 120), 1.0)
            else:
                kid["batterij"] = min(1.0, kid["batterij"] + dt * 0.16)
                if kid["leeg"] and kid["batterij"] > 0.35:
                    kid["leeg"] = False
        # nieuwe spoken
        self.nieuw_t -= dt
        maximum = 4 + (1 if self.n == 2 else 0) + int((self.speeltijd - self.tijd) / 20)
        if self.nieuw_t <= 0 and len(self.spoken) < maximum:
            self._nieuw_spook()
            self.nieuw_t = random.uniform(0.8, 1.8)
        for sp in self.spoken:
            sp["fase"] += dt
            sp["leef"] -= dt
            verlicht = None
            for i, kid in enumerate(self.kids):
                if self._in_bundel(kid, sp["x"], sp["y"]):
                    verlicht = i
            if verlicht is not None:
                sp["vang"] += dt
                # verlichte spoken proberen weg te glippen
                weg = 1 if sp["x"] > self.kids[verlicht]["x"] else -1
                sp["vx"] += weg * 260 * dt
                sp["licht_door"] = verlicht
                if sp["vang"] >= sp["nodig"]:
                    self._vang(sp, verlicht)
            else:
                sp["vang"] = max(0.0, sp["vang"] - dt * 0.6)
            sp["vx"] = max(-220, min(220, sp["vx"]))
            sp["x"] += sp["vx"] * dt
            sp["y"] += math.sin(sp["fase"] * 1.7) * 30 * dt
            if sp["x"] < 70 or sp["x"] > W - 70:
                sp["vx"] *= -1
                sp["x"] = max(70, min(W - 70, sp["x"]))
        self.spoken = [s for s in self.spoken if s["vang"] >= 0 and s["leef"] > 0]
        # vleermuizen duiken
        self.vleer_t -= dt
        if self.vleer_t <= 0:
            doel = random.randrange(self.n)
            kant = random.choice((-1, 1))
            self.vleermuizen.append(dict(x=W / 2 + kant * (W / 2 + 40), y=random.uniform(80, 200), doel=doel,
                                         v=random.uniform(320, 420), fladder=0.0, weg=False))
            self.vleer_t = max(2.2, random.uniform(3.5, 6.5) - (self.speeltijd - self.tijd) / 30)
        for v in self.vleermuizen:
            v["fladder"] += dt * 14
            kid = self.kids[v["doel"]]
            if v["weg"]:
                v["y"] -= 420 * dt
                continue
            tx, ty = kid["x"], LAMP_Y - 30
            dx, dy = tx - v["x"], ty - v["y"]
            afst = max(1.0, math.hypot(dx, dy))
            v["x"] += dx / afst * v["v"] * dt
            v["y"] += dy / afst * v["v"] * dt
            if any(self._in_bundel(k, v["x"], v["y"]) for k in self.kids):
                v["weg"] = True
                self._punt(kid, 1, v["x"], v["y"], "Wegwezen! +1", (200, 200, 255))
                self.spel.geluid.speel("snoep")
            elif afst < 40:
                v["weg"] = True
                kid["schrik"] = 1.1
                kid["punten"] = max(0, kid["punten"] - 1)
                self.punten = max(0, self.punten - 1)
                self.zweef(kid["x"], LAMP_Y - 120, "BOE! -1", (255, 120, 120), 1.0)
                self.spel.geluid.speel("stap")
        self.vleermuizen = [v for v in self.vleermuizen if v["y"] > -60]
        for f in self.flarden:
            f[0] += f[2] * dt
            f[1] += f[3] * dt
            f[4] -= dt
        self.flarden = [f for f in self.flarden if f[4] > 0]

    def _punt(self, kid, n, x, y, t, kleur):
        kid["punten"] += n
        self.punten += n
        self.zweef(x, y - 50, t, kleur, 1.0)

    def _vang(self, sp, i):
        kid = self.kids[i]
        sp["vang"] = -1
        kid["gevangen"] += 1
        if sp["gouden"]:
            self._punt(kid, 5, sp["x"], sp["y"], "Pompoenspook! +5", (255, 200, 60))
            self.spel.geluid.speel("ster")
        else:
            self._punt(kid, 1, sp["x"], sp["y"], "Gevangen! +1", (255, 255, 255))
            self.spel.geluid.speel("snoep")
        for _ in range(14):
            a = random.random() * math.tau
            self.flarden.append([sp["x"], sp["y"], math.cos(a) * 180, math.sin(a) * 180, random.uniform(0.4, 0.8)])

    def einde(self):
        drempel = [10, 18, 26] if self.n == 1 else [16, 28, 40]
        sterren = sum(1 for d in drempel if self.punten >= d)
        gevangen = sum(k["gevangen"] for k in self.kids)
        regels = ["%d spoken gevangen!" % gevangen, "%d punten" % self.punten]
        if self.n == 2:
            regels.append("Speler 1: %d   ·   Speler 2: %d" % (self.kids[0]["punten"], self.kids[1]["punten"]))
        self.spel.uitslag("halloween", "Fijne Halloween!", self.punten, sterren, regels)

    # ---- tekenen
    def achter(self, s):
        if self.stijl == "retro":   # effen nachtzwart, anders maakt het 16-kleurenpalet er blauw/roze van
            s.fill((0, 0, 0), (0, 0, W, GROND))
        else:
            for y in range(0, GROND, 4):
                pygame.draw.rect(s, mix(self.k((14, 10, 34)), self.k((60, 30, 70)), y / GROND), (0, y, W, 4))
        for x, y in self.sterren:
            s.set_at((x, y), (230, 230, 255))
        pygame.draw.circle(s, self.k((245, 240, 205)), (1080, 120), 62)
        pygame.draw.circle(s, self.k((230, 220, 180)), (1060, 108), 12)
        pygame.draw.circle(s, self.k((230, 220, 180)), (1100, 140), 8)
        # spookhuizen als silhouet
        for x, h in self.huizen:
            kl = (68, 68, 68) if self.stijl == "retro" else self.k((26, 20, 36))
            pygame.draw.rect(s, kl, (x, GROND - h, 150, h))
            pygame.draw.polygon(s, kl, [(x - 12, GROND - h), (x + 75, GROND - h - 70), (x + 162, GROND - h)])
            for rx in (x + 24, x + 96):
                aan = (rx // 7 + int(self.t * 0.7)) % 3 != 0
                pygame.draw.rect(s, self.k((250, 190, 80) if aan else (50, 40, 60)), (rx, GROND - h + 34, 28, 34))
        # hek en graven
        for x in range(0, W, 26):
            pygame.draw.rect(s, self.k((40, 36, 48)), (x, GROND - 64, 6, 64))
        pygame.draw.rect(s, self.k((40, 36, 48)), (0, GROND - 50, W, 6))
        for x, v in self.graven:
            pygame.draw.rect(s, self.k((110, 110, 125)), (x, GROND - 52 - v * 6, 38, 52 + v * 6), border_radius=16)
            pygame.draw.line(s, self.k((70, 70, 85)), (x + 19, GROND - 40 - v * 6), (x + 19, GROND - 18), 3)
            pygame.draw.line(s, self.k((70, 70, 85)), (x + 11, GROND - 32 - v * 6), (x + 27, GROND - 32 - v * 6), 3)

    def _spook(self, s, sp):
        x, y = int(sp["x"]), int(sp["y"])
        golf = math.sin(sp["fase"] * 6) * 4
        kleur = self.k((255, 190, 70)) if sp["gouden"] else self.k((235, 235, 245))
        lichaam = pygame.Surface((90, 110), pygame.SRCALPHA)
        a = 230 if sp["licht_door"] is not None and sp["vang"] > 0 else 190
        pygame.draw.circle(lichaam, kleur + (a,), (45, 40), 36)
        pygame.draw.rect(lichaam, kleur + (a,), (9, 40, 72, 44))
        for i in range(4):
            pygame.draw.circle(lichaam, kleur + (a,), (18 + i * 18, 84 + (golf if i % 2 else -golf) * 0.5), 10)
        s.blit(lichaam, (x - 45, y - 45))
        oog = (40, 20, 10) if sp["gouden"] else (30, 30, 40)
        pygame.draw.ellipse(s, oog, (x - 20, y - 16, 12, 18))
        pygame.draw.ellipse(s, oog, (x + 8, y - 16, 12, 18))
        if sp["gouden"]:
            pygame.draw.polygon(s, (40, 20, 10), [(x - 14, y + 10), (x + 14, y + 10), (x, y + 22)])
            pygame.draw.rect(s, self.k((40, 120, 40)), (x - 4, y - 50, 8, 12))
        else:
            pygame.draw.ellipse(s, oog, (x - 6, y + 8, 12, 14))
        if sp["vang"] > 0:
            k = min(1, sp["vang"] / sp["nodig"])
            pygame.draw.rect(s, (30, 20, 40), (x - 40, y - 66, 80, 10), border_radius=4)
            pygame.draw.rect(s, KLEUR_LICHT[sp["licht_door"] or 0], (x - 40, y - 66, int(80 * k), 10), border_radius=4)

    def voor(self, s):
        pygame.draw.rect(s, self.k((34, 40, 36)), (0, GROND, W, H - GROND))
        pygame.draw.rect(s, self.k((50, 58, 48)), (0, GROND, W, 8))
        # lichtbundels
        for i, kid in enumerate(self.kids):
            if kid["lamp"] and not kid["leeg"] and kid["schrik"] <= 0:
                laag = pygame.Surface((W, H), pygame.SRCALPHA)
                x = kid["x"]
                sterkte = int(70 + 60 * kid["batterij"])
                pygame.draw.polygon(laag, KLEUR_LICHT[i] + (sterkte,),
                                    [(x - 14, LAMP_Y), (x + 14, LAMP_Y), (x + BUNDEL + 30, 60), (x - BUNDEL - 30, 60)])
                s.blit(laag, (0, 0))
        for sp in self.spoken:
            if sp["vang"] >= 0:
                self._spook(s, sp)
        for v in self.vleermuizen:
            vl = math.sin(v["fladder"]) * 16
            x, y = int(v["x"]), int(v["y"])
            kl = self.k((50, 30, 70))
            pygame.draw.polygon(s, kl, [(x, y), (x - 36, y - 10 + vl), (x - 18, y + 6)])
            pygame.draw.polygon(s, kl, [(x, y), (x + 36, y - 10 + vl), (x + 18, y + 6)])
            pygame.draw.circle(s, kl, (x, y), 10)
            s.set_at((x - 3, y - 2), (255, 220, 60))
            s.set_at((x + 3, y - 2), (255, 220, 60))
        for f in self.flarden:
            pygame.draw.circle(s, (240, 240, 255), (int(f[0]), int(f[1])), 4)
        # kinderen met zaklamp, verkleed als heks en als pompoen
        for i, kid in enumerate(self.kids):
            jas = [(110, 50, 160), (240, 120, 30)][i]
            muts = [(40, 30, 50), (40, 120, 40)][i]
            beef = math.sin(self.t * 40) * 4 if kid["schrik"] > 0 else 0
            teken_kind(s, kid["x"] + beef, GROND + 20, 1.0, self.k(jas), self.k(muts), kid["r"], kid["stap"], lijn=False)
            lx = int(kid["x"] + 20 * kid["r"])
            pygame.draw.rect(s, (60, 60, 70), (lx - 6, LAMP_Y - 4, 12, 26), border_radius=3)
            pygame.draw.circle(s, KLEUR_LICHT[i] if kid["lamp"] and not kid["leeg"] else (90, 90, 90), (lx, LAMP_Y - 4), 7)
            # batterij-meter
            bx, by = int(kid["x"]) - 40, GROND + 34
            pygame.draw.rect(s, (20, 20, 26), (bx, by, 80, 14), border_radius=4)
            kl = (120, 230, 120) if kid["batterij"] > 0.35 else (240, 120, 90)
            pygame.draw.rect(s, kl, (bx + 2, by + 2, int(76 * kid["batterij"]), 10), border_radius=3)

    def effect(self, s):
        for kid in self.kids:
            if kid["schrik"] > 0:
                tekst(s, "Aaah!", (int(kid["x"]), GROND - 350), 34, (255, 150, 140), midden=True, vet=True)
            if kid["leeg"]:
                tekst(s, "laden...", (int(kid["x"]), GROND + 52), 20, (255, 190, 150), midden=True)

    def balk(self):
        return ("Halloween", "Punten: %d" % self.punten, "Tijd: %d" % max(0, math.ceil(self.tijd)))

    def uitleg_regels(self):
        r = ["Halloween: spoken vangen",
             "Houd spatie (of pijl omhoog) ingedrukt: je zaklamp gaat aan.",
             "Schijn op een spook tot zijn balkje vol is: gevangen! (+1)",
             "Het gouden Pompoenspook is lastig, maar levert +5 op.",
             "Vleermuizen duiken op je af: schijn ze weg (+1), anders BOE! (-1)",
             "Let op je batterij: is hij leeg, dan moet hij even laden."]
        if self.n == 2:
            r.append("Speler 2 (links): A en D = lopen, W of E = zaklamp")
        return r
