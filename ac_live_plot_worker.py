"""
AC live plot worker for ECM GUI.

This file is launched as a separate Python process by ac_live_plot_subprocess.py.
It reads JSON-line commands from stdin and updates a matplotlib plot. Keeping
matplotlib in this separate process prevents redraws from slowing the ECM
acquisition / encoder-counting loop.
"""

import json
import queue
import sys
import threading
import time

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import numpy as np


class _ACPlotWorker:
    def __init__(self):
        self.cmd_q = queue.Queue()
        self.running = True
        self.configured = False
        self.fig = None
        self.ax = None
        self.lines = []
        self.xdata = []
        self.ydata = []
        self.ydim = []
        self.update_interval = 0.25
        self.initial_ylim = (0, 10e-8)
        self.last_draw = 0.0
        self.needs_draw = False

    def start_reader_thread(self):
        thread = threading.Thread(target=self._reader_loop, daemon=True)
        thread.start()

    def _reader_loop(self):
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                self.cmd_q.put(json.loads(line))
            except Exception:
                # Ignore malformed messages rather than killing the plot process.
                pass
        self.cmd_q.put({"cmd": "close"})

    def _configure(self, msg):
        self.ydim = list(msg.get("ydim", []))
        x_max = float(msg.get("x_max", 1.0))
        title = msg.get("title", "AC Runs - Live")
        self.update_interval = float(msg.get("update_interval", 0.25))
        self.initial_ylim = tuple(msg.get("initial_ylim", [0, 10e-8]))

        cmap = matplotlib.colormaps.get_cmap("coolwarm")

        plt.ion()
        self.fig, self.ax = plt.subplots(1, 1, figsize=(8, 5), dpi=100)
        self.ax.set_title(title)
        self.ax.set_xlabel("Distance Along Track (mm)")
        self.ax.set_ylabel("Conductivity")
        self.ax.set_xlim(0, x_max)
        self.ax.set_ylim(*self.initial_ylim)

        self.xdata = [[] for _ in self.ydim]
        self.ydata = [[] for _ in self.ydim]
        self.lines = []
        for i, yval in enumerate(self.ydim):
            line, = self.ax.plot([], [], color=cmap(i / max(len(self.ydim), 1)), label=str(round(yval, 3)))
            self.lines.append(line)

        self.ax.legend(title="Distance across core:", fontsize=8)
        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()
        self.last_draw = time.time()
        self.configured = True

    def _point(self, msg):
        if not self.configured:
            return
        track = int(msg.get("track", -1))
        if track < 0 or track >= len(self.lines):
            return
        x = msg.get("x", None)
        y = msg.get("y", None)
        if x is None or y is None:
            return
        try:
            x = float(x)
            y = float(y)
        except Exception:
            return
        if not np.isfinite(y):
            return
        self.xdata[track].append(x)
        self.ydata[track].append(y)
        self.lines[track].set_data(self.xdata[track], self.ydata[track])
        self.needs_draw = True

    def _replace_track(self, msg):
        if not self.configured:
            return
        track = int(msg.get("track", -1))
        if track < 0 or track >= len(self.lines):
            return
        x = np.asarray(msg.get("x", []), dtype=float)
        y = np.asarray(msg.get("y", []), dtype=float)
        good = np.isfinite(x) & np.isfinite(y)
        self.xdata[track] = x[good].tolist()
        self.ydata[track] = y[good].tolist()
        self.lines[track].set_data(self.xdata[track], self.ydata[track])
        self.needs_draw = True

    def _finish_track(self, msg):
        if not self.configured:
            return
        # Autoscale y only at the end of a track. Keep x fixed as distance.
        self.ax.relim()
        self.ax.autoscale_view(scalex=False, scaley=True)
        self.needs_draw = True
        self._draw(force=True)

    def _draw(self, force=False):
        if not self.configured or self.fig is None:
            return
        now = time.time()
        if force or (self.needs_draw and (now - self.last_draw >= self.update_interval)):
            try:
                self.fig.canvas.draw_idle()
                self.fig.canvas.flush_events()
            except Exception:
                self.running = False
            self.last_draw = now
            self.needs_draw = False

    def _handle_msg(self, msg):
        cmd = msg.get("cmd")
        if cmd == "configure":
            self._configure(msg)
        elif cmd == "point":
            self._point(msg)
        elif cmd == "replace_track":
            self._replace_track(msg)
        elif cmd == "finish_track":
            self._finish_track(msg)
        elif cmd == "close":
            self.running = False

    def run(self):
        self.start_reader_thread()
        while self.running:
            try:
                while True:
                    self._handle_msg(self.cmd_q.get_nowait())
            except queue.Empty:
                pass

            if self.fig is not None and not plt.fignum_exists(self.fig.number):
                self.running = False
                break

            self._draw(force=False)
            plt.pause(0.02)

        try:
            plt.close("all")
        except Exception:
            pass


if __name__ == "__main__":
    _ACPlotWorker().run()
