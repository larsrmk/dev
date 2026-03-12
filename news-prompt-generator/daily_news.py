# -*- coding: utf-8 -*-
"""
Daily Prompt GUI für zweisprachige, quellengesicherte Tagesnews (Vortag)
Finale Version (2026):
- Kein Wochentag-Eingabefeld: automatische Berechnung
- Datumsauswahl per Kalender-Popup
- Kalender neutrale Farben
- Copy-Button -> nur eine Meldung
- HD-Fenster (1920x1080)
- Enthält den vollständigen Prompt

Start:
    python3 daily_prompt_qt.py
"""

import sys
import datetime as dt
import locale

# PyQt5 laden
try:
    from PyQt5 import QtWidgets, QtGui, QtCore
except ImportError:
    print("PyQt5 ist nicht installiert. Bitte 'pip install PyQt5' ausführen.")
    raise


# ======================================================================
# OPTIONAL: Locale für deutsche Wochentage setzen
# ======================================================================
try:
    locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")
except locale.Error:
    pass  # Falls Locale fehlt → fallback wird genutzt


# ======================================================================
# VOLLSTÄNDIGE PROMPT-VORLAGE
# ======================================================================

PROMPT_TEMPLATE = r"""Rolle & Ziel:
Du bist ein akribischer, neutraler News-Researcher & Redakteur. Erstelle eine umfassende, fakten- und quellengesicherte Nachrichtenübersicht zum Vortag ({{DATE}}) für einen deutschsprachigen Leser mit anschließender präziser englischer Übersetzung unter jedem einzelnen deutschen Abschnitt.

Leserprofil:
- Spricht Deutsch, wünscht unter jedem Abschnitt eine präzise englische Übersetzung.
- Interessensschwerpunkte: Sport (mit Fokus auf Fußball), Politik (In- & Ausland), Wirtschaft sowie weitere wichtige/kuriose Meldungen des Tages (Wissenschaft/Tech/Kultur/Unfälle/Justiz/Klima etc.).
- Erwartung: Nicht nur Top-Schlagzeilen, sondern auch weniger prominente Ereignisse.

Verbindliche Anforderungen:
1) Zeitraum:
   - Berücksichtige ausschließlich Ereignisse/Meldungen, die am {{DATE}} (lokale Zeit {{TIMEZONE}}) stattfanden oder publiziert wurden. Gib bei Bedarf Uhrzeiten und Zeitzonen an.

2) Umfang & Tiefe:
   - Gesamtumfang (DE+EN) > 2.000 Wörter. Der deutsche Teil > 1.000 Wörter.
   - Jeder Abschnitt soll inhaltlich **genau beschreiben, was passiert ist**, Hintergründe kontextualisieren (wer, was, wann, wo, warum, wie, Folgeeinschätzungen), und auch **weniger prominente** Schlagzeilen berücksichtigen.

3) Struktur & Zweisprachigkeit (exakte Reihenfolge):
   - Hauptüberschrift (H1): Nachrichtenüberblick vom {{DATE}}
   - Einleitung (kurzer deutscher Überblick, 5–8 Sätze)
   - **Danach für jeden Themenblock** (Sport, Politik Inland, Politik Ausland, Wirtschaft, Weitere Meldungen):
       A) Deutscher Abschnitt mit Zwischenüberschrift (H2/H3)
          - Volltext (detailliert, narrativ, faktensicher)
          - **Unmittelbar darunter die Quellenangaben (mind. 2, besser 3+)**
       B) **Direkt darunter die englische Übersetzung desselben Abschnitts** (präzise, natürlich klingend, keine Paraphrasen, sondern inhaltliche Deckungsgleichheit)
   - Reihenfolge:
       1) Sport (Fußball priorisiert, aber auch andere Sportarten)
       2) Politik Inland (Deutschland)
       3) Politik Ausland
       4) Wirtschaft/Finanzen/Unternehmen/Märkte
       5) Weitere wichtige/erwähnenswerte Meldungen (Wissenschaft/Tech/Klima/Kultur/Justiz/Unfälle etc.)

4) Quellen & Belege:
   - **Jeder deutsche Unterabschnitt** endet mit **„Quellen:“** und listet **mindestens 2 (idealerweise 3–5) unterschiedliche, glaubwürdige Medien** mit direktem Link (keine URL-Shortener).
   - Vergleiche die Angaben über mehrere Quellen, weise auf **Widersprüche** oder **Updates** hin.
   - Kennzeichne **Zeitstempel** (z. B. „Stand: 23:40 CET“) bei sich entwickelnden Lagen.
   - Nutze möglichst **Primärquellen** (offizielle Statements, Behörden, Verbände, Unternehmensmitteilungen) plus **renommierte Medien**. Bei Paywalls: nenne zusätzlich frei zugängliche Berichte.

5) Qualität & Stil:
   - Neutral, sachlich, präzise. Keine Spekulationen. Trenne sicher bestätigte Fakten klar von noch unbestätigten Informationen (mit Formulierungen wie „laut Polizeiangaben“, „nach Unternehmensmitteilung“, „Berichten zufolge“).
   - Vermeide Redundanz. Fasse identische Meldungen **einmal** zusammen und referenziere Varianten/Widersprüche.
   - Verwende **eindeutige Zahlen, Orte, Eigennamen, Positionen, direkte Zitate**, wenn belegt.
   - Bei Fußball (Sport): Nenne **Liga/Bewerb**, **Teams**, **Ergebnis**, **Torschützen**, **Tabellenauswirkungen**, **Verletzungen/Transfers**, **Statements**.

6) Ausgabeformat (genau einhalten, inklusive Sprachenfolge und Quellenplatzierung):
   # Nachrichtenüberblick vom {{DATE}}

   ## Einleitung (DE)
   [5–8 Sätze Überblick über die wichtigsten Themen und Trends des Tages. Keine Quellen hier.]

   ## Sport
   ### [präzise deutsche Schlagzeile/Subthema 1]
   [Deutscher Abschnitt …]
   **Quellen:** [..., ..., ...]

   ### [English translation of the exact same subtopic 1]
   [English …]

   ### [präzise deutsche Schlagzeile/Subthema 2]
   [Deutscher Abschnitt …]
   **Quellen:** [...]

   ### [English translation …]
   [English …]

   [Weitere Sport-Unterthemen analog]

   ## Politik Inland
   ### [deutsche Schlagzeile/Subthema 1]
   [Deutscher Abschnitt …]
   **Quellen:** [...]

   ### [English translation …]
   [English …]

   [... weitere Subthemen ...]

   ## Politik Ausland
   [gleiche Struktur]

   ## Wirtschaft
   [gleiche Struktur]

   ## Weitere wichtige Meldungen
   [gleiche Struktur]

7) Recherche- & Prüfprozess:
   - Prüfe mehrere Quellen pro Meldung
   - Prüfe Publikationszeitpunkt
   - Markiere Updates
   - Vergleiche widersprüchliche Angaben

8) Lokalisierung:
   - Deutsche Abschnitte → Deutsch
   - Direkt darunter englische Übersetzung
   - Zahlenformat deutsch vs. englisch beachten

9) Compliance:
   - Keine Paywall-Texte
   - Keine Spekulation
   - Keine ungesicherten Behauptungen

10) Vollständigkeitscheck:
   - [ ] DE+EN > 2000 Wörter
   - [ ] DE > 1000 Wörter
   - [ ] Quellen vollständig
   - [ ] Struktur eingehalten

Parameter:
- {{DATE}} = Vortag (z. B. 10.03.2026)
- {{TIMEZONE}} = CET/CEST
"""

