#!/usr/bin/env python3
import json
import subprocess
import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path
from datetime import datetime
import webbrowser
import os
import math

# =========================
# Windows: Console verstecken
# =========================
if os.name == "nt":
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0
        )
    except Exception:
        pass

# =========================
# Layout / Design
# =========================
WINDOW_W = 1280
WINDOW_H = 720
SIDE_PADDING = 40

HEADER_HEIGHT = 56
HEADER_MARGIN = SIDE_PADDING

CARDS_PER_ROW = 3

CARD_GAP = 20
CARD_W = (WINDOW_W - SIDE_PADDING * 2 - CARD_GAP * (CARDS_PER_ROW - 1)) // CARDS_PER_ROW
CARD_H = 175
URL_BUTTON_GAP = 40

LB_LABEL = "io.x-k8s.cloud-provider-kind.loadbalancer.name"

COLOR_BG = "white"
COLOR_HEADER = "#f5f5f5"
COLOR_CARD = "#f3f3f3"
COLOR_BTN = "#e6e6e6"
COLOR_BTN_HOVER = "#dcdcdc"

# =========================
# Backend
# =========================
def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr)
    return r.stdout

def run_json(cmd):
    return json.loads(run(cmd))

def get_loadbalancer_services():
    data = run_json(["kubectl", "get", "svc", "-A", "-o", "json"])
    return [
        s for s in data["items"]
        if s.get("spec", {}).get("type") == "LoadBalancer"
        and s.get("status", {}).get("loadBalancer", {}).get("ingress")
    ]

def docker_ps():
    out = run(["docker", "ps", "--format", "{{json .}}"])
    return [json.loads(l) for l in out.splitlines() if l.strip()]

def docker_inspect(ids):
    return run_json(["docker", "inspect"] + list(ids)) if ids else []

def pick_relevant_port(ports):
    for p in ports:
        if p.startswith("0.0.0.0:") and "->" in p:
            return p
    return ""

def resolve_services():
    services = get_loadbalancer_services()
    ps = docker_ps()
    ps_by_id = {c["ID"]: c for c in ps}
    inspected = docker_inspect(ps_by_id.keys())

    docker_data = []
    for c in inspected:
        ps_entry = next((v for k, v in ps_by_id.items() if c["Id"].startswith(k)), None)
        ports = ps_entry.get("Ports", "").split(",") if ps_entry else []
        docker_data.append({
            "name": c["Name"].lstrip("/"),
            "labels": c["Config"].get("Labels", {}) or {},
            "ports": [p.strip() for p in ports if p.strip()]
        })

    resolved = []
    for svc in services:
        key = f"{svc['metadata']['namespace']}/{svc['metadata']['name']}"
        for c in docker_data:
            label = c["labels"].get(LB_LABEL, "")
            if label.endswith(f"/{key}"):
                port = pick_relevant_port(c["ports"])
                if not port:
                    continue
                host_port = port.split("->")[0].split(":")[-1]
                proto = "https" if "->443/" in port else "http"
                resolved.append({
                    "service": svc["metadata"]["name"],
                    "container": c["name"],
                    "port": port,
                    "url": f"{proto}://localhost:{host_port}"
                })
    return resolved

# =========================
# UI Helper
# =========================
def rounded_rect(canvas, x, y, w, h, r, color):
    return canvas.create_polygon(
        x+r, y, x+w-r, y, x+w, y, x+w, y+r,
        x+w, y+h-r, x+w, y+h, x+w-r, y+h,
        x+r, y+h, x, y+h, x, y+h-r,
        x, y+r, x, y,
        smooth=True,
        fill=color,
        outline=""
    )

