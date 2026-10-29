import os
import sys
import json
import ctypes
import threading
import tkinter as tk
from ctypes import wintypes
from playwright.sync_api import sync_playwright

# ---------- ألوان ----------
BG_TOP    = "#0a0416"
BG_MID    = "#1a0b2e"
BG_BOTTOM = "#040a18"
CARD      = "#1e1238"
CARD2     = "#2a1a4f"
BORDER    = "#6a3bd1"
ACCENT    = "#b15cff"
ACCENT2   = "#ff5cd0"
ACCENT3   = "#5cd0ff"
TEXT      = "#f5f0ff"
MUTED     = "#9a90c0"
GREEN     = "#4ade80"
RED       = "#ff5c7a"
YELLOW    = "#ffd45c"

W, H = 640, 600


def resource_path(filename):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, filename)


# ---------- إظهار النافذة في شريط المهام ----------
def show_in_taskbar(root):
    if os.name != "nt":
        return
    try:
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        root.withdraw()
        root.after(10, root.deiconify)
    except Exception as e:
        print(f"[taskbar] {e}")


# ---------- الحقن عبر Playwright ----------
def inject_value(url: str, key: str, value: str) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=False)
        context = browser.new_context()

        key_js = json.dumps(key)
        value_js = json.dumps(value)

        context.add_init_script(f"""
            try {{
                if (localStorage.getItem({key_js}) === null) {{
                    localStorage.setItem({key_js}, {value_js});
                }}
            }} catch (e) {{
                console.error(e);
            }}
        """)

        page = context.new_page()
        page.goto(url, wait_until="load")
        page.wait_for_event("close", timeout=0)
        browser.close()


# ---------- زر متدرّج ----------
def create_gradient_button(master, text, c1, c2, command,
                           width=480, height=48,
                           font=("Segoe UI", 12, "bold")):
    frame = tk.Frame(master, width=width, height=height, bg=CARD, bd=0)
    frame.pack_propagate(False)
    canvas = tk.Canvas(frame, width=width, height=height,
                       bg=CARD, highlightthickness=0, bd=0,
                       cursor="hand2")
    canvas.pack(fill="both", expand=True)
    state = {"text": text, "c1": c1, "c2": c2, "command": command,
             "hover": False, "pressed": False, "font": font,
             "w": width, "h": height}

    def draw():
        canvas.delete("all")
        cc1, cc2 = state["c1"], state["c2"]
        if state["pressed"]:
            cc1, cc2 = cc2, cc1
        elif state["hover"]:
            cc1 = "#e0b8ff"
            cc2 = "#ffb8e8"
        for i in range(state["w"]):
            t = i / state["w"]
            r1, g1, b1 = (int(cc1[1:3], 16), int(cc1[3:5], 16), int(cc1[5:7], 16))
            r2, g2, b2 = (int(cc2[1:3], 16), int(cc2[3:5], 16), int(cc2[5:7], 16))
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            canvas.create_line(i, 0, i, state["h"],
                               fill=f"#{r:02x}{g:02x}{b:02x}")
        canvas.create_text(state["w"] / 2, state["h"] / 2,
                           text=state["text"], fill="white",
                           font=state["font"])

    def on_enter(e): state["hover"] = True; draw()
    def on_leave(e): state["hover"] = False; state["pressed"] = False; draw()
    def on_press(e): state["pressed"] = True; draw()
    def on_release(e):
        state["pressed"] = False; draw()
        if state["command"]: state["command"]()

    for w in (frame, canvas):
        w.bind("<Enter>", on_enter)
        w.bind("<Leave>", on_leave)
        w.bind("<ButtonPress-1>", on_press)
        w.bind("<ButtonRelease-1>", on_release)

    def set_text(t): state["text"] = t; draw()
    def set_state(st): state["command"] = None if st == "disabled" else command
    frame.set_text = set_text
    frame.set_state = set_state
    draw()
    return frame