# ======================================================================
# Hilfsfunktionen
# ======================================================================

def to_pydate(qdate: QtCore.QDate) -> dt.date:
    return dt.date(qdate.year(), qdate.month(), qdate.day())


def german_weekday_name(d: dt.date) -> str:
    try:
        name = d.strftime("%A")
    except:
        name = ["Montag", "Dienstag", "Mittwoch", "Donnerstag",
                "Freitag", "Samstag", "Sonntag"][d.weekday()]

    eng2de = {
        "Monday": "Montag",
        "Tuesday": "Dienstag",
        "Wednesday": "Mittwoch",
        "Thursday": "Donnerstag",
        "Friday": "Freitag",
        "Saturday": "Samstag",
        "Sunday": "Sonntag"
    }
    return eng2de.get(name, name)


def build_prompt(vortag: dt.date, timezone_str: str) -> str:
    date_str = vortag.strftime("%d.%m.%Y")
    tz = timezone_str.strip() if timezone_str.strip() else "CET/CEST"
    return PROMPT_TEMPLATE.replace("{{DATE}}", date_str).replace("{{TIMEZONE}}", tz)


# ======================================================================
# Eingabedialog (Datum + TZ)
# ======================================================================

class InputDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Datum auswählen")
        self.setModal(True)

        # Kalender-Popup
        self.date_edit = QtWidgets.QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        today = QtCore.QDate.currentDate()
        self.date_edit.setDate(today)

        # Min/Max
        self.date_edit.setMinimumDate(today.addYears(-10))
        self.date_edit.setMaximumDate(today.addYears(10))

        # Kalender neutral färben
        calendar = self.date_edit.calendarWidget()
        calendar.setStyleSheet("""
            QCalendarWidget QWidget {
                background-color: white;
                color: black;
            }
            QCalendarWidget QAbstractItemView:enabled {
                background-color: white;
                color: black;
                selection-background-color: #cccccc;
                selection-color: black;
            }
            QCalendarWidget QToolButton {
                background: white;
                color: black;
                border: none;
            }
            QCalendarWidget QToolButton:hover {
                background: #e6e6e6;
            }
            QCalendarWidget QSpinBox {
                color: black;
                background: white;
            }
        """)

        # Zeitzone
        self.tz_edit = QtWidgets.QLineEdit()
        self.tz_edit.setPlaceholderText("z. B. CET/CEST")
        self.tz_edit.setText("CET/CEST")

        form = QtWidgets.QFormLayout()
        form.addRow("Heutiges Datum:", self.date_edit)
        form.addRow("Zeitzone:", self.tz_edit)

        btn_ok = QtWidgets.QPushButton("OK")
        btn_cancel = QtWidgets.QPushButton("Abbrechen")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        btns = QtWidgets.QHBoxLayout()
        btns.addStretch(1)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(btns)
        self.setLayout(layout)

    def get_values(self):
        return self.date_edit.date(), self.tz_edit.text().strip()


