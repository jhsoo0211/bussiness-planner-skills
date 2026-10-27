#!/usr/bin/env python3
"""bizplan reel 사운드트랙: 120 BPM 음악 + 화면 이벤트 동기 효과음 (numpy만 사용).

render.cjs가 만든 events.json을 읽어, 영상 길이 그대로 루프가 이어지도록(끝 꼬리를 앞에 겹침) 48kHz 스테레오 WAV를 만든다.

    python sound.py <frames>/events.json bizplan-reel.wav
"""

import json
import sys
import wave

import numpy as np

SR = 48000
BEAT = 0.5
RNG = np.random.default_rng(7)

# 마디(2초)별 스타일은 events.json의 music.styles(paper / blue / note)를 따른다.

# Am – F – C – G (베이스 루트, 3화음)
CHORDS = [(45, [57, 60, 64]), (41, [53, 57, 60]), (48, [55, 60, 64]), (43, [55, 59, 62])]
midi = lambda n: 440.0 * 2 ** ((n - 69) / 12)


# ───────────── DSP helpers ─────────────
def _resp(n, kind, fc, order):
    f = np.fft.rfftfreq(n, 1 / SR)
    if kind == "lp":
        return 1 / np.sqrt(1 + (f / fc) ** (2 * order))
    return 1 / np.sqrt(1 + (fc / np.maximum(f, 1e-3)) ** (2 * order))


def lp(x, fc, order=2):
    return np.fft.irfft(np.fft.rfft(x) * _resp(len(x), "lp", fc, order), len(x))


def hp(x, fc, order=2):
    return np.fft.irfft(np.fft.rfft(x) * _resp(len(x), "hp", fc, order), len(x))


def bp(x, lo, hi, order=2):
    return hp(lp(x, hi, order), lo, order)


def env(n, attack=0.002, decay=0.2, curve=1.0):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-np.maximum(t - attack, 0) / decay) ** curve


def noise(n):
    return RNG.uniform(-1, 1, n)


def secs(d):
    return max(1, int(d * SR))


class Bus:
    def __init__(self, n):
        self.l = np.zeros(n)
        self.r = np.zeros(n)

    def add(self, t, sig, gain=1.0, pan=0.0):
        i = int(round(t * SR))
        if i < 0 or i >= len(self.l):
            return
        sig = sig[: len(self.l) - i] * gain
        self.l[i:i + len(sig)] += sig * np.sqrt((1 - pan) / 2) * 1.414
        self.r[i:i + len(sig)] += sig * np.sqrt((1 + pan) / 2) * 1.414


# ───────────── instruments ─────────────
def kick(soft=False):
    n = secs(0.45)
    t = np.arange(n) / SR
    f = 46 + 110 * np.exp(-t / 0.035)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.32)
    click = hp(noise(n) * env(n, 0.0005, 0.006), 2500)
    return (body + 0.25 * click) * (0.6 if soft else 1.0)


def clap(rim=False):
    n = secs(0.3)
    if rim:
        t = np.arange(n) / SR
        return np.sin(2 * np.pi * 1650 * t) * env(n, 0.0005, 0.018) + 0.3 * bp(noise(n), 2000, 6000) * env(n, 0.0005, 0.01)
    e = sum(np.concatenate([np.zeros(o), env(n - o, 0.001, 0.012)]) for o in (0, secs(0.011), secs(0.022))) + env(n, 0.001, 0.09)
    return bp(noise(n), 900, 5200) * e * 0.8


def hat(open_=False):
    n = secs(0.25 if open_ else 0.06)
    return hp(noise(n), 7000, 3) * env(n, 0.0005, 0.08 if open_ else 0.014)


def bass(note, dur, bright=False):
    n = secs(dur)
    t = np.arange(n) / SR
    f = midi(note)
    saw = 2 * ((t * f) % 1) - 1
    sig = np.sin(2 * np.pi * f * t) + (0.3 if bright else 0.15) * lp(saw, 420 if bright else 300)
    e = np.minimum(1, t / 0.004) * np.exp(-t / (dur * 1.6)) * np.clip((dur - t) / 0.02, 0, 1)
    return sig * e


