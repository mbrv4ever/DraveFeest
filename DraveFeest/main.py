# -*- coding: utf-8 -*-
# DraveFeest - een dorp vol feestdagen, met voor elke feestdag een eigen spel.
# Copyright (C) 2026 Dravenlock (Roger & Claudio). Vrije software onder de GNU GPL v3.0.
import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame  # noqa: E402

from basis import APP_NAAM, VERSIE, Opslag, Geluid, Scene, tekst, bron  # noqa: E402


class Uitslag(Scene):
    res = (1280, 720)

    def __init__(self, spel, titel, regels, sterren, record):
        super().__init__(spel)
        self.titel, self.regels, self.sterren, self.record = titel, regels, sterren, record
        self.t = 0.0
        self._gespeeld = 0

    def toets(self, ev):
        if ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_e) and self.t > 0.8:
            self.spel.naar_dorp()

    def muis(self, ev, pos):
        if ev.type == pygame.MOUSEBUTTONDOWN and self.t > 0.8:
            self.spel.naar_dorp()

    def update(self, dt):
        self.t += dt
        n = min(self.sterren, int(self.t / 0.45))
        if n > self._gespeeld:
            self._gespeeld = n
            self.spel.geluid.speel("ster")

    def teken(self, s):
        s.fill((14, 14, 22))
        pygame.draw.rect(s, (26, 26, 40), (240, 90, 800, 540), border_radius=24)
        pygame.draw.rect(s, (255, 179, 71), (240, 90, 800, 540), 3, border_radius=24)
        tekst(s, self.titel, (640, 130), 52, (255, 255, 255), midden=True, vet=True)
        for i in range(3):
            aan = i < self._gespeeld
            self._ster(s, 470 + i * 170, 290, 60, (255, 205, 60) if aan else (60, 60, 75))
        y = 390
        for r in self.regels:
            tekst(s, r, (640, y), 32, (225, 225, 235), midden=True)
            y += 46
        if self.record:
            tekst(s, "Nieuw record!", (640, y + 6), 34, (90, 217, 136), midden=True, vet=True)
        if self.t > 0.8:
            tekst(s, "Druk op Enter om terug te gaan naar het dorp", (640, 580), 26, (150, 150, 165), midden=True)

    @staticmethod
    def _ster(s, cx, cy, r, kleur):
        import math
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.45
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        pygame.draw.polygon(s, kleur, pts)


