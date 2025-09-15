# -*- coding: utf-8 -*-
"""
功能：打开已有 .aedt 工程，列出：
  - 分析 Setup 与 Sweep
  - 边界条件 / 激励（含端口、辐射、PML、PerfectE/H、Floquet 等）
  - 设计变量、材料（可选）
  - 可绘制的 S 参数 traces（用来快速自检端口与网络是否存在）

仅读取与汇总，不改几何
"""

import os
from ansys.aedt.core import Desktop, Hfss

# ======= 必改：工程路径 & 设计名 =======
AEDT_VERSION = "2023.1"  # 你是 2023R1
PROJECT_FILE = r"D:\Ansoft\HawkeyeHardwareDesign.aedt"  # 你的 .aedt 文件全路径
NON_GRAPHICAL = False   # True=后台；False=带 GUI（新手建议 False，便于对照）
CLOSE_ON_EXIT = False

# 启动 AEDT 并载入工程

desk = Desktop(version=AEDT_VERSION, non_graphical=NON_GRAPHICAL)
app = desk.load_project(PROJECT_FILE)

print("\n=== 项目信息 ===")
print("Project:", PROJECT_FILE)
print("Design :", app.design_name)
print("Solution type:", app.solution_type)
print("Existing setups:", app.existing_analysis_setups)
# 边界/激励列表（如果真是空，基本确定未设置）
for b in app.boundaries:
    print(b.type, b.name)

# ---------- 1) 分析 Setup & Sweep ----------
print("\n=== 分析 Setups ===")
setups = app.existing_analysis_setups  # 列出已有 Setup 名称
print("已存在的 Setups:", setups)  # 例如 ['Setup1', 'Setup_24G', ...]

for s in setups:
    stp = app.get_setup(s)  # 取 Setup 对象
    print(f"\n[Setup] {s}")
    # 打印关键求解参数（不同版本/产品 props 键名略有差异，这里做安全访问）
    for k in ["Frequency", "MaximumPasses", "DeltaS", "MinimumConvergedPasses", "MaximumDeltaS", "BasisOrder", "PercentRefinementPerPass"]:
        if k in stp.props:
            print(f"  {k}: {stp.props[k]}")

    # 列出该 Setup 下的 Sweeps
    try:
        sweep_names = app.get_sweeps(s)  # 返回该 setup 的 sweep 名称列表
    except Exception:
        sweep_names = []
    print("  Sweeps:", sweep_names)

    # 展开每个 Sweep 的关键参数
    for sw in sweep_names:
        sw_obj = stp.get_sweep(sw)  # 取具体 sweep 对象
        print(f"   └─[Sweep] {sw}")
        # 常见键：RangeType / RangeStart / RangeEnd / RangeCount / SaveFields / Type 等
        for key in ["RangeType", "RangeStart", "RangeEnd", "RangeCount", "Type", "SaveFields", "SaveRadFieldsOnly"]:
            if key in sw_obj.props:
                print(f"      {key}: {sw_obj.props[key]}")

# ---------- 2) 边界条件 / 激励（含端口） ----------
print("\n=== 边界 / 激励（含端口） ===")
# app.boundaries 返回 BoundaryObject 列表（包含 Radiation、PML、PEC/PMC(PerfectE/H)、Symmetry、WavePort、LumpedPort、FloquetPort 等）
for b in app.boundaries:
    # BoundaryObject 常见字段：name/type/props/assignment 等（不同类型的 props 字段会不同）
    btype = getattr(b, "type", "Unknown")
    bname = getattr(b, "name", "Unnamed")
    print(f"[{btype}] {bname}")
    # 打印部分关键属性（存在才打印）
    props = getattr(b, "props", {})
    for key in ["Objects", "Faces", "FacesList", "IsAssignedToSketch", "Polarization", "Theta", "Phi", "Impedance", "Resistance", "Reactance", "RenormalizeAllTerminals"]:
        if key in props:
            print(f"   {key}: {props[key]}")

# ---------- 3) 变量（设计变量 / 材料变量等） ----------
print("\n=== 设计变量 ===")
try:
    vars_dict = app.variable_manager.variables  # 设计级变量
    for k, v in vars_dict.items():
        print(f"{k} = {v}")
except Exception:
    print("（此设计无显式变量或版本不支持此接口）")

# ---------- 4) 快速自检：可绘制的曲线（S 参数等） ----------
print("\n=== 可用的曲线（traces） ===")
try:
    traces = app.get_traces_for_plot(category="S")  # 试取 S 参数曲线名
    print(traces[:10] if traces else "（未发现 S 类曲线）")
except Exception as e:
    print("获取 traces 失败：", e)

# （可选）保存并不求解：这里只读
# app.save_project()

print("\n✅ 信息汇总完毕。如果你想把信息写入txt/CSV，也可以把上面的 print 改成文件写入。")

# 结束
if CLOSE_ON_EXIT:
    desk.release_desktop()