# =========================
# GUI
# =========================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("K8s Loadbalancer UIs")
        self.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.configure(bg=COLOR_BG)

        self.services = []
        self.generated = False
        self.scroll_enabled = False

        self._build_header()
        self._build_controls()
        self._build_content()

        self.load_services()

    # ---------- Header ----------
    def _build_header(self):
        self.header = tk.Canvas(
            self,
            height=HEADER_HEIGHT + HEADER_MARGIN * 2,
            bg=COLOR_BG,
            highlightthickness=0
        )
        self.header.pack(fill="x")
        self.header.bind("<Configure>", self._draw_header)

    def _draw_header(self, _=None):
        self.header.delete("all")
        w = self.header.winfo_width()
        if w <= HEADER_MARGIN * 2:
            return
        rounded_rect(
            self.header,
            HEADER_MARGIN,
            HEADER_MARGIN,
            w - HEADER_MARGIN * 2,
            HEADER_HEIGHT,
            HEADER_HEIGHT // 2,
            COLOR_HEADER
        )
        self.header.create_text(
            w // 2,
            HEADER_MARGIN + HEADER_HEIGHT // 2,
            text="K8s Loadbalancer UIs",
            font=("Segoe UI", 16, "bold"),
            fill="#222"
        )

    # ---------- Button ----------
    def _button(self, parent, text, command, *, width=220, height=40, radius=18):
        c = tk.Canvas(
            parent,
            width=width,
            height=height,
            bg=COLOR_CARD,
            highlightthickness=0
        )
        bg_id = rounded_rect(c, 0, 0, width, height, radius, COLOR_BTN)
        c.create_text(width // 2, height // 2, text=text, font=("Segoe UI", 10))
        c.bind("<Enter>", lambda e: c.itemconfigure(bg_id, fill=COLOR_BTN_HOVER))
        c.bind("<Leave>", lambda e: c.itemconfigure(bg_id, fill=COLOR_BTN))
        c.bind("<Button-1>", lambda e: command())
        return c

    # ---------- Controls ----------
    def _build_controls(self):
        self.controls = tk.Frame(self, bg=COLOR_BG)
        self.controls.pack(pady=10)

        row1 = tk.Frame(self.controls, bg=COLOR_BG)
        row1.pack()

        self.btn_generate = self._button(row1, "Generieren", self.on_generate)
        self.btn_generate.pack(side="left", padx=8)

        self.btn_export = self._button(row1, "Als .txt exportieren", self.export_txt)
        self.btn_export.pack(side="left", padx=8)
        self.btn_export.pack_forget()

        self.btn_open_all = self._button(self.controls, "Alle UIs öffnen", self.open_all)
        self.btn_open_all.pack(pady=(12, 0))
        self.btn_open_all.pack_forget()

        self.service_count = tk.Label(
            self.controls,
            text="",
            bg=COLOR_BG,
            fg="#333",
            font=("Segoe UI", 12, "bold")
        )
        self.service_count.pack(pady=(4, 0))
        self.service_count.pack_forget()

    # ---------- Content ----------
    def _build_content(self):
        self.canvas = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.content = tk.Frame(self.canvas, bg=COLOR_BG)
        self.content_window = self.canvas.create_window(
            (0, 0), window=self.content, anchor="nw"
        )

        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.content.bind("<Configure>", self._recalc_scroll)

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _on_canvas_resize(self, event):
        self.canvas.itemconfigure(self.content_window, width=event.width)
        self._recalc_scroll()

    def _recalc_scroll(self, _=None):
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox("all")
        if not bbox:
            self.scroll_enabled = False
            return

        content_height = bbox[3] - bbox[1]
        canvas_height = self.canvas.winfo_height()

        self.scroll_enabled = content_height > canvas_height

        if not self.scroll_enabled:
            self.canvas.configure(scrollregion=(0, 0, 0, canvas_height))
            self.canvas.yview_moveto(0)
        else:
            self.canvas.configure(scrollregion=bbox)

    def _on_mousewheel(self, event):
        if not self.scroll_enabled:
            return "break"

        if event.delta < 0 or event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(-1, "units")
        return "break"

    # ---------- Logic ----------
    def load_services(self):
        self.services = resolve_services()
        self.generated = False
        self.btn_export.pack_forget()
        self.btn_open_all.pack_forget()
        self.service_count.pack_forget()
        self.render_list()

    def on_generate(self):
        self.generated = True
        self.btn_export.pack(side="left", padx=8)
        self.btn_open_all.pack(pady=(12, 25))
        self.service_count.config(text=f"Services: {len(self.services)}")
        self.service_count.pack()
        self.render_cards()

    # ---------- Views ----------
    def clear(self):
        for w in self.content.winfo_children():
            w.destroy()

    def render_list(self):
        self.clear()
        for s in self.services:
            row = tk.Canvas(
                self.content,
                width=WINDOW_W - SIDE_PADDING * 2,
                height=52,
                bg=COLOR_BG,
                highlightthickness=0
            )
            rounded_rect(
                row,
                0,
                0,
                WINDOW_W - SIDE_PADDING * 2,
                52,
                16,
                COLOR_CARD
            )
            row.create_text(24, 26, anchor="w",
                            text=s["service"], font=("Segoe UI", 12))
            row.pack(padx=SIDE_PADDING, pady=6)

    def render_cards(self):
        self.clear()
        cards_area = tk.Frame(self.content, bg=COLOR_BG)
        cards_area.pack(anchor="center", pady=12)

        for i, s in enumerate(self.services):
            r, c = divmod(i, CARDS_PER_ROW)

            card = tk.Canvas(
                cards_area,
                width=CARD_W,
                height=CARD_H,
                bg=COLOR_BG,
                highlightthickness=0
            )
            rounded_rect(card, 0, 0, CARD_W, CARD_H, 18, COLOR_CARD)

            y = 20
            card.create_text(20, y, anchor="w",
                             text=s["service"], font=("Segoe UI", 13, "bold"))
            y += 35
            card.create_text(20, y, anchor="w",
                             text=f"Container: {s['container']}", font=("Segoe UI", 9))
            y += 25
            card.create_text(20, y, anchor="w",
                             text=f"Port: {s['port']}", font=("Segoe UI", 9))
            y += 25
            card.create_text(20, y, anchor="w",
                             text=s["url"], font=("Segoe UI", 9), fill="#0057d9")

            y += URL_BUTTON_GAP
            btn = self._button(
                card,
                "Im Browser öffnen",
                lambda url=s["url"]: webbrowser.open_new(url),
                width=160,
                height=30,
                radius=14
            )
            card.create_window(16, y, anchor="w", window=btn)

            card.grid(row=r, column=c, padx=CARD_GAP // 2, pady=10)

        self._recalc_scroll()

    # ---------- Actions ----------
    def open_all(self):
        for s in self.services:
            webbrowser.open_new_tab(s["url"])

    def export_txt(self):
        file = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile="k8s_loadbalancer_uis.txt"
        )
        if not file:
            return

        lines = [
            "Kubernetes LoadBalancer UIs",
            "=" * 40,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ""
        ]
        for s in self.services:
            lines += [
                f"Service: {s['service']}",
                f"  Container: {s['container']}",
                f"  Port: {s['port']}",
                f"  URL: {s['url']}",
                ""
            ]

        Path(file).write_text("\n".join(lines), encoding="utf-8")
        messagebox.showinfo("Exportiert", "Datei gespeichert")


# =========================
# Start
# =========================
if __name__ == "__main__":
    App().mainloop()