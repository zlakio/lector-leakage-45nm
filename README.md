# Leakage Reduction in a CMOS Inverter at the 45nm Node
### Implementing the LECTOR technique, then improving it (ngspice, PTM 45nm HP)

This project implements the **LECTOR** leakage-reduction technique on a CMOS inverter, measures its benefits and limitations in SPICE, and improves it by re-sizing the two extra transistors. Everything is simulated in ngspice with the 45nm High-Performance Predictive Technology Model (PTM).

| Stage | What was simulated |
|---|---|
| **Conventional** | Standard 2-transistor inverter (reference) |
| **Before: paper LECTOR** | LECTOR inverter as published, extra transistors the same size as the main ones |
| **After: improved LECTOR** | Same topology, with the PMOS extra transistor widened to 720 nm and the NMOS extra transistor to 180 nm |

## Key results

Conditions: 45nm PTM HP, Vdd = 1.0 V, 27 °C, 50 MHz square-wave input (20 ps edges), 5 fF load. Delays are measured in the second clock cycle (steady state).

| Metric | Conventional | Paper LECTOR | Improved LECTOR |
|---|---|---|---|
| Avg leakage power | 1.362 nW | 0.603 nW (-55.7%) | 0.647 nW (-52.5%) |
| Leakage, Vin = 0 / Vin = 1 | 1.952 / 0.772 nW | 0.969 / 0.237 nW | 1.019 / 0.276 nW |
| tpHL / tpLH | 29.8 / 22.5 ps | 73.9 / 97.0 ps | 71.6 / 58.8 ps |
| Avg delay | 26.2 ps | 85.5 ps (+227%) | 65.2 ps (+149%) |
| Output high level | 1.00 V | 0.80 V | 0.95 V |
| Dynamic power | 0.268 uW | 0.225 uW | 0.294 uW |
| Power-delay product | 7.0 aJ | 19.2 aJ | 19.2 aJ |
| Transistors / total width | 2 / 270 nm | 4 / 540 nm | 4 / 1170 nm |

**Improvement over the paper's LECTOR:** average delay -23.7%, output high level +0.14 V, at the cost of +7.4% leakage and about 2x the total transistor width.

The paper LECTOR's dynamic power looks lower mainly because its output swings less, so it should not be read as a saving.

### Leakage vs temperature (average of both input states)

| Temperature | Conventional | Paper LECTOR | Improved LECTOR |
|---|---|---|---|
| 27 °C | 1.36 nW | 0.60 nW | 0.65 nW |
| 50 °C | 2.18 nW | 0.96 nW | 1.04 nW |
| 75 °C | 3.47 nW | 1.54 nW | 1.68 nW |
| 110 °C | 6.13 nW | 2.80 nW | 3.08 nW |

## Findings

**Limitations of the paper's LECTOR (observed in simulation)**
- Delay is about 3.3x the conventional inverter's.
- The PMOS extra transistor operates just below threshold once the output is high, so the output rises slowly toward Vdd and reaches only about 0.80 V in a 10 ns half-cycle. The delay therefore depends on how high the output got in the previous cycle.
- Four transistors instead of two (twice the area).
- The saving is state-dependent: about 50% when Vin = 0 and about 69% when Vin = 1.

**Improvement: sizing the extra transistors**
A sweep of 12 width combinations (PMOS extra 180-720 nm, NMOS extra 90-360 nm) showed that widening the PMOS extra transistor raises the output high level, while widening the NMOS extra transistor mainly lowers delay (at some cost in Vin = 0 leakage). The 720 nm / 180 nm point gives the best balance: lower delay and a much cleaner output level, while keeping more than half of the leakage saving at every temperature tested.

## Figures
<img width="1100" height="1000" alt="fig1_vtc" src="https://github.com/user-attachments/assets/352a555d-b19d-4da1-85dc-91d869bf2096" />

<img width="1600" height="1100" alt="fig2_transient" src="https://github.com/user-attachments/assets/beda84df-b823-4fbd-95a8-8902d680ae98" />

