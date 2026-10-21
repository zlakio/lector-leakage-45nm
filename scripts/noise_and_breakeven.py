"""Noise margins (from the VTC) and break-even switching activity (from leakage and dynamic power).
Run from the scripts folder after the simulations in the README have been run."""
import os
import numpy as np

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
NAMES = ["Conventional", "Paper LECTOR", "Improved LECTOR"]

# ---------- 1. noise margins ----------
d = np.loadtxt(os.path.join(R, "vtc.txt"), skiprows=1)
vin = d[:, 0]
print("NOISE MARGINS (static, from the DC sweep)")
print(f"{'design':16s} {'VOH':>6s} {'VOL':>6s} {'VIL':>6s} {'VIH':>6s} {'NMH':>6s} {'NML':>6s}")
for i, n in enumerate(NAMES):
    v = d[:, 1 + i]
    g = np.gradient(v, vin)
    idx = np.where(g <= -1)[0]            # region where gain magnitude >= 1
    vil, vih = vin[idx[0]], vin[idx[-1]]  # unity-gain points (grid resolution 10 mV)
    voh, vol = v[0], v[-1]
    print(f"{n:16s} {voh:6.3f} {vol:6.3f} {vil:6.3f} {vih:6.3f} {voh - vih:6.3f} {vil - vol:6.3f}")

# at-speed high level (50 MHz, second cycle) from the summary file
summ = {}
for line in open(os.path.join(R, "all_designs_summary.txt")):
    name, rest = line.split(":", 1)
    a = [p.split() for p in rest.split("|")]
    summ[name.strip()] = dict(leak=(float(a[0][0]) + float(a[0][1])) / 2,
                              pdyn=abs(float(a[2][0])), vh=float(a[3][0]))
keys = ["conv", "paper", "improved"]
print("\nAt-speed output high (50 MHz) and the resulting high-side noise margin (VIH from above):")
for i, (n, k) in enumerate(zip(NAMES, keys)):
    v = d[:, 1 + i]; g = np.gradient(v, vin); vih = vin[np.where(g <= -1)[0][-1]]
    vh = min(summ[k]["vh"], 1.0)
    print(f"{n:16s} VOH(50 MHz) = {vh:5.3f} V   NMH = {vh - vih:6.3f} V")

# ---------- 2. break-even activity ----------
print("\nBREAK-EVEN (Improved LECTOR vs Conventional), 27 C")
c, m = summ["conv"], summ["improved"]
dleak = c["leak"] - m["leak"]
ddyn = m["pdyn"] - c["pdyn"]
f_test = 50e6
alpha = dleak / ddyn
print(f"leakage saved      : {dleak * 1e9:.3f} nW")
print(f"extra dynamic power: {ddyn * 1e9:.1f} nW at {f_test / 1e6:.0f} MHz (switching every cycle)")
print(f"break-even activity: {alpha * 100:.2f}% of full switching -> equivalent toggle rate {alpha * f_test / 1e6:.2f} MHz")

print("\nSame calculation at higher temperature (extra dynamic power assumed unchanged):")
rows = [l.split("|") for l in open(os.path.join(R, "leak_vs_temp.txt"))]
data = {}
for left, right in rows:
    T, v = left.split(); a = [float(x) for x in right.split()]
    data.setdefault(float(T), []).append(a)
for T in sorted(data):
    avg = np.mean(np.array(data[T]), axis=0)      # conv, paper, improved (A = W at 1 V)
    al = (avg[0] - avg[2]) / ddyn
    print(f"{T:5.0f} C: leakage saved {(avg[0] - avg[2]) * 1e9:5.2f} nW -> break-even {al * 100:5.2f}%  ({al * f_test / 1e6:5.2f} MHz)")
print("\nPaper LECTOR vs Conventional: dynamic power is LOWER only because its output swings less:")
p = summ["paper"]
print(f"dynamic {p['pdyn'] * 1e9:.1f} nW vs {c['pdyn'] * 1e9:.1f} nW; leakage {p['leak'] * 1e9:.3f} nW vs {c['leak'] * 1e9:.3f} nW")
