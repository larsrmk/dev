#!/usr/bin/env python3
import json
import subprocess
import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path
from datetime import datetime
import webbrowser
import os
import urllib.request
import urllib.error
import socket

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
    # Wichtig unter Windows bei .pyw: CREATE_NO_WINDOW verhindert,
    # dass bei jedem subprocess-Aufruf kurz ein cmd-Fenster aufblitzt.
    startupinfo = None
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    r = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)
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

def is_port_alive(host_port, proto):
    """
    Prüft, ob hinter dem localhost-Port ein erreichbarer Webserver hängt.
    Timeout ist sehr kurz gesetzt (0.5s), da es eh localhost ist.
    """
    url = f"{proto}://localhost:{host_port}"
    try:
        # ctx ignorieren (für https ohne zertifikat)
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(url, method="HEAD") # Nur Header abrufen spart Zeit
        with urllib.request.urlopen(req, timeout=0.5, context=ctx) as response:
            return True
    except urllib.error.HTTPError:
        # Ein HTTP Error (wie 404, 401, 403) bedeutet: Webserver läuft und antwortet!
        return True
    except (urllib.error.URLError, socket.timeout, ConnectionRefusedError):
        # Verbindung fehlgeschlagen oder Timeout = Webserver läuft dort nicht
        return False
    except Exception:
        return False

