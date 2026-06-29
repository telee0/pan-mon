import matplotlib
import numpy as np

matplotlib.use("TkAgg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


class Graph3D:
    def __init__(self, ctx):
        self.ctx = ctx

        plt.ion()
        print(matplotlib.get_backend())

        self.fig = plt.figure(figsize=(12, 7))
        self.ax = self.fig.add_subplot(111, projection='3d')

        self.colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
        self._setup_axes()

    def _setup_axes(self):
        # self.ax.set_xlabel("Time", labelpad=20, rotation=0)
        # self.ax.set_ylabel("DP", labelpad=15)
        self.ax.set_zlabel("Util %", labelpad=10)
        self.ax.set_zlim(0, 100)

        self.ax.view_init(elev=25,azim=-60)
        self.ax.dist = 6.0

        self.ax.set_box_aspect((6, 6, 3))

        self.ax.xaxis.pane.fill = False
        self.ax.yaxis.pane.fill = False
        self.ax.zaxis.pane.fill = False

    def update(self):
        history = self.ctx["history"]

        if len(history) < 2:
            return

        self.ax.cla()
        self._setup_axes()

        dp_names = sorted(list(history[-1]["dp"].keys()))
        n = len(dp_names)

        x0, xn = 0, 0
        ax_text = []

        for dp_index, dp_name in enumerate(dp_names, start=1):
            x, y, z = [], n - dp_index, []

            for sample in history:
                x.append(mdates.date2num(sample["time_stamp"]))
                cpu = sample["dp"][dp_name]["cpu-load-maximum"]
                values = [core[1] for core in cpu.values()]
                z.append(sum(values) / len(values) if values else 0)

            x0, xn = x[0], x[-1]

            color = self.colors[dp_index % len(self.colors)]

            verts_x = np.concatenate([[x[0]], x, [x[-1]]])
            verts_y = np.full_like(verts_x, y)  # Keep Y positive and aligned
            verts_z = np.concatenate([[0], z, [0]])

            verts = [list(zip(verts_x, verts_y, verts_z))]

            poly = Poly3DCollection(
                verts,
                facecolors=color,
                edgecolors=color,
                alpha=0.35,
                linewidths=1
            )
            self.ax.add_collection3d(poly)

            y_line = np.full_like(x, y)

            self.ax.plot(
                x,
                y_line,
                z,
                linewidth=2,
                color=color,
                label=dp_name
            )

            ax_text.append((x[-1], y, z[-1], color))

        for x, y, z, color in reversed(ax_text):
            self.ax.text(
                x, y, z,
                f"{z:.1f}%",
                fontsize=8,
                color=color,
                ha="right",
                va="top"
            )

        self.ax.set_xlim(x0, xn)
        self.ax.set_ylim(n, -0.5)
        self.ax.set_yticks(range(n))
        self.ax.set_yticklabels(reversed(dp_names))
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        self.fig.autofmt_xdate(bottom=0.25, rotation=0, ha='center')

        self.ax.set_title("Dataplane CPU Utilization", fontsize=16, pad=5, loc='center')
        self.ax.legend(loc='upper left', bbox_to_anchor=(0.95, 1.05), ncols=(n + 7) // 8,
                       frameon=True, facecolor='white', framealpha=0.8)

        self.fig.subplots_adjust(left=0.01, right=0.99, bottom=0.08, top=0.92)

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.001)

    def close(self):
        plt.close('all')


class Graph:

    def __init__(self, ctx):

        self.ctx = ctx

        plt.ion()

        print(matplotlib.get_backend())

        self.fig, (self.ax_cpu, self.ax_res) = plt.subplots(
            2, 1,
            sharex=True,
            figsize=(12, 8),
        )

        self.lines = {'cpu-load-average': None, 'cpu-load-maximum': None}
        self.fill = {}
        for c in self.lines.keys():
            self.lines[c], = self.ax_cpu.plot([], [], label=c)

        self.lines_res = {'session': None, 'packet buffer': None, 'packet descriptor': None, 'sw tags descriptor': None}
        for c in self.lines_res.keys():
            self.lines_res[c], = self.ax_res.plot([], [], label=c)

        self.ax_cpu.set_ylim(0, 100)
        self.ax_cpu.grid(
            True,
            linestyle="--",
            linewidth=0.5,
            alpha=0.6
        )
        self.ax_cpu.legend()
        self.ax_cpu.xaxis.set_major_formatter(
            mdates.DateFormatter("%H:%M:%S")
        )

        self.ax_res.set_ylim(0, 100)
        self.ax_res.grid(
            True,
            linestyle="--",
            linewidth=0.5,
            alpha=0.6
        )
        self.ax_res.legend()

        self.fig.autofmt_xdate()

    def update(self):
        history = self.ctx["history"]

        if not history:
            return

        x = []
        y1 = {c: [] for c in self.lines.keys()}
        y2 = {c: [] for c in self.lines_res.keys()}

        for sample in history:
            x.append(sample['time_stamp'])
            for c in self.lines.keys():
                cpu_load = sample['dp']['dp0'][c]
                values = []
                for core in cpu_load.values():
                    values.append(core[1])  # the second value
                value = 0
                if c == 'cpu-load-average':
                    value = sum(values) / len(values)
                elif c == 'cpu-load-maximum':
                    value = max(values)
                y1[c].append(value)
            for r in self.lines_res.keys():
                values = sample['dp']['dp0']['resource-utilization'][r]
                y2[r].append(values[1])

        print("x:", x[-1])
        for c in self.lines.keys():
            print(f"y1['{c}']:", y1[c][-1])
        for r in self.lines_res.keys():
            print(f"y2['{r}']:", y2[r][-1])

        for c in self.lines.keys():
            self.lines[c].set_data(x, y1[c])
            if c in self.fill:
                self.fill[c].remove()
        for c in self.lines.keys():
            self.fill[c] = self.ax_cpu.fill_between(
                x,
                y1[c],
                color=self.lines[c].get_color(),
                alpha=0.30,
            )
        for r in self.lines_res.keys():
            self.lines_res[r].set_data(x, y2[r])

        if len(x) > 1:
            self.ax_cpu.set_xlim(x[0], x[-1])

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

        plt.pause(0.01)

    def close(self):
        plt.close('all')
