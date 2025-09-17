# -*- coding: utf-8 -*-

import os
from ansys.aedt.core import Desktop
from ansys.aedt.core.visualization.plot.pdf import AnsysReport

# --- 项目和设计设置 ---
AEDT_VERSION = "2023.1"
PROJECT_FILE = r"D:\Ansoft\HawkeyeHardwareDesign.aedt"
DESIGN_NAME = "24GHzPlanarVAABackscatter"
IMAGE_DIR = r"D:\Ansoft\HawkeyeHardwareDesign\Images" # 建议将图片保存在单独的目录
REPORTS_DIR = r"D:\Ansoft\Reports"

# --- 创建输出目录 (如果不存在) ---
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

# --- 检查项目文件 ---
if not os.path.exists(PROJECT_FILE):
    print(f"项目文件不存在：{PROJECT_FILE}")
    exit() # 如果文件不存在，则退出脚本
else:
    print(f"项目文件存在：{PROJECT_FILE}")

print(f"指定的设计名称：{DESIGN_NAME}")

# --- 初始化 AEDT ---
desk = Desktop(version=AEDT_VERSION, non_graphical=False)
app = desk.load_project(PROJECT_FILE, design_name=DESIGN_NAME)

# --- 创建仿真设置 ---
setup = app.create_setup("Setup_24G")
setup.props["Frequency"] = "24GHz"
setup.props["MaximumPasses"] = 10
setup.props["DeltaS"] = 0.01
setup.props["MinimumConvergedPasses"] = 2

# --- 创建扫频设置 ---
app.create_linear_count_sweep(
    setup=setup.name,
    units="GHz",
    start_frequency=22.0,
    stop_frequency=26.0,
    num_of_freq_points=51,
    sweep_type="Discrete",
    name="Sweep_22_26G_fast",
    save_fields=True,
    save_rad_fields=True
)

# --- 插入远场采样球 ---
# 注意：如果项目中已存在 "Infinite Sphere 1"，此步会跳过或报错，具体取决于PyAEDT版本行为
# 最好在运行前确保项目中没有同名设置
if "Infinite Sphere 1" not in app.modeler.get_boundaries_name():
    app.insert_infinite_sphere(
        name="Infinite Sphere 1",
        definition="Theta-Phi",
        x_start="0deg", x_stop="180deg", x_step="5deg",
        y_start="0deg", y_stop="360deg", y_step="5deg"
    )

# --- 保存项目并开始分析 ---
app.save_project()
print("开始分析，请稍候...")
app.analyze(setup=setup.name)
print("分析完成。")

# --- 后处理：创建、导出远场辐射图 ---
post_processor = app.post
plot_name = "FarFieldPattern_3D"  # 定义图表名称

# 1. 在 AEDT 中创建远场辐射图 (3D Polar Plot)
print(f"正在创建报告: {plot_name}")
post_processor.create_report(
    plot_name,
    report_type="3D Polar Plot",
    display_type="Far Fields",
    far_field_setup="Infinite Sphere 1",
    primary_sweep_variable="Theta",
    secondary_sweep_variable="Phi",
    quantity="GainTotal", # 你可以根据需要改为 rETotal, RealizedGainTotal 等
    solution=setup.name + " : " + "Sweep_22_26G_fast"
)

# 2. 将创建的报告导出为 JPG 图像
image_path = os.path.join(IMAGE_DIR, f"{plot_name}.jpg")
print(f"正在导出图像到: {image_path}")
post_processor.export_report_to_jpg(IMAGE_DIR, plot_name)
# 注意: export_report_to_jpg 会自动在指定目录生成名为 "plot_name.jpg" 的文件

# --- 生成 PDF 仿真报告 ---
print("正在生成 PDF 报告...")
report = AnsysReport()
report.aedt_version = AEDT_VERSION
report.template_name = "AnsysTemplate"
report.project_name = os.path.basename(PROJECT_FILE)
report.design_name = DESIGN_NAME
report.create()

# 添加章节和图表
report.add_chapter("Far Field Analysis")
report.add_sub_chapter("Radiation Pattern")
if os.path.exists(image_path):
    report.add_image(image_path, width=400, caption="Far Field Radiation Pattern (GainTotal)")
else:
    print(f"警告: 未找到图像文件 {image_path}，无法添加到PDF。")
report.add_toc()

# 3. 保存 PDF 报告 (修正后的调用方式)
pdf_filename = "FarFieldReport.pdf"
report.save_pdf(output_dir=REPORTS_DIR, output_file=pdf_filename)
print(f"PDF 报告已保存到: {os.path.join(REPORTS_DIR, pdf_filename)}")

# --- 导出图形数据为 CSV 格式 ---
print(f"正在导出 {plot_name} 的数据为 CSV...")
exported_file = post_processor.export_report_to_file(REPORTS_DIR, plot_name, ".csv")
print(f"图形数据已导出到: {exported_file}")

# --- 释放 AEDT ---
desk.release_desktop()
print("脚本执行完毕。")

