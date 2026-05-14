import time
import tkinter as tk
from datetime import datetime

import customtkinter as ctk
from PIL import Image

from nte_auto_fish.gui.theme import (
    AMBER_ACC,
    BG_CARD,
    BG_ROOT,
    BG_TAB,
    BORDER,
    BORDER_DARK,
    GREEN_ACC,
    PINK_HI,
    PINK_MID,
    PINK_DIM,
    RED_ACC,
    TEXT_DIM,
    TEXT_MUTED,
    TEXT_PRIMARY,
)

BG_LOG = "#0a0d12"
FONT_MONO = ("JetBrains Mono", 9)
FONT_MONO_BOLD = ("JetBrains Mono", 10, "bold")


class Shell(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(
            master,
            width=400,
            height=580,
            fg_color=BG_ROOT,
            corner_radius=0,
            border_width=1,
            border_color=BORDER,
        )
        self.pack_propagate(False)
        self.bind("<Configure>", self._place_brackets)
        self._tl_h = ctk.CTkFrame(self, fg_color=PINK_MID, corner_radius=0)
        self._tl_v = ctk.CTkFrame(self, fg_color=PINK_MID, corner_radius=0)
        self._br_h = ctk.CTkFrame(self, fg_color=PINK_MID, corner_radius=0)
        self._br_v = ctk.CTkFrame(self, fg_color=PINK_MID, corner_radius=0)

    def _place_brackets(self, _event=None):
        w = self.winfo_width()
        h = self.winfo_height()
        s = 24
        t = 2
        placements = [
            (self._tl_h, 0, 0, s, t),
            (self._tl_v, 0, 0, t, s),
            (self._br_h, w - s, h - t, s, t),
            (self._br_v, w - t, h - s, t, s),
        ]
        for widget, x, y, width, height in placements:
            widget.configure(width=width, height=height)
            widget.place(x=x, y=y)
            widget.lift()


class HeaderButton(ctk.CTkButton):
    def __init__(self, master, text, command=None):
        super().__init__(
            master,
            text=text,
            width=34,
            height=34,
            corner_radius=10,
            fg_color=BG_TAB,
            hover_color="#151820",
            border_width=1,
            border_color="#40464f",
            text_color="#ffffff",
            font=("JetBrains Mono", 16, "bold"),
            command=command,
        )

    def start_pulse(self):
        self.configure(border_color=PINK_HI)

    def stop_pulse(self):
        self.configure(border_color="#40464f")


class Header(ctk.CTkFrame):
    def __init__(self, master, start_command, stop_command):
        super().__init__(master, fg_color=BG_TAB, height=86, corner_radius=0)
        self.pack_propagate(False)
        self._pulse = True
        self._logo_status = "idle"
        self._status_text = "IDLE"
        self._build(start_command, stop_command)

    def _build(self, start_command, stop_command):
        portrait = ctk.CTkFrame(self, width=86, height=86, corner_radius=0, fg_color="transparent")
        portrait.pack(side="left", padx=(0, 12), fill="y")
        portrait.pack_propagate(False)
        self._build_logo(portrait)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(side="right", padx=(0, 14))
        self.btn_start = HeaderButton(buttons, "▶", command=start_command)
        self.btn_start.pack(side="left", padx=(0, 6))
        self.btn_stop = HeaderButton(buttons, "■", command=stop_command)
        self.btn_stop.pack(side="left")

        self._status_pill = ctk.CTkFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=6,
            border_width=1,
            border_color=BORDER,
            height=24,
        )
        self._status_pill.pack(side="right", padx=(0, 8))
        self._dot = tk.Canvas(self._status_pill, width=7, height=7, bg=BG_CARD, highlightthickness=0)
        self._dot.pack(side="left", padx=(8, 4))
        self._dot_id = self._dot.create_oval(1, 1, 6, 6, fill=PINK_MID, outline="")
        self._status_label = ctk.CTkLabel(
            self._status_pill, text="IDLE", font=FONT_MONO_BOLD, text_color=PINK_MID
        )
        self._status_label.pack(side="left", padx=(0, 8))
        self._animate_dot()

        title = ctk.CTkFrame(self, fg_color="transparent")
        title.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(
            title,
            text="CHIZ FISHING TOOL",
            font=("Outfit", 13, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w", pady=(28, 0))
        ctk.CTkLabel(
            title,
            text="NTE AUTO-FISH",
            font=("JetBrains Mono", 9),
            text_color=TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w")

    def _build_logo(self, parent):
        from nte_auto_fish.utils.resource import resource_path
        logo_path = resource_path("assets/chiz_logo_header_transparent.png")
        try:
            image = Image.open(logo_path).convert("RGBA")
            self._logo = ctk.CTkImage(image, size=(76, 76))
            ctk.CTkLabel(parent, text="", image=self._logo, fg_color="transparent").place(
                relx=0.5, rely=0.5, anchor="center"
            )
        except Exception:
            mark = tk.Canvas(parent, width=76, height=76, bg=BG_TAB, highlightthickness=0)
            mark.place(relx=0.5, rely=0.5, anchor="center")
            mark.create_oval(7, 7, 69, 69, outline=PINK_MID, width=1)
            mark.create_polygon(
                38,
                18,
                43,
                33,
                58,
                38,
                43,
                43,
                38,
                58,
                33,
                43,
                18,
                38,
                33,
                33,
                fill=PINK_HI,
                outline="",
            )
    def _animate_dot(self):
        self._pulse = not self._pulse
        colors = {"idle": PINK_MID, "running": GREEN_ACC, "error": RED_ACC, "stopped": TEXT_MUTED}
        color = colors.get(self._logo_status, PINK_MID)
        pulse_fill = color if self._pulse else BG_CARD
        self._dot.itemconfig(self._dot_id, fill=pulse_fill)
        self._dot.after(900, self._animate_dot)

    def set_status(self, label, status="idle"):
        self._logo_status = status
        color = {"idle": PINK_MID, "running": GREEN_ACC, "error": RED_ACC, "stopped": TEXT_MUTED}.get(
            status, PINK_MID
        )
        self._status_label.configure(text=label.upper(), text_color=color)


class TabBar(ctk.CTkFrame):
    def __init__(self, master, on_tab):
        super().__init__(master, fg_color=BG_TAB, height=46, corner_radius=0)
        self.pack_propagate(False)
        self._buttons = {}
        for name in ("Monitor", "Settings"):
            btn = ctk.CTkButton(
                self,
                text=name.upper(),
                width=76,
                height=26,
                corner_radius=20,
                fg_color="transparent",
                hover_color="#131820",
                border_width=1,
                border_color=BG_TAB,
                text_color=TEXT_MUTED,
                font=FONT_MONO,
                command=lambda n=name: on_tab(n),
            )
            btn.pack(side="left", padx=(14 if name == "Monitor" else 0, 4), pady=10)
            self._buttons[name] = btn
        self.set_active("Monitor")

    def set_active(self, name):
        for tab, btn in self._buttons.items():
            if tab == name:
                btn.configure(fg_color="#1e1420", border_color=PINK_DIM, text_color=PINK_HI)
            else:
                btn.configure(fg_color="transparent", border_color=BG_TAB, text_color=TEXT_MUTED)


class Section(ctk.CTkFrame):
    def __init__(self, master, text):
        super().__init__(master, fg_color="transparent")
        self.columnconfigure(2, weight=1)
        ctk.CTkLabel(self, text="//", font=("JetBrains Mono", 11), text_color=PINK_MID).grid(
            row=0, column=0, sticky="w"
        )
        ctk.CTkLabel(self, text=text.upper(), font=("JetBrains Mono", 9), text_color=TEXT_MUTED).grid(
            row=0, column=1, padx=(6, 6), sticky="w"
        )
        ctk.CTkFrame(self, height=1, fg_color=BORDER_DARK).grid(row=0, column=2, sticky="ew")


class ValueCard(ctk.CTkFrame):
    def __init__(self, master, label, value="000", accent=PINK_HI):
        super().__init__(master, fg_color=BG_CARD, corner_radius=6, border_width=1, border_color=BORDER_DARK)
        ctk.CTkLabel(self, text=label.upper(), font=("JetBrains Mono", 9), text_color=TEXT_DIM).pack(
            anchor="w", padx=10, pady=(8, 2)
        )
        self._val = ctk.CTkLabel(self, text=value, font=("JetBrains Mono", 14, "bold"), text_color=accent)
        self._val.pack(anchor="w", padx=10, pady=(0, 8))

    def set(self, text, color=None):
        self._val.configure(text=text)
        if color:
            self._val.configure(text_color=color)

    def set_state(self, text, color=PINK_HI):
        self.set(f"• {text}", color)


class Gauge(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self._value = 0.0
        self._last_drawn = None
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(top, text="GOAL PROGRESS", font=("JetBrains Mono", 9), text_color=TEXT_DIM).pack(
            side="left"
        )
        self._label = ctk.CTkLabel(top, text="000%", font=("JetBrains Mono", 9), text_color=PINK_HI)
        self._label.pack(side="right")
        self._canvas = ctk.CTkCanvas(self, height=18, bg=BG_ROOT, highlightthickness=0)
        self._canvas.pack(fill="x")
        self._canvas.bind("<Configure>", lambda _event: self._draw_gauge())

    def set(self, value):
        next_value = max(0.0, min(1.0, float(value)))
        if abs(next_value - self._value) < 0.002:
            return
        self._value = next_value
        self._draw_gauge()

    def _draw_gauge(self):
        w = max(self._canvas.winfo_width(), 1)
        pct = int(self._value * 100)
        draw_key = (w, pct)
        if self._last_drawn == draw_key:
            return

        self._last_drawn = draw_key
        self._canvas.delete("all")
        segments = 18
        gap = 3
        usable_w = max(segments, w - gap * (segments - 1))
        seg_w = usable_w / segments
        filled = self._value * segments

        for idx in range(segments):
            x1 = int(idx * (seg_w + gap))
            x2 = int(x1 + seg_w)
            active = idx + 1 <= filled
            partial = idx < filled < idx + 1
            color = PINK_DIM if active else BG_CARD
            outline = PINK_DIM if active else BORDER_DARK
            self._canvas.create_rectangle(x1, 5, x2, 13, fill=color, outline=outline)
            if partial:
                partial_w = int(seg_w * (filled - idx))
                self._canvas.create_rectangle(x1, 5, x1 + partial_w, 13, fill=PINK_DIM, outline=PINK_DIM)

        marker_x = min(w - 2, max(1, int(w * self._value)))
        self._canvas.create_rectangle(marker_x - 1, 2, marker_x + 1, 16, fill=PINK_HI, outline=PINK_HI)
        self._label.configure(text=f"{pct:03d}%")


class StatusFeed(ctk.CTkFrame):
    def __init__(self, master, height=170):
        super().__init__(master, fg_color=BG_LOG, corner_radius=7, border_width=1, border_color=BORDER_DARK)
        self.configure(height=height)
        self.pack_propagate(False)
        self._labels = []
        self._history = []
        for idx in range(5):
            row = ctk.CTkFrame(self, fg_color="transparent", height=26)
            row.pack(fill="x", padx=10, pady=(8 if idx == 0 else 0, 0))
            ts = ctk.CTkLabel(row, text="", font=FONT_MONO, text_color=TEXT_DIM, width=48)
            ts.pack(side="left")
            arrow = ctk.CTkLabel(row, text="›", font=FONT_MONO_BOLD, text_color=TEXT_DIM, width=14)
            arrow.pack(side="left")
            msg = ctk.CTkLabel(row, text="", font=("JetBrains Mono", 10), text_color=TEXT_MUTED, anchor="w")
            msg.pack(side="left", fill="x", expand=True)
            self._labels.append((ts, arrow, msg))

    def append(self, msg, important=False):
        text = friendly_log_message(msg)
        now = time.time()
        
        # Debounce identical messages within 2 seconds
        if not hasattr(self, "_last_msg_times"):
            self._last_msg_times = {}
        if text in self._last_msg_times and now - self._last_msg_times[text] < 2.0:
            return
        self._last_msg_times[text] = now
            
        tone = log_tone(text, important)
        self._history.append((datetime.now().strftime("%H:%M"), text, tone))
        self._history = self._history[-5:]
        palette = {
            "golden": (AMBER_ACC, AMBER_ACC, ("JetBrains Mono", 10, "bold")),
            "important": (PINK_MID, "#f0d0e4", ("JetBrains Mono", 10, "bold")),
            "success": (GREEN_ACC, GREEN_ACC, ("JetBrains Mono", 10, "bold")),
            "danger": (RED_ACC, RED_ACC, ("JetBrains Mono", 10, "bold")),
            "normal": (TEXT_DIM, TEXT_MUTED, ("JetBrains Mono", 10)),
        }
        for idx, widgets in enumerate(self._labels):
            ts_label, arrow_label, msg_label = widgets
            if idx >= len(self._history):
                ts_label.configure(text="")
                arrow_label.configure(text="")
                msg_label.configure(text="")
                continue
            stamp, line, line_tone = self._history[idx]
            arrow_color, msg_color, font = palette[line_tone]
            ts_label.configure(text=stamp)
            arrow_label.configure(text="›", text_color=arrow_color)
            msg_label.configure(text=line, text_color=msg_color, font=font)

    def clear(self):
        self._history = []
        for ts_label, arrow_label, msg_label in self._labels:
            ts_label.configure(text="")
            arrow_label.configure(text="")
            msg_label.configure(text="")


def friendly_log_message(message):
    lower = message.lower()
    if "window" in lower and ("hook" in lower or "found" in lower):
        return "Game found."
    if "window not found" in lower or "game window not found" in lower:
        return "Game missing."
    if "settings" in lower and ("load" in lower or "config" in lower):
        return "Settings loaded."
    if "default config" in lower:
        return "Default config loaded."
    if "casting line" in lower:
        return "Casting."
    if "waiting... banner" in lower:
        return "Waiting for bite."
    if "banner bite" in lower:
        return "Banner bite detected."
    if "bar jump" in lower:
        return "Bar bite detected."
    if "button hook" in lower:
        return "Hook prompt detected."
    if "target lost" in lower or "result detected" in lower:
        return "Result detected."
    if "tested hook key" in lower:
        return message
    if "tested close key" in lower:
        return message
    if "start blocked" in lower or "calibrate missing" in lower:
        return "Setup needs attention."
    if "release" in lower or "stopped" in lower:
        return "Controls are safe."
    if "calibrated" in lower:
        return "ROI saved."
    if "calibration" in lower or "calibrating" in lower:
        return "Choose an area."
    if "started" in lower or "running" in lower:
        return "Bot started."
    if "fish caught" in lower:
        return message.replace("Fish caught -", "Fish caught:")
    if "golden fish" in lower:
        return "★ Golden fish caught!"
    if "limit reached" in lower:
        return "🏁 Goal reached! Auto-paused."
    if "out of bait" in lower:
        return "⚠️ Out of bait! Engine auto-paused."
    if "ready" in lower or "initialized" in lower:
        return "Ready to start."
    if "error" in lower:
        return "Something needs attention."
    return message


def log_tone(message, important=False):
    lower = message.lower()
    if "limit reached" in lower:
        return "success"
    if "out of bait" in lower or "attention" in lower:
        return "danger"
    if "golden" in lower:
        return "golden"
    if "found" in lower or "safe" in lower or "saved" in lower or "caught" in lower:
        return "success"
    if important or "ready" in lower or "started" in lower:
        return "important"
    return "normal"


class BotButton(ctk.CTkButton):
    def __init__(self, master, text, accent, command=None):
        super().__init__(
            master,
            text=text.upper(),
            height=34,
            corner_radius=6,
            fg_color=BG_CARD,
            hover_color="#1e1420",
            border_width=1,
            border_color=accent,
            text_color=accent,
            font=FONT_MONO_BOLD,
            command=command,
        )


class SettingValueRow(ctk.CTkFrame):
    def __init__(self, master, label, value="", accent=PINK_HI, hint=""):
        super().__init__(master, fg_color="transparent", height=34)
        self.pack_propagate(False)
        self._label = ctk.CTkLabel(self, text=label, font=FONT_MONO_BOLD, text_color="#5a7080", anchor="w")
        self._label.pack(side="left")
        self._entry = ctk.CTkEntry(
            self,
            width=86,
            height=26,
            corner_radius=6,
            fg_color=BG_LOG,
            border_width=1,
            border_color=BORDER_DARK,
            text_color=accent,
            font=FONT_MONO_BOLD,
        )
        self._entry.pack(side="right")
        self.set(value)

    def get(self):
        return self._entry.get()

    def set(self, value):
        self._entry.delete(0, "end")
        self._entry.insert(0, str(value))


class SettingsToggle(ctk.CTkFrame):
    def __init__(self, master, label, default=False):
        super().__init__(master, fg_color="transparent", height=30)
        self.pack_propagate(False)
        self._var = ctk.BooleanVar(value=default)
        ctk.CTkLabel(self, text=label, font=FONT_MONO_BOLD, text_color="#5a7080").pack(side="left")
        self._switch = ctk.CTkSwitch(
            self,
            text="",
            variable=self._var,
            onvalue=True,
            offvalue=False,
            fg_color=BORDER,
            progress_color=PINK_MID,
            button_color=PINK_HI,
            button_hover_color=PINK_DIM,
            width=40,
            height=20,
        )
        self._switch.pack(side="right")

    def get(self):
        return self._var.get()

    def set(self, value):
        self._var.set(bool(value))


class SettingsCard(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BG_CARD, corner_radius=7, border_width=1, border_color=BORDER_DARK)


class ChecklistRow(ctk.CTkFrame):
    def __init__(self, master, label):
        super().__init__(master, fg_color="transparent", height=24)
        self.pack_propagate(False)
        self._label = ctk.CTkLabel(self, text=label, font=FONT_MONO_BOLD, text_color="#5a7080")
        self._label.pack(side="left")
        self._value = ctk.CTkLabel(self, text="MISSING", font=FONT_MONO_BOLD, text_color=RED_ACC)
        self._value.pack(side="right")

    def set_status(self, text, ok=False, warn=False):
        color = GREEN_ACC if ok else (AMBER_ACC if warn else RED_ACC)
        self._value.configure(text=text.upper(), text_color=color)


class NTEFishingBotGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("Chiz Fishing Tool")
        self.geometry("420x620")
        self.resizable(False, False)
        self.configure(fg_color=BG_ROOT)
        self.attributes("-topmost", True)

        self._running = False
        self._start_time = None
        self._catch_count = 0
        self._miss_count = 0
        self._best_streak = 0
        self._current_streak = 0
        self._tabs = {}
        self._active_tab = None

        self._build_ui()

    def _build_ui(self):
        self._shell_border = ctk.CTkFrame(
            self,
            width=404,
            height=584,
            fg_color=BORDER,
            corner_radius=0,
        )
        self._shell_border.place(x=8, y=18)
        self._shell = Shell(self)
        self._shell.place(x=10, y=20)

        self._header = Header(self._shell, self._on_start, self._on_stop)
        self._header.pack(fill="x")
        self._btn_start = self._header.btn_start
        self._btn_stop = self._header.btn_stop

        ctk.CTkFrame(self._shell, height=1, fg_color=BORDER_DARK).pack(fill="x")
        self._tabbar = TabBar(self._shell, self._show_tab)
        self._tabbar.pack(fill="x")
        ctk.CTkFrame(self._shell, height=2, fg_color=PINK_MID).pack(fill="x")

        content = ctk.CTkFrame(self._shell, fg_color=BG_ROOT)
        content.pack(fill="both", expand=True)
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)
        self._build_monitor_tab(self._add_tab(content, "Monitor"))
        self._build_settings_tab(self._add_tab(content, "Settings"))
        self._show_tab("Monitor")

        self._build_footer(self._shell)
        self._shell.after(100, self._shell._place_brackets)
        self._shell.after(500, self._shell._place_brackets)
        self._shell.after(1000, self._shell._place_brackets)
        self._shell.lift()
        self._shell_border.lower()
        self._add_edge_brackets()

    def _add_edge_brackets(self):
        shell_x = 10
        shell_y = 20
        shell_w = 400
        shell_h = 580
        s = 22
        t = 2
        placements = [
            (shell_x, shell_y, s, t),
            (shell_x, shell_y, t, s),
            (shell_x + shell_w - s, shell_y + shell_h - t, s, t),
            (shell_x + shell_w - t, shell_y + shell_h - s, t, s),
        ]
        self._edge_brackets = []
        for x, y, width, height in placements:
            line = ctk.CTkFrame(self, width=width, height=height, fg_color=PINK_MID, corner_radius=0)
            line.place(x=x, y=y)
            line.lift()
            self._edge_brackets.append(line)
        self.after(250, self._lift_edge_brackets)
        self.after(1000, self._lift_edge_brackets)

    def _lift_edge_brackets(self):
        for line in getattr(self, "_edge_brackets", []):
            line.lift()

    def _add_tab(self, parent, name):
        frame = ctk.CTkFrame(parent, fg_color=BG_ROOT)
        frame.grid(row=0, column=0, sticky="nsew", padx=14, pady=12)
        self._tabs[name] = frame
        return frame

    def _show_tab(self, name):
        if self._active_tab == name:
            return
        self._tabs[name].tkraise()
        self._active_tab = name
        self._tabbar.set_active(name)
        if name == "Settings":
            self.after_idle(self._refresh_settings_tab)
            self.after(80, self._refresh_settings_tab)

    def _refresh_settings_tab(self):
        scroll = getattr(self, "_settings_scroll", None)
        if not scroll or not scroll.winfo_exists():
            return
        self.update_idletasks()
        scroll.update_idletasks()
        parent_canvas = getattr(scroll, "_parent_canvas", None)
        if parent_canvas:
            parent_canvas.update_idletasks()
            parent_canvas.configure(scrollregion=parent_canvas.bbox("all"))
            parent_canvas.yview_moveto(parent_canvas.yview()[0])

    def _build_monitor_tab(self, parent):
        Section(parent, "Live Status").pack(fill="x", pady=(0, 8))
        stat_row = ctk.CTkFrame(parent, fg_color="transparent")
        stat_row.pack(fill="x", pady=(0, 10))
        stat_row.columnconfigure((0, 1, 2), weight=1, uniform="stats")

        self._state_card = ValueCard(stat_row, "Engine", "• IDLE", PINK_HI)
        self._state_card.grid(row=0, column=0, sticky="nsew", padx=(0, 3))
        self._catch_card = ValueCard(stat_row, "Caught", "000", GREEN_ACC)
        self._catch_card.grid(row=0, column=1, sticky="nsew", padx=3)
        self._timer_card = ValueCard(stat_row, "Session", "00:00", AMBER_ACC)
        self._timer_card.grid(row=0, column=2, sticky="nsew", padx=(3, 0))

        self._gauge = Gauge(parent)
        self._gauge.pack(fill="x", pady=(0, 10))

        Section(parent, "Quick Feedback").pack(fill="x", pady=(0, 8))
        self._mon_log = StatusFeed(parent, height=170)
        self._mon_log.pack(fill="x")

    def _build_settings_tab(self, parent):
        scroll = ctk.CTkScrollableFrame(
            parent,
            fg_color="transparent",
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=PINK_DIM,
            height=300,
        )
        self._settings_scroll = scroll
        scroll.pack(fill="both", expand=True, pady=(0, 8))

        Section(scroll, "Basic setup").pack(fill="x", pady=(0, 6))
        basic = SettingsCard(scroll)
        basic.pack(fill="x", pady=(0, 8))
        basic.columnconfigure((0, 1), weight=1)

        self._set_scan_interval = SettingValueRow(basic, "Check speed", "50")
        self._set_scan_interval.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 8))
        self._set_confidence = SettingValueRow(basic, "Sensitivity", "2500")
        self._set_confidence.grid(row=0, column=1, sticky="ew", padx=10, pady=(8, 8))
        self._set_recast_delay = SettingValueRow(basic, "Wait", "2.0")
        self._set_recast_delay.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
        
        Section(scroll, "Auto-Stop Goals").pack(fill="x", pady=(0, 6))
        goals = SettingsCard(scroll)
        goals.pack(fill="x", pady=(0, 8))
        
        self._goal_type = ctk.CTkSegmentedButton(
            goals, 
            values=["Time Limit", "Fish Limit"],
            fg_color=BG_LOG,
            selected_color=PINK_MID,
            selected_hover_color=PINK_HI,
            unselected_color=BG_LOG,
            text_color=TEXT_DIM,
            font=FONT_MONO_BOLD,
        )
        self._goal_type.pack(fill="x", padx=10, pady=(8, 4))
        
        self._set_goal_value = SettingValueRow(goals, "Minutes", "120")
        self._set_goal_value.pack(fill="x", padx=10, pady=(4, 8))
        
        def _on_goal_change(value):
            self._set_goal_value._label.configure(text="Minutes" if value == "Time Limit" else "Target")
            
        self._goal_type.configure(command=_on_goal_change)

        ctk.CTkLabel(
            scroll,
            text="Setting the limit to 0 completely disables auto-stop.",
            font=("JetBrains Mono", 8),
            text_color=TEXT_DIM,
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        Section(scroll, "Keys").pack(fill="x", pady=(0, 6))
        keys = SettingsCard(scroll)
        keys.pack(fill="x", pady=(0, 8))
        self._set_hook_key = SettingValueRow(keys, "Catch key", "f")
        self._set_hook_key.pack(fill="x", padx=10, pady=(8, 2))
        self._set_close_key = SettingValueRow(keys, "Close popup", "escape")
        self._set_close_key.pack(fill="x", padx=10, pady=(2, 8))

        Section(scroll, "Window").pack(fill="x", pady=(0, 6))
        window = SettingsCard(scroll)
        window.pack(fill="x", pady=(0, 8))
        self._set_topmost = SettingsToggle(window, "Always on top", default=True)
        self._set_topmost.pack(fill="x", padx=10, pady=(8, 8))
        self._set_scanlines = SettingsToggle(window, "FX", default=False)

        Section(scroll, "Screen areas").pack(fill="x", pady=(0, 6))
        setup = SettingsCard(scroll)
        setup.pack(fill="x", pady=(0, 8))
        self._setup_config = ChecklistRow(setup, "Config")
        self._setup_config.pack(fill="x", padx=10, pady=(8, 1))
        self._setup_game = ChecklistRow(setup, "Game")
        self._setup_game.pack(fill="x", padx=10, pady=1)
        self._setup_bar = ChecklistRow(setup, "Bar")
        self._setup_bar.pack(fill="x", padx=10, pady=1)
        self._setup_banner = ChecklistRow(setup, "Notice")
        self._setup_banner.pack(fill="x", padx=10, pady=1)
        self._setup_button = ChecklistRow(setup, "Button")
        self._setup_button.pack(fill="x", padx=10, pady=(1, 8))

        cal_row = ctk.CTkFrame(scroll, fg_color="transparent")
        cal_row.pack(fill="x", pady=(0, 4))
        cal_row.columnconfigure((0, 1, 2), weight=1)
        self._btn_cal_bar = BotButton(cal_row, "Bar area", "#8a9ab5", command=self._on_calibrate_bar)
        self._btn_cal_bar.grid(row=0, column=0, sticky="ew", padx=(0, 3))
        self._btn_cal_banner = BotButton(
            cal_row, "Notice area", "#8a9ab5", command=self._on_calibrate_banner
        )
        self._btn_cal_banner.grid(row=0, column=1, sticky="ew", padx=3)
        self._btn_cal_button = BotButton(cal_row, "Button", "#8a9ab5", command=self._on_calibrate_button)
        self._btn_cal_button.grid(row=0, column=2, sticky="ew", padx=(3, 0))

        manual_row = ctk.CTkFrame(scroll, fg_color="transparent")
        manual_row.pack(fill="x", pady=(0, 8))
        manual_row.columnconfigure((0, 1), weight=1)
        self._btn_preview_roi = BotButton(manual_row, "Preview areas", PINK_MID, command=self._on_preview_rois)
        self._btn_preview_roi.grid(row=0, column=0, sticky="ew", padx=(0, 3), pady=(0, 4))
        self._btn_find_game = BotButton(manual_row, "Find game", PINK_MID, command=self._on_find_game)
        self._btn_find_game.grid(row=0, column=1, sticky="ew", padx=(3, 0), pady=(0, 4))
        self._btn_test_hook = BotButton(manual_row, "Test hook", "#8a9ab5", command=self._on_test_hook)
        self._btn_test_hook.grid(row=1, column=0, sticky="ew", padx=(0, 3), pady=(0, 4))
        self._btn_test_close = BotButton(manual_row, "Test close", "#8a9ab5", command=self._on_test_close)
        self._btn_test_close.grid(row=1, column=1, sticky="ew", padx=(3, 0), pady=(0, 4))
        self._btn_release = BotButton(manual_row, "Release", RED_ACC, command=self._on_release_controls)
        self._btn_release.grid(row=2, column=0, columnspan=2, sticky="ew")

        self._btn_save_settings = BotButton(parent, "Save Settings", PINK_MID, command=self._on_save_settings)
        self._btn_save_settings.pack(fill="x")

    def _build_footer(self, parent):
        footer = ctk.CTkFrame(parent, fg_color=BG_TAB, height=34, corner_radius=0)
        footer.pack(fill="x", side="bottom")
        ctk.CTkFrame(footer, height=1, fg_color=BORDER_DARK).pack(fill="x")
        row = ctk.CTkFrame(footer, fg_color="transparent")
        row.pack(fill="both", expand=True, padx=14)
        self._footer_status = ctk.CTkLabel(
            row, text="● Standby · ROI not set", font=FONT_MONO, text_color=TEXT_MUTED
        )
        self._footer_status.pack(side="left")
        ctk.CTkLabel(row, text="1.0 · pro", font=FONT_MONO, text_color=TEXT_DIM).pack(side="right")
        self._roi_badge = self._footer_status

    def set_roi_status(self, active: bool):
        if active:
            self._footer_status.configure(text="● Standby · ROI locked", text_color=TEXT_MUTED)
        else:
            self._footer_status.configure(text="● Standby · ROI not set", text_color=TEXT_MUTED)

    def set_setup_status(self, config_saved=False, game_found=False, rois=None):
        rois = rois or {}
        if not hasattr(self, "_setup_config"):
            return
        self._setup_config.set_status("saved" if config_saved else "default", ok=config_saved, warn=not config_saved)
        self._setup_game.set_status("found" if game_found else "missing", ok=game_found)
        self._setup_bar.set_status("set" if rois.get("bar") else "missing", ok=bool(rois.get("bar")))
        self._setup_banner.set_status("set" if rois.get("banner") else "missing", ok=bool(rois.get("banner")))
        self._setup_button.set_status("set" if rois.get("button_calibrated") else "default", ok=False, warn=bool(rois.get("button")))

    def _load_settings_to_ui(self, config):
        settings = config.settings
        self._set_scan_interval.set(int(settings.get("poll_interval", 0.05) * 1000))
        self._set_confidence.set(settings.get("banner_threshold", 2500))
        self._set_recast_delay.set(settings.get("recast_delay", 2.0))
        
        goal_mode = settings.get("goal_mode", "Time Limit")
        self._goal_type.set(goal_mode)
        self._set_goal_value._label.configure(text="Minutes" if goal_mode == "Time Limit" else "Target")
        if goal_mode == "Time Limit":
            self._set_goal_value.set(settings.get("session_cap_min", 120))
        else:
            self._set_goal_value.set(settings.get("session_cap_fish", 50))
            
        self._set_hook_key.set(settings.get("hook_key", "f"))
        self._set_close_key.set(settings.get("close_key", "escape"))
        self._set_topmost.set(True)
        self._log("Settings loaded.", important=False)

    def _save_settings_from_ui(self, config):
        try:
            config.settings["poll_interval"] = int(self._set_scan_interval.get()) / 1000.0
            config.settings["banner_threshold"] = int(self._set_confidence.get())
            config.settings["recast_delay"] = float(self._set_recast_delay.get())
            
            goal_mode = self._goal_type.get()
            config.settings["goal_mode"] = goal_mode
            val = int(self._set_goal_value.get())
            if goal_mode == "Time Limit":
                config.settings["session_cap_min"] = val
                config.settings["session_cap_fish"] = 0
            else:
                config.settings["session_cap_min"] = 0
                config.settings["session_cap_fish"] = val
                
            config.settings["hook_key"] = self._set_hook_key.get().strip() or "f"
            config.settings["close_key"] = self._set_close_key.get().strip() or "escape"
            config.save()
            self.attributes("-topmost", self._set_topmost.get())
            self._log("Settings saved.", important=True)
            return True
        except ValueError:
            self._log("Check your settings.", important=True)
            return False

    def _on_save_settings(self):
        self._log("Settings are display-only.", important=True)

    def _log(self, message: str, important: bool = False):
        if hasattr(self, "_mon_log"):
            self._mon_log.append(message, important)
        else:
            print(f"[LOG] {message}")

    def _set_state(self, state: str, color=PINK_HI):
        self._state_card.set_state(state, color)

    def _update_footer(self, text: str):
        friendly = text.replace("*", "●").replace("-", "·")
        self._footer_status.configure(text=friendly)

    def _tick(self, session_id):
        if not self._running or self._start_time is None or getattr(self, "_session_id", 0) != session_id:
            return
        elapsed = int(time.time() - self._start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60
        self._timer_card.set(f"{minutes:02d}:{seconds:02d}", AMBER_ACC)
        max_mins = 120
        max_fish = 0
        try:
            # We don't read from self._set_session_cap anymore because we rebuilt the UI
            goal_mode = self._goal_type.get()
            val = int(self._set_goal_value.get())
            if goal_mode == "Time Limit":
                max_mins = val
            else:
                max_fish = val
        except (TypeError, ValueError):
            pass
            
        time_progress = 0.0
        if max_mins > 0:
            time_progress = elapsed / (max_mins * 60)
            
        fish_progress = 0.0
        if max_fish > 0:
            fish_progress = self._catch_count / max(max_fish, 1)
            
        total_progress = max(time_progress, fish_progress)
        self._gauge.set(min(total_progress, 1.0))
        
        self.after(1000, lambda: self._tick(session_id))

    def _on_start(self):
        if self._running:
            return
        self._running = True
        self._start_time = time.time()
        self._catch_count = 0
        self._miss_count = 0
        self._current_streak = 0
        self._best_streak = 0
        self._catch_card.set("000", GREEN_ACC)
        self._set_state("ACTIVE", GREEN_ACC)
        self._header.set_status("RUNNING", "running")
        self._btn_start.start_pulse()
        self._btn_stop.stop_pulse()
        self._update_footer("● Running · ROI locked")
        self._log("Bot started.", important=True)
        self._session_id = getattr(self, "_session_id", 0) + 1
        self._tick(self._session_id)

    def _on_stop(self):
        if not self._running:
            return
        self._running = False
        
        # User Feedback: Wipe GUI counters directly on Stop
        self._catch_count = 0
        self._catch_card.set("000", GREEN_ACC)
        self._timer_card.set("00:00", AMBER_ACC)
        self._gauge.set(0.0)
        self._start_time = None
        
        self._set_state("STOPPED", RED_ACC)
        self._header.set_status("STOPPED", "stopped")
        self._btn_start.stop_pulse()
        self._btn_stop.start_pulse()
        self._update_footer("● Stopped · Controls are safe")
        self._log("Controls are safe.", important=True)

    def _on_calibrate_bar(self):
        self._log("Choose an area.", important=True)
        self._update_footer("● Calibrating · Bar ROI")

    def _on_calibrate_banner(self):
        self._log("Choose an area.", important=True)
        self._update_footer("● Calibrating · Banner ROI")

    def _on_calibrate_button(self):
        self._log("Choose an area.", important=True)
        self._update_footer("● Calibrating · Button ROI")

    def _on_preview_rois(self):
        self._log("Preview unavailable.", important=True)

    def _on_find_game(self):
        self._log("Game search unavailable.", important=True)

    def _on_test_hook(self):
        self._log("Hook test unavailable.", important=True)

    def _on_test_close(self):
        self._log("Close test unavailable.", important=True)

    def _on_release_controls(self):
        self._log("Release unavailable.", important=True)

    def _on_reset_counter(self):
        self._catch_count = 0
        self._miss_count = 0
        self._current_streak = 0
        self._best_streak = 0
        self._catch_card.set("000", GREEN_ACC)
        self._log("Counters reset.", important=False)

    def _on_manual_increment(self):
        self.increment_catch()

    def log(self, message: str, important: bool = False):
        self.after(0, lambda: self._log(message, important))

    def set_state(self, state: str):
        colors = {
            "IDLE": PINK_HI,
            "CASTING": PINK_HI,
            "HOOKING": AMBER_ACC,
            "STRUGGLING": AMBER_ACC,
            "WAITING": TEXT_MUTED,
            "RESULT": GREEN_ACC,
            "STOPPED": RED_ACC,
            "ERROR": RED_ACC,
        }
        state_upper = state.upper()
        color = colors.get(state_upper, PINK_HI)
        status = "running"
        if state_upper in ("IDLE"): status = "idle"
        elif state_upper in ("STOPPED"): status = "stopped"
        elif state_upper in ("ERROR"): status = "error"
        
        friendly_word = state_upper
        if state_upper == "STRUGGLING":
            friendly_word = "REELING"
            
        self.after(0, lambda: self._set_state(friendly_word, color))
        self.after(0, lambda: self._header.set_status(friendly_word, status))

    def increment_catch(self):
        self._catch_count += 1
        self._current_streak += 1
        self._best_streak = max(self._best_streak, self._current_streak)
        self.after(0, lambda: self._catch_card.set(f"{self._catch_count:03d}", GREEN_ACC))
        self.after(0, lambda: self._log(f"Fish caught: {self._catch_count:03d}", important=True))

    def increment_miss(self):
        self._miss_count += 1
        self._current_streak = 0
        self.after(0, lambda: self._log("Fish missed.", important=False))
