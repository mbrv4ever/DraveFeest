# -*- coding: utf-8 -*-
# DraveFeest - zelfgemaakte chiptune-muziek. Geen muziekbestanden: elk deuntje wordt in code gecomponeerd
# (akkoorden + melodie + bas + arpeggio + drums) en met numpy omgezet naar geluid.
# Alle melodieen zijn eigen composities van Dravenlock (gegenereerd uit vaste 'zaadjes').
# Copyright (C) 2026 Dravenlock (Roger & Claudio). Vrije software onder de GNU GPL v3.0.
import random

try:
    import numpy as np
except ImportError:      # zonder numpy geen muziek (geluidjes werken wel)
    np = None

SR = 22050
MAJEUR = [0, 2, 4, 5, 7, 9, 11]
MINEUR = [0, 2, 3, 5, 7, 8, 10]

# Per scene: tempo, maatsoort, grondtoon (midi), toonladder, akkoordenschema (trappen 0..6),
# ritme van de melodie (in tellen, per maat), instrumenten en drums.
NUMMERS = {
    "dorp": dict(bpm=104, maat=4, grond=60, ladder=MAJEUR, akk=[0, 5, 3, 4, 0, 3, 4, 0], ritme=[1, 0.5, 0.5, 1, 1],
                 lead="puls", arp=True, drums="zacht", zaad=7),
    "sintmaarten": dict(bpm=88, maat=3, grond=57, ladder=MINEUR, akk=[0, 5, 2, 6, 0, 3, 4, 0], ritme=[1, 1, 1],
                        lead="driehoek", arp=True, drums=None, zaad=11),
    "sinterklaas": dict(bpm=126, maat=2, grond=62, ladder=MAJEUR, akk=[0, 4, 0, 4, 3, 0, 4, 0], ritme=[0.5, 0.5, 0.5, 0.5],
                        lead="puls", arp=False, drums="mars", zaad=5),
    "kerst": dict(bpm=84, maat=3, grond=65, ladder=MAJEUR, akk=[0, 3, 0, 4, 5, 3, 4, 0], ritme=[2, 1],
                  lead="bel", arp=True, drums=None, zaad=25),
    "nieuwjaar": dict(bpm=140, maat=4, grond=64, ladder=MAJEUR, akk=[0, 4, 5, 3, 0, 4, 3, 4], ritme=[0.5, 0.5, 1, 0.5, 0.5, 1],
                      lead="puls", arp=True, drums="feest", zaad=31),
    "pasen": dict(bpm=112, maat=3, grond=67, ladder=MAJEUR, akk=[0, 3, 4, 0, 5, 3, 4, 0], ritme=[1, 0.5, 0.5, 1],
                  lead="driehoek", arp=True, drums="zacht", zaad=17),
    "koningsdag": dict(bpm=118, maat=4, grond=58, ladder=MAJEUR, akk=[0, 3, 4, 0, 0, 3, 4, 0], ritme=[1, 0.5, 0.5, 1, 0.5, 0.5],
                       lead="koper", arp=False, drums="mars", zaad=3),
    "valentijn": dict(bpm=92, maat=4, grond=63, ladder=MAJEUR, akk=[0, 5, 1, 4, 0, 5, 3, 4], ritme=[1.5, 0.5, 1, 1],
                      lead="driehoek", arp=True, drums="zacht", zaad=14),
    "carnaval": dict(bpm=132, maat=2, grond=60, ladder=MAJEUR, akk=[0, 4, 4, 0, 0, 4, 4, 0], ritme=[0.5, 0.5, 0.5, 0.5],
                     lead="koper", arp=False, drums="humpa", zaad=9),
}


def _hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12.0)


def _toon(freq, duur, vorm, vol=1.0):
    n = max(1, int(SR * duur))
    t = np.arange(n) / SR
    fase = (t * freq) % 1.0
    if vorm == "puls":
        v = np.where(fase < 0.25, 1.0, -0.6)
        env = np.minimum(1, t / 0.005) * (0.65 + 0.35 * np.exp(-t * 6))
    elif vorm == "driehoek":
        v = 4 * np.abs(fase - 0.5) - 1
        env = np.minimum(1, t / 0.01) * (0.7 + 0.3 * np.exp(-t * 4))
    elif vorm == "koper":
        v = np.where(fase < 0.5, 1.0, -1.0) * 0.6 + (2 * fase - 1) * 0.4
        env = np.minimum(1, t / 0.03) * (0.8 + 0.2 * np.sin(t * 30))
    elif vorm == "bel":
        v = (np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 2.0 * t) * np.exp(-t * 3)
             + 0.3 * np.sin(2 * np.pi * freq * 3.01 * t) * np.exp(-t * 5)) / 1.6
        env = np.exp(-t * 2.2)
    else:  # sinus
        v = np.sin(2 * np.pi * freq * t)
        env = np.ones(n)
    loslaten = np.minimum(1, (n - np.arange(n)) / (SR * 0.02))
    return v * env * loslaten * vol


def _drum(soort, n):
    t = np.arange(n) / SR
    if soort == "kick":
        f = 50 + 90 * np.exp(-t * 30)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 18)
    rnd = np.random.default_rng(len(soort))
    ruis = rnd.uniform(-1, 1, n)
    if soort == "snare":
        return ruis * np.exp(-t * 28) * 0.8
    return (ruis - np.concatenate([[0], ruis[:-1]])) * np.exp(-t * 90) * 0.35   # hihat: hoge ruis, heel kort


