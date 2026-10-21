"""Threshold-voltage corners on the 45nm card: |Vth| shifted by -50 mV, 0 and +50 mV for both device types.
Compares conventional, paper LECTOR and improved LECTOR at each corner.
Run from the scripts folder:  python3 vth_corners.py"""
import os, re, tempfile
import lector_sim as L

VDD, LMIN, WN, WP = 1.0, 45e-9, 90e-9, 180e-9
MODEL = os.path.join(L.MODELS, "45nm_HP.pm")


def shifted_model(src, dv, folder):
    """copy of the model card with |VTH0| increased by dv (volts) for both NMOS and PMOS"""
    def fix(m):
        v = float(m.group(2))
        return m.group(1) + f"{v + dv if v > 0 else v - dv:.5f}"
    text = re.sub(r"(\+vth0\s*=\s*)(-?[\d.]+)", fix, open(src).read(), flags=re.I)
    path = os.path.join(folder, f"vth_{dv:+.3f}.pm")
    open(path, "w").write(text)
    return path


def report(title, model):
    print(f"\n{title}")
    print(f"{'design':16s} {'leak(nW)':>9s} {'vs conv':>8s} {'tpd(ps)':>8s} {'vs conv':>8s} {'Vhigh(V)':>9s}")
    c = L.run(model, VDD, LMIN, "conv", WP, WN)
    designs = [("Conventional", c),
               ("Paper LECTOR", L.run(model, VDD, LMIN, "lector", WP, WN, WP, WN)),
               ("Improved LECTOR", L.run(model, VDD, LMIN, "lector", WP, WN, 4 * WP, 2 * WN))]
    for name, r in designs:
        red = (c["leak"] - r["leak"]) / c["leak"] * 100
        dl = (r["tpd"] / c["tpd"] - 1) * 100
        print(f"{name:16s} {r['leak'] * 1e9:9.3f} {red:7.1f}% {r['tpd'] * 1e12:8.1f} {dl:7.0f}% {r['vhigh']:9.3f}")


report("45nm HP, nominal", MODEL)
with tempfile.TemporaryDirectory() as d:
    for dv in (-0.05, 0.05):
        label = "faster, leakier" if dv < 0 else "slower, less leaky"
        report(f"45nm HP, |Vth| {dv * 1000:+.0f} mV ({label})", shifted_model(MODEL, dv, d))
