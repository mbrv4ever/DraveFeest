# -*- coding: utf-8 -*-
# DraveFeest - Sint-Maarten: de lampionnen-route. Loop langs de deuren, zing het liedje (pijltjes op de maat)
# en haal snoep op. Pas op voor de wind: houd je lampion vast!
# Copyright (C) 2026 Dravenlock (Roger & Claudio). Vrije software onder de GNU GPL v3.0.
import math
import random

import pygame

from basis import Scene, tekst, gloed, SPELER_TOETSEN, mix, pijl, vinkje, retro_klein, stijl_van

W, H = 1280, 720
STRAAT_Y = 600
SPEELTIJD = 100
LIEDJE = ["Sint-Maarten, Sint-Maarten,", "de koeien hebben staarten,", "de meisjes hebben rokjes aan,",
          "daar komt Sint-Maarten aan!"]
MELODIE = [392, 392, 440, 392, 523, 494, 392, 440, 392, 587, 523, 392]
PIJLEN = ["links", "rechts", "op", "neer"]
LAMPION_KLEUR = [(255, 140, 40), (90, 170, 255)]


class SintMaarten(Scene):
    res = (W, H)
    pixel = False
    naam = "sintmaarten"

    def __init__(self, spel):
        super().__init__(spel)
        rnd = random.Random()
        self.huizen = []
        x = 500
        for i in range(14):
            self.huizen.append(dict(x=x, b=rnd.randint(260, 330), h=rnd.randint(230, 300), thuis=rnd.random() < 0.8,
                                    gedaan=False, muur=rnd.choice([(92, 62, 52), (70, 74, 90), (100, 84, 64), (82, 58, 66)]),
                                    gloed=rnd.random() * 6))
            x += self.huizen[-1]["b"] + rnd.randint(60, 120)
        self.lengte = x + 300
        self.lantaarns = list(range(380, self.lengte, 700))
        self.n = 2 if spel.twee else 1
        self.kids = [dict(x=250.0 - i * 70, r=1, stap=0.0, vlam=1.0, zingt=None, aanmaak=0, snoep=0, schild=False)
                     for i in range(self.n)]
        self.snoep = 0
        self.tijd = SPEELTIJD
        self.t = 0.0
        self.cam = 0.0
        self.wind_wacht = rnd.uniform(9, 13)
        self.wind = 0.0          # >0 = het waait
        self.waarschuwing = 0.0
        self.blaadjes = []
        self.vliegsnoep = []
        self.start_tel = 3.0
        self.regel = 0
        self.melodie_i = 0
        self.uitleg = True
        self.sterrenhemel = [(rnd.randrange(W), rnd.randrange(330)) for _ in range(120)]
        self.ver = [(i * 90, rnd.randint(40, 140)) for i in range(self.lengte // 90 + 20)]
        self.gloed_cache = {}
        self.stijl = stijl_van(spel)   # mix | retro | kleurrijk

    # ------------------------------------------------------------- invoer
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
        if self.start_tel > 0 or self.tijd <= 0:
            return
        for i, kid in enumerate(self.kids):
            k = SPELER_TOETSEN[i]
            richting = {k["links"]: "links", k["rechts"]: "rechts", k["op"]: "op", k["neer"]: "neer"}.get(ev.key)
            if kid["zingt"]:
                if richting:
                    self._zing_toets(i, kid, richting)
                continue
            if kid["vlam"] <= 0:
                if ev.key == k["actie"]:
                    kid["aanmaak"] += 1
                    self.spel.geluid.speel("stap")
                    if kid["aanmaak"] >= 6:
                        kid["vlam"], kid["aanmaak"] = 1.0, 0
                        self.spel.geluid.speel("goed")
                continue
            if richting == "op":
                h = self._deur_bij(kid["x"])
                if h is not None and not h["gedaan"] and h["thuis"] and not self._deur_bezet(h):
                    self._begin_zingen(kid, h)
                elif h is not None and h["gedaan"]:
                    self.spel.geluid.speel("fout")

    def _deur_bezet(self, h):
        return any(k["zingt"] and k["zingt"]["huis"] is h for k in self.kids)

    def _begin_zingen(self, kid, h):
        reeks = [random.choice(PIJLEN) for _ in range(4)]
        kid["zingt"] = dict(huis=h, reeks=reeks, i=0, fouten=0, klok=1.6, regel=self.regel % len(LIEDJE))
        self.regel += 1
        self.spel.geluid.speel("deur")

    def _zing_toets(self, i, kid, richting):
        z = kid["zingt"]
        if richting == z["reeks"][z["i"]]:
            self.spel.geluid.noot(MELODIE[self.melodie_i % len(MELODIE)])
            self.melodie_i += 1
            z["i"] += 1
            z["klok"] = 1.6
            if z["i"] >= len(z["reeks"]):
                self._klaar_met_zingen(kid)
        else:
            z["fouten"] += 1
            self.spel.geluid.speel("fout")
            if z["fouten"] >= 3:
                kid["zingt"] = None  # te vals gezongen; probeer het nog eens
                self.spel.geluid.speel("fout")

    def _klaar_met_zingen(self, kid):
        z = kid["zingt"]
        h = z["huis"]
        h["gedaan"] = True
        n = 3 if z["fouten"] == 0 else 2 if z["fouten"] == 1 else 1
        kid["snoep"] += n
        self.snoep += n
        deur_x = h["x"] + h["b"] // 2
        for k in range(n):
            self.vliegsnoep.append(dict(x=deur_x, y=STRAAT_Y - 110, vx=random.uniform(-60, 60) + (kid["x"] - deur_x),
                                        vy=-random.uniform(200, 320), t=0.0, kleur=random.choice(
                                            [(255, 80, 80), (255, 220, 60), (120, 220, 120), (200, 120, 255)])))
        self.spel.geluid.speel("snoep")
        kid["zingt"] = None

    def _deur_bij(self, x):
        for h in self.huizen:
            if abs(x - (h["x"] + h["b"] / 2)) < 45:
                return h
        return None

    # ------------------------------------------------------------- bijwerken
    def update(self, dt):
        self.t += dt
        if self.uitleg:
            return
        if self.start_tel > 0:
            self.start_tel -= dt
            return
        if self.tijd <= 0:
            return
        self.tijd -= dt
        if self.tijd <= 0:
            self._einde()
            return
        toetsen = pygame.key.get_pressed()
        # wind
        if self.wind > 0:
            self.wind -= dt
        elif self.waarschuwing > 0:
            self.waarschuwing -= dt
            if self.waarschuwing <= 0:
                self.wind = 2.6
                self.spel.geluid.speel("wind")
        else:
            self.wind_wacht -= dt
            if self.wind_wacht <= 0:
                self.waarschuwing = 1.6
                self.wind_wacht = random.uniform(8, 13)
        if self.wind > 0 and random.random() < 0.6:
            self.blaadjes.append([self.cam - 20, random.uniform(200, STRAAT_Y), random.uniform(500, 800),
                                  random.uniform(-40, 40), random.uniform(0, 6)])
        for b in self.blaadjes:
            b[0] += b[2] * dt
            b[1] += b[3] * dt + math.sin(self.t * 5 + b[4]) * 40 * dt
        self.blaadjes = [b for b in self.blaadjes if b[0] < self.cam + W + 40]
        for i, kid in enumerate(self.kids):
            k = SPELER_TOETSEN[i]
            kid["schild"] = bool(toetsen[k["neer"]]) and not kid["zingt"]
            if self.wind > 0 and kid["vlam"] > 0:
                kid["vlam"] -= dt * (0.08 if kid["schild"] else 0.5)
                if kid["vlam"] <= 0:
                    kid["vlam"] = 0
                    kid["zingt"] = None
                    self.spel.geluid.speel("fout")
            elif kid["vlam"] > 0:
                kid["vlam"] = min(1.0, kid["vlam"] + dt * 0.05)
            if kid["zingt"]:
                kid["zingt"]["klok"] -= dt
                if kid["zingt"]["klok"] <= 0:
                    kid["zingt"]["fouten"] += 1
                    kid["zingt"]["klok"] = 1.6
                    self.spel.geluid.speel("fout")
                    if kid["zingt"]["fouten"] >= 3:
                        kid["zingt"] = None
                continue
            d = (1 if toetsen[k["rechts"]] else 0) - (1 if toetsen[k["links"]] else 0)
            if kid["schild"]:
                d *= 0.4
            if d:
                kid["x"] = max(60, min(self.lengte - 60, kid["x"] + d * 260 * dt))
                kid["r"] = 1 if d > 0 else -1
                kid["stap"] += dt * 8
        doel = sum(k["x"] for k in self.kids) / self.n - W * 0.4
        self.cam += (max(0, min(self.lengte - W, doel)) - self.cam) * min(1, dt * 4)
        for s in self.vliegsnoep:
            s["t"] += dt
            s["x"] += s["vx"] * dt
            s["y"] += s["vy"] * dt
            s["vy"] += 900 * dt
        self.vliegsnoep = [s for s in self.vliegsnoep if s["t"] < 0.7]

    def _einde(self):
        drempel = [8, 16, 26] if self.n == 1 else [12, 26, 40]
        sterren = sum(1 for d in drempel if self.snoep >= d)
        thuis = sum(1 for h in self.huizen if h["thuis"])
        gedaan = sum(1 for h in self.huizen if h["gedaan"])
        regels = ["Je hebt %d snoepjes opgehaald!" % self.snoep, "Je zong bij %d van de %d deuren." % (gedaan, thuis)]
        if self.n == 2:
            regels.append("Speler 1: %d   ·   Speler 2: %d" % (self.kids[0]["snoep"], self.kids[1]["snoep"]))
        self.spel.uitslag("sintmaarten", "Sint-Maarten", self.snoep, sterren, regels)

    # ------------------------------------------------------------- tekenen
    def _gloed(self, r, kleur, kracht):
        k = (r, kleur, round(kracht, 1))
        if k not in self.gloed_cache:
            self.gloed_cache[k] = gloed(r, kleur, kracht)
        return self.gloed_cache[k]

    def teken(self, s):
        if self.stijl == "kleurrijk":
            self._wereld_kleurrijk(s)
        else:
            self._wereld_mix(s)
        for i, kid in enumerate(self.kids):
            self._kind(s, i, kid)
        for st in self.vliegsnoep:
            if self.stijl == "kleurrijk":
                pygame.draw.circle(s, (30, 20, 50), (int(st["x"] - self.cam), int(st["y"])), 12)
            pygame.draw.circle(s, st["kleur"], (int(st["x"] - self.cam), int(st["y"])), 9)
        for b in self.blaadjes:
            pygame.draw.ellipse(s, (255, 150, 40) if self.stijl == "kleurrijk" else (170, 90, 30),
                                (b[0] - self.cam, b[1], 14, 7))
        if self.stijl == "retro":
            self._retro(s)
        else:
            self._balk(s)
        if self.uitleg:
            self._uitleg(s)

    def _wereld_mix(self, s):
        # lucht
        for y in range(0, STRAAT_Y, 4):
            pygame.draw.rect(s, mix((6, 8, 22), (30, 26, 58), y / STRAAT_Y), (0, y, W, 4))
        for i, (x, y) in enumerate(self.sterrenhemel):
            if (i + int(self.t * 1.5)) % 11:
                s.set_at((x, y), (200, 200, 230))
        pygame.draw.circle(s, (235, 235, 210), (1080, 110), 46)
        pygame.draw.circle(s, mix((6, 8, 22), (30, 26, 58), 0.2), (1100, 96), 42)
        # daken ver weg
        pts = [(-10, STRAAT_Y - 120)]
        for x, h in self.ver:
            xx = x - self.cam * 0.4
            pts += [(xx, STRAAT_Y - 120 - h), (xx + 60, STRAAT_Y - 120 - h)]
        pts.append((W + 10, STRAAT_Y - 120))
        pygame.draw.polygon(s, (16, 16, 32), pts)
        pygame.draw.rect(s, (16, 16, 32), (0, STRAAT_Y - 121, W, 121))
        # huizen
        for h in self.huizen:
            x = h["x"] - self.cam
            if x > W + 20 or x + h["b"] < -20:
                continue
            top = STRAAT_Y - h["h"]
            pygame.draw.rect(s, h["muur"], (x, top, h["b"], h["h"]))
            pygame.draw.polygon(s, tuple(int(c * 0.6) for c in h["muur"]),
                                [(x - 10, top), (x + h["b"] / 2, top - 90), (x + h["b"] + 10, top)])
            licht = h["thuis"]
            for rx in (x + 30, x + h["b"] - 90):
                kl = (255, 205, 110) if licht else (34, 36, 50)
                pygame.draw.rect(s, (30, 22, 20), (rx - 4, top + 36, 68, 78), border_radius=6)
                pygame.draw.rect(s, kl, (rx, top + 40, 60, 70), border_radius=4)
                pygame.draw.line(s, (30, 22, 20), (rx + 30, top + 40), (rx + 30, top + 110), 4)
                if licht:
                    self._licht(s, self._gloed(90, (110, 80, 30), 1.0), (rx - 60, top - 15))
            dx = x + h["b"] / 2 - 32
            pygame.draw.rect(s, (54, 34, 26), (dx, STRAAT_Y - 130, 64, 130), border_radius=8)
            pygame.draw.circle(s, (230, 190, 70), (int(dx + 52), STRAAT_Y - 64), 5)
            if h["gedaan"]:
                vinkje(s, dx + 32, STRAAT_Y - 158, 16, (90, 217, 136))
            elif h["thuis"]:
                self._licht(s, self._gloed(40, (120, 90, 40), 0.9), (dx - 8, STRAAT_Y - 176))
        # stoep + straat
        pygame.draw.rect(s, (38, 36, 44), (0, STRAAT_Y, W, H - STRAAT_Y))
        pygame.draw.rect(s, (56, 52, 60), (0, STRAAT_Y, W, 14))
        for lx in self.lantaarns:
            x = lx - self.cam
            if -60 < x < W + 60:
                pygame.draw.rect(s, (22, 22, 26), (x - 4, STRAAT_Y - 230, 8, 230))
                pygame.draw.rect(s, (22, 22, 26), (x - 16, STRAAT_Y - 250, 32, 24), border_radius=4)
                pygame.draw.rect(s, (255, 225, 150), (x - 12, STRAAT_Y - 246, 24, 16), border_radius=3)
                self._licht(s, self._gloed(170, (90, 80, 50), 1.0), (x - 170, STRAAT_Y - 410))

    def _licht(self, s, g, pos):
        """Zachte gloed erbij (niet in retro: daar bestaat geen zacht licht)."""
        if self.stijl != "retro":
            s.blit(g, pos, special_flags=pygame.BLEND_ADD)

    # ---- stijl 'kleurrijk': felle kleuren, dikke donkere randen, cartoon
    def _wereld_kleurrijk(self, s):
        LIJN = (30, 20, 50)
        for y in range(0, STRAAT_Y, 4):
            pygame.draw.rect(s, mix((60, 30, 140), (220, 80, 160), y / STRAAT_Y), (0, y, W, 4))
        for i, (x, y) in enumerate(self.sterrenhemel[::2]):
            r = 3 if i % 3 == 0 else 2
            pygame.draw.circle(s, (255, 250, 200), (x, y), r)
        pygame.draw.circle(s, LIJN, (1080, 110), 58)
        pygame.draw.circle(s, (255, 236, 140), (1080, 110), 52)
        pygame.draw.circle(s, (240, 210, 110), (1062, 96), 9)
        pygame.draw.circle(s, (240, 210, 110), (1098, 128), 6)
        # heuvels ver weg
        pts = [(-10, STRAAT_Y - 100)]
        for x, h in self.ver:
            xx = x - self.cam * 0.4
            pts.append((xx + 45, STRAAT_Y - 100 - h * 0.7))
        pts.append((W + 10, STRAAT_Y - 100))
        pygame.draw.polygon(s, (110, 50, 150), pts + [(W + 10, STRAAT_Y), (-10, STRAAT_Y)])
        pygame.draw.lines(s, LIJN, False, pts, 4)
        felle = [(40, 200, 190), (255, 200, 60), (255, 110, 90), (120, 200, 90), (90, 150, 255), (250, 140, 200)]
        for n, h in enumerate(self.huizen):
            x = h["x"] - self.cam
            if x > W + 20 or x + h["b"] < -20:
                continue
            top = STRAAT_Y - h["h"]
            muur = felle[n % len(felle)]
            dakkleur = tuple(int(c * 0.75) for c in felle[(n + 3) % len(felle)])
            romp = pygame.Rect(x, top, h["b"], h["h"])
            pygame.draw.rect(s, LIJN, romp.inflate(10, 10), border_radius=18)
            pygame.draw.rect(s, muur, romp, border_radius=14)
            dakpunten = [(x - 18, top + 4), (x + h["b"] / 2, top - 96), (x + h["b"] + 18, top + 4)]
            pygame.draw.polygon(s, dakkleur, dakpunten)
            pygame.draw.polygon(s, LIJN, dakpunten, 6)
            for rx in (x + 30, x + h["b"] - 90):
                kl = (255, 245, 150) if h["thuis"] else (70, 60, 110)
                pygame.draw.ellipse(s, LIJN, (rx - 6, top + 34, 72, 82))
                pygame.draw.ellipse(s, kl, (rx, top + 40, 60, 70))
                pygame.draw.line(s, LIJN, (rx + 30, top + 42), (rx + 30, top + 108), 5)
                if h["thuis"]:
                    self._licht(s, self._gloed(80, (90, 80, 20), 1.0), (rx - 50, top - 5))
            dx = x + h["b"] / 2 - 32
            pygame.draw.rect(s, LIJN, (dx - 5, STRAAT_Y - 135, 74, 140), border_top_left_radius=37, border_top_right_radius=37)
            pygame.draw.rect(s, (150, 80, 50), (dx, STRAAT_Y - 130, 64, 130), border_top_left_radius=32, border_top_right_radius=32)
            pygame.draw.circle(s, (255, 220, 60), (int(dx + 50), STRAAT_Y - 64), 7)
            if h["gedaan"]:
                pygame.draw.circle(s, LIJN, (int(dx + 32), STRAAT_Y - 170), 26)
                pygame.draw.circle(s, (90, 217, 136), (int(dx + 32), STRAAT_Y - 170), 21)
                vinkje(s, dx + 32, STRAAT_Y - 170, 12, (255, 255, 255))
        pygame.draw.rect(s, (80, 70, 120), (0, STRAAT_Y, W, H - STRAAT_Y))
        pygame.draw.rect(s, (150, 140, 190), (0, STRAAT_Y, W, 18))
        pygame.draw.line(s, LIJN, (0, STRAAT_Y), (W, STRAAT_Y), 5)
        for lx in self.lantaarns:
            x = lx - self.cam
            if -60 < x < W + 60:
                pygame.draw.rect(s, LIJN, (x - 7, STRAAT_Y - 232, 14, 232), border_radius=6)
                pygame.draw.circle(s, LIJN, (int(x), STRAAT_Y - 250), 26)
                pygame.draw.circle(s, (255, 240, 150), (int(x), STRAAT_Y - 250), 20)
                self._licht(s, self._gloed(150, (90, 80, 40), 1.0), (x - 150, STRAAT_Y - 400))

    # ---- stijl 'retro': alles in grove pixels met een beperkt kleurenpalet (C64-sfeer)
    def _retro(self, s):
        uit = retro_klein(s, 4, 0.27)
        laag = uit.get_size()
        # balk in pixelletters, op het lage scherm
        pygame.draw.rect(uit, (0, 0, 0), (0, 0, laag[0], 12))
        tekst(uit, "SINT-MAARTEN", (3, 2), 16, (255, 163, 0), pixel=True, schaduw=False)
        tekst(uit, "SNOEP %02d" % self.snoep, (laag[0] // 2, 2), 16, (255, 255, 255), midden=True, pixel=True, schaduw=False)
        tekst(uit, "TIJD %03d" % max(0, math.ceil(self.tijd)), (laag[0] - 3, 2), 16, (255, 255, 255), rechts=True,
              pixel=True, schaduw=False)
        if self.waarschuwing > 0 and int(self.t * 6) % 2:
            tekst(uit, "WIND! PIJL OMLAAG!", (laag[0] // 2, 18), 16, (255, 163, 0), midden=True, pixel=True)
        elif self.wind > 0:
            tekst(uit, "HOUD JE LAMPION VAST!", (laag[0] // 2, 18), 16, (255, 255, 255), midden=True, pixel=True)
        if self.start_tel > 0 and not self.uitleg:
            tekst(uit, str(math.ceil(self.start_tel)), (laag[0] // 2, 60), 48, (255, 255, 255), midden=True, pixel=True)
        s.blit(pygame.transform.scale(uit, (W, H)), (0, 0))

    def _kind(self, s, i, kid):
        x = int(kid["x"] - self.cam)
        y = STRAAT_Y + 60 - i * 16
        jas = [(70, 110, 200), (220, 120, 50)][i]
        been = math.sin(kid["stap"]) * 8
        if self.stijl == "kleurrijk":  # dikke cartoonranden
            LIJN = (30, 20, 50)
            pygame.draw.line(s, LIJN, (x - 8, y - 40), (x - 8 - been, y + 3), 17)
            pygame.draw.line(s, LIJN, (x + 8, y - 40), (x + 8 + been, y + 3), 17)
            pygame.draw.rect(s, LIJN, (x - 27, y - 105, 54, 74), border_radius=18)
            pygame.draw.circle(s, LIJN, (x, y - 122), 27)
            pygame.draw.ellipse(s, LIJN, (x - 29, y - 155, 58, 40))
        pygame.draw.line(s, (40, 40, 60), (x - 8, y - 40), (x - 8 - been, y), 9)
        pygame.draw.line(s, (40, 40, 60), (x + 8, y - 40), (x + 8 + been, y), 9)
        pygame.draw.rect(s, jas, (x - 22, y - 100, 44, 64), border_radius=14)
        pygame.draw.circle(s, (240, 205, 175), (x, y - 122), 22)
        pygame.draw.ellipse(s, [(200, 40, 50), (40, 160, 90)][i], (x - 24, y - 150, 48, 30))  # muts
        pygame.draw.circle(s, (255, 255, 255), (x, y - 152), 6)
        pygame.draw.circle(s, (30, 30, 30), (x + 7 * kid["r"], y - 124), 3)
        # stok + lampion
        hx = x + 26 * kid["r"]
        if kid["schild"]:
            lx, ly = x + 14 * kid["r"], y - 84
        else:
            lx, ly = hx + 34 * kid["r"], y - 118 + math.sin(self.t * 3 + i) * 4
        pygame.draw.line(s, (110, 80, 50), (x + 18 * kid["r"], y - 72), (lx, ly - 30), 5)
        pygame.draw.line(s, (60, 60, 60), (lx, ly - 30), (lx, ly - 18), 2)
        kl = LAMPION_KLEUR[i]
        v = kid["vlam"]
        if self.stijl == "kleurrijk":
            pygame.draw.ellipse(s, (30, 20, 50), (lx - 27, ly - 23, 54, 50))
        pygame.draw.ellipse(s, mix((60, 50, 50), kl, 0.4 + 0.6 * v), (lx - 22, ly - 18, 44, 40))
        pygame.draw.line(s, tuple(int(c * 0.6) for c in kl), (lx - 18, ly + 2), (lx + 18, ly + 2), 2)
        if v > 0:
            fl = 0.85 + 0.15 * math.sin(self.t * 13 + i)
            if self.wind > 0 and not kid["schild"]:
                fl *= 0.6 + 0.4 * math.sin(self.t * 30)
            self._licht(s, self._gloed(140, tuple(int(c * 0.55) for c in kl), round(v * fl, 1)), (lx - 140, ly - 140),
                   )
            pygame.draw.ellipse(s, (255, 240, 180), (lx - 5, ly - 6, 10, 14))
        else:
            tekst(s, "Lampion uit! Druk %dx op %s" % (6 - kid["aanmaak"], "spatie" if i == 0 else "E"),
                  (x, y - 210), 26, (255, 120, 90), midden=True, vet=True)
        if kid["schild"]:
            pygame.draw.circle(s, jas, (lx + 10 * kid["r"], ly - 4), 14)  # hand eromheen
        z = kid["zingt"]
        if z:
            bx = x - 130
            by = y - 300
            pygame.draw.rect(s, (20, 18, 30), (bx, by, 260, 110), border_radius=14)
            pygame.draw.rect(s, LAMPION_KLEUR[i], (bx, by, 260, 110), 3, border_radius=14)
            tekst(s, LIEDJE[z["regel"]], (x, by + 10), 20, (230, 230, 240), midden=True)
            for k, p in enumerate(z["reeks"]):
                kl = (90, 217, 136) if k < z["i"] else (255, 255, 255) if k == z["i"] else (110, 110, 130)
                pijl(s, p, bx + 48 + k * 55, by + 66, 18, kl)
            pygame.draw.rect(s, (255, 179, 71), (bx + 20, by + 96, int(220 * z["klok"] / 1.6), 6), border_radius=3)

    def _balk(self, s):
        pygame.draw.rect(s, (0, 0, 0), (0, 0, W, 60))
        tekst(s, "Sint-Maarten", (20, 12), 30, (255, 179, 71), vet=True)
        tekst(s, "Snoep: %d" % self.snoep, (W // 2, 12), 32, (255, 255, 255), midden=True, vet=True)
        tekst(s, "Tijd: %d" % max(0, math.ceil(self.tijd)), (W - 20, 12), 32,
              (255, 120, 90) if self.tijd < 15 else (255, 255, 255), rechts=True, vet=True)
        if self.waarschuwing > 0 and int(self.t * 6) % 2:
            tekst(s, "Er komt wind aan! Houd pijl omlaag ingedrukt" + (" (of S)" if self.n == 2 else ""),
                  (W // 2, 80), 34, (255, 220, 120), midden=True, vet=True)
        elif self.wind > 0:
            tekst(s, "Wind!  Houd je lampion vast!", (W // 2, 80), 38, (255, 255, 255), midden=True, vet=True)
        if self.start_tel > 0 and not self.uitleg:
            tekst(s, str(math.ceil(self.start_tel)), (W // 2, 260), 140, (255, 255, 255), midden=True, vet=True)

    def _uitleg(self, s):
        dek = pygame.Surface((W, H), pygame.SRCALPHA)
        dek.fill((0, 0, 0, 190))
        s.blit(dek, (0, 0))
        regels = [("Sint-Maarten: de lampionnen-route", 48, (255, 179, 71)), ("", 20, None),
                  ("Loop langs de huizen met je lampion.", 30, None),
                  ("Brandt er licht? Ga voor de deur staan en druk op pijl omhoog.", 30, None),
                  ("Druk dan de pijltjes in die boven je hoofd staan. Zo zing je het liedje.", 30, None),
                  ("Zonder fouten = 3 snoepjes!", 30, (90, 217, 136)), ("", 20, None),
                  ("Er komt wind aan? Houd pijl omlaag ingedrukt: dan houd je je lampion vast.", 30, None),
                  ("Is hij toch uit? Druk 6 keer op spatie om hem weer aan te steken.", 30, None),
                  ("", 20, None), ("Speler 2: W A S D + E", 26, (150, 150, 170)), ("", 20, None),
                  ("Druk op Enter om te beginnen  ·  Esc = terug naar het dorp", 28, (255, 255, 255))]
        y = 130
        for t, g, k in regels:
            if t:
                tekst(s, t, (W // 2, y), g, k or (230, 230, 240), midden=True, vet=g > 40)
            y += g + 14