def pluck(note, style):
    n = secs(0.6)
    t = np.arange(n) / SR
    f = midi(note)
    if style in ("paper", "note"):   # felt piano-ish (note: a touch brighter, shorter)
        sig = np.sin(2 * np.pi * f * t) + (0.3 if style == "paper" else 0.45) * np.sin(4 * np.pi * f * t) * np.exp(-t / 0.08)
        return sig * env(n, 0.003, 0.32 if style == "paper" else 0.22)
    tri = 2 * np.abs(2 * ((t * f) % 1) - 1) - 1   # blue: clean triangle pluck
    return lp(tri, 2600) * env(n, 0.002, 0.18)


def pad(notes, dur, style):
    n = secs(dur + 0.6)
    t = np.arange(n) / SR
    sig = np.zeros(n)
    for note in notes:
        f = midi(note)
        if style in ("paper", "note"):
            sig += np.sin(2 * np.pi * f * t)
        else:
            for d in (0.997, 1.003):
                sig += 0.5 * (2 * ((t * f * d) % 1) - 1)
    if style == "blue":
        sig = lp(sig, 900)
    e = np.clip(t / 0.35, 0, 1) * np.clip((dur + 0.6 - t) / 0.6, 0, 1)
    return sig * e / len(notes)


# ───────────── sound effects ─────────────
def sweep_noise(d, f0, f1, bands=8):
    n = secs(d)
    out = np.zeros(n)
    centres = np.geomspace(f0, f1, bands)
    pos = np.linspace(0, 1, n)
    for i, fc in enumerate(centres):
        w = np.exp(-((pos - i / (bands - 1)) ** 2) / (2 * (0.6 / bands) ** 2))
        out += bp(noise(n), fc / 1.4, fc * 1.4) * w
    return out


