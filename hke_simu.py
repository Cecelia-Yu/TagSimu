# -*- coding: utf-8 -*-
"""
脚本：打开已有的 aedt 工程，选一个 design，做扫频 / 仿真 /导出结果
适用于你只关心已有 geometry + 激励 + 边界情况的场景
"""

import os
from ansys.aedt.core import Desktop, Hfss  # PyAEDT API

# =====================
# 用户配置区（改成你的路径／名字）
# =====================
AEDT_VERSION = "2023.1"  # 你说你用 2023R1
PROJECT_FILE = r"D:\Ansoft\HawkeyeHardwareDesign.aedt"  # 全路径到你的已有 .aedt 文件
DESIGN_NAME = "ReflectTagDesign"  # design 名称（.aedt 中的 Design 标签），如果你只有一个 design，也可以不写

NON_GRAPHICAL = False  # False 则能看到 GUI，也方便调试；True 用于批处理
CLOSE_ON_EXIT = False  # 脚本结束后是否自动关闭 HFSS 界面／AEDT

# 扫频参数（如果已有 project 中没有设置或者你要修改／增加一个 sweep）
F0   = "24GHz"
FMIN = "22GHz"
FMAX = "26GHz"
NPTS = 201

# =====================
# 启动 AEDT + 加载工程
# =====================

# Option A: 用 Desktop + load_project
desktop = Desktop(version=AEDT_VERSION, non_graphical=NON_GRAPHICAL)
# load_project 返回一个 App 实例（例如 Hfss 对象，如果这个 project 的 active design 是 HFSS）
hfssapp = desktop.load_project(PROJECT_FILE, design_name=DESIGN_NAME)
# 注意：如果 design_name=None，则 load active design 或者第一个 design（视情况而定）

# Option B: 或者直接构造 Hfss 并给 project name 路径（效果类似）：
# hfssapp = Hfss(projectname=PROJECT_FILE, version=AEDT_VERSION, non_graphical=NON_GRAPHICAL, close_on_exit=CLOSE_ON_EXIT)
# 然后可以用 hfssapp.design_name 或 hfssapp.active_design 确定当前使用的 design

# =====================
# 检查 / 获取已经有的 setup 或者新建 setup
# =====================

# 获取已存在的 setup 列表
existing_setups = hfssapp.existing_analysis_setups
print("已有的 setup:", existing_setups)

# 如果你要建一个新的 sweep 或 setup，也可以
# 例如创建一个新的 Setup（如果已有的 setup 不满足你需求）
setup_name = "MyNewSetup24G"
if setup_name not in existing_setups:
    new_setup = hfssapp.create_setup(setup_name)
    new_setup.props["Frequency"] = F0
    new_setup.props["MaximumPasses"] = 10
    new_setup.props["DeltaS"] = 0.01
    new_setup.props["MinimumConvergedPasses"] = 2
    new_setup.props["MaximumDeltaS"] = 0.02
else:
    new_setup = hfssapp.get_setup(existing_setups[0])  # 用已有的第一个 setup；你可以改

# 创建或修改 Sweep
sweep_name = "Sweep_22_26G"
# 如果已有同名 sweep 可以先删除或直接复用
hfssapp.create_linear_count_sweep(
    setup=new_setup.name,
    units="GHz",
    start_frequency=float(FMIN.replace("GHz","")),
    stop_frequency=float(FMAX.replace("GHz","")),
    num_of_freq_points=NPTS,
    sweep_type="Interpolating",
    name=sweep_name,
    save_fields=False
)

# =====================
# 运行仿真
# =====================
hfssapp.save_project()
hfssapp.analyze(setupname=new_setup.name)

# =====================
# 后处理 / 导出结果示例
# =====================

# 比如获取 S 参数（如果 geometry + 激励里有端口定义的话）
# 或者获取报告 trace
# 这里举例，获取所有 S 类 trace 并导出一个 report
traces = hfssapp.get_traces_for_plot(category="S")
if traces:
    rpt = hfssapp.post.create_report(traces)
    # 你可以把报告保存成 CSV 或图，视 API 是否支持
    # 示例：导出 CSV
    result_dir = os.path.join(os.path.dirname(PROJECT_FILE), "results")
    os.makedirs(result_dir, exist_ok=True)
    rpt.export_to_file(os.path.join(result_dir, "S_parameters.csv"))

print("✅ 打开与求解完成，设计:", hfssapp.design_name)
print("项目路径：", PROJECT_FILE)

# =====================
# 结束时清理／关闭 AEDT（如果你想）
# =====================
desktop.release_desktop()  # 或者 hfssapp.close_project()，视情况而定
