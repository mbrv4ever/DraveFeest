# -*- coding: utf-8 -*-
# DraveFeest - gedeelde basis: paden, opslag, geluid, letters, hulpjes.
# Copyright (C) 2026 Dravenlock (Roger & Claudio). Vrije software onder de GNU GPL v3.0.
import array
import datetime
import json
import math
import os
import random
import sys

import pygame

APP_NAAM = "DraveFeest"
VERSIE = "0.6"


def app_map():
    return os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))


def bron(naam):
    for b in (getattr(sys, "_MEIPASS", None), app_map()):
        if b and os.path.exists(os.path.join(b, naam)):
            return os.path.join(b, naam)
    return os.path.join(app_map(), naam)


# ------------------------------------------------------------------ opslag
def _pad():
    p = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "DraveFeest")
    os.makedirs(p, exist_ok=True)
    return os.path.join(p, "spel.json")


class Opslag:
    def __init__(self):
        self.d = dict(sterren={}, hoogste={}, kerstdorp=[], twee=False, geluid=True)
        try:
            with open(_pad(), encoding="utf-8-sig") as f:
                self.d.update(json.load(f))
        except Exception:
            pass

    def bewaar(self):
        try:
            tmp = _pad() + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.d, f, ensure_ascii=False, indent=1)
            os.replace(tmp, _pad())
        except Exception:
            pass

    def sterren(self, spel):
        return int(self.d["sterren"].get(spel, 0))

    def totaal_sterren(self):
        return sum(int(v) for v in self.d["sterren"].values())

    def uitslag(self, spel, score, sterren):
        """Bewaart score en sterren (alleen als het beter is). Geeft True bij een nieuw record."""
        nieuw = score > int(self.d["hoogste"].get(spel, -1))
        if nieuw:
            self.d["hoogste"][spel] = score
        self.d["sterren"][spel] = max(self.sterren(spel), sterren)
        self.bewaar()
        return nieuw