<img width="1300" height="900" alt="fig3_leak_vs_temp" src="https://github.com/user-attachments/assets/83d82921-88f0-4825-b71c-11dce75db060" />

<img width="1400" height="1000" alt="fig4_sizing_tradeoff" src="https://github.com/user-attachments/assets/59e2583a-abc1-45dd-b1c1-b4251ce21df4" />

<img width="2000" height="760" alt="fig5_before_after" src="https://github.com/user-attachments/assets/ddb004ce-2990-4042-aee6-f8a6e6db39c4" />


## Repository layout

```
.
├── netlists/45nm/
│   ├── 5_all_designs.cir        Final results: all three designs, leakage + delay + power
│   ├── 3_lector_sweep.cir       Sizing sweep for the extra transistors
│   ├── 4_leak_vs_temp.cir       Leakage vs temperature, all three designs
│   ├── 6_export_waveforms.cir   Exports VTC and transient data for plotting
│   └── 1_*, 2_*                 Earlier step-by-step netlists (see note below)
├── scripts/plot_all.py          Generates the five figures
├── results/                     Data files and figures
└── models/                      NOT included (see "Model cards")
```

The early step-by-step netlists (`1_*`, `2_*`) measure delay on the first clock cycle only and were used to build up the design. Use `5_all_designs.cir` for the final numbers.

## Circuits

Conventional inverter: PMOS W = 180 nm, NMOS W = 90 nm, L = 45 nm.

LECTOR adds two transistors between the pull-up and pull-down transistors. The output is taken at their common drain. The gate of each extra transistor is driven by the source of the other one:

```
Mp   a    in   vdd  vdd  pmos      pull-up
Mlp  out  b    a    vdd  pmos      extra PMOS, gate = b
Mln  out  a    b    0    nmos      extra NMOS, gate = a
Mn   b    in   0    0    nmos      pull-down
```

## Model cards

The PTM 45nm HP model card is not included in this repository. Download `45nm_HP.pm` from the Predictive Technology Model site (ptm.asu.edu, maintained by Arizona State University) and place it in `models/`. The card defines models named `nmos` and `pmos` (BSIM4, level 54, nominal Vdd 1.0 V).

If you use PTM, please cite: Y. Cao et al., "New generation of Predictive Technology Model for sub-45 nm early design exploration," IEEE Transactions on Electron Devices, vol. 53, no. 11, pp. 2816-2823, Nov. 2006.

## Reproducing the results

Requirements: ngspice (tested with ngspice-47, inside IIC-OSIC-TOOLS), Python 3 with numpy and matplotlib.

```bash
cd netlists/45nm
ngspice -b 5_all_designs.cir | grep -E "^conv|^paper|^improved"
ngspice -b 3_lector_sweep.cir | grep -E "^[0-9]+n " > ../../results/sizing_sweep.txt
ngspice -b 4_leak_vs_temp.cir | grep -E "^[0-9]+ [01]" > ../../results/leak_vs_temp.txt
ngspice -b 6_export_waveforms.cir
cd ../../scripts
python3 plot_all.py
```

## Limitations of this study

- Single technology node (45nm); PTM is a predictive model, not a foundry PDK.
- Nominal process only, with no corners or Monte Carlo variation.
- One load (5 fF) and one frequency (50 MHz) for the delay and power figures.
- Leakage is reported at Vdd = 1.0 V, so leakage current in nA equals leakage power in nW.

## References

1. M. Hanchate and N. Ranganathan, "LECTOR: A Technique for Leakage Reduction in CMOS Circuits," IEEE Transactions on Very Large Scale Integration (VLSI) Systems, 2004.
2. K. Roy, S. Mukhopadhyay and H. Mahmoodi-Meimand, "Leakage current mechanisms and leakage reduction techniques in deep-submicrometer CMOS circuits," Proceedings of the IEEE, 2003.
3. Y. Cao et al., "New generation of Predictive Technology Model for sub-45 nm early design exploration," IEEE Transactions on Electron Devices, vol. 53, no. 11, 2006.