# ======================================================================
# Hauptfenster
# ======================================================================

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Daily News Prompt Generator (DE+EN) – Vortag")
        self.resize(1920, 1080)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        self.text_edit = QtWidgets.QPlainTextEdit()
        font = QtGui.QFont("Courier New")
        font.setPointSize(10)
        self.text_edit.setFont(font)

        self.copy_btn = QtWidgets.QPushButton("In Zwischenablage kopieren")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)

        self.new_btn = QtWidgets.QPushButton("Neu…")
        self.new_btn.clicked.connect(self.ask_and_generate)

        self.info_label = QtWidgets.QLabel("Bereit.")

        top = QtWidgets.QHBoxLayout()
        top.addWidget(self.new_btn)
        top.addStretch(1)
        top.addWidget(self.copy_btn)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.info_label)
        central.setLayout(layout)

        QtCore.QTimer.singleShot(0, self.ask_and_generate)

    def ask_and_generate(self):
        dlg = InputDialog(self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            qdate, tz = dlg.get_values()
            today = to_pydate(qdate)
            yesterday = today - dt.timedelta(days=1)

            prompt = build_prompt(yesterday, tz)
            self.text_edit.setPlainText(prompt)

            weekday = german_weekday_name(today)
            self.info_label.setText(
                f"Heute: {weekday} {today.strftime('%d.%m.%Y')}  |  "
                f"Vortag: {yesterday.strftime('%d.%m.%Y')}  |  "
                f"Zeitzone: {tz}"
            )
        else:
            if not self.text_edit.toPlainText().strip():
                QtWidgets.QApplication.instance().quit()

    def copy_to_clipboard(self):
        QtWidgets.QApplication.clipboard().setText(self.text_edit.toPlainText())
        self.info_label.setText("Prompt in die Zwischenablage kopiert.")


# ======================================================================
# MAIN
# ======================================================================

def main():
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    win = MainWindow()
    win.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()