# ------------------------------------------------------------------ geluid (zelf gemaakte piepjes, geen bestanden nodig)
class Geluid:
    SR = 22050

    def __init__(self, opslag):
        self.opslag = opslag
        self.ok = False
        self.cache = {}
        self.huidig = None          # welk nummer speelt er
        self._nummers = {}          # naam -> pygame.mixer.Sound (klaar)
        self._kanaal = None
        try:
            pygame.mixer.pre_init(self.SR, -16, 1, 512)
            pygame.mixer.init(self.SR, -16, 1, 512)
            pygame.mixer.set_reserved(1)
            self._kanaal = pygame.mixer.Channel(0)
            self.ok = True
        except Exception:
            pass
        if self.ok:
            import threading
            threading.Thread(target=self._maak_alles, daemon=True).start()

    # ---- muziek (zelf gecomponeerd, zie muziek.py)
    def _maak_alles(self):
        try:
            import muziek
        except Exception:
            return
        for naam in ["dorp"] + [n for n in muziek.NUMMERS if n != "dorp"]:
            try:
                data = muziek.maak(naam)
                if data:
                    self._nummers[naam] = pygame.mixer.Sound(buffer=data)
            except Exception:
                pass

    def muziek(self, naam):
        """Zet het nummer voor deze scene aan (als het al klaar is; anders straks vanzelf)."""
        if not self.ok:
            return
        aan = self.opslag.d.get("muziek", True) and self.opslag.d.get("geluid", True)
        if not aan:
            if self.huidig is not None:
                self._kanaal.fadeout(300)
            self.huidig = None
            return
        if naam == self.huidig and self._kanaal.get_busy():
            return
        nummer = self._nummers.get(naam)
        if nummer is None:
            return
        self._kanaal.set_volume(0.45)
        self._kanaal.play(nummer, loops=-1, fade_ms=600)
        self.huidig = naam

    def _toon(self, noten, vorm="blok", vol=0.25):
        """noten = [(frequentie, seconden), ...]; frequentie 0 = stilte."""
        sleutel = (tuple(noten), vorm, vol)
        if sleutel in self.cache:
            return self.cache[sleutel]
        buf = array.array("h")
        for freq, duur in noten:
            n = int(self.SR * duur)
            for i in range(n):
                if freq <= 0:
                    buf.append(0)
                    continue
                t = i / self.SR
                fase = (t * freq) % 1.0
                if vorm == "blok":
                    v = 1.0 if fase < 0.5 else -1.0
                elif vorm == "driehoek":
                    v = 4 * abs(fase - 0.5) - 1
                elif vorm == "bel":
                    v = math.sin(2 * math.pi * freq * t) * math.exp(-3.0 * t) + \
                        0.4 * math.sin(2 * math.pi * freq * 2.76 * t) * math.exp(-5.0 * t)
                else:  # ruis
                    v = random.uniform(-1, 1)
                env = min(1.0, i / 200.0, (n - i) / 300.0) if vorm != "bel" else min(1.0, (n - i) / 800.0)
                buf.append(int(max(-1, min(1, v)) * env * vol * 32767))
        try:
            s = pygame.mixer.Sound(buffer=buf.tobytes())
        except Exception:
            s = None
        self.cache[sleutel] = s
        return s

    def speel(self, naam):
        if not self.ok or not self.opslag.d.get("geluid", True):
            return
        n = {
            "stap": ([(220, 0.03)], "driehoek", 0.12),
            "deur": ([(330, 0.06), (440, 0.06), (660, 0.1)], "blok", 0.15),
            "goed": ([(660, 0.07), (880, 0.12)], "blok", 0.18),
            "fout": ([(200, 0.12), (150, 0.18)], "blok", 0.18),
            "snoep": ([(988, 0.05), (1319, 0.09)], "driehoek", 0.25),
            "wind": ([(0, 0.01)] + [(1, 0.6)], "ruis", 0.10),
            "plof": ([(140, 0.08)], "driehoek", 0.3),
            "ster": ([(523, 0.08), (659, 0.08), (784, 0.08), (1047, 0.25)], "blok", 0.18),
            "klok": ([(392, 2.2)], "bel", 0.45),
            "plaats": ([(523, 0.05), (784, 0.07)], "driehoek", 0.2),
            "weg": ([(392, 0.05), (262, 0.08)], "driehoek", 0.2),
        }.get(naam)
        if n:
            s = self._toon(*n)
            if s:
                s.play()

    def noot(self, freq, duur=0.18):
        if self.ok and self.opslag.d.get("geluid", True):
            s = self._toon([(freq, duur)], "driehoek", 0.22)
            if s:
                s.play()


# ------------------------------------------------------------------ letters
_fonts = {}


def letter(grootte, vet=False, pixel=False):
    sleutel = (grootte, vet, pixel)
    if sleutel not in _fonts:
        if pixel:
            f = pygame.font.Font(None, grootte)  # standaard pygame-letter: scherp als je hem niet gladmaakt
        else:
            f = None
            for naam in ("segoeui", "verdana", "arial", "dejavusans"):
                try:
                    p = pygame.font.match_font(naam, bold=vet)
                    if p:
                        f = pygame.font.Font(p, grootte)
                        break
                except Exception:
                    pass
            f = f or pygame.font.Font(None, int(grootte * 1.3))
        _fonts[sleutel] = f
    return _fonts[sleutel]


def tekst(surf, t, pos, grootte=24, kleur=(240, 240, 245), midden=False, vet=False, pixel=False, schaduw=True,
          rechts=False):
    f = letter(grootte, vet, pixel)
    aa = not pixel
    beeld = f.render(t, aa, kleur)
    x, y = pos
    if midden:
        x -= beeld.get_width() // 2
    elif rechts:
        x -= beeld.get_width()
    if schaduw:
        sch = f.render(t, aa, (0, 0, 0))
        d = 1 if pixel else 2
        surf.blit(sch, (x + d, y + d))
    surf.blit(beeld, (x, y))
    return beeld.get_width()


