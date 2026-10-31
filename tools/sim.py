"""Rechnung der Balancing-Ziele (Spec Abschnitt 7).

Zeit in Tagen, Tag 0 = Ende des Einstiegs (nach den 21 Tagen). Fokus dauert
cost x 7 Tage. Monatsschritt alle 30 Tage. Simuliert werden nur Parteibasis,
Aufschaukeln und Fehlurteile; Stabilitaet, PP, Kasse und Meinungen nicht.
"""
from __future__ import annotations

import heapq
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

MONTH = 30
HORIZON_DAYS = 120 * MONTH


@dataclass
class State:
    base: float
    osc: float
    wrong: float = 0
    month: float = 0.0
    fired: set[int] = field(default_factory=set)
    flags: set[int] = field(default_factory=set)  # fired-Flags (10-13, 20), auch von Spruengen mitgesetzt
    ended: bool = False


@dataclass
class Result:
    base_end: float
    osc_before_close: float
    months: float
    fired: set[int]
    reached_event20: bool
    base_max: float = 0.0


def _clamp(x: float) -> float:
    return max(0.0, min(100.0, x))


def add_base(s: State, delta: float) -> None:
    s.base = _clamp(s.base + delta)


def add_osc(s: State, delta: float) -> None:
    s.osc = _clamp(s.osc + delta)


@dataclass(frozen=True)
class Path_:
    focuses: tuple[str, ...]
    options: dict[int, str]
    damp_before_8a: bool = False
    review: bool = False


PATHS: dict[str, Path_] = {
    "sauber": Path_(("f2", "f3", "f4", "f6", "f7", "f8a"),
                    {1: "a", 2: "a", 3: "a", 4: "b", 10: "a"}, damp_before_8a=True),
    "radikal": Path_(("f2", "f3", "f4", "f5", "f6", "f7", "f8b"),
                     {1: "a", 2: "b", 3: "a", 4: "a", 5: "a", 10: "b", 11: "b"},
                     review=True),
    "nichts": Path_((), {1: "a", 2: "a", 10: "b", 11: "b"}),
}


class _Sim:
    def __init__(self, path: Path_, v: dict):
        self.v = v
        self.p = path
        self.s = State(base=v["base_start"], osc=v["osc_start"])
        self.t = 0
        self.amplified = False
        self.amplified_days = 0
        self.osc_before_close = 0.0
        self.base_max = self.s.base
        self.q: list = []
        self.seq = 0

    # --- Zeitplan ---
    def at(self, t: float, fn) -> None:
        self.seq += 1
        heapq.heappush(self.q, (t, self.seq, fn))

    def run(self) -> Result:
        v = self.v
        # Einstieg: Ereignis 1 sofort, 2 nach event2_delay_days, Schleife nach 30 Tagen
        self.event(1)
        self.at(v["event2_delay_days"], lambda: self.event(2))
        self.at(MONTH, self.monthly)
        t_focus = 0
        for f in self.p.focuses:
            if f == "f8a" and self.p.damp_before_8a:
                self.at(t_focus, self.damp)
            if f == "f8a":
                self.at(t_focus, self.mark_close)
            t_focus += v[f + "_cost"] * 7
            self.at(t_focus, lambda f=f: self.focus_done(f))
        while self.q and not self.s.ended:
            t, _, fn = heapq.heappop(self.q)
            if t > HORIZON_DAYS:
                break
            self.t = t
            self.s.month = t / MONTH
            fn()
            self.base_max = max(self.base_max, self.s.base)
        if not self.s.ended:
            self.t = HORIZON_DAYS
            self.s.month = HORIZON_DAYS / MONTH
        return Result(self.s.base, self.osc_before_close, self.t / MONTH,
                      set(self.s.fired), 20 in self.s.fired, self.base_max)

    # --- Aenderungen mit Schwellenpruefung ---
    def d_base(self, d: float) -> None:
        add_base(self.s, d)
        self.base_max = max(self.base_max, self.s.base)
        self.thresholds()

    def d_osc(self, d: float) -> None:
        add_osc(self.s, d)
        self.thresholds()

    def thresholds(self) -> None:
        """Wie cml_check_thresholds: nur die hoechste erreichte Schwelle feuert,
        die niedrigeren fired-Flags werden mitgesetzt."""
        v, s = self.v, self.s
        if s.ended:
            return
        chain = ((20, 13, self.amplified), (13, 13, not self.amplified),
                 (12, 12, True), (11, 11, True), (10, 10, True))
        for ev, thr, active in chain:
            if not active or s.osc < v[f"threshold_{thr}"]:
                continue
            if ev in s.flags:
                continue
            s.flags.add(ev)
            s.flags.update(n for n in (10, 11, 12) if n < ev)
            self.event(ev)
            return

    def opt(self, n: int) -> str:
        return self.p.options.get(n, "a")

    def event(self, n: int) -> None:
        v, s = self.v, self.s
        s.fired.add(n)
        o = self.opt(n)
        if n == 1:
            if o == "a":
                self.d_base(v["e1_a_base"]); self.d_osc(v["e1_a_osc"])
            else:
                self.d_osc(v["e1_b_osc"])
        elif n == 2:
            self.d_base(v["e2_a_base"] if o == "a" else v["e2_b_base"])
        elif n == 3:
            if o == "a":
                self.d_base(v["e3_a_base"]); self.d_osc(v["e3_a_osc"])
            else:
                self.d_osc(v["e3_b_osc"])
        elif n == 5:
            if o == "a":
                self.d_osc(v["e5_a_osc"])
            else:
                self.d_base(v["e5_b_base"])
        elif n == 10:
            if o == "a":
                self.d_osc(v["e10_a_osc"])
            else:
                self.d_base(v["e10_b_base"]); self.d_osc(v["e10_b_osc"])
        elif n == 11:
            if o == "a":
                self.d_base(v["e11_a_base"]); self.d_osc(v["e11_a_osc"])
            else:
                self.d_osc(v["e11_b_osc"])
        elif n == 12:
            self.d_base(v["e12_a_base"])
        elif n == 13:
            self.collapse()
        elif n == 20:
            if o == "b":
                self.collapse()
            else:
                add_base(s, v["e20_a_base"])
                s.ended = True
        # 4 und 6: keine Wirkung auf Basis/Aufschaukeln

    def collapse(self) -> None:
        self.s.base = _clamp(self.s.base / 2)
        self.s.ended = True

    # --- Fokusse und Entscheidungen ---
    def damp(self) -> None:
        self.d_osc(-self.v["damp_osc"]); self.d_base(-self.v["damp_base"])

    def mark_close(self) -> None:
        # Wert unmittelbar vor Start von 8a (nach dem Daempfen)
        self.osc_before_close = self.s.osc

    def focus_done(self, f: str) -> None:
        v, s = self.v, self.s
        if s.ended:
            return
        if f == "f2":
            self.d_base(v["f2_base"]); self.d_osc(v["f2_osc"])
            if self.p.review:
                self.at(self.t, self.review)
        elif f == "f3":
            self.d_base(v["f3_base"]); self.d_osc(v["f3_osc"])
            self.event(3)
        elif f == "f4":
            self.d_osc(v["f4_osc"])
            self.at(self.t + v["e4_delay_days"], lambda: s.fired.add(4))
        elif f == "f5":
            self.d_base(v["f5_base"]); self.d_osc(v["f5_osc"])
            self.event(5)
        elif f == "f6":
            self.d_base(v["f6_base"]); self.d_osc(-v["f6_osc_reduce"])
        elif f == "f7":
            s.fired.add(6)
        elif f == "f8a":
            self.d_base(v["f8a_base"])
            s.ended = True
        elif f == "f8b":
            self.amplified = True  # Flag zuerst: 100 durch 8b loest Ereignis 20 aus
            self.d_base(v["f8b_base"]); self.d_osc(v["f8b_osc"])

    def review(self) -> None:
        v, s = self.v, self.s
        if s.ended:
            return
        p = _clamp(v["review_wrong_base"] + s.osc * v["review_wrong_per_osc"]) / 100
        self.d_base((1 - p) * v["review_hit_base"])
        s.wrong += p
        self.d_osc(p * v["review_wrong_osc"])
        self.at(self.t + MONTH, self.review)

    def monthly(self) -> None:
        v, s = self.v, self.s
        if s.ended:
            return
        self.d_base(v["monthly_base"])
        if s.ended:
            return
        self.d_osc(v["monthly_osc_amplified"] if self.amplified else v["monthly_osc"])
        if s.ended:
            return
        if self.amplified:
            self.amplified_days += MONTH
            if self.amplified_days >= v["amplify_duration_days"] and 20 not in s.fired:
                self.event(20)
        if not s.ended:
            self.at(self.t + MONTH, self.monthly)


