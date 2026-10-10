"""Plots for the 45nm LECTOR study. Run from inv_leakage/scripts:  python3 plot_all.py"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
COL = {"conv": "#555555", "paper": "#d62728", "improved": "#1f77b4"}
LAB = {"conv": "Conventional", "paper": "Paper LECTOR", "improved": "Improved LECTOR"}


def si(s):
    """'180n' -> 1.8e-7"""
    return float(s[:-1]) * 1e-9 if s.endswith("n") else float(s)


# ---------- 1. VTC ----------
d = np.loadtxt(os.path.join(R, "vtc.txt"), skiprows=1)
vin = d[:, 0]
fig, ax = plt.subplots(figsize=(5.5, 5))
for i, k in enumerate(["conv", "paper", "improved"]):
    ax.plot(vin, d[:, 1 + i], color=COL[k], label=LAB[k], lw=2)
ax.plot([0, 1], [0, 1], "k--", lw=0.8, label="Vout = Vin")
ax.set_xlabel("Vin (V)"); ax.set_ylabel("Vout (V)")
ax.set_title("Voltage transfer characteristic (45nm)")
ax.grid(alpha=0.3); ax.legend()
fig.tight_layout(); fig.savefig(os.path.join(R, "fig1_vtc.png"), dpi=200); plt.close(fig)

# ---------- 2. Transient (one full cycle) ----------
d = np.loadtxt(os.path.join(R, "tran.txt"), skiprows=1)
t = d[:, 0] * 1e9
m = (t >= 20) & (t <= 42)
fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 5.5), sharex=True,
                             gridspec_kw={"height_ratios": [1, 3]})
a1.plot(t[m], d[m, 1], "k", lw=1.5); a1.set_ylabel("Vin (V)")
a1.set_title("Transient response at 50 MHz, 5 fF load (45nm)")
for i, k in enumerate(["conv", "paper", "improved"]):
    a2.plot(t[m], d[m, 2 + i], color=COL[k], label=LAB[k], lw=2)
a2.set_xlabel("Time (ns)"); a2.set_ylabel("Vout (V)")
a2.axhline(1.0, color="gray", ls=":", lw=0.8)
a2.grid(alpha=0.3); a2.legend(loc="center right")
a1.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(os.path.join(R, "fig2_transient.png"), dpi=200); plt.close(fig)

# ---------- 3. Leakage vs temperature ----------
rows = []
for line in open(os.path.join(R, "leak_vs_temp.txt")):
    left, right = line.split("|")
    T, v = left.split()
    rows.append([float(T), float(v)] + [float(x) for x in right.split()])
rows = np.array(rows)
temps = sorted(set(rows[:, 0]))
avg = {k: [] for k in COL}
for T in temps:
    sel = rows[rows[:, 0] == T]
    for i, k in enumerate(["conv", "paper", "improved"]):
        avg[k].append(sel[:, 2 + i].mean() * 1e9)   # nA ~ nW at 1.0 V
fig, ax = plt.subplots(figsize=(6.5, 4.5))
for k in ["conv", "paper", "improved"]:
    ax.plot(temps, avg[k], "o-", color=COL[k], label=LAB[k], lw=2)
ax.set_xlabel("Temperature (°C)"); ax.set_ylabel("Average leakage power (nW)")
ax.set_title("Leakage vs temperature (45nm, Vdd = 1.0 V)")
ax.grid(alpha=0.3); ax.legend()
fig.tight_layout(); fig.savefig(os.path.join(R, "fig3_leak_vs_temp.png"), dpi=200); plt.close(fig)

# ---------- 4. Sizing sweep: leakage vs delay ----------
pts = []
for line in open(os.path.join(R, "sizing_sweep.txt")):
    a, b, c, e, f = [p.split() for p in line.split("|")]
    wp, wn = si(a[0]), si(a[1])
    leak = (float(b[0]) + float(b[1])) / 2 * 1e9            # nW
    delay = (float(c[0]) + float(c[1])) / 2 * 1e12          # ps
    pts.append((wp, wn, leak, delay, float(e[0])))
fig, ax = plt.subplots(figsize=(7, 5))
sc = ax.scatter([p[3] for p in pts], [p[2] for p in pts], c=[p[4] for p in pts],
                cmap="viridis", s=70, edgecolor="k")
for wp, wn, leak, delay, vh in pts:
    mark = (wp, wn) in [(180e-9, 90e-9), (720e-9, 180e-9)]
    ax.annotate(f"{wp*1e9:.0f}/{wn*1e9:.0f}", (delay, leak), textcoords="offset points",
                xytext=(5, 5), fontsize=8, fontweight="bold" if mark else "normal")
cb = fig.colorbar(sc); cb.set_label("Output high level (V)")
ax.set_xlabel("Average delay (ps)"); ax.set_ylabel("Average leakage power (nW)")
ax.set_title("LECTOR sizing sweep: labels are PMOS-extra / NMOS-extra width (nm)")
ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(os.path.join(R, "fig4_sizing_tradeoff.png"), dpi=200); plt.close(fig)

# ---------- 5. Before / after bars at 27 C (delay and swing measured from tran.txt) ----------
def cross(t, y, level, rising, t0):
    """time of the first crossing of `level` after t0 (linear interpolation)"""
    for i in range(1, len(t)):
        if t[i] <= t0:
            continue
        a, b = y[i - 1] - level, y[i] - level
        if (rising and a < 0 <= b) or (not rising and a > 0 >= b):
            return t[i - 1] + (t[i] - t[i - 1]) * (-a) / (b - a)
    return float("nan")


ts = d[:, 0]
vin_w = d[:, 1]
t_in_r = cross(ts, vin_w, 0.5, True, 21e-9)
t_in_f = cross(ts, vin_w, 0.5, False, 30e-9)
delay, vhigh, tp = [], [], []
for i in range(3):
    vout = d[:, 2 + i]
    tphl = cross(ts, vout, 0.5, False, t_in_r) - t_in_r
    tplh = cross(ts, vout, 0.5, True, t_in_f) - t_in_f
    tp.append((tphl * 1e12, tplh * 1e12))
    delay.append((tphl + tplh) / 2 * 1e12)
    vhigh.append(float(np.interp(41.9e-9, ts, vout)))   # settled level just before the next input edge

sel = rows[rows[:, 0] == 27]
leak = [sel[:, 2 + i].mean() * 1e9 for i in range(3)]
fig, axs = plt.subplots(1, 3, figsize=(10, 3.8))
for ax, vals, ttl, unit in zip(axs, [leak, delay, vhigh],
                               ["Average leakage", "Average delay", "Output high level"],
                               ["nW", "ps", "V"]):
    bars = ax.bar([LAB[k].replace(" ", "\n") for k in ["conv", "paper", "improved"]], vals,
                  color=[COL[k] for k in ["conv", "paper", "improved"]])
    ax.bar_label(bars, fmt="%.3g", padding=2)
    ax.set_ylim(0, max(vals) * 1.18)
    ax.set_title(ttl); ax.set_ylabel(unit); ax.grid(axis="y", alpha=0.3)
fig.tight_layout(); fig.savefig(os.path.join(R, "fig5_before_after.png"), dpi=200); plt.close(fig)

print("\nSummary at 27 C, 50 MHz, 5 fF load")
for i, k in enumerate(["conv", "paper", "improved"]):
    print(f"{LAB[k]:16s} leak {leak[i]:.3f} nW | tpHL {tp[i][0]:.1f} ps  tpLH {tp[i][1]:.1f} ps  avg {delay[i]:.1f} ps | Vout high {vhigh[i]:.3f} V")
print("saved figures to", os.path.abspath(R))
