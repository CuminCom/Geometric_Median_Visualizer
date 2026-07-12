# 几何中位数可视化工具 (Geometric Median Visualizer)

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-3.5%2B-orange)](https://matplotlib.org/)
[![Tkinter](https://img.shields.io/badge/Tkinter-Standard-green)](https://docs.python.org/3/library/tkinter.html)

一个**高性能、交互式**的几何中位数可视化桌面程序，支持点集编辑、拖拽平移、缩放、撤销/重做、数据导入导出，并采用高精度 Weiszfeld 算法计算几何中位数。  
**特色**：完美跟随鼠标的视图平移，无抖动、无延迟，极致流畅。

---

## ✨ 功能特性

- **交互式点编辑**  
  - 打点模式：左键单击添加点，按住 `Shift` 连续添加  
  - 选择模式：单击选中/拖拽移动点，`Ctrl+单击` 多选，框选（拖拽空白区域）  
  - 平移模式：左键/右键拖拽平移视图（**完美跟随**，无滞后无抖动）

- **高性能渲染**  
  - 基于像素坐标的增量平移算法，鼠标与视图完全同步  
  - 同步绘制 + 60 FPS 节流，低速拖动依然丝滑  
  - 视图变化阈值过滤，避免无用刷新

- **高精度算法**  
  - 改进的 Weiszfeld 迭代算法（容差 `1e‑12`，最大迭代 `2000` 次）  
  - 自动处理退化情况（目标点落在数据点上）  
  - 双精度浮点运算，结果精确可靠

- **数据管理**  
  - 导出当前点集为 CSV（`x, y` 两列）  
  - 从 CSV 导入点集（自动忽略非数值行）  
  - 导出绘图为 PNG / PDF / SVG 矢量图

- **撤销/重做**  
  - 支持最多 50 步历史，`Ctrl+Z` / `Ctrl+Y` 轻松回溯

- **视图控制**  
  - 滚轮以鼠标为中心缩放  
  - 一键重置视图 / 自适应显示所有点与中位数

- **实时信息面板**  
  - 显示点数、几何中位数坐标、总距离、平均距离、鼠标实时坐标

---

## 📦 安装与运行

### 环境要求
- Python 3.8 或更高版本
- 依赖库：`numpy`, `matplotlib`

### 安装步骤
```bash
# 克隆仓库
git clone https://github.com/your-username/geometric-median-visualizer.git
cd geometric-median-visualizer

# 安装依赖（推荐使用虚拟环境）
pip install -r requirements.txt   # 或手动安装 numpy matplotlib
```

### 运行
```bash
python main.py
```

---

## 🎮 使用指南

### 模式切换（快捷键）
- `1` – **打点模式**：左键单击添加点；按住 `Shift` 可连续添加  
- `2` – **平移模式**：左键/右键拖拽平移视图  
- `3` – **选择模式**：左键单击选中点（拖拽移动），`Ctrl+单击` 多选，框选（拖拽空白区域），`Delete` 键删除选中点

### 通用操作
- **滚轮**：以鼠标位置为中心缩放  
- **右键拖拽**：任意模式下平移视图  
- **Ctrl+Z / Ctrl+Y**：撤销 / 重做  
- **空白处点击（选择模式）**：取消所有选中

### 数据导入/导出
- **导入 CSV**：点击 `📂 导入CSV`，选择包含 `x, y` 两列数据的 CSV 文件（第一行为表头可选）  
- **导出 CSV**：将当前点集保存为 CSV 文件（含表头 `x, y`）  
- **导出图片**：保存当前绘图为 PNG / PDF / SVG

### 视图控制
- **重置视图**：恢复初始坐标范围 `(-10, 10)`  
- **自适应视图**：自动缩放以显示所有点及中位数（带 20% 边距）

---

## 🧠 算法说明

**几何中位数**（Geometric Median）是使到所有数据点欧氏距离之和最小的点，其求解采用 **Weiszfeld 迭代算法**：

\[
\mathbf{m}^{(k+1)} = \frac{\sum_i \frac{\mathbf{p}_i}{\|\mathbf{p}_i - \mathbf{m}^{(k)}\|}}{\sum_i \frac{1}{\|\mathbf{p}_i - \mathbf{m}^{(k)}\|}}
\]

为避免除零，引入平滑项 `EPS = 1e-12`。若迭代点与某数据点重合（距离 < 1e-14），直接返回该点（退化情况）。  
初始点取数据集的逐维中位数，保证稳健性。  
迭代终止条件：两次迭代位移 < `1e-12` 或达到最大迭代次数 `2000`。

---

## 📁 CSV 数据格式

导入/导出的 CSV 文件应满足：
- 至少包含两列数值（`x` 和 `y`）
- 第一行可包含表头（程序自动跳过非数值行）
- 示例：
```csv
x, y
1.2, 3.4
-0.5, 2.1
4.0, -1.0
```

---

## ⌨️ 快捷键一览

| 按键 | 功能 |
|------|------|
| `1` | 切换到打点模式 |
| `2` | 切换到平移模式 |
| `3` | 切换到选择模式 |
| `Ctrl+Z` | 撤销 |
| `Ctrl+Y` | 重做 |
| `Delete` / `Backspace` | 删除选中点（选择模式下） |
| `Shift+单击` | 连续添加点（打点模式下） |
| `Ctrl+单击` | 多选/反选（选择模式下） |
| 滚轮 | 缩放 |
| 右键拖拽 | 平移视图（任意模式） |

---

## 📋 依赖项

- Python 3.8+
- [NumPy](https://numpy.org/) – 数值计算
- [Matplotlib](https://matplotlib.org/) – 绘图与交互

所有依赖可通过 `pip install -r requirements.txt` 一键安装。

---

## 🤝 贡献与致谢

- **开发辅助**：本项目在开发过程中广泛使用了 **DeepSeek** 人工智能助手进行代码优化、性能调优和文档撰写。
- 欢迎提交 Issue 和 Pull Request。

---

## 📄 许可证

[MIT License](LICENSE) – 可自由使用、修改和分发。

---

**Enjoy!** 如果觉得有用，记得给个 ⭐ 支持一下～
