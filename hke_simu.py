# -*- coding: utf-8 -*-
# Title: 24GHz mmWave Reflective Tag - HFSS PyAEDT Template
# Requires: PyAEDT >= 0.20, AEDT 2024R2+ (tested patterns in docs)
# Tip: Run in a Python env with AEDT installed and licensed.

import os
import pyaedt
from ansys.aedt.core import Hfss
print("PyAEDT version:", pyaedt.__version__)

hfss = Hfss()
print("HFSS object:", hfss)
# -------------------------
# User controls (edit here)
# -------------------------
USE_FSS_UNIT_CELL = True       # True: periodic unit cell with Floquet; False: finite tag + plane wave
PROJECT_NAME = "mmwave_reflect_tag_24GHz.aedt"
DESIGN_NAME  = "ReflectTag"
NG_MODE = False                # Non-graphical if True
AEDT_VERSION = None            # e.g. "2025.2" or None for default

# Frequency plan (24 GHz mmWave)
f0   = "24GHz"
fmin = "22GHz"
fmax = "26GHz"
npts = 401

# Geometry parameters (edit to your stackup)
px, py   = "6mm", "6mm"        # period (FSS) or tag cell pitch
t_sub    = "0.5mm"             # substrate thickness
eps_r    = 2.65                # example substrate
tan_d    = 0.001
copper_t = "18um"

# Angles & polarization
theta_inc = "0deg"
phi_inc   = "0deg"
pol       = "Vertical"         # "Vertical" / "Horizontal" or custom vector [Ex,Ey,Ez]

# -------------------------
# Launch HFSS
# -------------------------
hfss = Hfss(
    version=AEDT_VERSION,
    non_graphical=NG_MODE,
    project=PROJECT_NAME,
    design=DESIGN_NAME,
    solution_type="Modal" if USE_FSS_UNIT_CELL else "DrivenModal",
    close_on_exit=False
)

# -------------------------
# Variables & materials
# -------------------------
hfss["f0"] = f0
hfss["px"] = px
hfss["py"] = py
hfss["t_sub"] = t_sub
hfss["copper_t"] = copper_t

# Add substrate material if needed
matname = "MySub"
if matname not in hfss.materials.material_keys:
    hfss.materials.add_material(matname)
    m = hfss.materials[matname]
    m.permittivity = eps_r
    m.dielectric_loss_tangent = tan_d

# -------------------------
# Build simple stack (unit cell: ground + patch)
# -------------------------
# Substrate box
sub = hfss.modeler.create_box([0, 0, 0], ["px", "py", "t_sub"], name="Substrate", matname=matname)

# Ground (PEC sheet at z=0)
gnd = hfss.modeler.create_rectangle(cs_plane="XY", position=[0,0,0], dimension_list=["px","py"], name="GND")
hfss.assign_perfect_e(gnd.name)

# Simple patch (example: centered square at top surface)
patch_size = "4.5mm"  # <= period
patch = hfss.modeler.create_rectangle(
    cs_plane="XY",
    position=["(px-{} )/2".format(patch_size), "(py-{} )/2".format(patch_size), "t_sub"],
    dimension_list=[patch_size, patch_size],
    name="Patch"
)
hfss.modeler.thicken_sheet(patch.name, "copper_t", both_sides=False)
hfss.assign_material(patch.name, "copper")

# Surrounding air region & open/periodic boundaries
if USE_FSS_UNIT_CELL:
    # Create air region extended along +Z; auto-assign lattice pairs (periodic boundaries)
    # Using the same pattern as the official FSS example.
    air = hfss.modeler.create_air_region(z_pos="(px+py)")
    # Periodic (lattice pair) boundaries on side faces
    hfss.auto_assign_lattice_pairs(assignment=air.name)

    # Floquet port on top face with de-embed back to surface
    # Compute bounding box to point lattice vectors
    x_min, y_min, z_min, x_max, y_max, z_max = air.bounding_box
    port = hfss.create_floquet_port(
        assignment=air.top_face_z,
        lattice_origin=[x_min, y_min, z_max],
        lattice_a_end=[x_min, y_max, z_max],
        lattice_b_end=[x_max, y_min, z_max],
        name="FloquetTop",
        deembed_distance="(px+py)"
    )
else:
    # Finite tag: make a larger air box and create open region (radiation boundary)
    air = hfss.modeler.create_air_region(x_pos="px*2", y_pos="py*2", z_pos="px")
    hfss.create_open_region(frequency=f0, boundary="Radiation")

    # Plane wave excitation (incident from +Z toward -Z by default; set polarization)
    hfss.plane_wave(
        theta=theta_inc, phi=phi_inc, polarization=pol, origin=["0mm","0mm","0mm"], vector_format="Spherical"
    )

# -------------------------
# Analysis setup & sweep
# -------------------------
setup = hfss.create_setup("Setup_24G")
setup.props["Frequency"] = f0
setup.props["MaximumPasses"] = 10
setup.props["DeltaS"] = 0.01
setup.props["MinimumConvergedPasses"] = 2
setup.props["MaximumDeltaS"] = 0.02

hfss.create_linear_count_sweep(
    setup=setup.name,
    units="GHz",
    start_frequency=float(fmin.replace("GHz","")),
    stop_frequency=float(fmax.replace("GHz","")),
    num_of_freq_points=npts,
    sweep_type="Interpolating",
    name="Sweep_22_26G",
    save_fields=False
)

# Optional: far-field/RCS (finite tag only)
if not USE_FSS_UNIT_CELL:
    # Insert a near-field sphere to later compute far field patterns or RCS-like results.
    hfss.insert_near_field_sphere(radius="200mm", x_start=0, x_stop=180, x_step=2, y_start=0, y_stop=360, y_step=2)

# -------------------------
# Solve
# -------------------------
hfss.save_project()
hfss.analyze()

# -------------------------
# Basic post-processing helpers
# -------------------------
if USE_FSS_UNIT_CELL:
    # For Floquet, you can plot impedance or S-parameters among Floquet modes.
    traces = hfss.get_traces_for_plot(category="S")
    if traces:
        report = hfss.post.create_report(traces[:2])
else:
    # For finite tag, request a 3D radiation pattern/RCS-like post (requires far-field setup in GUI or API)
    pass

print("Done.")
