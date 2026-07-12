import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
import copy
import csv
import time


class PointApp:
    # ---------- 可调参数 ----------
    EPS = 1e-12
    MAX_ITER = 2000
    TOL = 1e-12
    DEFAULT_VIEW = (-10, 10, -10, 10)
    UPDATE_THRESHOLD = 1e-6      # 视图变化最小阈值
    FRAME_INTERVAL = 0.016       # ~60 FPS

    def __init__(self, root):
        self.root = root
        self.root.title("几何中位数可视化 ")
        self.root.geometry("1050x720")

        self.points = []
        self.target = None
        self.history = []
        self.history_index = -1

        self.view_xlim = (self.DEFAULT_VIEW[0], self.DEFAULT_VIEW[1])
        self.view_ylim = (self.DEFAULT_VIEW[2], self.DEFAULT_VIEW[3])

        self.mode = 'add'
        self.selected_indices = set()
        self.drag_data = {
            'index': None,          # 选中点索引
            'start_pixel': None,    # 平移起始像素坐标 (event.x, event.y)
            'start_lim': None,      # 平移起始视图极限 (xlim, ylim)
        }
        self.rect_patch = None

        # 节流控制
        self.last_update_time = 0

        self._build_ui()
        self._bind_events()
        self._save_state()
        self.set_mode_add()
        self.update_plot()

    # ==================== UI 构建 ====================
    def _build_ui(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        info_frame = tk.Frame(main_frame, width=240, bd=2, relief=tk.GROOVE)
        info_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        info_frame.pack_propagate(False)

        tk.Label(info_frame, text="⚡ 几何中位数可视化", font=('Segoe UI', 12, 'bold')).pack(pady=5)

        self.lbl_point_count = tk.Label(info_frame, text="点数: 0", font=('Consolas', 10))
        self.lbl_point_count.pack(anchor=tk.W, padx=8, pady=2)

        self.lbl_target = tk.Label(info_frame, text="几何中位数: 无", font=('Consolas', 10))
        self.lbl_target.pack(anchor=tk.W, padx=8, pady=2)

        self.lbl_total_dist = tk.Label(info_frame, text="总距离: 0.000", font=('Consolas', 10))
        self.lbl_total_dist.pack(anchor=tk.W, padx=8, pady=2)

        self.lbl_avg_dist = tk.Label(info_frame, text="平均距离: 0.000", font=('Consolas', 10))
        self.lbl_avg_dist.pack(anchor=tk.W, padx=8, pady=2)

        self.lbl_mouse = tk.Label(info_frame, text="鼠标: (-, -)", font=('Consolas', 10))
        self.lbl_mouse.pack(anchor=tk.W, padx=8, pady=2)

        tk.Label(info_frame, text="", height=1).pack()
        self.lbl_extra = tk.Label(info_frame, text="", font=('Consolas', 9), fg='gray')
        self.lbl_extra.pack(anchor=tk.W, padx=8, pady=2)

        tk.Label(info_frame, text="⌨️ 快捷键", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, padx=8, pady=(10, 3))
        shortcuts = [
            "1 : 打点模式",
            "2 : 平移模式",
            "3 : 选择模式",
            "Ctrl+Z : 撤销",
            "Ctrl+Y : 重做",
            "Delete : 删除选中",
            "滚轮 : 缩放",
            "右键拖拽 : 平移视图",
            "Ctrl+单击 : 多选",
            "Shift+单击 : 连续打点"
        ]
        for s in shortcuts:
            tk.Label(info_frame, text=s, font=('Consolas', 9)).pack(anchor=tk.W, padx=8)

        tk.Button(info_frame, text="📖 帮助", command=self.show_help, bg='#e0e0e0').pack(pady=5)

        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlim(*self.view_xlim)
        self.ax.set_ylim(*self.view_ylim)
        self.ax.grid(True, alpha=0.3)
        self.ax.set_aspect('equal', adjustable='box')

        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar1 = tk.Frame(right_frame)
        toolbar1.pack(fill=tk.X, padx=5, pady=3)

        self.btn_add = tk.Button(toolbar1, text="打点 (1)", command=self.set_mode_add, width=8)
        self.btn_add.pack(side=tk.LEFT, padx=2)

        self.btn_move = tk.Button(toolbar1, text="平移 (2)", command=self.set_mode_move, width=8)
        self.btn_move.pack(side=tk.LEFT, padx=2)

        self.btn_select = tk.Button(toolbar1, text="选择 (3)", command=self.set_mode_select, width=8)
        self.btn_select.pack(side=tk.LEFT, padx=2)

        tk.Frame(toolbar1, width=2, bd=2, relief=tk.SUNKEN).pack(side=tk.LEFT, fill=tk.Y, padx=6)

        self.btn_undo = tk.Button(toolbar1, text="↩ 撤销", command=self.undo, width=8)
        self.btn_undo.pack(side=tk.LEFT, padx=2)

        self.btn_redo = tk.Button(toolbar1, text="↪ 重做", command=self.redo, width=8)
        self.btn_redo.pack(side=tk.LEFT, padx=2)

        self.btn_clear = tk.Button(toolbar1, text="🗑 清空", command=self.clear_all, width=8)
        self.btn_clear.pack(side=tk.LEFT, padx=2)

        toolbar2 = tk.Frame(right_frame)
        toolbar2.pack(fill=tk.X, padx=5, pady=3)

        self.btn_import = tk.Button(toolbar2, text="📂 导入CSV", command=self.import_csv, width=10)
        self.btn_import.pack(side=tk.LEFT, padx=2)

        self.btn_export_csv = tk.Button(toolbar2, text="💾 导出CSV", command=self.export_csv, width=10)
        self.btn_export_csv.pack(side=tk.LEFT, padx=2)

        self.btn_export_img = tk.Button(toolbar2, text="🖼 导出图片", command=self.export_image, width=10)
        self.btn_export_img.pack(side=tk.LEFT, padx=2)

        tk.Frame(toolbar2, width=2, bd=2, relief=tk.SUNKEN).pack(side=tk.LEFT, fill=tk.Y, padx=6)

        self.btn_reset_view = tk.Button(toolbar2, text="🔄 重置视图", command=self.reset_view, width=10)
        self.btn_reset_view.pack(side=tk.LEFT, padx=2)

        self.btn_fit_view = tk.Button(toolbar2, text="📐 自适应视图", command=self.fit_view, width=10)
        self.btn_fit_view.pack(side=tk.LEFT, padx=2)

        self.status = tk.Label(right_frame, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    def _bind_events(self):
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.canvas.mpl_connect('scroll_event', self.on_scroll)

        self.root.bind('<Key>', self.on_key)
        self.root.bind('<Control-z>', lambda e: self.undo())
        self.root.bind('<Control-y>', lambda e: self.redo())

    # ==================== 模式切换 ====================
    def set_mode_add(self):
        self.mode = 'add'
        self.status.config(text="模式: 打点 | 左键添加点，Shift+单击连续添加，滚轮缩放")
        self._highlight_btn(self.btn_add)

    def set_mode_move(self):
        self.mode = 'move'
        self.status.config(text="模式: 平移 | 左键/右键拖拽平移，滚轮缩放")
        self._highlight_btn(self.btn_move)

    def set_mode_select(self):
        self.mode = 'select'
        self.status.config(text="模式: 选择 | 左键选中/框选，Ctrl+多选，Delete删除，空白点击取消选中")
        self._highlight_btn(self.btn_select)

    def _highlight_btn(self, active):
        for btn in (self.btn_add, self.btn_move, self.btn_select):
            btn.config(relief=tk.RAISED, bg='SystemButtonFace')
        active.config(relief=tk.SUNKEN, bg='lightblue')

    def clear_selection(self):
        self.selected_indices.clear()
        self.drag_data['index'] = None
        if self.rect_patch:
            self.rect_patch.remove()
            self.rect_patch = None

    # ==================== 历史管理 ====================
    def _save_state(self):
        state = {
            'points': copy.deepcopy(self.points),
            'target': self.target,
            'selected': self.selected_indices.copy()
        }
        self.history = self.history[:self.history_index + 1]
        self.history.append(state)
        self.history_index += 1
        if len(self.history) > 50:
            self.history.pop(0)
            self.history_index -= 1

    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self._load_state(self.history[self.history_index])
            self.status.config(text="已撤销")

    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self._load_state(self.history[self.history_index])
            self.status.config(text="已重做")

    def _load_state(self, state):
        self.points = copy.deepcopy(state['points'])
        self.target = state['target']
        self.selected_indices = state['selected'].copy()
        self.clear_selection()
        self.compute_target()
        self.update_plot()

    def clear_all(self):
        if not self.points:
            return
        if messagebox.askyesno("确认", "确定清空所有点？"):
            self._save_state()
            self.points.clear()
            self.target = None
            self.clear_selection()
            self.update_plot()
            self.status.config(text="已清空所有点")

    # ==================== 核心算法（高精度） ====================
    def compute_target(self):
        if not self.points:
            self.target = None
            return
        pts = np.array(self.points, dtype=np.float64)
        target = np.median(pts, axis=0)

        for _ in range(self.MAX_ITER):
            dist = np.linalg.norm(pts - target, axis=1)
            zero_mask = dist < 1e-14
            if np.any(zero_mask):
                self.target = tuple(target)
                return
            weights = 1.0 / (dist + self.EPS)
            new_target = np.sum(pts * weights[:, None], axis=0) / np.sum(weights)
            if np.linalg.norm(new_target - target) < self.TOL:
                target = new_target
                break
            target = new_target
        self.target = tuple(target)

    def get_total_distance(self):
        if self.target is None or not self.points:
            return 0.0
        pts = np.array(self.points)
        return float(np.sum(np.linalg.norm(pts - np.array(self.target), axis=1)))

    def get_avg_distance(self):
        total = self.get_total_distance()
        return total / len(self.points) if self.points else 0.0

    # ==================== 绘图 ====================
    def update_plot(self, force=False):
        """强制完整重绘"""
        self.view_xlim = self.ax.get_xlim()
        self.view_ylim = self.ax.get_ylim()

        self.ax.clear()
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlim(*self.view_xlim)
        self.ax.set_ylim(*self.view_ylim)
        self.ax.set_aspect('equal', adjustable='box')

        if self.target and self.points:
            tx, ty = self.target
            for px, py in self.points:
                self.ax.plot([px, tx], [py, ty], 'g--', alpha=0.25, linewidth=0.8)

        if self.points:
            xs, ys = zip(*self.points)
            self.ax.plot(xs, ys, 'ko', markersize=8)
            for i, (x, y) in enumerate(self.points):
                if i not in self.selected_indices:
                    self.ax.annotate(str(i), (x, y), textcoords="offset points",
                                     xytext=(5, 5), fontsize=8, alpha=0.6)

        if self.selected_indices:
            sel_x = [self.points[i][0] for i in self.selected_indices]
            sel_y = [self.points[i][1] for i in self.selected_indices]
            self.ax.plot(sel_x, sel_y, 'ro', markersize=12,
                         markeredgecolor='darkred', markeredgewidth=2, alpha=0.85)
            for i in self.selected_indices:
                x, y = self.points[i]
                self.ax.annotate(str(i), (x, y), textcoords="offset points",
                                 xytext=(5, 5), fontsize=9, color='red', fontweight='bold')

        if self.target:
            tx, ty = self.target
            self.ax.plot(tx, ty, 'r*', markersize=18,
                         markeredgecolor='darkred', markeredgewidth=1.5)
            circle = plt.Circle((tx, ty), 0.5, color='red', fill=False, alpha=0.3, linestyle='--')
            self.ax.add_patch(circle)
            self.ax.annotate(f"({tx:.2f}, {ty:.2f})", (tx, ty),
                             textcoords="offset points", xytext=(10, -15),
                             fontsize=9, color='red',
                             bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))

        if self.rect_patch:
            self.ax.add_patch(self.rect_patch)

        self.canvas.draw()  # 同步绘制，确保即时反馈
        self._update_info_panel()

    def _update_info_panel(self):
        self.lbl_point_count.config(text=f"点数: {len(self.points)}")
        if self.target:
            tx, ty = self.target
            self.lbl_target.config(text=f"几何中位数: ({tx:.6f}, {ty:.6f})")
            total = self.get_total_distance()
            avg = self.get_avg_distance()
            self.lbl_total_dist.config(text=f"总距离: {total:.6f}")
            self.lbl_avg_dist.config(text=f"平均距离: {avg:.6f}")
        else:
            self.lbl_target.config(text="几何中位数: 无")
            self.lbl_total_dist.config(text="总距离: 0")
            self.lbl_avg_dist.config(text="平均距离: 0")

    # ==================== 事件处理（完美平移） ====================
    def _should_update(self):
        now = time.time()
        if now - self.last_update_time >= self.FRAME_INTERVAL:
            self.last_update_time = now
            return True
        return False

    def on_press(self, event):
        if event.inaxes != self.ax:
            return
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return

        if event.button == 3:  # 右键平移
            self.drag_data['start_pixel'] = (event.x, event.y)
            self.drag_data['start_lim'] = (self.ax.get_xlim(), self.ax.get_ylim())
            self.status.config(text="平移中... (右键)")
            return

        if event.button != 1:
            return

        if self.mode == 'add':
            self._save_state()
            self.points.append((float(x), float(y)))
            self.compute_target()
            self.update_plot()
            if event.key == 'shift':
                self.status.config(text="连续添加模式 (松开Shift退出)")
            else:
                self.status.config(text="已添加点")

        elif self.mode == 'move':
            self.drag_data['start_pixel'] = (event.x, event.y)
            self.drag_data['start_lim'] = (self.ax.get_xlim(), self.ax.get_ylim())
            self.status.config(text="平移中... (左键)")

        elif self.mode == 'select':
            idx = self._find_nearest_point(x, y, threshold=0.5)
            ctrl = (event.key == 'control')

            if idx is not None:
                if ctrl:
                    self.selected_indices.symmetric_difference_update({idx})
                else:
                    self.selected_indices = {idx}
                self.drag_data['index'] = idx
                self.update_plot()
            else:
                if not ctrl:
                    self.selected_indices.clear()
                self.drag_data['start_pixel'] = (event.x, event.y)  # 用于框选
                self.drag_data['index'] = None
                if self.rect_patch:
                    self.rect_patch.remove()
                    self.rect_patch = None
                self.update_plot()

    def on_motion(self, event):
        if event.inaxes != self.ax:
            return
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return

        # 更新鼠标坐标显示
        self.lbl_mouse.config(text=f"鼠标: ({x:.2f}, {y:.2f})")

        # ---------- 平移处理（基于像素坐标，完美跟随） ----------
        if self.mode in ('move', 'select') and self.drag_data.get('start_pixel') is not None:
            # 只处理左键平移（模式 move）或右键（已在press中处理），这里统一用start_pixel判断
            # 但注意选择模式下也有start_pixel用于框选，所以需要区分
            if self.mode == 'move' or (self.mode == 'select' and event.button == 3):
                start_px, start_py = self.drag_data['start_pixel']
                dx_pixel = event.x - start_px
                dy_pixel = event.y - start_py

                # 获取当前轴的数据范围
                xlim = self.ax.get_xlim()
                ylim = self.ax.get_ylim()
                # 获取像素宽度和高度
                bbox = self.ax.bbox
                width_px = bbox.width
                height_px = bbox.height

                # 数据坐标位移
                dx_data = dx_pixel * (xlim[1] - xlim[0]) / width_px
                dy_data = dy_pixel * (ylim[1] - ylim[0]) / height_px

                # 从起始极限计算新极限
                xlim0, ylim0 = self.drag_data['start_lim']
                new_xlim = (xlim0[0] - dx_data, xlim0[1] - dx_data)
                new_ylim = (ylim0[0] - dy_data, ylim0[1] - dy_data)

                # 过滤微小变化
                if (abs(new_xlim[0] - self.ax.get_xlim()[0]) > self.UPDATE_THRESHOLD or
                    abs(new_ylim[0] - self.ax.get_ylim()[0]) > self.UPDATE_THRESHOLD):
                    self.ax.set_xlim(*new_xlim)
                    self.ax.set_ylim(*new_ylim)
                    if self._should_update():
                        self.canvas.draw()  # 同步绘制，消除抖动
                return

        # ---------- 选择模式：拖拽点 ----------
        if self.mode == 'select' and self.drag_data.get('index') is not None:
            idx = self.drag_data['index']
            self.points[idx] = (float(x), float(y))
            self.compute_target()
            if self._should_update():
                self.update_plot()
            return

        # ---------- 选择模式：框选矩形 ----------
        if self.mode == 'select' and self.drag_data.get('start_pixel') is not None and self.drag_data.get('index') is None:
            # 框选基于像素坐标的矩形，但我们需要用数据坐标来画矩形，所以用xdata,ydata
            if self.drag_data.get('start_xdata') is None:
                # 存储起始数据坐标
                self.drag_data['start_xdata'] = x
                self.drag_data['start_ydata'] = y
            else:
                x0 = self.drag_data['start_xdata']
                y0 = self.drag_data['start_ydata']
                if self.rect_patch:
                    self.rect_patch.remove()
                self.rect_patch = Rectangle(
                    (min(x0, x), min(y0, y)), abs(x - x0), abs(y - y0),
                    fill=True, alpha=0.12, color='blue', edgecolor='blue', linestyle='dashed', linewidth=1
                )
                self.ax.add_patch(self.rect_patch)
                if self._should_update():
                    self.canvas.draw()
            return

    def on_release(self, event):
        if event.inaxes != self.ax:
            return
        x, y = event.xdata, event.ydata

        # 结束平移
        if event.button == 3 or self.mode == 'move':
            self.drag_data['start_pixel'] = None
            self.drag_data['start_lim'] = None
            self.status.config(text="就绪")
            return

        if event.button != 1:
            return

        # 选择模式框选结束
        if self.mode == 'select' and self.drag_data.get('index') is None:
            if self.drag_data.get('start_xdata') is not None and x is not None and y is not None:
                x0 = self.drag_data['start_xdata']
                y0 = self.drag_data['start_ydata']
                if abs(x - x0) > 0.1 or abs(y - y0) > 0.1:
                    xmin, xmax = sorted([x0, x])
                    ymin, ymax = sorted([y0, y])
                    new_sel = {
                        i for i, (px, py) in enumerate(self.points)
                        if xmin <= px <= xmax and ymin <= py <= ymax
                    }
                    if event.key == 'control':
                        self.selected_indices.update(new_sel)
                    else:
                        self.selected_indices = new_sel
                else:
                    if event.key != 'control':
                        self.selected_indices.clear()
                        self.status.config(text="已取消选中")

                if self.rect_patch:
                    self.rect_patch.remove()
                    self.rect_patch = None
                self.update_plot()
                self.drag_data['start_xdata'] = None
                self.drag_data['start_ydata'] = None
            self.drag_data['start_pixel'] = None
            return

        # 点拖拽结束保存历史
        if self.mode == 'select' and self.drag_data.get('index') is not None:
            self._save_state()
            self.drag_data['index'] = None
            self.status.config(text="点已移动")

        if self.mode == 'add' and event.key == 'shift':
            self.status.config(text="模式: 打点 | 左键添加点，Shift+单击连续添加")

    def on_scroll(self, event):
        if event.inaxes != self.ax:
            return
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        cx = event.xdata if event.xdata is not None else (xlim[0] + xlim[1]) / 2
        cy = event.ydata if event.ydata is not None else (ylim[0] + ylim[1]) / 2

        factor = 0.8 if event.button == 'up' else 1.25
        half_w = (xlim[1] - xlim[0]) / 2 * factor
        half_h = (ylim[1] - ylim[0]) / 2 * factor

        new_xlim = (cx - half_w, cx + half_w)
        new_ylim = (cy - half_h, cy + half_h)
        if (abs(self.ax.get_xlim()[0] - new_xlim[0]) > self.UPDATE_THRESHOLD or
            abs(self.ax.get_ylim()[0] - new_ylim[0]) > self.UPDATE_THRESHOLD):
            self.ax.set_xlim(*new_xlim)
            self.ax.set_ylim(*new_ylim)
            if self._should_update():
                self.canvas.draw()

    def on_key(self, event):
        key = event.keysym.lower()
        if key == '1':
            self.set_mode_add()
        elif key == '2':
            self.set_mode_move()
        elif key == '3':
            self.set_mode_select()
        elif key in ('delete', 'backspace'):
            if self.selected_indices and self.mode == 'select':
                self._save_state()
                for idx in sorted(self.selected_indices, reverse=True):
                    if 0 <= idx < len(self.points):
                        del self.points[idx]
                self.selected_indices.clear()
                self.compute_target()
                self.update_plot()
                self.status.config(text="已删除选中点")

    def _find_nearest_point(self, x, y, threshold):
        best_idx = None
        best_dist = threshold ** 2
        for i, (px, py) in enumerate(self.points):
            d = (px - x) ** 2 + (py - y) ** 2
            if d < best_dist:
                best_dist = d
                best_idx = i
        return best_idx

    # ==================== 视图控制 ====================
    def reset_view(self):
        self.ax.set_xlim(self.DEFAULT_VIEW[0], self.DEFAULT_VIEW[1])
        self.ax.set_ylim(self.DEFAULT_VIEW[2], self.DEFAULT_VIEW[3])
        self.canvas.draw()
        self.status.config(text="视图已重置")

    def fit_view(self):
        if not self.points and self.target is None:
            return
        all_x = [p[0] for p in self.points]
        all_y = [p[1] for p in self.points]
        if self.target:
            all_x.append(self.target[0])
            all_y.append(self.target[1])
        if not all_x:
            return
        xmin, xmax = min(all_x), max(all_x)
        ymin, ymax = min(all_y), max(all_y)
        margin = max((xmax - xmin) * 0.2, 0.5)
        self.ax.set_xlim(xmin - margin, xmax + margin)
        self.ax.set_ylim(ymin - margin, ymax + margin)
        self.canvas.draw()
        self.status.config(text="已自适应视图")

    # ==================== 数据导入/导出 ====================
    def import_csv(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file_path:
            return
        try:
            new_points = []
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        try:
                            x = float(row[0].strip())
                            y = float(row[1].strip())
                            new_points.append((x, y))
                        except ValueError:
                            continue
            if new_points:
                self._save_state()
                self.points = new_points
                self.clear_selection()
                self.compute_target()
                self.update_plot()
                self.status.config(text=f"已导入 {len(self.points)} 个点")
            else:
                messagebox.showwarning("导入失败", "未找到有效坐标数据")
        except Exception as e:
            messagebox.showerror("导入错误", str(e))

    def export_csv(self):
        if not self.points:
            messagebox.showinfo("提示", "没有点可导出")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file_path:
            return
        try:
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["x", "y"])
                for x, y in self.points:
                    writer.writerow([x, y])
            self.status.config(text=f"已导出 {len(self.points)} 个点到 {file_path}")
        except Exception as e:
            messagebox.showerror("导出错误", str(e))

    def export_image(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG 图片", "*.png"),
                ("PDF 文档", "*.pdf"),
                ("SVG 矢量图", "*.svg"),
                ("所有文件", "*.*")
            ]
        )
        if path:
            try:
                self.fig.savefig(path, dpi=300, bbox_inches='tight')
                self.status.config(text=f"导出成功: {path}")
            except Exception as e:
                messagebox.showerror("导出失败", str(e))

    # ==================== 帮助 ====================
    def show_help(self):
        help_text = """⚡ 几何中位数可视化工具

【性能特点】
- 基于像素坐标的增量平移，鼠标与视图完全同步
- 同步绘制，无延迟无抖动
- 60 FPS 节流，性能优化
- 高精度 Weiszfeld 算法 (容差 1e-12)

【模式快捷键】
  1 - 打点模式
  2 - 平移模式
  3 - 选择模式
  Ctrl+Z / Ctrl+Y - 撤销/重做
  Delete - 删除选中点

【操作提示】
  滚轮缩放，右键/左键拖拽平移
  Shift+单击连续打点
  框选（拖拽空白区域）配合 Ctrl 多选

【数据管理】
  导入/导出 CSV，导出图片/PDF/SVG
"""
        messagebox.showinfo("帮助", help_text)


if __name__ == "__main__":
    root = tk.Tk()
    app = PointApp(root)
    root.mainloop()