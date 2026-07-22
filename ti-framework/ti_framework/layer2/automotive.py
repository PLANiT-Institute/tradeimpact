# SPDX-License-Identifier: GPL-3.0-or-later
"""Automotive Layer 2 — sold-vehicle emissions (Guideline §3).

Three cases:
    ICEEmissions  — ICE / non-plug-in HEV: E = I_export,ICE * D_c   (fixed at sale-year).
    BEVEmissions  — E = eta_EV * G_c(t) * D_c,  G declining at r_power,c.
    PHEVEmissions — E = [UF*eta_elec*G_c(t) + (1-UF)*I_ICE_mode] * D_c.

r_power,c is supplied independently of r_fleet,c (Guideline §3.4 — must never be set equal;
see NOTES.md D1 for how the engine surfaces the pro-rata identity when only one rate exists).
"""

from __future__ import annotations

from dataclasses import dataclass

from ti_framework.layer2.base import ProductEmissions


@dataclass
class GridTrajectory:
    """Grid carbon intensity trajectory G_c(t) = G_c(0) * (1 - r_power)^t [kgCO2e/kWh]."""

    g0: float
    r_power: float

    def at(self, t: int) -> float:
        return self.g0 * (1.0 - self.r_power) ** t


@dataclass
class ICEEmissions(ProductEmissions):
    """ICE / non-plug-in HEV — fixed at sale-year efficiency (Guideline §3.3)."""

    ice_intensity: float  # I_export,ICE [kgCO2e/km], real-world corrected
    distance: float

    def emissions(self, t: int) -> float:
        return self.ice_intensity * self.distance


@dataclass
class BEVEmissions(ProductEmissions):
    """BEV — grid-declining emissions (Guideline §3.4)."""

    eta_ev: float  # kWh/km
    grid: GridTrajectory
    distance: float

    def emissions(self, t: int) -> float:
        return self.eta_ev * self.grid.at(t) * self.distance


@dataclass
class PHEVEmissions(ProductEmissions):
    """PHEV — Utility-Factor composite of EV-mode grid and ICE-mode combustion (Guideline §3.5).

    UF is the share of distance driven electrically. Mandatory sensitivity UF ± 0.15;
    regulatory UF overstates real-world electric share, so central results are upper bounds.
    """

    uf: float  # 0..1
    eta_elec: float  # kWh/km (EV mode)
    ice_mode_intensity: float  # kgCO2e/km (charge-sustaining)
    grid: GridTrajectory
    distance: float

    def emissions(self, t: int) -> float:
        electric = self.uf * self.eta_elec * self.grid.at(t)
        combustion = (1.0 - self.uf) * self.ice_mode_intensity
        return (electric + combustion) * self.distance