def sfx(kind, e):
    d = e.get("d", 0.2)
    if kind == "key":
        n = secs(0.04)
        t = np.arange(n) / SR
        v = 0.6 + 0.4 * RNG.random()
        return (hp(noise(n), 3000) * env(n, 0.0003, 0.004) + 0.4 * np.sin(2 * np.pi * 1100 * t) * env(n, 0.0003, 0.008)) * v, 0.32, RNG.uniform(-0.3, 0.3)
    if kind in ("pencil", "scribble"):
        n = secs(d + 0.05)
        t = np.arange(n) / SR
        strokes = np.abs(np.sin(2 * np.pi * (11 if kind == "pencil" else 16) * t + RNG.random() * 6)) ** 0.6
        grain = bp(noise(n), 1800, 6500) * (0.6 + 0.4 * (RNG.random(n) > 0.6))
        e2 = np.clip(t / 0.01, 0, 1) * np.clip((d + 0.05 - t) / 0.05, 0, 1)
        return grain * strokes * e2, 0.22 if kind == "pencil" else 0.17, RNG.uniform(-0.2, 0.2)
    if kind == "ticks":
        n = secs(d + 0.05)
        out = np.zeros(n)
        for i in range(41):
            # tick i is revealed when expo-out progress reaches i/40 (same curve as the picture)
            j = secs(d * min(1.0, -np.log2(max(1e-9, 1 - i / 40)) / 10))
            m = secs(0.01)
            out[j:j + m] += hp(noise(m), 4000)[: len(out) - j] * env(m, 0.0002, 0.002)[: len(out) - j]
        return out, 0.3, 0.0
    if kind in ("whoosh", "whip", "flood", "riser"):
        dd = {"whip": 0.22, "flood": e.get("d", 0.45) + 0.05}.get(kind, d + 0.1)
        lo, hi = {"whoosh": (300, 4000), "whip": (600, 8000), "flood": (120, 5000), "riser": (300, 3000)}[kind]
        sig = sweep_noise(dd, lo, hi)
        n = len(sig)
        t = np.arange(n) / SR
        shape = np.sin(np.pi * np.clip(t / dd, 0, 1)) ** (2 if kind != "flood" else 0.7)
        if kind == "flood":
            shape *= np.clip(t / dd, 0, 1) ** 1.5
        g = {"whoosh": 0.22, "whip": 0.3, "flood": 0.42, "riser": 0.16}[kind]
        return sig * shape, g, 0.0
    if kind in ("impact", "press"):
        n = secs(1.2 if kind == "impact" else 0.4)
        t = np.arange(n) / SR
        f = 38 + 60 * np.exp(-t / 0.05)
        boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.45 if kind == "impact" else 0.18)
        smack = lp(noise(n), 1200) * env(n, 0.0005, 0.03)
        return boom + 0.5 * smack, 0.75 if kind == "impact" else 0.6, 0.0
    if kind == "clap":
        c, k = clap(), kick(True)
        c = np.pad(c, (0, len(k) - len(c)))
        return c * 1.1 + 0.4 * k, 0.55, 0.0
    if kind == "drop":
        n = secs(0.08)
        t = np.arange(n) / SR
        f = 1100 - 500 * t / 0.08
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.0005, 0.03), 0.18, RNG.uniform(-0.4, 0.4)
    if kind == "stamp":
        n = secs(0.25)
        t = np.arange(n) / SR
        thud = np.sin(2 * np.pi * 120 * t) * env(n, 0.0005, 0.06) + lp(noise(n), 900) * env(n, 0.0005, 0.02)
        return thud, 0.38 if e.get("soft") else 0.6, 0.0
    if kind in ("tick", "pop"):
        n = secs(0.05)
        t = np.arange(n) / SR
        if kind == "pop":
            f = 520 + 600 * t / 0.05
            return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.015), 0.22, RNG.uniform(-0.5, 0.5)
        return np.sin(2 * np.pi * 2100 * t) * env(n, 0.0003, 0.006), 0.2 if e.get("soft") else 0.28, RNG.uniform(-0.3, 0.3)
    if kind == "type":
        n = secs(d + 0.05)
        out = np.zeros(n)
        for i in range(e.get("n", 8)):
            j = secs(d * i / e.get("n", 8))
            m = secs(0.02)
            out[j:j + m] += (hp(noise(m), 2500) * env(m, 0.0003, 0.004))[: n - j]
        return out, 0.28, 0.1
    if kind in ("ding", "reply"):
        n = secs(0.9)
        t = np.arange(n) / SR
        if kind == "ding":
            sig = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / dcy) for f, a, dcy in ((1318.5, 1, 0.35), (2637, 0.35, 0.18), (1975.5, 0.25, 0.25)))
            return sig * np.minimum(1, t / 0.002), 0.22, 0.0
        sig = np.sin(2 * np.pi * 1046.5 * t) * env(n, 0.002, 0.08) + np.sin(2 * np.pi * 1318.5 * t) * env(n, 0.002, 0.12) * (t > 0.07)
        return sig, 0.14, 0.0
    if kind == "scan":
        n = secs(d + 0.1)
        t = np.arange(n) / SR
        f = 180 * (2400 / 180) ** np.clip(t / d, 0, 1)
        zap = lp(2 * ((np.cumsum(f) / SR) % 1) - 1, 5000) * np.sin(np.pi * np.clip(t / (d + 0.1), 0, 1))
        return zap * 0.6 + 0.4 * sweep_noise(d + 0.1, 400, 7000), 0.3, 0.0
    if kind == "sweep":
        n = secs(d + 0.1)
        t = np.arange(n) / SR
        shimmer = np.sin(2 * np.pi * (1800 + 1800 * t / d) * t) * np.sin(np.pi * np.clip(t / (d + 0.1), 0, 1))
        return 0.5 * shimmer + 0.5 * sweep_noise(d + 0.1, 2000, 9000), 0.12, 0.0
    if kind == "steps":
        n = secs(d + 0.1)
        out = np.zeros(n)
        k = 0
        while k / 6 < d:
            j = secs(k / 6)
            m = secs(0.05)
            tt = np.arange(m) / SR
            out[j:j + m] += (np.sin(2 * np.pi * 180 * tt) * env(m, 0.0005, 0.015))[: n - j]
            k += 1
        return out, 0.25, 0.0
    return np.zeros(1), 0.0, 0.0


