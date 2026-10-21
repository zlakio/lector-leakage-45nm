"""Helper: simulate one inverter design (conventional or LECTOR) in ngspice and return its metrics.
Used by iso_delay.py and corners_and_32nm.py. Needs ngspice on the PATH."""
import os, re, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(HERE, "..", "models")


def netlist(model, vdd, lmin, topo, wp, wn, wlcp=None, wlcn=None, cload="5f", temp=27):
    """topo = 'conv' or 'lector'. Widths in metres. Returns netlist text."""
    if topo == "conv":
        ckt = (f"Mp out in vdd vdd pmos W={wp} L={lmin}\n"
               f"Mn out in 0 0 nmos W={wn} L={lmin}\n")
    else:
        ckt = (f"Mp   a   in  vdd vdd pmos W={wp} L={lmin}\n"
               f"Mlp  out b   a   vdd pmos W={wlcp} L={lmin}\n"
               f"Mln  out a   b   0   nmos W={wlcn} L={lmin}\n"
               f"Mn   b   in  0   0   nmos W={wn} L={lmin}\n")
    return f"""* single design
.include {os.path.abspath(model)}
.csparam vddv={vdd}
Vin in 0 DC 0 PULSE(0 {vdd} 2n 20p 20p 10n 20n)
Vdd vdd 0 {vdd}
{ckt}Cl out 0 {cload}
.control
set temp = {temp}
let half = vddv/2
alter vin dc = 0
op
let c0 = abs(i(vdd))
set s0 = "$&c0"
alter vin dc = $&vddv
op
let c1 = abs(i(vdd))
set s1 = "$&c1"
alter vin dc = 0
tran 2p 42n
meas tran tphl TRIG v(in) VAL=$&half RISE=2 TARG v(out) VAL=$&half FALL=2
meas tran tplh TRIG v(in) VAL=$&half FALL=2 TARG v(out) VAL=$&half RISE=2
meas tran iavg AVG i(vdd) FROM=22n TO=42n
meas tran vend FIND v(out) AT=41.9n
echo "RES $s0 $s1 $&tphl $&tplh $&iavg $&vend"
.endc
.end
"""


def run(model, vdd, lmin, topo, wp, wn, wlcp=None, wlcn=None, cload="5f", temp=27):
    """Run one design. Widths and length in metres (floats). Returns a dict of metrics."""
    f = lambda x: None if x is None else f"{x:.6e}"
    text = netlist(model, vdd, f(lmin), topo, f(wp), f(wn), f(wlcp), f(wlcn), cload, temp)
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.cir")
        open(p, "w").write(text)
        out = subprocess.run(["ngspice", "-b", p], capture_output=True, text=True).stdout
    m = re.search(r"^RES (.*)$", out, re.M)
    if not m:
        raise RuntimeError("no result from ngspice:\n" + out[-800:])
    l0, l1, tphl, tplh, iavg, vend = [float(x) for x in m.group(1).split()]
    return dict(leak0=l0 * vdd, leak1=l1 * vdd, leak=(l0 + l1) / 2 * vdd,
                tphl=tphl, tplh=tplh, tpd=(tphl + tplh) / 2,
                pdyn=abs(iavg) * vdd, vhigh=vend,
                width=wp + wn + (0 if topo == "conv" else wlcp + wlcn))
