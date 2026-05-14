import tkinter as tk

import win32api


class TkRoiPicker:
    def __init__(self, callback, prompt="SELECT ROI", color="cyan"):
        self.callback = callback
        self.root = tk.Tk()
        self.root.withdraw()
        self._closed = False

        self.sw = win32api.GetSystemMetrics(0)
        self.sh = win32api.GetSystemMetrics(1)
        self.overlay = tk.Toplevel(self.root)
        self.overlay.geometry(f"{self.sw}x{self.sh}+0+0")
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-alpha", 0.4)
        self.overlay.attributes("-topmost", True)
        self.overlay.configure(bg="black")
        self.color = color

        self.canvas = tk.Canvas(self.overlay, cursor="cross", bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.start_x = 0
        self.start_y = 0
        self.rect = None

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Escape>", self.on_cancel)
        self.overlay.bind("<Escape>", self.on_cancel)
        self.canvas.bind("<Escape>", self.on_cancel)
        self.canvas.create_text(
            self.sw // 2,
            100,
            text=f"{prompt.upper()} (ESC TO CANCEL)",
            fill=self.color,
            font=("Courier New", 24, "bold"),
        )
        self.overlay.after(50, self.overlay.focus_force)
        self.overlay.after(60, self.canvas.focus_set)

    def on_cancel(self, _event=None):
        self.close()
        return "break"

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.start_x,
            self.start_y,
            outline=self.color,
            width=3,
        )

    def on_drag(self, event):
        if self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
        x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
        if x2 > x1 and y2 > y1:
            self.callback({"left": x1, "top": y1, "width": x2 - x1, "height": y2 - y1})
        self.close()

    def close(self):
        if self._closed:
            return
        self._closed = True
        self.root.destroy()

    def show(self):
        self.root.mainloop()


class TkRoiPreview:
    def __init__(self, rois, prompt="ROI PREVIEW"):
        self.root = tk.Tk()
        self.root.withdraw()
        self._closed = False
        self.sw = win32api.GetSystemMetrics(0)
        self.sh = win32api.GetSystemMetrics(1)
        self.overlay = tk.Toplevel(self.root)
        self.overlay.geometry(f"{self.sw}x{self.sh}+0+0")
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-alpha", 0.32)
        self.overlay.attributes("-topmost", True)
        self.overlay.configure(bg="black")
        self.canvas = tk.Canvas(self.overlay, cursor="cross", bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.root.bind("<Escape>", self.on_cancel)
        self.overlay.bind("<Escape>", self.on_cancel)
        self.canvas.bind("<Escape>", self.on_cancel)
        self.overlay.bind("<ButtonRelease-1>", self.on_cancel)
        self.canvas.bind("<ButtonRelease-1>", self.on_cancel)
        self.canvas.create_text(
            self.sw // 2,
            80,
            text=f"{prompt.upper()} (CLICK OR ESC TO CLOSE)",
            fill="#f0d8e8",
            font=("Courier New", 22, "bold"),
        )
        self._draw_rois(rois)
        self.overlay.after(50, self.overlay.focus_force)
        self.overlay.after(60, self.canvas.focus_set)

    def on_cancel(self, _event=None):
        self.close()
        return "break"

    def _draw_rois(self, rois):
        colors = {"bar": "#f0d8e8", "banner": "#65DBFF", "button": "#FFB86C"}
        for name, roi in rois.items():
            left = int(roi["left"])
            top = int(roi["top"])
            right = left + int(roi["width"])
            bottom = top + int(roi["height"])
            color = colors.get(name, "#ffffff")
            self.canvas.create_rectangle(left, top, right, bottom, outline=color, width=3)
            self.canvas.create_text(
                left + 6,
                max(12, top - 12),
                text=name.upper(),
                fill=color,
                font=("Courier New", 13, "bold"),
                anchor="w",
            )

    def close(self):
        if self._closed:
            return
        self._closed = True
        self.root.destroy()

    def show(self):
        self.root.mainloop()