# ───────────── arrangement ─────────────
def build(events, duration, styles):
    n = int(duration * SR)
    total = n + 3 * SR
    drums, music, fx = Bus(total), Bus(total), Bus(total)
    duck = np.ones(total)
    bars = int(duration / 2)
    first, last = 0, bars - 1   # the first and last bars are kept sparse so the loop joins cleanly

    for b in range(bars):
        sec = styles[b]
        t0 = b * 2.0
        root, triad = CHORDS[b % 4]
        # drums
        kicks = {"paper": [0, 2], "blue": [0, 2, 3.5], "note": [0, 1, 2, 3]}[sec]
        for k in kicks:
            tk = t0 + k * BEAT
            drums.add(tk, kick(soft=sec == "paper"), 0.85)
            i = int(tk * SR)
            m = secs(0.25)
            duck[i:i + m] = np.minimum(duck[i:i + m], 1 - 0.35 * np.exp(-np.arange(m) / SR / 0.09))
        sparse = b in (first, last) or (sec == "paper" and b < 2)
        if not sparse:
            for k in (1, 3):
                drums.add(t0 + k * BEAT, clap(rim=sec == "paper"), 0.3 if sec == "paper" else 0.4, 0.05)
        hats = 0 if sparse else (16 if sec == "note" else 8)
        for h in range(hats):
            th = t0 + h * (2.0 / hats)
            accent = (h % 2 == 1) if hats == 8 else (h % 4 == 2)
            drums.add(th, hat(open_=sec == "note" and h % 8 == 6), (0.15 if accent else 0.07) * (0.8 if sec == "paper" else 1), 0.25)
        # bass
        if not sparse:
            step = 0.5 if sec == "paper" else 0.25
            for s in range(int(2 / step)):
                note = root + (12 if sec == "note" and s % 4 == 3 else 0)
                music.add(t0 + s * step, bass(note, step * 0.9, sec == "blue"), 0.42)
        # arp
        tones = triad + [triad[0] + 12]
        pattern = [0, 1, 2, 3, 2, 1, 2, 3]
        step = 0.25 if sec == "paper" else 0.125
        shift = {"paper": 0, "blue": 12, "note": 12}[sec]
        for s in range(int(2 / step)):
            music.add(t0 + s * step, pluck(tones[pattern[s % 8]] + shift, sec),
                      {"paper": 0.2, "blue": 0.13, "note": 0.12}[sec], -0.35 if s % 2 else 0.35)
        # pad
        music.add(t0, pad([triad[0] - 12] + triad, 2.0, sec), {"paper": 0.08, "blue": 0.12, "note": 0.09}[sec])

    for e in events:
        sig, gain, pan = sfx(e["kind"], e)
        if gain > 0:
            fx.add(e["t"], sig, gain, pan)

    music.l *= duck
    music.r *= duck
    dry_l = drums.l + music.l + fx.l
    dry_r = drums.r + music.r + fx.r
    # small room: exponentially decaying noise IR, sent from music + fx
    m = secs(1.1)
    tt = np.arange(m) / SR
    irs = [lp(noise(m), 5000) * np.exp(-tt / 0.32) for _ in range(2)]
    irs = [ir / np.sqrt(np.sum(ir ** 2)) for ir in irs]
    size = 1 << int(np.ceil(np.log2(total + m)))
    wet = []
    for send, ir in ((music.l + fx.l, irs[0]), (music.r + fx.r, irs[1])):
        wet.append(np.fft.irfft(np.fft.rfft(send, size) * np.fft.rfft(ir, size), size)[:total])
    left = dry_l + 0.22 * wet[0]
    right = dry_r + 0.22 * wet[1]

    # loop: fold the tail past `duration` back onto the start
    out = np.stack([left[:n].copy(), right[:n].copy()])
    out[0, : total - n] += left[n:]
    out[1, : total - n] += right[n:]
    out = np.tanh(out * 1.1) / np.tanh(1.1)
    out *= 0.56 / np.max(np.abs(out))   # ≈ -14 LUFS, headroom for AAC
    return out


def main():
    events_path, out_path = sys.argv[1], sys.argv[2]
    data = json.load(open(events_path, encoding="utf-8"))
    bars = int(data["duration"] / 2)
    styles = (data.get("music") or {}).get("styles") or ["paper"] * bars
    audio = build(data["events"], data["duration"], styles)
    pcm = (np.clip(audio.T, -1, 1) * 32767).astype("<i2")
    with wave.open(out_path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"wrote {out_path} ({audio.shape[1] / SR:.2f}s)")


if __name__ == "__main__":
    main()
