# Analytical Model for Height-Graded Inclined-Pillar Pressure Sensors

This code predicts sequential pillar engagement, total reaction force, and nominal pressure for the sensor configurations described in the paper. The model formulation and calibration are presented in Section 2.4 of the main text and Section S3 of the Supporting Information.

## How to run

1. Install Python 3.7 or later. No additional packages are required.
2. Download `Analytical-Model.py` and run:
   ```bash
   python Analytical-Model.py
   ```
3. Enter the pillar thickness, width, heights, and projected loading-plate area when prompted. Use **mm** for lengths and **mm²** for area. Separate pillar heights with commas or spaces, including repeated heights.
4. Enter the start displacement, end displacement, and positive displacement increment in **mm**.
5. The program prints the pillar-engagement table and the predicted **force in mN** and **pressure in kPa**.

Width and thickness are each constant across all pillars within a configuration. The calibrated coefficients and Young’s modulus are already included in the script.

## Example

Enter these values in the prompted order:

```text
Thickness:              1.30
Width:                  1.30
Heights:                2.50, 2.30, 2.10
Loading-plate area:     27
Start displacement:     0
End displacement:       0.50
Displacement increment: 0.10
```

At **0.500 mm**, the predicted total force is **17.727838 mN** and nominal pressure is **0.656587 kPa**, matching the worked example in Section S3.3 of the Supporting Information.
