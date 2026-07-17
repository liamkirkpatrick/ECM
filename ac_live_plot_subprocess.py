"""
Non-blocking AC live plot controller for ECM GUI.

The main acquisition script calls send_point() from the encoder-critical loop.
That call only pushes a small tuple into an in-process queue. A background
writer thread serializes those messages to a separate matplotlib worker process.
This avoids matplotlib redraws and pipe writes from blocking encoder polling.
"""

import json
import os
import queue
import subprocess
import sys
import threading
import time

import numpy as np


class ACSubprocessLivePlot:
    def __init__(self, ydim, x_distance, title="AC Runs - Live",
                 initial_ylim=(0, 10e-8), update_interval=0.25,
                 send_every_points=5, max_queue=10000):
        self.ydim = np.asarray(ydim, dtype=float)
        self.x_distance = np.asarray(x_distance, dtype=float)
        self.title = title
        self.initial_ylim = initial_ylim
        self.update_interval = update_interval
        self.send_every_points = max(1, int(send_every_points))
        self.q = queue.Queue(maxsize=max_queue)
        self.closed = False
        self.dropped_messages = 0

        worker_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ac_live_plot_worker.py")
        self.proc = subprocess.Popen(
            [sys.executable, worker_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )

        self.writer = threading.Thread(target=self._writer_loop, daemon=True)
        self.writer.start()

        x_max = float(np.nanmax(self.x_distance)) if self.x_distance.size else 1.0
        self._enqueue({
            "cmd": "configure",
            "ydim": self.ydim.tolist(),
            "x_max": x_max,
            "title": title,
            "initial_ylim": list(initial_ylim),
            "update_interval": float(update_interval),
        })

    def _enqueue(self, msg):
        if self.closed:
            return
        try:
            self.q.put_nowait(msg)
        except queue.Full:
            # Drop live-plot messages rather than blocking acquisition.
            self.dropped_messages += 1

    def _writer_loop(self):
        pending = []
        last_flush = time.time()
        while True:
            try:
                msg = self.q.get(timeout=0.1)
            except queue.Empty:
                msg = None

            if msg is not None:
                if msg.get("cmd") == "__writer_close__":
                    break
                pending.append(msg)

            now = time.time()
            if pending and (len(pending) >= 50 or now - last_flush >= 0.1 or msg is None):
                try:
                    for item in pending:
                        self.proc.stdin.write(json.dumps(item, separators=(",", ":")) + "\n")
                    self.proc.stdin.flush()
                except Exception:
                    break
                pending = []
                last_flush = now

        # Flush anything left, then ask the worker to close.
        try:
            for item in pending:
                self.proc.stdin.write(json.dumps(item, separators=(",", ":")) + "\n")
            self.proc.stdin.write(json.dumps({"cmd": "close"}) + "\n")
            self.proc.stdin.flush()
            self.proc.stdin.close()
        except Exception:
            pass

    def send_point(self, track, point_index, x_mm, y_value):
        """Queue one live point. Safe to call inside the encoder loop."""
        if self.closed:
            return
        try:
            point_index = int(point_index)
        except Exception:
            return
        if point_index % self.send_every_points != 0:
            return
        try:
            y_float = float(y_value)
        except Exception:
            return
        if not np.isfinite(y_float):
            return
        self._enqueue({
            "cmd": "point",
            "track": int(track),
            "x": float(x_mm),
            "y": y_float,
        })

    def finish_track(self, track, x_values, y_values):
        """Send the completed track and autoscale y in the worker process."""
        if self.closed:
            return
        x = np.asarray(x_values, dtype=float)
        y = np.asarray(y_values, dtype=float)
        n = min(len(x), len(y))
        x = x[:n]
        y = y[:n]
        good = np.isfinite(x) & np.isfinite(y)
        self._enqueue({
            "cmd": "replace_track",
            "track": int(track),
            "x": x[good].tolist(),
            "y": y[good].tolist(),
        })
        self._enqueue({"cmd": "finish_track", "track": int(track)})

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            self.q.put_nowait({"cmd": "__writer_close__"})
        except Exception:
            pass
        try:
            self.writer.join(timeout=1.0)
        except Exception:
            pass
        try:
            if self.proc.poll() is None:
                self.proc.terminate()
        except Exception:
            pass
