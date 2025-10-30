# Umfassende Anleitung: Sicheres Gitea-Upgrade auf die neueste Version

## Inhaltsverzeichnis
1. [Vorbereitung und Voraussetzungen](#vorbereitung-und-voraussetzungen)
2. [Pre-Upgrade-Checkliste](#pre-upgrade-checkliste)
3. [Sicherung durchführen](#sicherung-durchführen)
4. [Test-Upgrade in separater Umgebung](#test-upgrade-in-separater-umgebung)
5. [Production-Upgrade durchführen](#production-upgrade-durchführen)
6. [Post-Upgrade-Validierung](#post-upgrade-validierung)
7. [Troubleshooting und Rollback](#troubleshooting-und-rollback)

---

## Vorbereitung und Voraussetzungen

### Systemanforderungen prüfen

Bevor Sie mit dem Upgrade beginnen, überprüfen Sie:

- **Gitea-Version ermitteln:**
  ```bash
  sudo -u git /usr/local/bin/gitea --version
  ```

- **Aktuelle Gitea-Version herunterladen:**
  Besuchen Sie [GitHub Gitea Releases](https://github.com/go-gitea/gitea/releases) um die neueste stabile Version zu ermitteln (z.B. v1.24.7).

- **Systemressourcen:**
  - Ausreichend Festplattenspeicher für Backups (~1,5x Größe der aktuellen Installation)
  - RAM für Datenbankmigrationen (mindestens 512 MB frei)

- **Zugriff auf VM und Proxmox:**
  - SSH-Zugriff zur Gitea-VM
  - Proxmox-Zugriff zur Snapshot-Erstellung

### Datenbankkompatibilität verstehen

**Wichtig: Versionssprünge und Datenbankmigrationen**

| Szenario | Kompatibilität | Aktion |
|----------|----------------|--------|
| 1.4.0 → 1.4.1 | ✅ Patch-Update (identische DB-Struktur) | Direkt aktualisieren |
| 1.4.x → 1.5.y | ✅ Minor-Update (DB wird migriert) | Direkt aktualisieren |
| 1.5.y → 1.4.x | ❌ Downgrade nicht möglich | Backup erforderlich! |
| Beliebig → neueste | ✅ In den meisten Fällen möglich | Befolgen Sie diese Anleitung |

**Datenbankkompatibilität:** Bei Minor/Major-Versionssprüngen wird die Datenbankstruktur automatisch migriert. Ein Downgrade ist danach nicht möglich – daher sind Backups essentiell.

---

## Pre-Upgrade-Checkliste

### 1. Changelog auf Breaking Changes prüfen

```bash
# Öffnen Sie den Changelog für die neue Version
# z.B. https://github.com/go-gitea/gitea/releases/tag/v1.24.7
# Prüfen Sie nach:
# - "BREAKING CHANGES"
# - Deprecated configuration options
# - Datenbankinkompatibilität
```

**Auf der Gitea Admin-Seite prüfen:**
- Navigieren Sie zu: **Administration** → **Site Administration** → **Configuration**
- Suchen Sie nach Warnungen wie: `Deprecated Configuration` oder `Unsupported Configuration`
- Falls Warnungen vorhanden: Diese Konfigurationsoptionen korrigieren, bevor Sie upgraden

### 2. Aktivierte Optionen und Customizations dokumentieren

```bash
# Eingeloggt auf der Gitea-VM als Root/Sudo-Benutzer

# SSH-Zugriff zur VM:
ssh root@<gitea-vm-ip>

# Wichtige Konfiguration sichern:
cat /etc/gitea/app.ini | grep -E "^\[|^[A-Z_]" > ~/gitea-config-backup.txt

# Customizations prüfen:
ls -la /var/lib/gitea/custom/templates/
ls -la /var/lib/gitea/custom/public/
```

**Dokumentieren Sie:**
- Sind custom Templates vorhanden?
- Gibt es angepasste Themes?
- Welche externe Authentifizierung ist konfiguriert (OAuth2, LDAP)?
- Sind LFS, Webhooks oder Actions aktiviert?

### 3. Benutzer informieren

- **Ankündigung:** Teilen Sie mit, wann das Maintenance-Fenster stattfindet
- **Zeitrahmen:** Geben Sie ein realistisches Zeitfenster an (z.B. 1-2 Stunden)
- **Dauer des Downtimes:** Bei Datenbankmigrationen kann es 5-30 Minuten dauern (abhängig von Datenbankgröße)
- **Kommunikationskanal:** Definieren Sie, wie Sie Benutzer benachrichtigen, wenn Gitea wieder online ist

---

## Sicherung durchführen

### Phase 1: Proxmox VM Snapshot erstellen

**Vorteile:** Schnelle Wiederherstellung der gesamten VM, falls etwas schief geht.

```bash
# Auf dem Proxmox-Host:
# 1. Proxmox Web-UI öffnen oder SSH verwenden

# Via SSH zum Proxmox-Host:
ssh root@<proxmox-host>

# VM-ID ermitteln (z.B. 100):
qm list | grep gitea

# Snapshot erstellen (z.B. vor dem Upgrade):
qm snapshot 100 pre-upgrade-snapshot --description "Gitea backup before v1.24.7 upgrade"

# Snapshots auflisten:
qm listsnapshot 100
```

### Phase 2: Gitea Dump erstellen (empfohlen)

Der `gitea dump`-Befehl erstellt ein ZIP-Archiv mit allen wichtigen Daten:
- `app.ini` (oder Kopie, falls extern gespeichert)
- `custom/` Verzeichnis (Templates, Themes, Konfigurationen)
- `data/` Verzeichnis (Attachments, Avatare, LFS, Indexer, SQLite-DB)
- `repos/` Verzeichnis (alle Git-Repositories)
- `gitea-db.sql` (SQL-Dump der Datenbank)
- `gitea-repo.zip` (Backup der Repositories)

```bash
# SSH zur Gitea-VM:
ssh root@<gitea-vm-ip>

# Zum Gitea-Benutzer wechseln:
su - git

# Dump erstellen (Gitea muss NICHT laufen):
/usr/local/bin/gitea dump -c /etc/gitea/app.ini -f gitea-dump-$(date +%Y%m%d-%H%M%S).zip

# Output sollte ähnlich aussehen:
# 2025/10/30 22:00:01 Creating tmp work dir: /tmp/gitea-dump-xxx
# 2025/10/30 22:00:02 Dumping local repositories...
# 2025/10/30 22:00:15 Dumping database...
# 2025/10/30 22:00:16 Packing dump files...
# 2025/10/30 22:00:45 Removing tmp work dir: /tmp/gitea-dump-xxx
# 2025/10/30 22:00:45 Finish dumping in file gitea-dump-20251030-220045.zip

# Dump verifizieren:
ls -lh gitea-dump-*.zip

# Dump auf externen Storage kopieren (z.B. NAS, USB-Drive, Cloud):
# Beispiel mit SCP:
exit  # Zurück zu Root
scp /home/git/gitea-dump-*.zip backup-user@backup-server:/backups/gitea/
```

### Phase 3: Separate Datenbank-Backups

**Für PostgreSQL oder MySQL zusätzlich den nativen Dump verwenden:**

```bash
# PostgreSQL (empfohlen für PostgreSQL-Instanzen):
pg_dump -U gitea -d gitea_db > gitea-db-$(date +%Y%m%d-%H%M%S).sql

# MySQL/MariaDB:
mysqldump -u gitea -p gitea_db > gitea-db-$(date +%Y%m%d-%H%M%S).sql
```

### Phase 4: Konfigurationsdateien sichern

```bash
# App-Konfiguration:
cp /etc/gitea/app.ini /etc/gitea/app.ini.backup-$(date +%Y%m%d)

# Alte Gitea-Binary sichern:
cp /usr/local/bin/gitea /usr/local/bin/gitea.backup-v$(sudo -u git /usr/local/bin/gitea --version | awk '{print $3}')

# Alle Backups zusammenfassen:
mkdir -p /tmp/gitea-pre-upgrade-backup
cp /etc/gitea/app.ini.backup-* /tmp/gitea-pre-upgrade-backup/
cp /usr/local/bin/gitea.backup-* /tmp/gitea-pre-upgrade-backup/
tar czf gitea-pre-upgrade-backup-$(date +%Y%m%d-%H%M%S).tar.gz /tmp/gitea-pre-upgrade-backup/

# Auf externen Storage:
scp gitea-pre-upgrade-backup-*.tar.gz backup-user@backup-server:/backups/gitea/
```

---

## Test-Upgrade in separater Umgebung

**Warum ein Test-Upgrade?**
- Prüfung auf Kompatibilitätsprobleme
- Validierung von custom Templates/Themes
- Schätzung der Migrations-Dauer
- Identifikation von Fehlern vor Production-Upgrade

### Schritt 1: Test-VM aus Snapshot erstellen

```bash
# Auf Proxmox-Host:
ssh root@<proxmox-host>

# VM-ID und Snapshot-Namen ermitteln:
qm listsnapshot 100 | grep pre-upgrade

# Neue VM aus Snapshot erstellen:
qm clone 100 101 --name gitea-test --full

# Oder via Web-UI:
# 1. Rechtsklick auf VM "gitea"
# 2. "Clone" wählen
# 3. "Full Clone" auswählen
# 4. Name: "gitea-test"
```

### Schritt 2: Test-VM starten und vorbereiten

```bash
# Test-VM starten:
qm start 101

# Auf Test-VM zugreifen:
ssh root@<test-vm-ip>

# Gitea-Service stoppen:
systemctl stop gitea

# Gitea aktuelle Version überprüfen:
/usr/local/bin/gitea --version
```

### Schritt 3: Neue Gitea-Version herunterladen

```bash
# Als Root auf der Test-VM:

# Temporäres Verzeichnis für neuen Binary:
mkdir -p /tmp/gitea-new

cd /tmp/gitea-new

# Neueste Gitea-Version herunterladen (z.B. v1.24.7 für Linux x64):
wget https://github.com/go-gitea/gitea/releases/download/v1.24.7/gitea-1.24.7-linux-amd64 -O gitea-new

# Oder für ARM64 (z.B. Raspberry Pi):
wget https://github.com/go-gitea/gitea/releases/download/v1.24.7/gitea-1.24.7-linux-arm64 -O gitea-new

# Ausführbarkeit prüfen:
chmod +x gitea-new

# Test: Neue Version starten (ohne Web-Service):
./gitea-new --version
# Output: Gitea version 1.24.7 built with Go 1.21.5 ...
```

### Schritt 4: Binary austauschen und Test-Upgrade durchführen

```bash
# Wichtig: Binary-Namen NICHT ändern (immer "gitea" heißen lassen)!

# Alte Binary durch neue ersetzen:
cp /usr/local/bin/gitea /usr/local/bin/gitea.bak-test
cp /tmp/gitea-new/gitea-new /usr/local/bin/gitea

# Ownership und Permissions setzen:
chown git:git /usr/local/bin/gitea
chmod 755 /usr/local/bin/gitea

# Gitea mit neuem Binary starten:
systemctl start gitea

# Logs auf Fehler prüfen:
journalctl -u gitea -n 50 -f

# In separatem Terminal nach ~30 Sekunden prüfen:
systemctl status gitea
```

### Schritt 5: Test-Datenbankmigrationen prüfen

```bash
# In Logs prüfen (sollte ca. 5-30 Minuten dauern, abhängig von Datenbankgröße):
journalctl -u gitea | grep -i "migration\|database\|schema"

# Nach Completion sollte Gitea online sein:
curl http://localhost:3000

# Web-UI öffnen und prüfen:
# - Repositories vorhanden?
# - Benutzer sichtbar?
# - Repositories können geklont werden?
# - Webhooks/Actions funktionieren?
# - Custom Templates/Themes angewendet?
```

### Schritt 6: Custom Templates/Themes validieren

```bash
# Gitea Web-UI aufrufen: http://<test-vm-ip>:3000

# Prüfen:
1. Seiten-Layout und Styling korrekt?
2. Custom CSS/Themes angewendet?
3. Navigation/Header custom angepasst?
4. Keine 500-Fehler beim Laden von Seiten?
5. Alle Funktionen erreichbar (Repos, Users, Admin)?

# Bei Problemen mit Templates:
# - Alte Templates in /var/lib/gitea/custom/templates/ löschen
# - Kompatible Templates für neue Version verwenden
# - Gitea neu starten
systemctl restart gitea
```

### Schritt 7: Admin-Seite Checks durchführen

```bash
# Als Admin in Web-UI einloggen
# Navigieren zu: Administration → Site Administration

# Prüfen:
1. Configuration-Tab: Keine Warnungen?
2. Monitoring-Tab: Keine Fehler?
3. System Health: Alles grün?
4. Database: Migrationen erfolgreich?
5. Repositories: Können alle Repos erreicht werden?
```

### Schritt 8: Test-VM löschen

```bash
# Nach erfolgreicher Test-Phase auf Proxmox-Host:
qm stop 101
qm destroy 101
```

---

## Production-Upgrade durchführen

### Schritt 1: Finales Maintenance-Fenster ankündigen

```bash
# Gitea ist für alle Benutzer offline - Kommunikation ist wichtig!
# Zeitfenster: ~1-2 Stunden (abhängig von Datenbankgröße)
```

### Schritt 2: Proxmox VM Snapshot vor Upgrade

```bash
# Auf Proxmox-Host:
ssh root@<proxmox-host>

qm snapshot 100 pre-upgrade-production-$(date +%Y%m%d-%H%M%S) \
  --description "Pre-upgrade snapshot for v1.24.7 upgrade"
```

### Schritt 3: Gitea Service stoppen

```bash
# SSH zur Gitea-VM:
ssh root@<gitea-vm-ip>

# Gitea stoppen:
systemctl stop gitea

# Verify stopped:
systemctl status gitea
# Active: inactive (dead)

# Keine laufenden Gitea-Prozesse:
ps aux | grep gitea | grep -v grep
# (sollte leer sein)

# Alternative mit Zeitlimit warten:
systemctl stop gitea
sleep 10
ps aux | grep -i gitea | grep -v grep | awk '{print $2}' | xargs -r kill -9
```

### Schritt 4: Finale Sicherung vor Production-Upgrade

```bash
# Nochmals Gitea Dump erstellen (schnell, da kein Service läuft):
su - git
/usr/local/bin/gitea dump -c /etc/gitea/app.ini -f gitea-dump-final-$(date +%Y%m%d-%H%M%S).zip
exit

# Auf externen Storage kopieren:
scp /home/git/gitea-dump-final-*.zip backup-user@backup-server:/backups/gitea/
```

### Schritt 5: Neue Gitea-Binary herunterladen

```bash
# Als Root auf Production-VM:

mkdir -p /tmp/gitea-upgrade

cd /tmp/gitea-upgrade

# Neueste Gitea-Version herunterladen:
wget https://github.com/go-gitea/gitea/releases/download/v1.24.7/gitea-1.24.7-linux-amd64 -O gitea-new

chmod +x gitea-new

# Integrität prüfen (optional, aber empfohlen):
./gitea-new --version
```

### Schritt 6: Binary austauschen (Production)

```bash
# Alte Binary sichern:
cp /usr/local/bin/gitea /usr/local/bin/gitea.backup-prod-$(date +%Y%m%d)

# Neue Binary einsetzen:
cp /tmp/gitea-upgrade/gitea-new /usr/local/bin/gitea

# Ownership und Permissions:
chown git:git /usr/local/bin/gitea
chmod 755 /usr/local/bin/gitea

# Verify:
/usr/local/bin/gitea --version
# Gitea version 1.24.7 ...
```

### Schritt 7: Gitea Service starten (Production Upgrade)

```bash
# Service starten:
systemctl start gitea

# Logs beobachten (im Hintergrund läuft die Datenbankmigration):
journalctl -u gitea -f

# Warten, bis Migration abgeschlossen ist:
# - "Trying to migrate" → Migration läuft
# - Keine neuen Log-Einträge nach 1-2 Minuten → Wahrscheinlich abgeschlossen
# - "Starting web service..." oder ähnlich → Service läuft jetzt

# In separatem Terminal Status prüfen:
systemctl status gitea
# Active: active (running)

# Web-UI testen (sollte nach 30-60 Sekunden erreichbar sein):
curl http://localhost:3000
```

### Schritt 8: Service-Autostart prüfen

```bash
# Sicherstellen, dass Gitea nach Reboot autostartet:
systemctl is-enabled gitea
# Output: enabled

# Falls disabled:
systemctl enable gitea
```

---

## Post-Upgrade-Validierung

### 1. Grundsätzliche Funktionalität prüfen

```bash
# SSH zur Gitea-VM:
ssh root@<gitea-vm-ip>

# Service läuft:
systemctl status gitea

# Binary korrekte Version:
/usr/local/bin/gitea --version

# Web-UI erreichbar:
curl -I http://localhost:3000
# HTTP/1.1 200 OK

# Logs ohne kritische Fehler:
journalctl -u gitea | grep -i "error\|panic\|fatal" | head -20
# (sollte leer sein oder nur bekannte Fehler zeigen)
```

### 2. Web-UI Validierung (als Admin)

```
Öffnen Sie http://<gitea-url>:3000 im Browser und prüfen:

1. Dashboard:
   - Repositories sichtbar?
   - Statistiken angezeigt?
   - Letzte Aktivitäten vorhanden?

2. Repositories:
   - Alle Repos vorhanden?
   - Clonen möglich (HTTP)?
   - Commits, Branches sichtbar?

3. Administration:
   - Administration → Site Administration erreichbar?
   - Konfiguration Tab: Keine Warnungen?
   - Database Status: OK?
   - System Health: Keine Fehler?

4. Benutzer & Authentifizierung:
   - Login funktioniert?
   - LDAP/OAuth2 (falls konfiguriert) funktioniert?
   - Neue Benutzer können sich registrieren (falls enabled)?

5. SSH-Zugriff:
   - SSH-Key zu Profil hinzufügen (Settings → SSH/GPG Keys)
   - Clone via SSH:
     git clone git@<gitea-host>:username/repo.git
```

### 3. Datenbank-Migrationen verifizieren

```bash
# SSH zur Gitea-VM:
ssh root@<gitea-vm-ip>

# Doctor Check durchführen:
su - git
/usr/local/bin/gitea doctor check --default

# Output sollte sein:
# [I] Using 'git' user to run
# [I] Checking [...]
# ✓ All checks passed
```

### 4. Repositories-Validierung

```bash
# SQL-Basiert (für PostgreSQL/MySQL):
# Als Gitea-Datenbankbenutzer einloggen und prüfen:

# PostgreSQL:
psql -U gitea -d gitea_db -c "SELECT COUNT(*) FROM repository;"
# Sollte die erwartete Anzahl Repos zeigen

# MySQL:
mysql -u gitea -p gitea_db -e "SELECT COUNT(*) FROM repository;"
```

### 5. SSH-Hooks regenerieren (falls nötig)

```bash
# Nachdem alles funktioniert, SSH-Hooks regenerieren:
su - git
/usr/local/bin/gitea admin regenerate hooks

# Output sollte sein:
# Regenerate hooks of all repositories

# Danach können Benutzer via SSH pushen
```

### 6. Pre-Receive Hooks synchronisieren

```bash
# Falls Webhooks/Actions verwendet werden:
su - git
/usr/local/bin/gitea admin regenerate hooks

# Oder über Web-UI:
# Administration → Maintenance → Resynchronize pre-receive, 
# update and post-receive hooks of all repositories
```

### 7. Custom Templates/Themes verifizieren

```bash
# Web-UI prüfen:
# - Sind custom CSS-Themes angewendet?
# - Ist das Layout correct?
# - Keine 500-Fehler?
# - Alle UI-Elemente vorhanden?

# Falls Probleme:
# 1. Web-Browser Cache clearen (Ctrl+Shift+Del oder Cmd+Shift+Del)
# 2. Gitea Service neu starten:
systemctl restart gitea

# 3. Logs prüfen:
journalctl -u gitea | tail -50
```

### 8. Externe Services verifizieren

```
Prüfen Sie alle integrierten Services:

1. **Webhooks:**
   - Ein Test-Webhook triggern
   - Log-Einträge in Gitea prüfen

2. **External Git Services (GitHub, GitLab Mirrors):**
   - Mirror-Synchronization funktioniert?

3. **Authentifizierung:**
   - LDAP-Benutzer können sich einloggen?
   - OAuth2 (GitHub, Gitea) funktioniert?

4. **LFS (Large File Storage):**
   - Falls aktiviert: LFS-Objekte funktionieren?

5. **Package Registry:**
   - Falls aktiviert: Packages abrufbar?

6. **Actions/CI/CD:**
   - Falls aktiviert: Runner verbunden?
   - Jobs können ausgeführt werden?
```

### 9. Benutzer benachrichtigen (Service Online)

```
Kommunikieren Sie:
- Gitea ist wieder online
- Upgrade auf Version 1.24.7 erfolgreich
- Falls Probleme: Support-Kanal angeben
```

---

## Troubleshooting und Rollback

### Problem: Gitea startet nicht nach Upgrade

```bash
# Logs prüfen:
journalctl -u gitea -n 100

# Typische Fehler:
# 1. Binary falsch: /usr/local/bin/gitea muss eine gültige Datei sein
#    → Binary erneut downloaden und ersetzen

# 2. Konfiguration inkompatibel:
#    → app.ini mit Changelog abgleichen
#    → Alte Konfigurationsoptionen ggf. löschen

# 3. Datenbankmigrationen fehlgeschlagen:
#    → Siehe nächster Abschnitt

# 4. Port bereits in Verwendung:
#    → netstat -tlnp | grep 3000
#    → Anderen Prozess stoppen oder Port ändern
```

### Problem: Datenbank-Migration fehlgeschlagen

```bash
# Logs prüfen:
journalctl -u gitea | grep -i "migration\|database error"

# Reparaturversuch:
su - git
/usr/local/bin/gitea doctor check --all --fix

# Falls immer noch problematisch:
# → Rollback durchführen (siehe nächster Abschnitt)
```

### Problem: Custom Templates/Themes funktionieren nicht

```bash
# Ursachen:
# - Template-Syntax für neue Version inkompatibel
# - CSS-Klassen geändert
# - Template-Pfade verschoben

# Lösung:
# 1. Custom Templates temporär deaktivieren:
su - git
mv /var/lib/gitea/custom/templates /var/lib/gitea/custom/templates.bak

# 2. Gitea neu starten:
systemctl restart gitea

# 3. Web-UI funktioniert jetzt?
# → Ja: Templates sind schuld
#    - Neue Templates für Version 1.24.7 besorgen
#    - Kompatible Versionen von GitHub prüfen

# 4. Custom Templates zurückbringen (optional):
mv /var/lib/gitea/custom/templates.bak /var/lib/gitea/custom/templates
```

### Rollback: Zurück zur alten Version

**Nur wenn Upgrade fehlgeschlagen ist und nicht wiederhergestellt werden kann!**

#### Option 1: Aus Backup (bevorzugt)

```bash
# 1. Aktuelle (kaputte) Datenbank-Datei sichern:
su - git
mv /var/lib/gitea/data/gitea.db /var/lib/gitea/data/gitea.db.broken-upgrade

# 2. Dump-Backup einspielen:
# (Falls Sie einen dump vor Upgrade gemacht haben)
unzip gitea-dump-final-XXXXXX.zip
psql -U gitea -d gitea_db < gitea-db.sql  # PostgreSQL
# ODER
mysql -u gitea -p gitea_db < gitea-db.sql  # MySQL

# 3. Alte Gitea-Binary zurückstellen:
cp /usr/local/bin/gitea.backup-prod-XXXXXX /usr/local/bin/gitea

# 4. Service starten:
systemctl start gitea

# 5. Alte Version sollte jetzt laufen
/usr/local/bin/gitea --version
```

#### Option 2: Aus Proxmox Snapshot

```bash
# Auf Proxmox-Host:
ssh root@<proxmox-host>

# VM herunterfahren:
qm stop 100

# Zu Snapshot vor Upgrade zurücksetzen:
qm snapshot 100 pre-upgrade-production-20251030-220000 --rollback

# VM starten:
qm start 100

# Gitea sollte in alter Version laufen
```

#### Option 3: Datenbankversion manuell zurücksetzen (VORSICHT!)

```bash
# NUR als letztes Resort!
# Kann zu Datenverlust führen!

su - git

# PostgreSQL:
psql -U gitea -d gitea_db
UPDATE version SET version=299 WHERE id=1;
\q

# Gitea mit alter Binary starten:
systemctl start gitea

# Schnellstmöglich verifizieren und vollständiges Restore durchführen!
```

---

## Checkliste für erfolgreiche Upgrades

Vor Upgrade:
- [ ] Changelog gelesen und breaking changes überprüft
- [ ] Admin-Seite auf deprecated Optionen geprüft
- [ ] Proxmox Snapshot erstellt
- [ ] Gitea Dump erstellt und extern gespeichert
- [ ] Datenbank-Backup erstellt
- [ ] Benutzer informiert
- [ ] Test-Upgrade durchgeführt

Upgrade:
- [ ] Production Snapshot erstellt
- [ ] Gitea Service gestoppt
- [ ] Finale Sicherung erstellt
- [ ] Neue Binary heruntergeladen
- [ ] Binary ausgetauscht
- [ ] Gitea Service gestartet
- [ ] Datenbankmigration abgewartet

Nach Upgrade:
- [ ] Service läuft (systemctl status gitea)
- [ ] Web-UI erreichbar
- [ ] Repos vorhanden und klonbar
- [ ] SSH funktioniert
- [ ] Custom Templates/Themes OK
- [ ] Admin-Checks durchgeführt
- [ ] Benutzer benachrichtigt

---

## Häufig gestellte Fragen

**F: Wie lange dauert das Upgrade?**
A: 5-30 Minuten für Datenbankmigrationen, abhängig von Repositoriy-Anzahl und Datenbankgröße.

**F: Gibt es Downtime?**
A: Ja, Gitea ist während Datenbankmigrationen offline (~5-30 Min).

**F: Kann ich von 1.18 direkt zu 1.24 upgraden?**
A: Ja, Sie können zwischen beliebigen Versionen upgraden. Gitea führt alle Migrationen automatisch durch.

**F: Was, wenn das Upgrade fehlschlägt?**
A: Nutzen Sie einen Proxmox Snapshot oder das Backup zum Rückgängigmachen.

**F: Muss ich SSH-Keys neu setzen?**
A: Nein, aber SSH-Hooks sollten regeneriert werden: `gitea admin regenerate hooks`

---

## Zusammenfassung

Ein sicheres Gitea-Upgrade erfordert:

1. **Vorbereitung:** Changelog lesen, Konfiguration prüfen, Benutzer informieren
2. **Sicherung:** Proxmox Snapshot + Gitea Dump + Datenbankbackup
3. **Testing:** Test-Upgrade in separater VM durchführen
4. **Execution:** Service stoppen → Binary ersetzen → Service starten
5. **Validation:** Datenbankmigrationen abwarten, Funktionalität prüfen
6. **Recovery:** Rollback vorbereitet für Fall der Fälle

Dieser Prozess schützt Sie vor Datenverlusten und ermöglicht schnelle Wiederherstellung bei Problemen.