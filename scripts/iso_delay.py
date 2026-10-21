"""Iso-delay comparison: scale ALL transistors of a LECTOR inverter by a factor k until its average delay
equals the conventional inverter's, then compare leakage, area and output level.
Run from the scripts folder:  python3 iso_delay.py"""
import os, math
import lector_sim as L

M = os.path.join(L.MODELS, "45nm_HP.pm")
VDD, LMIN, WP, WN = 1.0, 45e-9, 180e-9, 90e-9
conv = L.run(M, VDD, LMIN, "conv", WP, WN)
target = conv["tpd"]
print(f"Conventional: tpd {target * 1e12:.2f} ps, leakage {conv['leak'] * 1e9:.3f} nW, width {conv['width'] * 1e9:.0f} nm\n")
print("LCT ratios are relative to the main transistor of the same type; k scales the whole inverter.")
print(f"{'PMOS/NMOS LCT':>14s} {'k':>6s} {'width(nm)':>10s} {'leak(nW)':>9s} {'vs conv':>8s} {'tpd(ps)':>8s} {'Vhigh':>6s} {'Pdyn(nW)':>9s} {'PDP(aJ)':>8s}")
rows = []


def sim(k, mp, mn):
    return L.run(M, VDD, LMIN, "lector", WP * k, WN * k, WP * k * mp, WN * k * mn)


for mp, mn in [(1, 1), (2, 1), (2, 2), (4, 2), (4, 1)]:
    lo, hi = 1.0, 24.0
    if sim(hi, mp, mn)["tpd"] > target:
        print(f"{mp}x/{mn}x: delay not reachable up to k = {hi}")
        continue
    for _ in range(14):                       # bisection on log k
        mid = math.sqrt(lo * hi)
        if sim(mid, mp, mn)["tpd"] > target:
            lo = mid
        else:
            hi = mid
    k = hi
    r = sim(k, mp, mn)
    red = (conv["leak"] - r["leak"]) / conv["leak"] * 100
    print(f"{str(mp) + 'x / ' + str(mn) + 'x':>14s} {k:6.2f} {r['width'] * 1e9:10.0f} {r['leak'] * 1e9:9.3f} {red:7.1f}% {r['tpd'] * 1e12:8.2f} {r['vhigh']:6.3f} {r['pdyn'] * 1e9:9.1f} {r['pdyn'] * r['tpd'] * 1e18:8.1f}")
    rows.append((mp, mn, k, r))

# ---- second check: instead of scaling LECTOR up, shrink the conventional inverter to LECTOR's (slower) delay ----
print("\nConventional inverter simply shrunk (scale s on both widths) to match a LECTOR delay:")
print("(widths below the technology's minimum width are not manufacturable; the model may also be inaccurate there)")
for name, mp, mn in [("unsized LECTOR", 1, 1), ("improved LECTOR", 4, 2)]:
    lect = sim(1.0, mp, mn)
    lo, hi = 0.2, 1.0
    for _ in range(14):
        mid = math.sqrt(lo * hi)
        if L.run(M, VDD, LMIN, "conv", WP * mid, WN * mid)["tpd"] > lect["tpd"]:
            lo = mid                          # still too slow: needs a larger s
        else:
            hi = mid
    r = L.run(M, VDD, LMIN, "conv", WP * hi, WN * hi)
    print(f"{name:16s} (tpd {lect['tpd'] * 1e12:.1f} ps, leak {lect['leak'] * 1e9:.3f} nW)  vs  shrunk conventional: "
          f"s = {hi:.2f} (Wn {WN * hi * 1e9:.0f} nm, Wp {WP * hi * 1e9:.0f} nm), tpd {r['tpd'] * 1e12:.1f} ps, leak {r['leak'] * 1e9:.3f} nW")
