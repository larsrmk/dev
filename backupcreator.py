import os
import shutil
import datetime
import re
import tkinter as tk
from tkinter import filedialog, messagebox

BG_MAIN = "#F0F2F5"         
FG_MAIN = "#1C1E21"         
FG_SUB = "#606770"         
BTN_BG = "#E4E6EB"         
BTN_HOVER = "#D8DADF"       
BTN_ACTION = "#0866FF"      
BTN_ACTION_HOVER = "#0056D6"
BTN_ACTION_FG = "#FFFFFF"  
DISABLED_BG = "#E0E0E0"     
DISABLED_FG = "#A0A0A0"     

FONT_TITLE = ("Segoe UI", 11, "bold")
FONT_MAIN = ("Segoe UI", 10)
FONT_BTN = ("Segoe UI", 9, "bold")

def center_window(window, width, height):
    """Zentriert das Fenster auf dem Bildschirm."""
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))
    window.geometry(f"{width}x{height}+{x}+{y}")

class StyledButton(tk.Button):
    """Button mit Hover-Effekt und Deaktivierungs-Logik."""
    def __init__(self, master, bg_color, hover_color, fg_color, **kwargs):
        super().__init__(master, **kwargs)
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.fg_color = fg_color
        self.is_disabled = False

        self.configure(
            bg=self.bg_color, fg=self.fg_color, font=FONT_BTN, 
            relief="flat", activebackground=self.hover_color, 
            activeforeground=self.fg_color, bd=0, padx=15, pady=8, cursor="hand2"
        )
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        if not self.is_disabled:
            self['background'] = self.hover_color

    def on_leave(self, e):
        if not self.is_disabled:
            self['background'] = self.bg_color

    def disable(self):
        self.is_disabled = True
        self.configure(state="disabled", bg=DISABLED_BG, fg=DISABLED_FG, cursor="arrow")

    def enable(self):
        self.is_disabled = False
        self.configure(state="normal", bg=self.bg_color, fg=self.fg_color, cursor="hand2")

class CustomOverwriteDialog(tk.Toplevel):
    """Modernes Pop-up für die Überschreiben-Frage."""
    def __init__(self, parent, title, message):
        super().__init__(parent)
        self.result = False
        
        self.title(title)
        self.configure(bg="#FFFFFF")
        self.resizable(False, False)
        
        center_window(self, 420, 200)
        self.transient(parent)
        self.grab_set()

        lbl_msg = tk.Label(self, text=message, bg="#FFFFFF", fg=FG_MAIN, font=FONT_MAIN, justify="center", wraplength=380)
        lbl_msg.pack(expand=True, padx=20, pady=20)

        frame_btn = tk.Frame(self, bg="#FFFFFF")
        frame_btn.pack(fill="x", pady=15)

        btn_yes = StyledButton(frame_btn, BTN_ACTION, BTN_ACTION_HOVER, BTN_ACTION_FG, text="Ja, überschreiben", command=self.on_yes)
        btn_yes.pack(side="right", padx=20)

        btn_no = StyledButton(frame_btn, BTN_BG, BTN_HOVER, FG_MAIN, text="Nein, überspringen", command=self.on_no)
        btn_no.pack(side="left", padx=20)

        self.wait_window()

    def on_yes(self):
        self.result = True
        self.destroy()

    def on_no(self):
        self.result = False
        self.destroy()

class BackupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System Backup Manager")
        self.root.configure(bg=BG_MAIN)
        
        center_window(self.root, 580, 560)

        self.source_file = ""
        self.dest_paths = []

        self.build_ui()
        self.check_ready_state()

    def build_ui(self):
        frame_source = tk.Frame(self.root, bg=BG_MAIN)
        frame_source.pack(fill="x", padx=30, pady=(30, 5))

        lbl_source_title = tk.Label(frame_source, text="1. QUELLDATEI WÄHLEN", bg=BG_MAIN, fg=FG_MAIN, font=FONT_TITLE)
        lbl_source_title.pack(anchor="w")

        self.lbl_source_val = tk.Label(frame_source, text="Noch keine Datei ausgewählt", bg=BG_MAIN, fg=FG_SUB, font=FONT_MAIN, wraplength=520, justify="left")
        self.lbl_source_val.pack(anchor="w", pady=(5, 12))

        btn_select_file = StyledButton(frame_source, BTN_BG, BTN_HOVER, FG_MAIN, text="DATEI SUCHEN", command=self.select_file)
        btn_select_file.pack(anchor="w")

        frame_line1 = tk.Frame(self.root, bg="#DCDFE5", height=1)
        frame_line1.pack(fill="x", padx=30, pady=20)

        frame_dest = tk.Frame(self.root, bg=BG_MAIN)
        frame_dest.pack(fill="both", expand=True, padx=30)

        lbl_dest_title = tk.Label(frame_dest, text="2. ZIELPFADE DEFINIEREN", bg=BG_MAIN, fg=FG_MAIN, font=FONT_TITLE)
        lbl_dest_title.pack(anchor="w")

        self.paths_container = tk.Frame(frame_dest, bg=BG_MAIN)
        self.paths_container.pack(fill="x", pady=(10, 15))

        btn_add_dest = StyledButton(frame_dest, BTN_BG, BTN_HOVER, FG_MAIN, text="+ PFAD HINZUFÜGEN", command=self.add_dest_path)
        btn_add_dest.pack(anchor="w")

        frame_line2 = tk.Frame(self.root, bg="#DCDFE5", height=1)
        frame_line2.pack(fill="x", padx=30, pady=20)

        frame_buttons = tk.Frame(self.root, bg=BG_MAIN)
        frame_buttons.pack(side="bottom", fill="x", padx=30, pady=(0, 30))

        btn_cancel = StyledButton(frame_buttons, BTN_BG, BTN_HOVER, FG_MAIN, text="ABBRECHEN", command=self.root.destroy)
        btn_cancel.pack(side="left")

        self.btn_backup = StyledButton(frame_buttons, BTN_ACTION, BTN_ACTION_HOVER, BTN_ACTION_FG, text="BACKUP ERSTELLEN", command=self.create_backup)
        self.btn_backup.pack(side="right")

    def check_ready_state(self):
        """Aktiviert den Backup-Button nur, wenn Datei und min. 1 Pfad gewählt sind."""
        if self.source_file and len(self.dest_paths) > 0:
            self.btn_backup.enable()
        else:
            self.btn_backup.disable()

    def select_file(self):
        filepath = filedialog.askopenfilename(title="Wähle genau eine Datei für das Backup")
        if filepath:
            self.source_file = filepath
            self.lbl_source_val.config(text=f"📄 {os.path.basename(self.source_file)}", fg=BTN_ACTION, font=("Segoe UI", 10, "bold"))
            self.check_ready_state()

    def add_dest_path(self):
        dirpath = filedialog.askdirectory(title="Wähle ein Zielverzeichnis aus")
        if dirpath:
            if dirpath not in self.dest_paths:
                self.dest_paths.append(dirpath)
                
                path_badge = tk.Frame(self.paths_container, bg="#E4E6EB", pady=6, padx=10)
                path_badge.pack(fill="x", pady=3)
                
                lbl_icon = tk.Label(path_badge, text="📁", bg="#E4E6EB", fg=FG_MAIN, font=FONT_MAIN)
                lbl_icon.pack(side="left", padx=(0, 10))
                
                lbl_text = tk.Label(path_badge, text=dirpath, bg="#E4E6EB", fg=FG_MAIN, font=FONT_MAIN)
                lbl_text.pack(side="left")
                
                self.check_ready_state()
            else:
                messagebox.showinfo("Info", "Dieser Pfad wurde bereits hinzugefügt.")

    def create_backup(self):
        filename = os.path.basename(self.source_file)
        name, ext = os.path.splitext(filename)
        
        # Timestamp
        timestamp = datetime.datetime.now().strftime("%d_%m_%Y")
        new_filename = f"{name}_bak_{timestamp}{ext}"

        pattern_str = re.escape(name) + r"_bak_\d{2}_\d{2}_\d{4}" + re.escape(ext)
        pattern = re.compile(pattern_str)

        erfolgreiche_kopien = 0

        for d in self.dest_paths:
            existierende_backups = []
            
            if os.path.exists(d):
                for f in os.listdir(d):
                    if pattern.match(f):
                        existierende_backups.append(f)

            soll_kopieren = True
            
            if existierende_backups:
                msg = f"Im Verzeichnis:\n{d}\n\ngibt es bereits eine Backup-Datei für heute. Soll diese überschrieben werden?"
                dialog = CustomOverwriteDialog(self.root, "Backup existiert bereits", msg)
                überschreiben = dialog.result
                
                if überschreiben:
                    for old_file in existierende_backups:
                        try:
                            os.remove(os.path.join(d, old_file))
                        except Exception:
                            pass
                else:
                    soll_kopieren = False

            if soll_kopieren:
                dest_path = os.path.join(d, new_filename)
                try:
                    shutil.copy2(self.source_file, dest_path)
                    erfolgreiche_kopien += 1
                except Exception as e:
                    messagebox.showerror("Fehler", f"Fehler beim Kopieren nach {d}:\n{e}")
                    return

        # Pop-Up
        if erfolgreiche_kopien > 0:
            messagebox.showinfo("Backup erstellt", f"Erfolgreich! Das Backup wurde in {erfolgreiche_kopien} Pfad(e) gespeichert.")
        else:
            messagebox.showinfo("Vorgang beendet", "Es wurden keine neuen Dateien kopiert.")

if __name__ == "__main__":
    root = tk.Tk()
    app = BackupApp(root)
    root.mainloop()