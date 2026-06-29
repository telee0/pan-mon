import matplotlib
import numpy as np

matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
import matplotlib.dates as mdates


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