def simulate(path_name: str, values: dict) -> Result:
    return _Sim(PATHS[path_name], dict(values)).run()


def check_targets(results: dict[str, Result]) -> list[str]:
    miss: list[str] = []
    s = results["sauber"]
    if not 6 <= s.months <= 9:
        miss.append(f"sauber: Abschluss nach {s.months:.1f} Monaten (Ziel 6-9)")
    if not 70 <= s.base_end <= 85:
        miss.append(f"sauber: Parteibasis {s.base_end:.1f} (Ziel 70-85)")
    if not 10 <= s.osc_before_close <= 45:
        miss.append(f"sauber: Aufschaukeln vor 8a {s.osc_before_close:.1f} (Ziel 10-45)")
    if s.fired & {11, 12, 13}:
        miss.append(f"sauber: Ereignis {sorted(s.fired & {11, 12, 13})} ausgeloest (Ziel keines von 11-13)")
    r = results["radikal"]
    if r.base_max < 100:
        miss.append(f"radikal: Parteibasis maximal {r.base_max:.1f} (Ziel 100)")
    if not {10, 11} <= r.fired:
        miss.append(f"radikal: Ereignisse {sorted(r.fired & {10, 11})} statt 10 und 11")
    if not r.reached_event20:
        miss.append("radikal: Ereignis 20 nicht erreicht")
    n = results["nichts"]
    if not 34 <= n.months <= 50:
        miss.append(f"nichts: Aufschaukeln 100 nach {n.months:.1f} Monaten (Ziel 34-50)")
    return miss


def load_values(path: Path) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    v = load_values(root / "base" / "werte.toml")
    results = {name: simulate(name, v) for name in ("sauber", "radikal", "nichts")}
    for name, r in results.items():
        print(f"Weg {name}: Monate={r.months:.1f} Basis_Ende={r.base_end:.1f} "
              f"Basis_max={r.base_max:.1f} Aufschaukeln_vor_Schluss={r.osc_before_close:.1f} "
              f"Ereignisse={sorted(r.fired)} Ereignis20={r.reached_event20}")
    miss = check_targets(results)
    for name in results:
        bad = [m for m in miss if m.startswith(name + ":")]
        print(f"{name}: {'verfehlt' if bad else 'erfuellt'}")
        for m in bad:
            print("  " + m)
    return 1 if miss else 0


if __name__ == "__main__":
    sys.exit(main())
