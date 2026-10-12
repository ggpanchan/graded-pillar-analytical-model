#!/usr/bin/env python3
"""
Supporting Information

Reduced-Order Analytical Model for Sequential Structural Recruitment
--------------------------------------------------------------------

This script implements the reduced-order analytical model described in the
manuscript. It predicts the staged force and pressure response of a
multi-height bending-pillar pressure sensor without finite element analysis.

The user defines:
    - pillar thickness, t
    - pillar width, w
    - pillar heights, H_i
    - top-plate loading area, A_p
    - displacement start, end, and increment

The script returns:
    - structural recruitment table
    - pressure prediction table

Model equation
--------------
For each pillar i,

    F_i = gamma * E * (w * t^3 / H_i^3) * delta_i
          * [1 + b * (delta_i / H_i)^m]

where

    g_i     = H_1 - H_i
    delta_i = max(d - g_i, 0)
    F(d)    = sum(F_i)
    P(d)    = F(d) / A_p

Units
-----
E in MPa, lengths in mm, force in mN, and pressure in kPa.

Calibrated constants
--------------------
gamma = 18.542
b     = 374.47
m     = 6.952
E     = 4.95 MPa
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ModelConstants:
    """Calibrated model constants."""
    gamma: float = 18.542
    b: float = 374.47
    m: float = 6.952
    E: float = 4.95  # MPa


class BendingPillarModel:
    """Reduced-order predictor for a height-graded bending-pillar sensor."""

    def __init__(
        self,
        thickness: float,
        width: float,
        heights: List[float],
        top_plate_area: float,
        constants: Optional[ModelConstants] = None,
    ):
        if len(heights) < 1:
            raise ValueError("At least one pillar height must be provided.")

        if thickness <= 0:
            raise ValueError("Pillar thickness must be positive.")

        if width <= 0:
            raise ValueError("Pillar width must be positive.")

        if top_plate_area <= 0:
            raise ValueError("Top-plate loading area must be positive.")

        self.t = float(thickness)
        self.w = float(width)
        self.H = sorted([float(h) for h in heights], reverse=True)
        self.Ap = float(top_plate_area)
        self.constants = constants or ModelConstants()

        if any(h <= 0 for h in self.H):
            raise ValueError("All pillar heights must be positive.")

    # ------------------------------------------------------------------
    # Structural recruitment
    # ------------------------------------------------------------------
    def activation_gap(self, height: float) -> float:
        """Return activation gap for a pillar of height H_i."""
        return self.H[0] - height

    def effective_displacement(self, height: float, displacement: float) -> float:
        """Return post-contact displacement for a pillar at applied displacement d."""
        gap = self.activation_gap(height)
        return max(displacement - gap, 0.0)

    def structural_recruitment(self) -> List[dict]:
        """Return height, spacing, gap, and engagement displacement for each pillar."""
        rows = []

        for i, height in enumerate(self.H):
            spacing = None if i == 0 else self.H[i - 1] - height
            gap = self.activation_gap(height)

            rows.append(
                {
                    "pillar": f"P{i + 1}",
                    "height_mm": height,
                    "spacing_mm": spacing,
                    "gap_mm": gap,
                    "engages_at_mm": gap,
                }
            )

        return rows

    # ------------------------------------------------------------------
    # Force and pressure prediction
    # ------------------------------------------------------------------
    def pillar_force(self, height: float, displacement: float) -> float:
        """Return force carried by one pillar at applied displacement d."""
        delta = self.effective_displacement(height, displacement)

        if delta <= 0:
            return 0.0

        c = self.constants
        stiffness = c.gamma * c.E * (self.w * self.t**3 / height**3)
        hardening = 1.0 + c.b * (delta / height) ** c.m

        return stiffness * delta * hardening

    def total_force(self, displacement: float) -> float:
        """Return total reaction force at applied displacement d."""
        return sum(self.pillar_force(height, displacement) for height in self.H)

    def pressure(self, displacement: float) -> float:
        """Return pressure at applied displacement d."""
        return self.total_force(displacement) / self.Ap

    def active_pillars(self, displacement: float) -> str:
        """Return active pillar labels at applied displacement d."""
        active = []

        for i, height in enumerate(self.H):
            delta = self.effective_displacement(height, displacement)
            if delta > 0:
                active.append(f"P{i + 1}")

        return ",".join(active) if active else "-"

    def predict_response(self, displacement: float) -> dict:
        """Return response at one displacement."""
        force = self.total_force(displacement)
        pressure = force / self.Ap

        return {
            "d_mm": displacement,
            "active_pillars": self.active_pillars(displacement),
            "force_mN": force,
            "pressure_kPa": pressure,
        }

    def predict_curve(
        self,
        d_start: float,
        d_end: float,
        d_step: float,
    ) -> List[dict]:
        """Return pressure response over a user-defined displacement range."""
        if d_step <= 0:
            raise ValueError("Displacement increment must be positive.")

        if d_end < d_start:
            raise ValueError("Displacement end must be greater than or equal to start.")

        rows = []
        d = float(d_start)

        while d <= d_end + 1e-12:
            rows.append(self.predict_response(round(d, 12)))
            d += d_step

        return rows


# ----------------------------------------------------------------------
# Input utilities
# ----------------------------------------------------------------------
def read_float(prompt: str, default: Optional[float] = None) -> float:
    """Read a floating-point value from the user."""
    while True:
        if default is None:
            raw = input(prompt).strip()
        else:
            raw = input(f"{prompt} [{default}]: ").strip()

        if raw == "" and default is not None:
            return float(default)

        try:
            value = float(raw)
            return value
        except ValueError:
            print("Please enter a valid number.")


def read_heights(prompt: str) -> List[float]:
    """Read comma- or space-separated pillar heights."""
    while True:
        raw = input(prompt).strip()

        try:
            values = [float(x) for x in raw.replace(",", " ").split()]
            if len(values) == 0:
                raise ValueError
            if any(v <= 0 for v in values):
                raise ValueError
            return values
        except ValueError:
            print("Enter positive pillar heights separated by commas or spaces.")
            print("Example: 2.5, 2.3, 2.1")


# ----------------------------------------------------------------------
# Printing utilities
# ----------------------------------------------------------------------
def print_structural_recruitment(model: BendingPillarModel):
    """Print structural recruitment table."""
    rows = model.structural_recruitment()

    print()
    print("=" * 78)
    print("SECTION 1 -- STRUCTURAL RECRUITMENT")
    print("=" * 78)
    print(
        f"{'Pillar':>8}"
        f"{'Height (mm)':>15}"
        f"{'Spacing dh (mm)':>18}"
        f"{'Gap g_i (mm)':>17}"
        f"{'Engages at d (mm)':>20}"
    )
    print("-" * 78)

    for row in rows:
        spacing = "-" if row["spacing_mm"] is None else f"{row['spacing_mm']:.4f}"

        print(
            f"{row['pillar']:>8}"
            f"{row['height_mm']:>15.4f}"
            f"{spacing:>18}"
            f"{row['gap_mm']:>17.4f}"
            f"{row['engages_at_mm']:>20.4f}"
        )

    print("-" * 78)
    print(f"Tallest pillar height H_1 = {model.H[0]:.4f} mm")
    print(f"All pillars recruited after d = {model.H[0] - model.H[-1]:.4f} mm")
    print()


def print_pressure_prediction(curve: List[dict]):
    """Print pressure prediction table."""
    print()
    print("=" * 78)
    print("SECTION 2 -- PRESSURE PREDICTION")
    print("=" * 78)
    print(
        f"{'d (mm)':>10}"
        f"{'Active Pillars':>18}"
        f"{'Force (mN)':>18}"
        f"{'Pressure (kPa)':>20}"
    )
    print("-" * 78)

    for row in curve:
        print(
            f"{row['d_mm']:>10.4f}"
            f"{row['active_pillars']:>18}"
            f"{row['force_mN']:>18.6f}"
            f"{row['pressure_kPa']:>20.6f}"
        )

    print("-" * 78)
    print()


# ----------------------------------------------------------------------
# Main program
# ----------------------------------------------------------------------
def main():
    print()
    print("=" * 78)
    print("HEIGHT-GRADED BENDING-PILLAR PRESSURE SENSOR")
    print("REDUCED-ORDER ANALYTICAL MODEL")
    print("=" * 78)
    print("All dimensions must be entered in mm.")
    print("Top-plate area must be entered in mm^2.")
    print()

    thickness = read_float("Pillar thickness, t (mm): ")
    width = read_float("Pillar width, w (mm): ")
    heights = read_heights("Pillar heights, H_i (mm): ")
    top_plate_area = read_float("Top-plate loading area, A_p (mm^2): ")

    print()
    print("Displacement range")
    d_start = read_float("Start displacement, d_start (mm)", default=0.0)
    d_end = read_float("End displacement, d_end (mm): ")
    d_step = read_float("Displacement increment, d_step (mm): ")

    model = BendingPillarModel(
        thickness=thickness,
        width=width,
        heights=heights,
        top_plate_area=top_plate_area,
    )

    curve = model.predict_curve(
        d_start=d_start,
        d_end=d_end,
        d_step=d_step,
    )

    print_structural_recruitment(model)
    print_pressure_prediction(curve)


if __name__ == "__main__":
    main()
