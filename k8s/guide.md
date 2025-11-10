# Lokales Kubernetes-Cluster aufbauen: Detaillierte Schritt-für-Schritt-Anleitung (Windows 11)

Eine vollständige Anleitung zum Aufbau eines lokalen Kubernetes-Clusters mit Kind, kubectl, K9s und Headlamp unter Windows 11. Das Cluster wird mit 1 Control Plane Node und 3 Worker Nodes konfiguriert.

---

## Inhaltsverzeichnis

1. [Voraussetzungen](#voraussetzungen)
2. [Tool-Übersicht: Was brauchen wir und warum?](#tool-übersicht-was-brauchen-wir-und-warum)
3. [Kind, kubectl und K9s in PATH integrieren](#kind-kubectl-und-k9s-in-path-integrieren)
4. [Headlamp installieren](#headlamp-installieren)
5. [Kubernetes-Cluster mit Kind erstellen](#kubernetes-cluster-mit-kind-erstellen)
6. [K9s installieren und konfigurieren](#k9s-installieren-und-konfigurieren)
7. [Headlamp im Browser starten](#headlamp-im-browser-starten)
8. [Cluster-Verifikation](#cluster-verifikation)
9. [Häufig verwendete Befehle](#häufig-verwendete-befehle)

---

## Voraussetzungen

Bevor du startest, benötigst du:

- **Windows 11** (was du bereits hast)
- **Docker Desktop** oder ein gleichwertiges Docker-System (Kind benötigt Docker zum Ausführen der Kubernetes-Nodes als Container)
- **Die exe-Dateien**: `kind.exe`, `kubectl.exe` und `k9s.exe` (die du bereits besitzt)
- Administratorrechte auf deinem System
- PowerShell oder Windows Terminal
- Mindestens 4 GB RAM verfügbar (besser 8 GB für 4 Nodes)
- Mindestens 20 GB freier Festplattenspeicher

### Docker überprüfen

Starte Docker Desktop und vergewissere dich, dass es läuft. Öffne PowerShell und führe diese Befehle aus:

```powershell
docker --version
docker run hello-world
```

Beide Befehle sollten ohne Fehler ausgeführt werden.

---

## Tool-Übersicht: Was brauchen wir und warum?

### Kind (Kubernetes in Docker)

**Was ist Kind?**
Kind ist ein minimales Kubernetes-Cluster-Setup, das Kubernetes-Nodes als Docker-Container ausführt. Statt eine vollständige VM hochzufahren, werden die Nodes als Container bereitgestellt – ideal für lokale Entwicklung.

**Warum brauchen wir es?**
- Ermöglicht es uns, ein vollständiges Multi-Node-Cluster lokal zu erstellen
- Einfach zu installieren und zu konfigurieren
- Benötigt weniger Ressourcen als Minikube oder VMs
- Unterstützt YAML-Konfiguration für präzise Node-Topologien

**Was werden wir damit machen?**
1. Die `kind.exe` in den PATH integrieren, damit sie überall in PowerShell aufrufbar ist
2. Eine YAML-Konfigurationsdatei erstellen, die die Cluster-Topologie definiert (1 Control Plane + 3 Worker Nodes)
3. Das Cluster damit hochfahren

---

### kubectl (Kubernetes Command Line Tool)

**Was ist kubectl?**
kubectl ist die Kommandozeilen-Schnittstelle für Kubernetes. Sie ist das primäre Werkzeug, um mit Clustern zu kommunizieren.

**Warum brauchen wir es?**
- Alle Kubernetes-Operationen (Pod-Management, Deployments, Services, etc.) laufen über kubectl
- K9s und andere Tools bauen auf kubectl auf
- Es ist der Standard für Kubernetes-Verwaltung

**Was werden wir damit machen?**
1. Die `kubectl.exe` in den PATH integrieren, damit sie überall in PowerShell aufrufbar ist
2. kubectl mit dem Kind-Cluster verbinden
3. Cluster-Status überprüfen und erste Befehle ausführen

---

### K9s (Terminal UI für Kubernetes)

**Was ist K9s?**
K9s ist eine Terminal-basierte Benutzeroberfläche für Kubernetes. Es bietet ein interaktives, echtzeit-Dashboard direkt in der PowerShell mit Navigations- und Bearbeitungsfunktionen.

**Warum brauchen wir es?**
- Viel schneller und übersichtlicher als kubectl für Debugging und Überwachung
- Ermöglicht Echtzeit-Ansicht von Pods, Nodes, Services und deren Status
- Interaktives Interface mit Suche, Filtering und Inline-Editing
- Zeigt automatisch Fehler und Logs von Containern

**Was werden wir damit machen?**
1. Die `k9s.exe` in den PATH integrieren, damit sie überall in PowerShell aufrufbar ist
2. Mit dem Kind-Cluster verbinden
3. Cluster-Ressourcen visualisieren und debuggen

---

### Headlamp (Web-basiertes Kubernetes-Dashboard)

**Was ist Headlamp?**
Headlamp ist ein Web-basiertes Kubernetes-Dashboard mit Grafischer Benutzeroberfläche im Browser. Es bietet eine übersichtliche Darstellung aller Cluster-Ressourcen.

**Warum brauchen wir es?**
- Graphische Alternative zu Kommandozeilen-Tools
- Gut für visuelle Überwachung und Verwaltung
- Ermöglicht Zugriff aus jedem Browser heraus
- Unterstützt RBAC-Kontrolle und Multi-Cluster-Management

**Was werden wir damit machen?**
1. Headlamp als Desktop-Anwendung installieren
2. Mit dem Kind-Cluster verbinden
3. Im Browser auf das Dashboard zugreifen

---

## Kind, kubectl und K9s in PATH integrieren

Dies ist ein wichtiger Schritt, damit du die Tools überall in PowerShell aufrufen kannst, ohne den vollständigen Pfad eingeben zu müssen.

### Schritt 1: Verzeichnisse für die Tools erstellen

Öffne PowerShell **als Administrator** und führe folgende Befehle aus:

```powershell
# Verzeichnisse erstellen für die Tools
New-Item -ItemType Directory -Path "C:\Tools\kubernetes" -Force
New-Item -ItemType Directory -Path "C:\Tools\kubernetes\kind" -Force
New-Item -ItemType Directory -Path "C:\Tools\kubernetes\kubectl" -Force
New-Item -ItemType Directory -Path "C:\Tools\kubernetes\k9s" -Force
```

Diese Befehle erstellen drei Ordner: `C:\Tools\kubernetes\kind`, `C:\Tools\kubernetes\kubectl` und `C:\Tools\kubernetes\k9s`.

---

### Schritt 2: exe-Dateien verschieben

Du hast bereits die exe-Dateien. Kopiere sie in die entsprechenden Verzeichnisse:

**Methode A: Mit PowerShell (als Administrator)**

Gehe zunächst in das Verzeichnis, wo deine exe-Dateien liegen. Beispiel: Falls sie im Downloads-Ordner sind:

```powershell
cd C:\Users\[DeinBenutzername]\Downloads
```

Dann kopiere die Dateien:

```powershell
# kind.exe kopieren
Copy-Item -Path ".\kind.exe" -Destination "C:\Tools\kubernetes\kind\kind.exe"

# kubectl.exe kopieren
Copy-Item -Path ".\kubectl.exe" -Destination "C:\Tools\kubernetes\kubectl\kubectl.exe"

# k9s.exe kopieren
Copy-Item -Path ".\k9s.exe" -Destination "C:\Tools\kubernetes\k9s\k9s.exe"
```

**Methode B: Mit Windows Explorer (manuell)**

1. Öffne den Windows Explorer
2. Navigiere zu deinem Downloads-Ordner (oder wo die exe-Dateien sind)
3. Kopiere `kind.exe` in `C:\Tools\kubernetes\kind\`
4. Kopiere `kubectl.exe` in `C:\Tools\kubernetes\kubectl\`
5. Kopiere `k9s.exe` in `C:\Tools\kubernetes\k9s\`

---

### Schritt 3: Verzeichnisse zum Windows PATH hinzufügen

Dies ist der kritische Schritt, damit du die Tools überall aufrufen kannst.

**Wichtig:** Du musst dies als Administrator durchführen!

In PowerShell (als Administrator) führe folgende Befehle aus:

```powershell
# KIND zum PATH hinzufügen
[System.Environment]::SetEnvironmentVariable(
    "Path",
    $env:Path + ";C:\Tools\kubernetes\kind",
    [System.EnvironmentVariableTarget]::User
)

# KUBECTL zum PATH hinzufügen
[System.Environment]::SetEnvironmentVariable(
    "Path",
    $env:Path + ";C:\Tools\kubernetes\kubectl",
    [System.EnvironmentVariableTarget]::User
)

# K9S zum PATH hinzufügen
[System.Environment]::SetEnvironmentVariable(
    "Path",
    $env:Path + ";C:\Tools\kubernetes\k9s",
    [System.EnvironmentVariableTarget]::User
)
```

Nach diesen Befehlen sollte die PowerShell-Ausgabe ähnlich aussehen:

```
Success!
Success!
Success!
```

---

### Schritt 4: PATH-Integration überprüfen

**Schließe PowerShell vollständig!** (Das ist wichtig, denn die neue PATH-Konfiguration wird erst von neuen PowerShell-Instanzen geladen)

Öffne dann eine **NEUE** PowerShell-Instanz (nicht als Administrator nötig) und führe aus:

```powershell
kind version
kubectl version --client
k9s version
```

Du solltest jeweils die Versionsnummern sehen. Falls das funktioniert, herzlichen Glückwunsch – die PATH-Integration war erfolgreich!

**Beispielausgabe:**

```
kind version 0.20.0
Client Version: v1.28.0
k9s version 0.32.0
```

Falls einer dieser Befehle nicht funktioniert und du einen Fehler wie `Der Begriff 'kind' ist nicht als Name eines Cmdlet, einer Funktion, eines Skriptdateien oder eines ausführbaren Programms erkannt worden` erhältst:

1. Überprüfe, dass die exe-Dateien wirklich in den richtigen Verzeichnissen sind
2. Starte deinen Computer neu (manchmal hilft das bei PATH-Problemen)
3. Öffne PowerShell erneut und versuche es nochmal

---

## Headlamp installieren

### Schritt 1: Headlamp herunterladen

1. Besuche die Headlamp-Release-Seite: https://github.com/kinvolk/headlamp/releases
2. Suche die neueste Version mit dem Namen `Headlamp-Setup-X.X.X.exe` (z.B. `Headlamp-Setup-1.6.0.exe`)
3. Klicke auf die Datei zum Herunterladen

---

### Schritt 2: Headlamp installieren

1. Öffne dein Downloads-Verzeichnis
2. Doppelklick auf `Headlamp-Setup-X.X.X.exe`
3. Folge dem Installationsassistenten:
   - Akzeptiere die Lizenzbedingungen
   - Wähle das Installationsverzeichnis (Standard ist empfohlen)
   - Klicke auf „Install"
4. Nach der Installation wird Headlamp möglicherweise automatisch gestartet

---

### Schritt 3: Headlamp zum Startmenü hinzufügen (Optional, aber empfohlen)

Nach der Installation findest du Headlamp unter:

- **Windows Startmenü** → Suche nach „Headlamp"
- Klicke auf die App, um sie zu starten
- Alternativ: Überprüfe, ob ein Desktop-Shortcut erstellt wurde

---

## Kubernetes-Cluster mit Kind erstellen

### Schritt 1: Cluster-Konfigurationsdatei erstellen

Du benötigst eine YAML-Konfigurationsdatei, die Kind mitteilt, wie viele Nodes es erstellen soll.

**Erstelle einen Ordner für dein Kubernetes-Projekt:**

Öffne PowerShell und führe aus (oder erstelle den Ordner manuell):

```powershell
New-Item -ItemType Directory -Path "C:\Kubernetes-Homelab" -Force
cd C:\Kubernetes-Homelab
```

**Erstelle die Konfigurationsdatei:**

Öffne einen Text-Editor (z.B. Notepad, VS Code oder PowerShell ISE) und erstelle eine neue Datei. Speichere sie mit dem Namen `kind-cluster-config.yaml` im Ordner `C:\Kubernetes-Homelab`.

Kopiere diesen Inhalt in die Datei:

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: homelab-cluster
nodes:
  # Control Plane Node
  - role: control-plane
    image: kindest/node:v1.28.0
    extraPortMappings:
      - containerPort: 80
        hostPort: 80
      - containerPort: 443
        hostPort: 443
  # Worker Node 1
  - role: worker
    image: kindest/node:v1.28.0
  # Worker Node 2
  - role: worker
    image: kindest/node:v1.28.0
  # Worker Node 3
  - role: worker
    image: kindest/node:v1.28.0
```

**Erklärung der Konfiguration:**

- `kind: Cluster` = Dies ist eine Kind-Cluster-Konfiguration
- `name: homelab-cluster` = Cluster-Name (frei wählbar)
- `nodes:` = Definition der Nodes
- `role: control-plane` = Dies ist der Control Plane Node (das „Gehirn" des Clusters)
- `role: worker` = Dies sind Worker Nodes (führen Container aus)
- `image: kindest/node:v1.28.0` = Kubernetes-Version (hier 1.28.0; du kannst eine neuere nutzen, wenn verfügbar)
- `extraPortMappings` = Portweiterleitung von Container zu Host (für später, wenn du Services exposest)

**Speichere die Datei!**

---

### Schritt 2: Kind-Cluster starten

Öffne PowerShell (normal, nicht als Administrator) und navigiere in dein Projekt-Verzeichnis:

```powershell
cd C:\Kubernetes-Homelab
```

Starte dann das Cluster mit diesem Befehl:

```powershell
kind create cluster --config kind-cluster-config.yaml
```

**Was passiert jetzt?**

1. Kind lädt die Kubernetes-Images herunter (beim ersten Mal dauert das ca. 5-10 Minuten, abhängig von deiner Internetgeschwindigkeit)
2. Es erstellt 4 Docker-Container (1 Control Plane + 3 Worker Nodes)
3. Diese Container werden als Kubernetes-Nodes konfiguriert
4. Das Cluster wird initialisiert und ist dann betriebsbereit

**Die Ausgabe sollte ungefähr so aussehen:**

```
enabling experimental podman provider
Creating cluster "homelab-cluster" ...
 ✓ Ensuring node image (kindest/node:v1.28.0) 🖼
 ✓ Preparing nodes (capacity: 1c, memory: 1100Mi, disk: 20GiB) 📦
 ✓ Writing configuration 📜
 ✓ Starting control-plane 🕐
 ✓ Installing CNI 🔌
 ✓ Installing StorageClass 💾
 ✓ Joining worker nodes 🚚
Set kubectl context to "kind-homelab-cluster"
You can now use your cluster with:

kubectl cluster-info --context kind-homelab-cluster

Have a nice day! 👋
```

**Wenn du diese Meldung siehst, ist dein Cluster erfolgreich erstellt!**

---

### Schritt 3: Cluster-Verbindung überprüfen

Nach erfolgreichem Start wird die kubeconfig automatisch in `C:\Users\[DeinBenutzername]\.kube\config` gespeichert, und kubectl konfiguriert sich selbst.

Überprüfe, ob alles funktioniert:

```powershell
kubectl cluster-info
```

Du solltest etwa diese Ausgabe sehen:

```
Kubernetes control plane is running at https://127.0.0.1:xxxxx
CoreDNS is running at https://127.0.0.1:xxxxx/api/v1/namespaces/kube-system/services/coredns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
```

---

### Schritt 4: Nodes überprüfen

```powershell
kubectl get nodes
```

Du solltest 4 Nodes sehen (1 Control Plane + 3 Worker):

```
NAME                          STATUS   ROLES           AGE   VERSION
homelab-cluster-control-plane   Ready    control-plane   2m    v1.28.0
homelab-cluster-worker          Ready    <none>          2m    v1.28.0
homelab-cluster-worker2         Ready    <none>          2m    v1.28.0
homelab-cluster-worker3         Ready    <none>          2m    v1.28.0
```

**Alle sollten `Ready` Status haben!**

Falls ein Node noch `NotReady` ist, warte 1-2 Minuten und führe den Befehl erneut aus.

---

### Schritt 5: Pods überprüfen

```powershell
kubectl get pods --all-namespaces
```

Du solltest verschiedene System-Pods sehen (coredns, etcd, kube-apiserver, etc.). Dies ist normal und zeigt, dass die Kubernetes-Systemkomponenten laufen.

---

## K9s installieren und konfigurieren

Nachdem Kind installiert und das Cluster läuft, kannst du K9s nutzen.

### Schritt 1: K9s starten

Öffne PowerShell und führe aus:

```powershell
k9s
```

### Schritt 2: K9s verbindet sich mit dem Cluster

K9s erkennt automatisch die kubeconfig in `C:\Users\[DeinBenutzername]\.kube\config` und verbindet sich mit dem gerade erstellten Kind-Cluster. Du solltest ein Terminal-Dashboard sehen mit:

- Oben: Cluster-Info und aktiver Context
- Links: Navigation zwischen verschiedenen Ressourcentypen (Pods, Nodes, Services, etc.)
- Mitte: Liste der Pods/Resources des ausgewählten Typs

**Beispiel K9s Dashboard:**

```
 ___  .____     _____
|_  ||_  |  _ |_   _|   TUI for Kubernetes
  | | | | | | | | |       v0.32.0
 _| |_| | |_| | | |       © 2025 Derailed
|_____||_|\__,_| |_|       Licensed under Apache License 2.0

🐶 homelab-cluster                                                               default|All [0/0]
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ NAME     READY   STATUS   RESTARTS   AGE   IP         NODE                 NOMINATED   TAINT
│ ...
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Schritt 3: Navigation in K9s

**Häufige Tastenkombinationen:**

- `:pods` = Zu Pods navigieren (eingeben und Enter drücken)
- `:nodes` = Zu Nodes navigieren
- `:svc` = Zu Services navigieren
- `:logs` = Logs des ausgewählten Pods anzeigen (oder `l` auf einem Pod drücken)
- `?` = Hilfe anzeigen
- `q` = K9s beenden
- `/` = Suche/Filter aktivieren (z.B. `/coredns` um nach coredns zu filtern)
- `d` = Resource löschen (vorsichtig!)
- `e` = Resource bearbeiten (YAML-Editor)
- `Ctrl+D` = Details des ausgewählten Items anzeigen

---

### Schritt 4: Erstes K9s-Abenteuer

1. Starte K9s: `k9s`
2. Du landest automatisch bei den Pods im Default-Namespace
3. Navigiere zu System-Pods: Tippe `:pods` → Enter → Tippe `/coredns` → Enter
4. Wähle einen coredns-Pod aus und drücke `l`, um die Logs zu sehen
5. Drücke `q`, um zurückzugehen
6. Tippe `:nodes` → Enter, um alle Nodes zu sehen
7. Drücke nochmal `q` um K9s zu beenden

---

## Headlamp im Browser starten

### Schritt 1: Headlamp Desktop App starten

Nach der Installation findest du Headlamp in deinen Windows-Anwendungen:

- **Windows Startmenü** → Suche nach „Headlamp"
- Klicke auf die App, um sie zu starten
- Oder: Doppelklick auf den Desktop-Shortcut (falls vorhanden)

Die Headlamp-Anwendung startet und öffnet einen lokalen Web-Server im Hintergrund.

---

### Schritt 2: Cluster hinzufügen (beim ersten Start)

Beim ersten Start von Headlamp wirst du gefragt, welches Cluster du verwenden möchtest:

1. Es sollte eine Popup-Seite oder ein Dialog-Fenster erscheinen
2. Headlamp erkennt automatisch die kubeconfig in `C:\Users\[DeinBenutzername]\.kube\config`
3. Es sollte `homelab-cluster` (oder `kind-homelab-cluster`) in der Liste auftauchen
4. Wähle es aus und bestätige die Verbindung

Falls Headlamp das Cluster nicht automatisch findet:

1. Klicke auf „Add Cluster" oder „New Cluster"
2. Wähle als Verbindungstyp „Local kubeconfig"
3. Navigiere zu `C:\Users\[DeinBenutzername]\.kube\config`
4. Wähle die Datei aus und bestätige

---

### Schritt 3: Headlamp im Browser öffnen

Die Headlamp Desktop App lädt einen lokalen Web-Server. Normalerweise öffnet sich der Browser automatisch. Falls nicht:

1. Öffne deinen Browser (Chrome, Firefox, Safari, Edge)
2. Navigiere zu: `http://localhost:6644` oder `http://localhost:3000`
3. Du solltest das Headlamp-Dashboard sehen

Falls port 6644 nicht funktioniert, versuche:
- `http://localhost:3000`
- `http://127.0.0.1:6644`

---

### Schritt 4: Dashboard erkunden

Im Headlamp-Dashboard kannst du:

- **Cluster-Übersicht** sehen (Nodes, Pods, Deployments auf einen Blick)
- **Nodes** sehen und deren Status überprüfen (CPU, Memory, Status)
- **Pods** in verschiedenen Namespaces verwalten (erstellen, löschen, neu starten)
- **Deployments** erstellen und verwalten
- **Services** und deren Endpoints anzeigen
- **Logs** von Pods anzeigen und durchsuchen
- **YAML-Manifeste** direkt im Browser bearbeiten
- **Multi-Cluster-Management** (falls mehrere Cluster konfiguriert)

Das Dashboard ist sehr intuitiv – einfach durch die verschiedenen Menüpunkte klicken und erkunden!

---

## Cluster-Verifikation

Nachdem alles installiert und konfiguriert ist, überprüfe dein Setup vollständig:

### Mit kubectl (PowerShell)

```powershell
# Cluster-Info
kubectl cluster-info

# Nodes anzeigen mit detaillierten Infos
kubectl get nodes -o wide

# Alle Pods in allen Namespaces
kubectl get pods --all-namespaces

# Detaillierte Node-Informationen
kubectl describe nodes

# System-Komponenten-Status überprüfen
kubectl get componentstatus

# Aktiven Kontext anzeigen
kubectl config current-context

# Alle verfügbaren Kontexte anzeigen
kubectl config get-contexts
```

### Mit K9s (Terminal UI)

```powershell
k9s
```

Navigiere durch die verschiedenen Ressourcentypen (Pods, Nodes, Services) und überprüfe, dass alles grün/Ready ist.

### Mit Headlamp (Web Browser)

Öffne `http://localhost:6644` im Browser und:

1. Überprüfe die Cluster-Übersicht (sollten 4 Nodes angezeigt werden)
2. Navigiere zu „Nodes" und überprüfe, dass alle `Ready` sind
3. Navigiere zu „Workloads" → „Pods" und überprüfe die System-Pods

---

## Häufig verwendete Befehle

### kubectl (Befehlszeile - PowerShell)

```powershell
# Cluster-Status
kubectl cluster-info
kubectl get componentstatus

# Nodes verwalten
kubectl get nodes
kubectl get nodes -o wide
kubectl describe node <node-name>

# Pods verwalten
kubectl get pods
kubectl get pods -n kube-system
kubectl get pods --all-namespaces
kubectl describe pod <pod-name>
kubectl logs <pod-name>
kubectl exec -it <pod-name> -- powershell

# Deployments
kubectl create deployment test-app --image=nginx
kubectl get deployments
kubectl delete deployment <deployment-name>

# Services
kubectl expose deployment test-app --port=80 --type=LoadBalancer
kubectl get services
kubectl delete service <service-name>

# Kontext-Management
kubectl config current-context
kubectl config get-contexts
kubectl config use-context <context-name>

# Manifeste anwenden/löschen
kubectl apply -f manifest.yaml
kubectl delete -f manifest.yaml

# Output-Formate
kubectl get nodes -o json
kubectl get nodes -o yaml
kubectl get pods -o wide
```

### K9s (Terminal UI)

```powershell
# K9s starten
k9s

# Mit spezifischem Kontext starten
k9s --context kind-homelab-cluster

# Mit spezifischem Namespace
k9s --namespace kube-system

# Im Read-Only-Modus starten
k9s --readonly

# Version überprüfen
k9s version

# Hilfe anzeigen
k9s -h
```

### K9s Shortcuts in der UI

```
:pods             -> Pods anzeigen
:nodes            -> Nodes anzeigen
:svc              -> Services anzeigen
:deploy           -> Deployments anzeigen
:logs             -> Logs anzeigen (oder 'l' auf Pod)
?                 -> Hilfe
q                 -> Zurück/Beenden
/                 -> Suchen/Filtern
d                 -> Löschen
e                 -> Bearbeiten
Ctrl+D            -> Details
```

### Kind (Cluster-Management)

```powershell
# Cluster erstellen
kind create cluster --config kind-cluster-config.yaml

# Cluster-Liste anzeigen
kind get clusters

# Kubeconfig exportieren
kind get kubeconfig --name homelab-cluster

# Cluster löschen
kind delete cluster --name homelab-cluster

# Kind-Version überprüfen
kind version

# Logs eines Nodes ansehen
kind export logs --name homelab-cluster
```

---

## Troubleshooting

### Problem: kubectl/kind/k9s funktioniert nicht nach PATH-Integration

**Lösung:**
1. Schließe PowerShell vollständig (alle Fenster)
2. Öffne eine NEUE PowerShell-Instanz
3. Versuche erneut: `kind version` / `kubectl version --client` / `k9s version`
4. Falls weiterhin Fehler: Überprüfe ob die exe-Dateien wirklich in den richtigen Verzeichnissen sind

**Überprüfung:**
```powershell
# Überprüfe die PATH-Variable
$env:Path

# Diese Verzeichnisse sollten dort auftauchen:
# C:\Tools\kubernetes\kind
# C:\Tools\kubernetes\kubectl
# C:\Tools\kubernetes\k9s
```

Falls die Verzeichnisse fehlen, führe die PATH-Integration erneut durch.

---

### Problem: Kind-Cluster startet nicht

**Symptom:** Fehlermeldung bei `kind create cluster`

**Lösungen:**
1. Überprüfe, dass Docker läuft:
```powershell
docker version
docker ps
```

2. Falls Docker nicht läuft, starte Docker Desktop

3. Überprüfe, dass genug Festplattenspeicher vorhanden ist (mindestens 20 GB)

4. Löschen eines fehlgeschlagenen Clusters und neu starten:
```powershell
kind delete cluster --name homelab-cluster
kind create cluster --config kind-cluster-config.yaml
```

5. Falls Fehler mit Port 6443 (Kubernetes API):
   - Überprüfe ob der Port bereits belegt ist
   - Oder ändere den API-Port in der YAML-Datei: `apiServerPort: 6443` zu `apiServerPort: 6444`

---

### Problem: K9s zeigt „No clusters available" oder verbindet sich nicht

**Lösung:**
1. Überprüfe, dass das Kind-Cluster läuft:
```powershell
kind get clusters
kubectl get nodes
```

2. Falls das Cluster nicht läuft, starte es:
```powershell
kind create cluster --config kind-cluster-config.yaml
```

3. Überprüfe die kubeconfig-Datei:
```powershell
# Überprüfe ob die Datei existiert
Test-Path C:\Users\$env:USERNAME\.kube\config

# Falls nicht, erstelle sie durch Cluster-Neustart
kind delete cluster --name homelab-cluster
kind create cluster --config kind-cluster-config.yaml
```

4. Starte K9s mit expliziter Kubeconfig:
```powershell
k9s --kubeconfig $env:USERPROFILE\.kube\config
```

---

### Problem: Headlamp verbindet sich nicht zum Cluster

**Symptom:** Headlamp lädt, aber zeigt keine Ressourcen oder gibt Verbindungsfehler

**Lösung:**
1. Stelle sicher, dass das Kind-Cluster läuft:
```powershell
kind get clusters
kubectl get nodes
```

2. Überprüfe, dass Headlamp läuft (die Desktop-App sollte sichtbar sein)

3. Versuche diese Browser-URLs nacheinander:
   - `http://localhost:6644`
   - `http://127.0.0.1:6644`
   - `http://localhost:3000`
   - `http://127.0.0.1:3000`

4. Falls immer noch nicht funktioniert, starte Headlamp neu:
   - Schließe die Headlamp Desktop-App (vollständig, auch der Taskbar-Eintrag)
   - Starte Headlamp erneut

5. Falls Port besetzt ist, versuche einen anderen Port in der Headlamp-Konfiguration

---

### Problem: Nodes sind im Status „NotReady"

**Symptom:** `kubectl get nodes` zeigt Nodes mit Status `NotReady`

**Lösung:**
1. Das ist oft normal direkt nach dem Cluster-Start. Warte 1-2 Minuten
2. Überprüfe den Status erneut:
```powershell
kubectl get nodes
```

3. Für detailliertere Informationen:
```powershell
kubectl describe node <node-name>
```

4. Falls nach 5 Minuten immer noch NotReady:
   - Starte das Cluster neu:
```powershell
kind delete cluster --name homelab-cluster
kind create cluster --config kind-cluster-config.yaml
```

---

### Problem: Docker benötigt zu viel Speicher oder CPU

**Symptom:** Computer wird langsam, wenn das Cluster läuft

**Lösung:**
1. Überprüfe die Docker Desktop-Ressourcen:
   - Docker Desktop öffnen → Settings → Resources
   - Reduziere „CPUs" und „Memory" auf deine Bedürfnisse (z.B. 4 CPUs, 4 GB RAM statt mehr)
   
2. Falls weiterhin Probleme: Reduziere die Anzahl der Worker Nodes von 3 auf 2 in der `kind-cluster-config.yaml`

---

## Nächste Schritte

Nach erfolgreichem Setup kannst du:

1. **Test-Deployments** erstellen (z.B. mit `kubectl create deployment nginx --image=nginx`)
2. **Services** exponieren und auf sie zugreifen
3. **Eigene Anwendungen** in Containern deployen
4. **Monitoring** einrichten (später mit CheckMK)
5. **GitOps-Workflows** aufbauen (später mit ArgoCD und Crossplane)

---

## Hilfreiche Ressourcen

- **Kind Dokumentation**: https://kind.sigs.k8s.io/
- **kubectl Dokumentation**: https://kubernetes.io/docs/reference/kubectl/
- **K9s Dokumentation**: https://k9scli.io/
- **Headlamp Dokumentation**: https://headlamp.dev/
- **Kubernetes Offiziell**: https://kubernetes.io/docs/

---

**Gratulationen! Du hast ein vollständiges lokales Kubernetes-Cluster mit 1 Control Plane und 3 Worker Nodes unter Windows 11 erstellt! 🎉**
