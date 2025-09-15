本项目用于天线反射性能的参数化仿真。

脚本介绍

`hke_simu.py` 设置激励条件，输出仿真结果

`hke_read.py` 查看当前项目的结构化信息


debug log

`hke_read.py` 运行报错，成功打开HFSS但是未能打开项目，具体报错信息如下
```bash
PyAEDT ERROR: **************************************************************
PyAEDT ERROR:   File "C:\Users\yuwy\PycharmProjects\simulation\hke_read.py", line 28, in <module>
PyAEDT ERROR:     app = desk.load_project(PROJECT_FILE) 
PyAEDT ERROR: AEDT API Error on load_project
PyAEDT ERROR: Method arguments: 
PyAEDT ERROR:     project_file = D:\Ansoft\HawkeyeHardwareDesign.aedt 
PyAEDT ERROR: **************************************************************
```
因为之前打开了该项目，应关闭窗口后重新运行程序。