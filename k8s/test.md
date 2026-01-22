HELM PLATFORM CHART - ALLE DATEIEN

================================================================================
DATEI 1: Chart.yaml
================================================================================

apiVersion: v2
name: platform
description: "Platform Helm Chart für ArgoCD-basierte Multi-App-Deployment"
type: application
version: 1.0.0
appVersion: "1.0"
keywords:
  - platform
  - argocd
  - gitops
maintainers:
  - name: Infrastructure Team
    email: admin@example.com


================================================================================
DATEI 2: values.yaml
================================================================================

# Platform Helm Chart Configuration
# Definiert, welche Helm Charts aus dem Apps-Ordner deployed werden

# GitOps Repository
gitea:
  url: "http://gitea.gitea:3000"  # Anpassen an deine Gitea-Instanz
  org: "infrastructure"             # Organization in Gitea
  repo: "platform-config"           # Repository Name
  branch: "main"                    # Branch

# ArgoCD Namespace (wo die ApplicationSet deployed wird)
argocd:
  namespace: "argocd"

# Zielnamespaces (werden automatisch erstellt)
namespaces:
  - platform-apps
  - monitoring
  - ingress
  - storage

# Apps die deployed werden
apps:
  # Beispiel App 1
  - name: "prometheus"
    namespace: "monitoring"
    enabled: true
    gitPath: "apps/prometheus"     # Pfad im Repo relativ zu Apps-Ordner
    valuesOverride:
      persistence:
        enabled: true
        size: "10Gi"

  # Beispiel App 2
  - name: "nginx-ingress"
    namespace: "ingress"
    enabled: true
    gitPath: "apps/nginx-ingress"
    valuesOverride: {}

  # Beispiel App 3
  - name: "cert-manager"
    namespace: "cert-manager"
    enabled: true
    gitPath: "apps/cert-manager"
    valuesOverride:
      installCRDs: true

  # Beispiel App 4 (disabled)
  - name: "unused-app"
    namespace: "platform-apps"
    enabled: false
    gitPath: "apps/unused-app"
    valuesOverride: {}

# ServiceAccount für ArgoCD Permissions
serviceAccount:
  name: "platform-deployer"
  create: true

# RBAC
rbac:
  create: true


================================================================================
DATEI 3: templates/namespace.yaml
================================================================================

{{- range .Values.namespaces }}
---
apiVersion: v1
kind: Namespace
metadata:
  name: {{ . }}
  labels:
    managed-by: platform-helm
{{- end }}


================================================================================
DATEI 4: templates/serviceaccount.yaml
================================================================================

{{- if .Values.rbac.create }}
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ .Values.serviceAccount.name }}
  namespace: {{ .Values.argocd.namespace }}
  labels:
    app: platform
    version: {{ .Chart.Version }}
{{- end }}


================================================================================
DATEI 5: templates/clusterrole.yaml
================================================================================

{{- if .Values.rbac.create }}
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: {{ .Values.serviceAccount.name }}
  labels:
    app: platform
    version: {{ .Chart.Version }}
