import math
import queue
import threading
import tkinter as tk


class AssistantOrb:
    """A small, round animated orb for the desktop assistant."""

    _PALETTES = {
        "Listening": ("#42E8F5", "#125D76", "#071D32"),
        "Thinking": ("#C09AFF", "#593B8A", "#1C1238"),
        "Speaking": ("#62F5C1", "#176C58", "#08291F"),
        "Ready": ("#70BFFF", "#285B85", "#0A1B30"),
    }

    def __init__(self):
        self._commands = queue.Queue()
        self._stop_event = threading.Event()

    def show(self, state="Listening"):
        self._commands.put(("show", state))

    def show_idle(self):
        self.show("Ready")

    def set_state(self, state):
        self._commands.put(("state", state))

    def hide(self):
        self._commands.put(("hide", None))

    def close(self):
        self._stop_event.set()
        self._commands.put(("close", None))

    @property
    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        root = tk.Tk()
        root.title("US AI")
        root.resizable(False, False)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.99)
        root.attributes("-transparentcolor", "#000000")
        root.overrideredirect(True)

        size = 250
        margin = 28
        x = max(root.winfo_screenwidth() - size - margin, 0)
        y = max(root.winfo_screenheight() - size - margin - 26, 0)
        root.geometry(f"{size}x{size}+{x}+{y}")
        root.configure(bg="#000000")

        canvas = tk.Canvas(root, width=size, height=size, bg="#000000", highlightthickness=0, bd=0)
        canvas.pack()

        drag = {"x": 0, "y": 0}

        def start_drag(event):
            drag["x"] = event.x_root - root.winfo_x()
            drag["y"] = event.y_root - root.winfo_y()

        def move_window(event):
            root.geometry(f"+{event.x_root - drag['x']}+{event.y_root - drag['y']}")

        canvas.bind("<ButtonPress-1>", start_drag)
        canvas.bind("<B1-Motion>", move_window)

        anim = {"state": "Ready", "visible": True, "tick": 0, "after_id": None}

        def draw_orb():
            if not anim["visible"]:
                anim["after_id"] = None
                return

            canvas.delete("all")
            tick = anim["tick"]
            anim["tick"] += 1
            accent, mid, shadow = self._PALETTES.get(
                anim["state"], self._PALETTES["Ready"]
            )
            cx = size / 2
            cy = size / 2 + math.sin(tick * 0.035) * 2
            pulse = (math.sin(tick * 0.07) + 1) / 2

            # Soft outer aura and fine circular instrument rings.
            canvas.create_oval(
                cx - 108 - pulse * 3, cy - 108 - pulse * 3,
                cx + 108 + pulse * 3, cy + 108 + pulse * 3,
                fill=shadow, outline="", stipple="gray25",
            )
            canvas.create_oval(
                cx - 101, cy - 101, cx + 101, cy + 101,
                outline="#142F46", width=1,
            )
            canvas.create_oval(
                cx - 94, cy - 94, cx + 94, cy + 94,
                outline="#193C55", width=1,
            )
            canvas.create_arc(
                cx - 101, cy - 101, cx + 101, cy + 101,
                start=(tick * 1.7) % 360, extent=86, style="arc",
                outline=accent, width=2,
            )
            canvas.create_arc(
                cx - 94, cy - 94, cx + 94, cy + 94,
                start=(-tick * 1.1) % 360, extent=58, style="arc",
                outline=mid, width=2,
            )

            # A shaded sphere, lit from the upper-left, gives the orb its depth.
            radius = 67 + pulse * 1.5
            canvas.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                fill="#06121E", outline=mid, width=2,
            )
            for layer in range(18, 0, -1):
                fraction = layer / 18
                layer_radius = radius * fraction
                offset_x = -radius * 0.23 * (1 - fraction)
                offset_y = -radius * 0.27 * (1 - fraction)
                canvas.create_oval(
                    cx + offset_x - layer_radius,
                    cy + offset_y - layer_radius,
                    cx + offset_x + layer_radius,
                    cy + offset_y + layer_radius,
                    fill=_blend(shadow, accent, 0.12 + (1 - fraction) * 0.52),
                    outline="",
                )
            canvas.create_oval(
                cx - 44, cy - 42, cx - 10, cy - 8,
                fill="#D9FFFF", outline="", stipple="gray50",
            )
            canvas.create_oval(
                cx - 37, cy - 36, cx - 20, cy - 19,
                fill="#FFFFFF", outline="",
            )

            # Rotating elliptical arcs and orbiting lights imply a turning 3D core.
            angle = tick * 0.055
            points = []
            for step in range(65):
                theta = step * math.tau / 64
                px = math.cos(theta) * 83
                py = math.sin(theta) * 27
                rx = px * math.cos(angle) - py * math.sin(angle) * 0.35
                ry = px * math.sin(angle) * 0.35 + py * math.cos(angle)
                points.extend((cx + rx, cy + ry))
            canvas.create_line(*points, fill=mid, width=2, smooth=True)

            for index in range(3):
                orbit_angle = angle + index * math.tau / 3
                px = cx + math.cos(orbit_angle) * 88
                py = cy + math.sin(orbit_angle) * 31
                canvas.create_oval(
                    px - 2.5, py - 2.5, px + 2.5, py + 2.5,
                    fill=accent, outline="",
                )

            canvas.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                outline=accent, width=1,
            )
            canvas.create_text(
                cx, size - 22,
                text=anim["state"].upper(),
                fill=accent,
                font=("Segoe UI", 9, "bold"),
            )
            anim["after_id"] = root.after(40, draw_orb)

        def drain_commands():
            while True:
                try:
                    action, value = self._commands.get_nowait()
                except queue.Empty:
                    break

                if action == "close":
                    root.destroy()
                    return
                if action == "hide":
                    anim["visible"] = False
                    if anim["after_id"] is not None:
                        root.after_cancel(anim["after_id"])
                        anim["after_id"] = None
                    root.withdraw()
                elif action == "show":
                    anim["state"] = value or "Ready"
                    was_visible = anim["visible"]
                    anim["visible"] = True
                    root.deiconify()
                    root.lift()
                    if not was_visible:
                        draw_orb()
                elif action == "state":
                    anim["state"] = value or "Ready"

            root.after(30, drain_commands)

        root.deiconify()
        draw_orb()
        root.after(30, drain_commands)
        root.protocol("WM_DELETE_WINDOW", self.hide)
        root.mainloop()


def _blend(start, end, amount):
    start_rgb = tuple(int(start[index:index + 2], 16) for index in (1, 3, 5))
    end_rgb = tuple(int(end[index:index + 2], 16) for index in (1, 3, 5))
    channels = tuple(
        round(first + (last - first) * amount)
        for first, last in zip(start_rgb, end_rgb)
    )
    return "#{:02X}{:02X}{:02X}".format(*channels)