def pick_relevant_port_string(ports):
    """
    Gibt den GESAMTEN String des Ports zurück (z.B. '0.0.0.0:9090->9090/tcp'),
    der tatsächlich erreichbar ist. Wenn keiner erreichbar ist, nimm den ersten.
    """
    candidates = []
    
    # Alle Host-gebundenen Ports sammeln
    for p in ports:
        if p.startswith("0.0.0.0:") and "->" in p:
            candidates.append(p)
            
    if not candidates:
        return ""
        
    # Versuche jeden Port zu erreichen
    for p in candidates:
        # Extrahiere den Host-Port, z.B. 9090 aus "0.0.0.0:9090->..."
        host_port = p.split("->")[0].split(":")[-1]
        proto = "https" if "->443/" in p else "http"
        
        if is_port_alive(host_port, proto):
            return p
            
    # Fallback: Wenn wirklich gar nichts antwortet, geben wir den ersten gebundenen Port zurück
    return candidates[0]

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
                
                # NUTZT NUN DIE NEUE LOGIK MIT HEALTH CHECK!
                port = pick_relevant_port_string(c["ports"])
                
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

        # Icon oben links im Fenster
        icon_path = Path(__file__).parent / "icons8-python-48.ico"
        if icon_path.exists():
            self.iconbitmap(str(icon_path))

        self.services = []
        self.new_service_names = set()
        self.generated = False
        self.scroll_enabled = False
        self.placeholder_text = "Services gefunden: 0"

        self._build_header()
        self._build_controls()
        self._build_content()

        self.load_services()

        self.bind_all("<Button-1>", self._remove_focus, add="+")

    def _remove_focus(self, event):
        if hasattr(self, "search_entry"):
            if event.widget not in (self.search_entry, self.search_clear_lbl):
                self.focus_set()

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
        c.create_text(width // 2, height // 2, text=text, font=("Segoe UI", 10), tags="btn_text")
        c.bind("<Enter>", lambda e: c.itemconfigure(bg_id, fill=COLOR_BTN_HOVER))
        c.bind("<Leave>", lambda e: c.itemconfigure(bg_id, fill=COLOR_BTN))
        c.bind("<Button-1>", lambda e: command())
        return c

    # ---------- Controls ----------
    def _build_controls(self):
        self.controls = tk.Frame(self, bg=COLOR_BG)
        # pady=25 sorgt für den exakt gleichen Abstand nach oben (zum Header) und unten (zur Liste/zu den Karten)
        self.controls.pack(pady=25)

        row1 = tk.Frame(self.controls, bg=COLOR_BG)
        row1.pack()

        self.btn_generate = self._button(row1, "Generieren", self.handle_main_btn)
        self.btn_generate.pack(side="left", padx=8)

        self.btn_export = self._button(row1, "Als .txt exportieren", self.export_txt)
        self.btn_export.pack(side="left", padx=8)
        self.btn_export.pack_forget()

        self.btn_open_all = self._button(self.controls, "Alle UIs öffnen", self.open_all)
        self.btn_open_all.pack(pady=(15, 0))
        self.btn_open_all.pack_forget()

        # ---------- Info & Search Row ----------
        self.info_row = tk.Frame(self.controls, bg=COLOR_BG)
        self.info_row.pack(pady=(15, 0))
        self.info_row.pack_forget()

        # Suchfeld (Abgerundet via Canvas, mittig)
        search_width = 250
        search_height = 36
        self.search_canvas = tk.Canvas(
            self.info_row, 
            width=search_width, 
            height=search_height, 
            bg=COLOR_BG, 
            highlightthickness=0
        )
        self.search_canvas.pack(anchor="center")

        rounded_rect(self.search_canvas, 0, 0, search_width, search_height, 18, "#cccccc")
        rounded_rect(self.search_canvas, 1, 1, search_width-2, search_height-2, 17, "white")

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            self.search_canvas, 
            textvariable=self.search_var, 
            bd=0, 
            font=("Segoe UI", 11), 
            bg="white",
            fg="grey",
            highlightthickness=0
        )
        self.search_canvas.create_window(15, search_height//2, anchor="w", window=self.search_entry, width=search_width-45)

        self.search_clear_lbl = tk.Label(
            self.search_canvas, 
            text="✕", 
            bg="white", 
            fg="#999", 
            font=("Segoe UI", 10, "bold"), 
            cursor="hand2"
        )
        
        self.search_entry.bind("<FocusIn>", self._search_focus_in)
        self.search_entry.bind("<FocusOut>", self._search_focus_out)
        self.search_clear_lbl.bind("<Button-1>", self._clear_search)
        self.search_var.trace_add("write", self.on_search_change)

    def update_placeholder(self):
        self.placeholder_text = f"Services gefunden: {len(self.services)}"
        current = self.search_var.get()
        if not current or current.startswith("Services gefunden:"):
            self.search_var.set(self.placeholder_text)
            self.search_entry.config(fg="grey")

    def _search_focus_in(self, event):
        if self.search_var.get() == self.placeholder_text:
            self.search_var.set("")
            self.search_entry.config(fg="black")

    def _search_focus_out(self, event):
        if not self.search_var.get():
            self.search_var.set(self.placeholder_text)
            self.search_entry.config(fg="grey")

    def _clear_search(self, event):
        self.search_var.set("")
        self.search_entry.focus_set()

    def on_search_change(self, *args):
        val = self.search_var.get()
        if val and val != self.placeholder_text:
            self.search_clear_lbl.place(x=235, y=18, anchor="center")
        else:
            self.search_clear_lbl.place_forget()
            
        filtered = self.get_filtered_services()
        
        if self.generated:
            self.render_cards(filtered)
        else:
            self.render_list(filtered)

    def get_filtered_services(self):
        query = self.search_var.get()
        if query == self.placeholder_text or not query.strip():
            return self.services
        query = query.lower()
        return [s for s in self.services if query in s['service'].lower()]

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

        # Scrollen ist nur aktiv, wenn der Inhalt größer ist als das Fenster
        self.scroll_enabled = content_height > canvas_height

        if not self.scroll_enabled:
            self.canvas.configure(scrollregion=(0, 0, 0, canvas_height))
            self.canvas.yview_moveto(0)
        else:
            # +20 Puffer ganz unten, damit es schöner abschließt beim Scrollen
            self.canvas.configure(scrollregion=(bbox[0], bbox[1], bbox[2], bbox[3] + 20))

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
        self.config(cursor="wait")
        self.update()
        try:
            self.services = resolve_services()
            self.new_service_names = set()
            self.generated = False
            self.btn_export.pack_forget()
            self.btn_open_all.pack_forget()
            self.info_row.pack_forget()
            self.btn_generate.itemconfigure("btn_text", text="Generieren")
            self.update_placeholder()
            self.render_list()
        finally:
            self.config(cursor="")

    def handle_main_btn(self):
        if not self.generated:
            self.on_generate()
        else:
            self.on_regenerate()

    def on_generate(self):
        self.generated = True
        self.btn_generate.itemconfigure("btn_text", text="Erneut generieren")
        self.btn_export.pack(side="left", padx=8)
        self.btn_open_all.pack(pady=(15, 0))
        
        self.info_row.pack(pady=(15, 0))
        self.update_placeholder()
        
        self.render_cards(self.get_filtered_services())

    def on_regenerate(self):
        self.config(cursor="wait")
        self.update()
        try:
            old_names = {s['service'] for s in self.services}
            
            new_fetched = resolve_services()
            
            new_services = [s for s in new_fetched if s['service'] not in old_names]
            existing_services = [s for s in new_fetched if s['service'] in old_names]
            
            self.new_service_names = {s['service'] for s in new_services}
            self.services = new_services + existing_services
            
            self.generated = False
            self.update_placeholder()
            
            self.btn_generate.itemconfigure("btn_text", text="Generieren")
            self.btn_export.pack_forget()
            self.btn_open_all.pack_forget()
            self.info_row.pack_forget()
            
            self.render_list()
        finally:
            self.config(cursor="")

    # ---------- Views ----------
    def clear(self):
        for w in self.content.winfo_children():
            w.destroy()

    def render_list(self, services_to_render=None):
        self.clear()
        if services_to_render is None:
            services_to_render = self.services
            
        for s in services_to_render:
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
            
            is_new = s["service"] in self.new_service_names
            if is_new:
                row.create_oval(14, 22, 22, 30, fill="#28a745", outline="")
            
            row.create_text(32, 26, anchor="w",
                            text=s["service"], font=("Segoe UI", 12))
            row.pack(padx=SIDE_PADDING, pady=6)
        self._recalc_scroll()

    def render_cards(self, services_to_render=None):
        self.clear()
        if services_to_render is None:
            services_to_render = self.services
            
        cards_area = tk.Frame(self.content, bg=COLOR_BG)
        cards_area.pack(anchor="center", pady=12)

        for i, s in enumerate(services_to_render):
            r, c = divmod(i, CARDS_PER_ROW)

            card = tk.Canvas(
                cards_area,
                width=CARD_W,
                height=CARD_H,
                bg=COLOR_BG,
                highlightthickness=0
            )
            rounded_rect(card, 0, 0, CARD_W, CARD_H, 18, COLOR_CARD)

            port_text = s['port'].replace("->", " → ")

            y = 20
            card.create_text(20, y, anchor="w",
                             text=s["service"], font=("Segoe UI", 13, "bold"))
            y += 35
            card.create_text(20, y, anchor="w",
                             text=f"Container: {s['container']}", font=("Segoe UI", 9))
            y += 25
            card.create_text(20, y, anchor="w",
                             text=f"Port: {port_text}", font=("Segoe UI", 9))
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
        filtered = self.get_filtered_services()
        for s in filtered:
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
        
        filtered = self.get_filtered_services()
        for s in filtered:
            port_text = s['port'].replace("->", " → ")
            lines += [
                f"Service: {s['service']}",
                f"  Container: {s['container']}",
                f"  Port: {port_text}",
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