def maak(naam):
    """Geeft een 16-bits mono buffer (bytes) terug voor dit nummer, of None zonder numpy."""
    if np is None or naam not in NUMMERS:
        return None
    s = NUMMERS[naam]
    rnd = random.Random(s["zaad"])
    tel = 60.0 / s["bpm"]
    maat = s["maat"]
    akk = s["akk"] * 2                   # twee keer het schema: A en A'
    totaal = int(SR * tel * maat * len(akk))
    lead = np.zeros(totaal)
    bas = np.zeros(totaal)
    arp = np.zeros(totaal)
    drum = np.zeros(totaal)
    lad = s["ladder"]

    def noot(trap, octaaf=0):
        o, d = divmod(trap, 7)
        return s["grond"] + 12 * (o + octaaf) + lad[d]

    def leg(spoor, start, data):
        a = int(start * SR)
        b = min(len(spoor), a + len(data))
        if a < b:
            spoor[a:b] += data[:b - a]

    # een vast ritme per maat, met af en toe een variatie
    ritme = list(s["ritme"])
    while sum(ritme) < maat:
        ritme.append(maat - sum(ritme))
    vorige = 2
    motief = []
    for m, a in enumerate(akk):
        tijd0 = m * maat * tel
        akkoord = [a, a + 2, a + 4]
        # melodie: op de zware tel een akkoordtoon, daartussen stapjes; einde van een zin = grondtoon, lang
        eind_zin = (m % 4) == 3
        if m < len(s["akk"]):
            r = ritme if not eind_zin else [maat]
            noten = []
            for i, d in enumerate(r):
                if i == 0 or rnd.random() < 0.45:
                    kandidaten = [x + 7 * k for x in akkoord for k in (0, 1)]
                else:
                    kandidaten = [vorige - 1, vorige + 1, vorige - 2, vorige + 2]
                kandidaten = [x for x in kandidaten if 0 <= x <= 11]
                kandidaten.sort(key=lambda x: abs(x - vorige) + rnd.random() * 1.5 + (1.6 if x == vorige else 0))
                p = kandidaten[0] if not (eind_zin and i == 0) else (a % 7) + (7 if a % 7 < 3 else 0)
                noten.append((p, d))
                vorige = p
            motief.append(noten)
        else:
            # tweede helft: dezelfde melodie, met kleine versieringen (zo blijft het herkenbaar)
            noten = []
            for p, d in motief[m - len(s["akk"])]:
                if d >= 1 and rnd.random() < 0.3:
                    noten += [(p, d / 2), (min(11, p + 1), d / 2)]
                else:
                    noten.append((p, d))
        t = tijd0
        for p, d in noten:
            leg(lead, t, _toon(_hz(noot(p, 1)), d * tel * 0.92, s["lead"], 0.34))
            t += d * tel
        # bas: grondtoon op tel 1, kwint halverwege (bij humpa: op elke tel om en om)
        for b in range(maat):
            if s["drums"] == "humpa" or b == 0 or (maat == 4 and b == 2):
                trap = a if (b % 2 == 0) else a + 4
                leg(bas, tijd0 + b * tel, _toon(_hz(noot(trap, -1)), tel * 0.8, "driehoek", 0.42))
        # arpeggio: akkoordtonen snel achter elkaar, zacht
        if s["arp"]:
            stap = tel / 2
            for k in range(int(maat * 2)):
                trap = akkoord[k % 3]
                leg(arp, tijd0 + k * stap, _toon(_hz(noot(trap, 0)), stap * 0.9, "driehoek", 0.13))
        # drums
        d = s["drums"]
        if d:
            for b in range(maat):
                tb = tijd0 + b * tel
                if d in ("feest", "mars", "zacht", "humpa") and (b % 2 == 0):
                    leg(drum, tb, _drum("kick", int(SR * 0.18)) * (0.5 if d == "zacht" else 0.8))
                if d in ("feest", "mars", "humpa") and (b % 2 == 1):
                    leg(drum, tb, _drum("snare", int(SR * 0.12)) * 0.5)
                if d in ("feest", "zacht"):
                    for h in (0, 0.5):
                        leg(drum, tb + h * tel, _drum("hihat", int(SR * 0.04)) * (0.6 if d == "feest" else 0.35))
    mixje = lead + bas + arp + drum * 0.7
    # zachte galm voor een warmer geluid
    vertraging = int(SR * 0.12)
    galm = np.zeros_like(mixje)
    galm[vertraging:] = mixje[:-vertraging] * 0.22
    mixje = mixje + galm
    piek = np.max(np.abs(mixje)) or 1.0
    mixje = mixje / piek * 0.8
    # begin en eind zacht laten aansluiten (het nummer herhaalt zich)
    kant = int(SR * 0.01)
    mixje[:kant] *= np.linspace(0, 1, kant)
    mixje[-kant:] *= np.linspace(1, 0, kant)
    return (mixje * 32767).astype(np.int16).tobytes()


if __name__ == "__main__":   # proef: schrijf alle nummers als .wav
    import sys
    import wave
    import time
    for naam in NUMMERS:
        t0 = time.time()
        data = maak(naam)
        with wave.open((sys.argv[1] if len(sys.argv) > 1 else ".") + "/%s.wav" % naam, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(data)
        print(naam, "%.1f s muziek, gemaakt in %.2f s" % (len(data) / 2 / SR, time.time() - t0))
