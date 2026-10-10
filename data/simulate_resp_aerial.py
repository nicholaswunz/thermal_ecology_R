"""
Simulate a closed-system (stop-flow) aerial respirometry export for teaching.

Creates data/resp_aerial_lizard.csv used in phys_respirometry.qmd.
The trace mimics an optical oxygen sensor spot reading O2 partial pressure (hPa)
inside a sealed 150 mL glass chamber holding a 4.2 g lizard at 25 degC, plus an
empty "blank" chamber run in parallel. The data are SIMULATED, not measured.

Built-in features (so learners can find them):
  * 0-8 min   : elevated uptake after handling, decaying to rest
  * 40-47 min : burst of activity (4x resting uptake)
  * 47-60 min : recovery back to rest
  * two sensor drop-outs written as NaN in Ch1
  * a 60 s logger pause (rows missing) near 70 min
  * a slow background decline in both chambers (sensor drift / micro-organisms)

True values used in the simulation (for checking answers):
  resting O2 uptake of the lizard = 22.5 umol O2 h-1 (= 0.504 mL O2 h-1 STPD)
  background decline              = 0.40 hPa h-1 in both chambers
"""
import numpy as np
import datetime as dt

rng = np.random.default_rng(2024)

R = 8.314462618          # J mol-1 K-1
T_K = 298.15             # 25 degC
V_air = 0.150 - 0.0042   # L of air (chamber minus lizard volume, density ~1 g/mL)

rest_umol_h = 22.5                                     # umol O2 per hour
rest_hpa_min = rest_umol_h * 1e-6 / V_air * R * T_K * 1000 / 100 / 60  # hPa per min
bg_hpa_min = 0.40 / 60

secs = np.arange(0, 6001, 10)
mins = secs / 60

mult = np.ones_like(mins)
mult += np.where(mins < 8, 1.5 * np.exp(-mins / 2.5), 0)
mult = np.where((mins >= 40) & (mins < 47), 4.0, mult)
mult = np.where((mins >= 47) & (mins < 60), 1 + np.exp(-(mins - 47) / 3.5), mult)
mult = np.where(mins >= 60, 0.97, mult)

dt_min = np.diff(mins, prepend=0)
ch1_true = 208.6 - np.cumsum((rest_hpa_min * mult + bg_hpa_min) * dt_min)
ch2_true = 208.8 - np.cumsum(bg_hpa_min * dt_min)

ch1 = ch1_true + rng.normal(0, 0.10, mins.size)
ch2 = ch2_true + rng.normal(0, 0.10, mins.size)
temp = 25.0 + rng.normal(0, 0.03, mins.size)
baro = 1012.4 + 0.3 * np.sin(mins / 100 * np.pi)

ch1[np.isin(secs, [2510, 2520])] = np.nan              # sensor drop-outs
keep = ~((secs > 4200) & (secs < 4260))                # logger pause

start = dt.datetime(2025, 3, 14, 9, 12, 0)
lines = [
    "# Simulated closed-system aerial respirometry export (teaching data, Thermal Ecology in R)",
    "# Ch1 = sealed chamber with a 4.2 g lizard; Ch2 = empty blank chamber; both chambers 150 mL glass",
    "# Oxygen = O2 partial pressure (hPa) from optical sensor spots; Temp = chamber temperature (degC); Pressure = barometric (hPa)",
    "# SIMULATED DATA - not real measurements. See data/simulate_resp_aerial.py",
    "Date,Time,dt (s),Ch1 Oxygen (hPa),Ch2 Oxygen (hPa),Temp (degC),Pressure (hPa)",
]
for s, o1, o2, tc, p in zip(secs[keep], ch1[keep], ch2[keep], temp[keep], baro[keep]):
    stamp = start + dt.timedelta(seconds=int(s))
    o1s = "NaN" if np.isnan(o1) else f"{o1:.2f}"
    lines.append(f"{stamp:%d/%m/%Y},{stamp:%H:%M:%S},{int(s)},{o1s},{o2:.2f},{tc:.2f},{p:.1f}")

with open("data/resp_aerial_lizard.csv", "w") as fh:
    fh.write("\n".join(lines) + "\n")

print(f"resting slope (hPa/min) = {rest_hpa_min:.5f}; background = {bg_hpa_min:.5f}")
