# -*- coding: utf-8 -*-
# 目标：在已有几何上进行“平面波入射 → 反射/散射评估”
# 关键修正点：
#  - plane_wave 用 propagation_vector，而不是 theta/phi 命名参数
#  - 无端口问题用 Discrete（或 Fast）扫频，并开启 save_fields/save_rad_fields
#  - Region 已存在则不再新建空气域

from ansys.aedt.core import Desktop

AEDT_VERSION = "2023.1"
PROJECT_FILE = r"D:\Ansoft\HawkeyeHardwareDesign.aedt"
DESIGN_NAME  = "24GHzPlanarVAABackscatter"

F0, FMIN, FMAX, NPTS = "24GHz", "22GHz", "26GHz", 201

desk = Desktop(version=AEDT_VERSION, non_graphical=False)
app  = desk.load_project(PROJECT_FILE, design_name=DESIGN_NAME)

# 1) 开域（如果工程已有人为的 air region，可仅调用 create_open_region）
#    若你明确知道已有 Region，可注释掉 create_air_region 这行
try:
    app.modeler.create_air_region(x_pos="10mm", y_pos="10mm", z_pos="10mm")
except Exception:
    # Region 已存在会抛信息，不致命；忽略
    pass

app.create_open_region(frequency=F0, boundary="Radiation")   # 或 boundary="PML"
# 文档：Hfss.create_open_region(frequency, boundary, ...)
# https://aedt.docs.pyansys.com/.../Hfss.create_open_region.html

# 2) 平面波激励：正入射（phi=0deg, theta=0deg），垂直极化
#    正确用法：vector_format + propagation_vector
app.plane_wave(
    vector_format="Spherical",
    polarization="Vertical",  # 或 "Horizontal"；也可给自定义极化向量
    propagation_vector=[["0deg","0deg",1], ["0deg","0deg",1]],
    origin=["0mm","0mm","0mm"]
)
# 文档签名与参数说明见：
# https://aedt.docs.pyansys.com/.../Hfss.plane_wave.html

# 3) Setup + 离散扫频（保存场数据，否则无端口问题会报错）
setup = app.create_setup("Setup_24G")
setup.props["Frequency"] = F0
setup.props["MaximumPasses"] = 10
setup.props["DeltaS"] = 0.01
setup.props["MinimumConvergedPasses"] = 2

app.create_linear_count_sweep(
    setup=setup.name,
    units="GHz",
    start_frequency=float(FMIN.replace("GHz","")),
    stop_frequency=float(FMAX.replace("GHz","")),
    num_of_freq_points=NPTS,
    sweep_type="Discrete",     # 关键：无端口用 Discrete / Fast
    name="Sweep_22_26G",
    save_fields=True,          # 关键：至少保存一次场
    save_rad_fields=True       # 可选：仅保存辐射场，便于做远场
)
# 文档：Hfss.create_linear_count_sweep(..., save_fields, save_rad_fields, sweep_type)
# https://aedt.docs.pyansys.com/.../Hfss.create_linear_count_sweep.html

# （可选）4) 插入远场采样球（用于辐射/散射方向图/RCS）
#    例如：phi: 0→360° step 5°, theta: 0→180° step 5°
app.insert_infinite_sphere(definition="Theta-Phi", x_start="0deg", x_stop="180deg", x_step="5deg",
                            y_start="0deg", y_stop="360deg", y_step="5deg")
# 文档：insert_infinite_sphere
# https://aedt.docs.pyansys.com/.../Hfss.insert_infinite_sphere.html

app.save_project()
app.analyze(setup=setup.name)   # 正确参数名是 setup
# 文档：Hfss.analyze(...)
# https://aedt.docs.pyansys.com/version/stable/API/_autosummary/ansys.aedt.core.hfss.Hfss.analyze.html

print("✅ 求解完成；请在 GUI 里用 Far Fields / Radiation Pattern 查看散射或回波方向图。")

# desk.release_desktop()