class Spel:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(APP_NAAM)
        try:
            pygame.display.set_icon(pygame.image.load(bron(os.path.join("assets", "icon.png"))))
        except Exception:
            pass
        info = pygame.display.Info()
        w = min(1440, int(info.current_w * 0.9)) if info.current_w > 0 else 1280
        self.venster = pygame.display.set_mode((w, w * 9 // 16), pygame.RESIZABLE)
        self.volscherm = False
        self.klok = pygame.time.Clock()
        self.opslag = Opslag()
        self.geluid = Geluid(self.opslag)
        self.scene = None
        self._doekjes = {}
        self._toast, self._toast_t = "", 0.0
        self.naar_dorp()

    # ---- wisselen
    def naar_dorp(self):
        from dorp import Dorp
        if not hasattr(self, "_dorp"):
            self._dorp = Dorp(self)
        self._dorp.terug()
        self.scene = self._dorp

    def start(self, scene_cls):
        self.geluid.speel("deur")
        self.scene = scene_cls(self)

    def uitslag(self, spelcode, titel, score, sterren, regels):
        record = self.opslag.uitslag(spelcode, score, sterren)
        self.scene = Uitslag(self, titel, regels, sterren, record)

    @property
    def twee(self):
        return bool(self.opslag.d.get("twee"))

    # ---- scherm
    def _doek(self):
        r = self.scene.res
        if r not in self._doekjes:
            self._doekjes[r] = pygame.Surface(r).convert()
        return self._doekjes[r]

    def _plek(self):
        """Waar het spelbeeld in het venster staat (met zwarte randen als de verhouding anders is)."""
        vw, vh = self.venster.get_size()
        rw, rh = self.scene.res
        f = min(vw / rw, vh / rh)
        if self.scene.pixel and f >= 1:
            f = max(1, int(f))  # hele getallen = scherpe pixels
        w, h = int(rw * f), int(rh * f)
        return pygame.Rect((vw - w) // 2, (vh - h) // 2, w, h)

    def muis_pos(self, pos):
        p = self._plek()
        rw, rh = self.scene.res
        return ((pos[0] - p.x) * rw / max(1, p.w), (pos[1] - p.y) * rh / max(1, p.h))

    def wissel_volscherm(self):
        self.volscherm = not self.volscherm
        if self.volscherm:
            self.venster = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.venster = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)

    def toast(self, t, duur=2.2):
        self._toast, self._toast_t = t, duur

    # ---- vangnet: een fout in een spel laat niet het hele spel crashen
    def _fout(self, e):
        import traceback
        try:
            pad = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "DraveFeest", "fout.log")
            with open(pad, "a", encoding="utf-8") as f:
                f.write("\n==== %s  v%s\n%s" % (__import__("datetime").datetime.now(), VERSIE, traceback.format_exc()))
        except Exception:
            pass
        naam = getattr(self.scene, "naam", "") or type(self.scene).__name__
        if naam == "dorp":
            raise e
        self.naar_dorp()
        self._dorp.meld("Oeps, er ging iets mis in %s. Meld het via dravenlock.nl (fout.log)." % naam)

    # ---- lus
    def loop(self, max_frames=None):
        n = 0
        while True:
            dt = min(0.05, self.klok.tick(60) / 1000.0)
            try:
                if self._stap(dt) == "stop":
                    return
            except Exception as e:  # noqa: BLE001
                self._fout(e)
            n += 1
            if max_frames and n >= max_frames:
                return

    def _stap(self, dt):
        if True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    if hasattr(self.scene, "bij_afsluiten"):
                        self.scene.bij_afsluiten()
                    self.opslag.bewaar()
                    return "stop"
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_F11 or (ev.key == pygame.K_RETURN and ev.mod & pygame.KMOD_ALT):
                        self.wissel_volscherm()
                        continue
                    if ev.key == pygame.K_m and not getattr(self.scene, "typt", False):
                        # M: alles aan -> muziek uit -> alles uit -> alles aan
                        g, m = self.opslag.d.get("geluid", True), self.opslag.d.get("muziek", True)
                        if g and m:
                            g, m, t = True, False, "Muziek uit (geluidjes aan)"
                        elif g:
                            g, m, t = False, False, "Geluid en muziek uit"
                        else:
                            g, m, t = True, True, "Geluid en muziek aan"
                        self.opslag.d["geluid"], self.opslag.d["muziek"] = g, m
                        self.opslag.bewaar()
                        self.toast(t)
                        continue
                    self.scene.toets(ev)
                elif ev.type == pygame.KEYUP and hasattr(self.scene, "los"):
                    self.scene.los(ev)
                elif ev.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION, pygame.MOUSEWHEEL):
                    pos = self.muis_pos(ev.pos if hasattr(ev, "pos") else pygame.mouse.get_pos())
                    self.scene.muis(ev, pos)
            scene = self.scene
            wil = getattr(scene, "naam", "")
            if wil:                       # de uitslag (naam leeg) houdt het nummer van het spel
                self.geluid.muziek(wil)
            scene.update(dt)
            if scene is not self.scene:
                return
            doek = self._doek()
            scene.teken(doek)
            self.venster.fill((0, 0, 0))
            p = self._plek()
            if p.size == doek.get_size():
                self.venster.blit(doek, p.topleft)
            elif scene.pixel:
                self.venster.blit(pygame.transform.scale(doek, p.size), p.topleft)
            else:
                self.venster.blit(pygame.transform.smoothscale(doek, p.size), p.topleft)
            if self._toast_t > 0:
                self._toast_t -= dt
                from basis import tekst
                vw = self.venster.get_width()
                f = max(18, self.venster.get_height() // 30)
                pygame.draw.rect(self.venster, (20, 16, 40), (vw // 2 - f * 9, f // 2, f * 18, int(f * 1.8)), border_radius=12)
                tekst(self.venster, self._toast, (vw // 2, int(f * 0.8)), f, (255, 230, 150), midden=True, vet=True)
            pygame.display.flip()


def main():
    spel = Spel()
    try:  # Dravenlock: stille update-check (uit te zetten in de melding)
        import drave_update
        drave_update.start(None, APP_NAAM, VERSIE)
    except Exception:
        pass
    spel.loop()
    pygame.quit()


if __name__ == "__main__":
    main()