# ---------- الواجهة ----------
class LauncherApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("FreeGameX — LocalStorage Injector")
        self.root.geometry(f"{W}x{H}")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_TOP)
        self.root.overrideredirect(True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self._drag_x = 0
        self._drag_y = 0

        self._build_ui()

        self.root.after(200, lambda: show_in_taskbar(self.root))

    def _build_ui(self):
        # خلفية متدرجة
        self.canvas = tk.Canvas(self.root, width=W, height=H,
                                highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        steps = 60
        for y in range(H):
            t = y / H
            r1, g1, b1 = (10, 4, 22)
            r2, g2, b2 = (4, 10, 24)
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            self.canvas.create_line(0, y, W, y, fill=f"#{r:02x}{g:02x}{b:02x}")

        # إطار
        self.canvas.create_rectangle(4, 4, W - 4, H - 4, outline="#000000", width=2)
        self.canvas.create_rectangle(8, 8, W - 8, H - 8, outline=BORDER, width=2)

        self._build_titlebar()

        # البطاقة
        self.canvas.create_rectangle(36, 92, W - 36, H - 56,
                                     fill=CARD, outline=CARD2, width=2)

        self.canvas.create_text(W // 2, 130, text="❖  LOCALSTORAGE  ❖",
                                fill=ACCENT2, font=("Segoe UI", 20, "bold"))
        self.canvas.create_text(W // 2, 158, text="Key • URL • Value Injector",
                                fill=MUTED, font=("Segoe UI", 10))
        self.canvas.create_line(90, 180, W - 90, 180, fill=ACCENT, width=1)

        # الحقول
        self.key_var = tk.StringVar()
        self.url_var = tk.StringVar()
        self.value_var = tk.StringVar()

        y = 210
        self.canvas.create_text(78, y, text="KEY", fill=ACCENT3,
                                font=("Segoe UI", 10, "bold"), anchor="w")
        self.key_entry = tk.Entry(self.root, textvariable=self.key_var,
                                  bg=BG_MID, fg=TEXT, insertbackground=ACCENT2,
                                  relief="flat", font=("Consolas", 11),
                                  bd=0, highlightthickness=1,
                                  highlightbackground=BORDER,
                                  highlightcolor=ACCENT2)
        self.key_entry.place(x=78, y=y + 20, width=W - 156, height=34)

        y = 290
        self.canvas.create_text(78, y, text="URL", fill=ACCENT3,
                                font=("Segoe UI", 10, "bold"), anchor="w")
        self.url_entry = tk.Entry(self.root, textvariable=self.url_var,
                                  bg=BG_MID, fg=TEXT, insertbackground=ACCENT2,
                                  relief="flat", font=("Consolas", 11),
                                  bd=0, highlightthickness=1,
                                  highlightbackground=BORDER,
                                  highlightcolor=ACCENT2)
        self.url_entry.place(x=78, y=y + 20, width=W - 156, height=34)

        y = 370
        self.canvas.create_text(78, y, text="VALUE", fill=ACCENT3,
                                font=("Segoe UI", 10, "bold"), anchor="w")
        self.value_entry = tk.Entry(self.root, textvariable=self.value_var,
                                    bg=BG_MID, fg=TEXT, insertbackground=ACCENT2,
                                    relief="flat", font=("Consolas", 11), show="•",
                                    bd=0, highlightthickness=1,
                                    highlightbackground=BORDER,
                                    highlightcolor=ACCENT2)
        self.value_entry.place(x=78, y=y + 20, width=W - 156, height=34)

        # زر التشغيل
        self.run_btn = create_gradient_button(
            self.root, "  ➤  INJECT & OPEN  ",
            ACCENT, ACCENT2, self.on_launch,
            width=W - 156, height=48,
        )
        self.run_btn.place(x=78, y=440, width=W - 156, height=48)

        # سطر الحالة
        self.status_var = tk.StringVar(value="Fill all fields and press INJECT.")
        self.status_lbl = tk.Label(
            self.root, textvariable=self.status_var,
            bg=CARD, fg=MUTED, font=("Segoe UI", 10),
        )
        self.status_lbl.place(x=78, y=500, width=W - 156, height=22)

        # اسمك أسفل النافذة
        self.canvas.create_text(
            W // 2, H - 30,
            text="MEHDIYAD13",
            fill=ACCENT2, font=("Segoe UI", 10, "bold"),
        )

        self.key_entry.focus_set()

    def _build_titlebar(self):
        bar = tk.Frame(self.root, bg=CARD2, height=36)
        bar.place(x=10, y=10, width=W - 20, height=36)
        dot = tk.Label(bar, text="●", bg=CARD2, fg=ACCENT2, font=("Segoe UI", 12))
        dot.pack(side="left", padx=(8, 0))
        title = tk.Label(bar, text=" FreeGameX Injector", bg=CARD2, fg=TEXT,
                         font=("Segoe UI", 10, "bold"), anchor="w")
        title.pack(side="left")
        close_btn = tk.Button(bar, text="✕", command=self.on_close,
                              bg=CARD2, fg=RED, activebackground=RED,
                              activeforeground="white", bd=0, relief="flat",
                              font=("Segoe UI", 11, "bold"), cursor="hand2")
        close_btn.pack(side="right", padx=6)
        min_btn = tk.Button(bar, text="—", command=self._minimize,
                            bg=CARD2, fg=MUTED, activebackground=CARD,
                            activeforeground=TEXT, bd=0, relief="flat",
                            font=("Segoe UI", 11, "bold"), cursor="hand2")
        min_btn.pack(side="right", padx=2)
        for w in (bar, title, dot):
            w.bind("<Button-1>", self._start_drag)
            w.bind("<B1-Motion>", self._do_drag)

    def _start_drag(self, e):
        self._drag_x = e.x_root - self.root.winfo_x()
        self._drag_y = e.y_root - self.root.winfo_y()

    def _do_drag(self, e):
        self.root.geometry(f"+{e.x_root - self._drag_x}+{e.y_root - self._drag_y}")

    def _minimize(self):
        # إخفاء النافذة (تبقى الأيقونة في شريط المهام)
        self.root.overrideredirect(False)
        self.root.iconify()
        self._restore_job = self.root.after(200, self._check_restore)

    def _check_restore(self):
        # إذا عادت النافذة من شريط المهام، أعد النمط المخصّص
        if self.root.state() == "normal":
            self.root.overrideredirect(True)
            self.root.after(50, lambda: show_in_taskbar(self.root))
            self.root.after(80, lambda: set_taskbar_icon(
                self.root, resource_path("icon.ico")))
        else:
            self._restore_job = self.root.after(200, self._check_restore)
    def set_status(self, text, color=MUTED):
        self.status_var.set(text)
        self.status_lbl.config(fg=color)

    def on_launch(self):
        key = self.key_var.get().strip()
        url = self.url_var.get().strip()
        value = self.value_var.get().strip()

        if not key or not url or not value:
            self.set_status("✖ Please fill KEY, URL and VALUE.", RED)
            return

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        self.run_btn.set_text("  ◇  OPENING...  ")
        self.set_status("◇ Injecting and opening browser...", YELLOW)

        threading.Thread(target=self._worker, args=(url, key, value),
                         daemon=True).start()

    def _worker(self, url, key, value):
        try:
            inject_value(url, key, value)
            self.root.after(0, lambda: self.set_status(
                "✔ Browser opened with injected value.", GREEN))
            self.root.after(0, lambda: self.run_btn.set_text(
                "  ➤  INJECT & OPEN  "))
        except Exception as e:
            msg = str(e)
            self.root.after(0, lambda: self.set_status(f"✖ Error: {msg}", RED))
            self.root.after(0, lambda: self.run_btn.set_text(
                "  ➤  INJECT & OPEN  "))

    def on_close(self):
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    LauncherApp(root)
    root.mainloop()