def pijl(surf, richting, cx, cy, r, kleur):
    """Een dikke pijl (zelf getekend, werkt met elk lettertype)."""
    vorm = [(1, 0), (0, -1), (0, -0.4), (-1, -0.4), (-1, 0.4), (0, 0.4), (0, 1)]  # wijst naar rechts
    hoek = {"rechts": 0, "neer": math.pi / 2, "links": math.pi, "op": -math.pi / 2}[richting]
    c, s_ = math.cos(hoek), math.sin(hoek)
    pygame.draw.polygon(surf, kleur, [(cx + (x * c - y * s_) * r, cy + (x * s_ + y * c) * r) for x, y in vorm])


def vinkje(surf, cx, cy, r, kleur):
    pygame.draw.lines(surf, kleur, False, [(cx - r, cy), (cx - r * 0.3, cy + r * 0.7), (cx + r, cy - r * 0.8)],
                      max(3, r // 3))


# ------------------------------------------------------------------ seizoen en tijd van de echte wereld
def seizoen(nu=None):
    m = (nu or datetime.datetime.now()).month
    return "winter" if m in (12, 1, 2) else "lente" if m in (3, 4, 5) else "zomer" if m in (6, 7, 8) else "herfst"


def is_avond(nu=None):
    u = (nu or datetime.datetime.now()).hour
    return u >= 19 or u < 7


def gloed(straal, kleur, kracht=1.0):
    """Zachte lichtcirkel (om met BLEND_ADD over een donkere scène te leggen)."""
    s = pygame.Surface((straal * 2, straal * 2), pygame.SRCALPHA)
    for r in range(straal, 0, -2):
        a = (1 - r / straal) ** 2
        c = tuple(min(255, int(k * a * kracht)) for k in kleur)
        pygame.draw.circle(s, c + (255,), (straal, straal), r)
    return s


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ------------------------------------------------------------------ stijlen: mix (standaard), retro, kleurrijk
STIJLEN = ["mix", "retro", "kleurrijk"]
STIJL_NAAM = {"mix": "Mix", "retro": "Retro", "kleurrijk": "Kleurrijk"}
LIJN = (30, 20, 50)   # de donkere cartoonrand bij 'kleurrijk'
PALET = [(0, 0, 0), (29, 43, 83), (126, 37, 83), (0, 135, 81), (171, 82, 54), (95, 87, 79), (194, 195, 199),
         (255, 241, 232), (255, 0, 77), (255, 163, 0), (255, 236, 39), (0, 228, 54), (41, 173, 255),
         (131, 118, 156), (255, 119, 168), (255, 204, 170)]   # het bekende 16-kleuren 'PICO-8'-palet
_palet_doek = {}


def stijl_van(spel):
    st = spel.opslag.d.get("stijl", "mix")
    return st if st in STIJLEN else "mix"


def palet_filter(surf, licht=0.0):
    """Zet een plaatje om naar de 16 retrokleuren (geeft een nieuw plaatje terug).
    licht > 0 maakt donkere (nacht)kleuren eerst wat lichter, anders worden ze allemaal zwart."""
    if licht:
        helft = surf.copy()
        m = int(255 * licht)
        helft.fill((m, m, m), special_flags=pygame.BLEND_RGB_MULT)
        surf = surf.copy()
        surf.blit(helft, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        surf.fill((14, 22, 50), special_flags=pygame.BLEND_RGB_ADD)
    try:
        import numpy as np
        if not hasattr(palet_filter, "_lut"):
            # eenmalig: voor elke kleur (5 bits per kanaal) de dichtstbijzijnde retrokleur opzoeken
            pal = np.array(PALET, dtype=np.int32)
            stap = np.arange(32, dtype=np.int32) * 8 + 4
            r, g, b = np.meshgrid(stap, stap, stap, indexing="ij")
            kl = np.stack([r, g, b], axis=-1).reshape(-1, 3)
            d = ((kl[:, None, :] - pal[None, :, :]) ** 2 * np.array([3, 4, 2])).sum(axis=2)
            palet_filter._lut = pal[d.argmin(axis=1)].astype(np.uint8).reshape(32, 32, 32, 3)
        arr = pygame.surfarray.pixels3d(surf) >> 3
        uit_arr = palet_filter._lut[arr[..., 0], arr[..., 1], arr[..., 2]]
        del arr
        return pygame.surfarray.make_surface(uit_arr)
    except ImportError:
        pass
    maat = surf.get_size()   # zonder numpy: SDL doet het (iets minder precies)
    if maat not in _palet_doek:
        d = pygame.Surface(maat, 0, 8)
        d.set_palette(PALET + [(0, 0, 0)] * (256 - len(PALET)))
        _palet_doek[maat] = d
    d = _palet_doek[maat]
    d.blit(surf, (0, 0))
    uit = pygame.Surface(maat)
    uit.blit(d, (0, 0))
    return uit


def retro_klein(surf, factor=4, licht=0.27):
    """Een glad (hoge resolutie) beeld als grove pixels: verkleinen + 16 kleuren. Geeft het kleine beeld terug."""
    w, h = surf.get_size()
    klein = pygame.transform.smoothscale(surf, (w // factor, h // factor))
    return palet_filter(klein, licht)


def omlijn(laag, dikte=4, kleur=LIJN):
    """Tekent een donkere rand om alles wat op een doorzichtige laag staat (cartoonstijl).
    Geeft een nieuwe laag terug: eerst de rand, dan de laag zelf erop."""
    masker = pygame.mask.from_surface(laag, 30)
    rand = masker.to_surface(setcolor=kleur + (255,), unsetcolor=(0, 0, 0, 0))
    uit = pygame.Surface(laag.get_size(), pygame.SRCALPHA)
    d2 = int(dikte * 0.7)
    for dx, dy in ((dikte, 0), (-dikte, 0), (0, dikte), (0, -dikte), (d2, d2), (-d2, d2), (d2, -d2), (-d2, -d2)):
        uit.blit(rand, (dx, dy))
    uit.blit(laag, (0, 0))
    return uit


def teken_kind(s, x, y, f, jas, muts, r=1, stap=0.0, lijn=True):
    """Cartoon-kind (voor de stijl 'kleurrijk'). x,y = voeten midden, f = grootte."""
    been = math.sin(stap) * 8 * f
    if lijn:
        pygame.draw.line(s, LIJN, (x - 8 * f, y - 40 * f), (x - 8 * f - been, y + 3 * f), int(17 * f))
        pygame.draw.line(s, LIJN, (x + 8 * f, y - 40 * f), (x + 8 * f + been, y + 3 * f), int(17 * f))
        pygame.draw.rect(s, LIJN, (x - 27 * f, y - 105 * f, 54 * f, 74 * f), border_radius=int(18 * f))
        pygame.draw.circle(s, LIJN, (int(x), int(y - 122 * f)), int(27 * f))
        pygame.draw.ellipse(s, LIJN, (x - 29 * f, y - 155 * f, 58 * f, 40 * f))
    pygame.draw.line(s, (40, 40, 60), (x - 8 * f, y - 40 * f), (x - 8 * f - been, y), int(9 * f))
    pygame.draw.line(s, (40, 40, 60), (x + 8 * f, y - 40 * f), (x + 8 * f + been, y), int(9 * f))
    pygame.draw.rect(s, jas, (x - 22 * f, y - 100 * f, 44 * f, 64 * f), border_radius=int(14 * f))
    pygame.draw.circle(s, (240, 205, 175), (int(x), int(y - 122 * f)), int(22 * f))
    pygame.draw.ellipse(s, muts, (x - 24 * f, y - 150 * f, 48 * f, 30 * f))
    pygame.draw.circle(s, (255, 255, 255), (int(x), int(y - 152 * f)), int(6 * f))
    pygame.draw.circle(s, (30, 30, 30), (int(x + 7 * f * r), int(y - 124 * f)), max(2, int(3 * f)))


def ster(s, cx, cy, r, kleur, rand=None):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    pygame.draw.polygon(s, kleur, pts)
    if rand:
        pygame.draw.polygon(s, rand, pts, max(2, int(r / 6)))


# ------------------------------------------------------------------ toetsen voor 2 spelers
SPELER_TOETSEN = [
    dict(links=pygame.K_LEFT, rechts=pygame.K_RIGHT, op=pygame.K_UP, neer=pygame.K_DOWN, actie=pygame.K_SPACE,
         naam="Speler 1", uitleg="pijltjes + spatie"),
    dict(links=pygame.K_a, rechts=pygame.K_d, op=pygame.K_w, neer=pygame.K_s, actie=pygame.K_e,
         naam="Speler 2", uitleg="W A S D + E"),
]


class Scene:
    """Elke minigame is een Scene. res = interne grootte, pixel = scherp (retro) of glad opschalen."""
    res = (1280, 720)
    pixel = False
    naam = ""

    def __init__(self, spel):
        self.spel = spel
        self.klaar = False

    def toets(self, ev):
        pass

    def muis(self, ev, pos):
        pass

    def update(self, dt):
        pass

    def teken(self, s):
        pass


# ================================================================== basis voor nieuwe spellen (alle 3 stijlen)
def fel(kleur, stijl):
    """Bij 'kleurrijk' worden kleuren feller (meer verzadiging)."""
    if stijl != "kleurrijk":
        return kleur
    import colorsys
    h, l, sat = colorsys.rgb_to_hls(*(c / 255 for c in kleur))
    r, g, b = colorsys.hls_to_rgb(h, min(0.75, l * 1.08 + 0.04), min(1.0, sat * 1.5 + 0.15))
    return (int(r * 255), int(g * 255), int(b * 255))


class HDSpel(Scene):
    """Een spel op 1280 x 720. De subklasse tekent; deze klasse regelt de drie stijlen:
    mix = gewoon, kleurrijk = felle kleuren + dikke randen om de voorgrond, retro = grove pixels in 16 kleuren.
    Ook gemeen: uitleg-scherm, aftellen 3-2-1, speeltijd, de balk bovenaan."""
    res = (1280, 720)
    pixel = False
    titel = ""
    speeltijd = 60
    retro_licht = 0.0          # >0 voor donkere (nacht)spellen

    def __init__(self, spel):
        super().__init__(spel)
        self.stijl = stijl_van(spel)
        self.n = 2 if spel.twee else 1
        self.uitleg = True
        self.start_tel = 3.0
        self.tijd = float(self.speeltijd)
        self.t = 0.0
        self.klaar_t = None      # aftellen na het einde, voor de uitslag
        self.teksten = []        # zwevende tekstjes [x, y, tekst, kleur, levensduur]

    # ---- door de subklasse in te vullen
    def achter(self, s):
        pass

    def voor(self, s):
        pass

    def effect(self, s):
        pass

    def spel_update(self, dt):
        pass

    def spel_toets(self, ev):
        pass

    def balk(self):
        """(links, midden, rechts) teksten voor de balk bovenaan."""
        return (self.titel, "", "Tijd: %d" % max(0, math.ceil(self.tijd)))

    def uitleg_regels(self):
        return [self.titel]

    def einde(self):
        self.spel.naar_dorp()

    # ---- gemeenschappelijk
    def k(self, kleur):
        # ook bij retro iets feller: dan kiest het 16-kleurenpalet de goede kleur (groen blijft groen)
        return fel(kleur, "kleurrijk" if self.stijl in ("kleurrijk", "retro") else self.stijl)

    def zweef(self, x, y, t, kleur=(255, 255, 255), duur=1.0):
        self.teksten.append([x, y, t, kleur, duur])

    def stop_spel(self, na=1.2):
        if self.klaar_t is None:
            self.klaar_t = na

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
        if self.start_tel > 0 or self.klaar_t is not None:
            return
        self.spel_toets(ev)

    def update(self, dt):
        self.t += dt
        for t in self.teksten:
            t[1] -= 50 * dt
            t[4] -= dt
        self.teksten = [t for t in self.teksten if t[4] > 0]
        if self.uitleg:
            return
        if self.start_tel > 0:
            self.start_tel -= dt
            return
        if self.klaar_t is not None:
            self.klaar_t -= dt
            self.spel_update(dt)
            if self.klaar_t <= 0:
                self.einde()
            return
        if self.speeltijd:
            self.tijd -= dt
            if self.tijd <= 0:
                self.tijd = 0
                self.stop_spel(0.8)
        self.spel_update(dt)

    def teken(self, s):
        self.achter(s)
        if self.stijl == "kleurrijk":
            laag = pygame.Surface(self.res, pygame.SRCALPHA)
            self.voor(laag)
            s.blit(omlijn(laag, 3), (0, 0))
        else:
            self.voor(s)
        self.effect(s)
        for x, y, t, kl, _ in self.teksten:
            tekst(s, t, (int(x), int(y)), 34, kl, midden=True, vet=True)
        links, midden, rechts = self.balk()
        if self.stijl == "retro":
            klein = retro_klein(s, 4, self.retro_licht)
            lw = klein.get_width()
            pygame.draw.rect(klein, (0, 0, 0), (0, 0, lw, 12))
            tekst(klein, links.upper(), (3, 2), 16, (255, 163, 0), pixel=True, schaduw=False)
            tekst(klein, midden.upper(), (lw // 2, 2), 16, (255, 255, 255), midden=True, pixel=True, schaduw=False)
            tekst(klein, rechts.upper(), (lw - 3, 2), 16, (255, 255, 255), rechts=True, pixel=True, schaduw=False)
            if self.start_tel > 0 and not self.uitleg:
                tekst(klein, str(math.ceil(self.start_tel)), (lw // 2, 60), 48, (255, 255, 255), midden=True, pixel=True)
            s.blit(pygame.transform.scale(klein, self.res), (0, 0))
        else:
            W, H = self.res
            pygame.draw.rect(s, (0, 0, 0), (0, 0, W, 56))
            tekst(s, links, (20, 10), 32, (255, 179, 71), vet=True)
            tekst(s, midden, (W // 2, 10), 32, (255, 255, 255), midden=True, vet=True)
            tekst(s, rechts, (W - 20, 10), 32, (255, 120, 90) if (self.speeltijd and self.tijd < 10) else (255, 255, 255),
                  rechts=True, vet=True)
            if self.start_tel > 0 and not self.uitleg:
                tekst(s, str(math.ceil(self.start_tel)), (W // 2, 250), 140, (255, 255, 255), midden=True, vet=True)
        if self.uitleg:
            self._teken_uitleg(s)

    def _teken_uitleg(self, s):
        W, H = self.res
        dek = pygame.Surface((W, H), pygame.SRCALPHA)
        dek.fill((8, 8, 20, 215))
        s.blit(dek, (0, 0))
        regels = self.uitleg_regels() + ["", "Enter = beginnen   ·   Esc = terug naar het dorp"]
        y = max(40, H // 2 - len(regels) * 21)
        for i, r in enumerate(regels):
            if r:
                if i == 0:
                    tekst(s, r, (W // 2, y), 46, (255, 179, 71), midden=True, vet=True)
                else:
                    tekst(s, r, (W // 2, y), 28, (235, 235, 245), midden=True)
            y += 58 if i == 0 else 42