rules:
  # Permissions für alle Apps
  - apiGroups: [""]
    resources: ["services", "pods", "configmaps", "secrets", "persistentvolumeclaims"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  
  # Permissions für Deployments, StatefulSets, DaemonSets
  - apiGroups: ["apps"]
    resources: ["deployments", "statefulsets", "daemonsets", "replicasets"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  
  # Permissions für Ingress
  - apiGroups: ["networking.k8s.io"]
    resources: ["ingresses", "networkpolicies"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  
  # Permissions für RBAC
  - apiGroups: ["rbac.authorization.k8s.io"]
    resources: ["roles", "rolebindings"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  
  # Permissions für Certificates (cert-manager)
  - apiGroups: ["cert-manager.io"]
    resources: ["certificates", "certificaterequests", "issuers", "clusterissuers"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  
  # Permissions für ArgoCD Resources
  - apiGroups: ["argoproj.io"]
    resources: ["applications", "appprojects", "applicationsets"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  
  # Permissions für CRDs (Custom Resource Definitions)
  - apiGroups: ["apiextensions.k8s.io"]
    resources: ["customresourcedefinitions"]
    verbs: ["get", "list", "watch"]
  
  # Permissions für Namespaces
  - apiGroups: [""]
    resources: ["namespaces"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
  
  # Permissions für ServiceAccounts
  - apiGroups: [""]
    resources: ["serviceaccounts"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]

  # Permissions für Storage
  - apiGroups: ["storage.k8s.io"]
    resources: ["storageclasses"]
    verbs: ["get", "list", "watch"]

  # Permissions für Jobs, CronJobs
  - apiGroups: ["batch"]
    resources: ["jobs", "cronjobs"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]

{{- end }}


================================================================================
DATEI 6: templates/clusterrolebinding.yaml
================================================================================

{{- if .Values.rbac.create }}
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: {{ .Values.serviceAccount.name }}
  labels:
    app: platform
    version: {{ .Chart.Version }}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: {{ .Values.serviceAccount.name }}
subjects:
  - kind: ServiceAccount
    name: {{ .Values.serviceAccount.name }}
    namespace: {{ .Values.argocd.namespace }}
{{- end }}

{{- range .Values.namespaces }}
---
# Zusätzliche Namespace-spezifische RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: {{ include "platform.serviceAccountName" $ }}
  namespace: {{ . }}
  labels:
    app: platform
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: {{ $.Values.serviceAccount.name }}
subjects:
  - kind: ServiceAccount
    name: {{ $.Values.serviceAccount.name }}
    namespace: {{ $.Values.argocd.namespace }}
{{- end }}


================================================================================
DATEI 7: templates/applicationset.yaml
================================================================================

{{- $root := . }}
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: platform-apps
  namespace: {{ .Values.argocd.namespace }}
  labels:
    app.kubernetes.io/name: platform-apps
    app.kubernetes.io/version: {{ .Chart.Version }}
spec:
  generators:
    # Generator basierend auf enabled Apps in values.yaml
    - list:
        elements:
          {{- range .Values.apps }}
          {{- if .enabled }}
          - name: {{ .name }}
            namespace: {{ .namespace }}
            gitPath: {{ .gitPath }}
            valuesOverride: {{ .valuesOverride | toJson }}
          {{- end }}
          {{- end }}

  template:
    metadata:
      name: "{{ '{{' }} generator.list.name {{ '}}' }}"
      namespace: {{ .Values.argocd.namespace }}
    spec:
      project: default
      
      source:
        repoURL: "{{ .Values.gitea.url }}/{{ .Values.gitea.org }}/{{ .Values.gitea.repo }}"
        targetRevision: "{{ .Values.gitea.branch }}"
        path: "{{ '{{' }} generator.list.gitPath {{ '}}' }}"
        
        helm:
          releaseName: "{{ '{{' }} generator.list.name {{ '}}' }}"
          values: "{{ '{{' }} generator.list.valuesOverride {{ '}}' }}"
          
          # Falls Custom Values File existiert
          valueFiles:
            - "values.yaml"
            - "values-{{ '{{' }} generator.list.namespace {{ '}}' }}.yaml"  # Namespace-spezifische Values

      destination:
        server: "https://kubernetes.default.svc"
        namespace: "{{ '{{' }} generator.list.namespace {{ '}}' }}"

      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
          - PrunePropagationPolicy=foreground
          - RespectIgnoreDifferences=true

      # Health Assessment
      ignoreDifferences:
        - group: apps
          kind: Deployment
          jsonPointers:
            - /spec/replicas

{{- /*
WICHTIGE HINWEISE ZUM APPLICATIONSET:

1. **Generator**: Nur enabled Apps werden deployed (if .enabled)
2. **Repository**: Verweist auf deine selbst-gehostete Gitea-Instanz
3. **Path**: Nutzt den gitPath aus der App-Definition
4. **Values Override**: Wird beim Helm Deployment angewendet
5. **Automation**: Auto-Sync mit Pruning aktiviert
6. **Namespace**: Wird automatisch erstellt (CreateNamespace=true)
7. **ServiceAccount**: Nutzt den definierten Platform-ServiceAccount
*/ -}}


================================================================================
DATEI 8: templates/_helpers.tpl
================================================================================

{{/*
Expand the name of the chart.
*/}}
{{- define "platform.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "platform.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "platform.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "platform.labels" -}}
helm.sh/chart: {{ include "platform.chart" . }}
{{ include "platform.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "platform.selectorLabels" -}}
app.kubernetes.io/name: {{ include "platform.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "platform.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "platform.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}


================================================================================
DEPLOYMENT ANLEITUNG
================================================================================

## 1. Voraussetzungen
- Kubernetes Cluster läuft (Kind, k3s, etc.)
- ArgoCD ist installiert und läuft
- Gitea Repository existiert mit folgender Struktur:

infrastructure/platform-config/
├── apps/
│   ├── prometheus/
│   │   ├── Chart.yaml
│   │   └── values.yaml
│   ├── nginx-ingress/
│   │   ├── Chart.yaml
│   │   └── values.yaml
│   └── (weitere Apps)

## 2. Platform Helm Chart vorbereiten

mkdir -p meta-charts/platform/templates
# Alle Dateien (Chart.yaml, values.yaml, templates/*) in die Ordner kopieren

## 3. values.yaml anpassen

Folgende Parameter an deine Umgebung anpassen:
- gitea.url: Deine Gitea-URL
- gitea.org: Deine Organization in Gitea
- gitea.repo: Dein Repository Name
- gitea.branch: Branch (meist main)
- namespaces: Alle Zielnamespaces auflisten
- apps: Nur Apps hinzufügen, die deployed werden sollen

## 4. Platform Chart deployen

helm install platform meta-charts/platform/ \
  --namespace argocd \
  --values meta-charts/platform/values.yaml

## 5. Verifikation

# Prüfe ob ServiceAccount erstellt wurde
kubectl get sa -n argocd | grep platform-deployer

# Prüfe ob ClusterRole existiert
kubectl get clusterrole | grep platform-deployer

# Prüfe ob ApplicationSet erstellt wurde
kubectl get applicationset -n argocd

# Prüfe ob ArgoCD Applications erstellt wurden
kubectl get applications -n argocd

# Überprüfe den Sync Status
argocd app list

## 6. Troubleshooting

# Logs der ApplicationSet
kubectl describe applicationset platform-apps -n argocd

# Logs einer erstellten Application
kubectl describe application <app-name> -n argocd

# ArgoCD Logs
kubectl logs -n argocd deployment/argocd-application-controller -f

## 7. Apps hinzufügen/entfernen

1. values.yaml öffnen
2. Neue App in der `apps:` Liste hinzufügen oder entfernen
3. Platform Chart updaten:

helm upgrade platform meta-charts/platform/ \
  --namespace argocd \
  --values meta-charts/platform/values.yaml

ArgoCD wird automatisch neue Applications erstellen oder löschen.

================================================================================
