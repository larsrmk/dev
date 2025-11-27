Die bisherige Anleitung war ja schon ganz gut. Allerdings bleibt der Sync-Status auf Unknown Master und folgende Fehlermeldung bleibt trotzdem gleich:
ComparisonError:
Failed to load target state: failed to generate manifest for source 1 of 1: rpc error: code = Unknown desc = failed to list refs: error creating SSH agent: "SSH agent requested but SSH_AUTH_SOCK not-specified"
Versuchen wir es nochmal von Anfang an. Aber diesmal ein bisschen weniger in der CLI sondern mehr in VS Code wenn es estwas gibt. Ich habe in der ArgoCD Doku ein paar Sachen gefunden, die wichtig und interessant sein könnten. Hier die folgenden Links:
https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/#repositories
https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/#applications
https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/#helm
Schau dir bitte die Links an. Wenn möglich würde ich gerne solche sachen wie die ConfigMap, die wir bisher nur über die CLI erstellt oder die Credentials optisch sehen und wissen was wir da genau machen. Eigentlich von allem wo es möglich ist. Das Ziel bleibt das Gleiche und die Gegebenheiten auch. Erstelle also wieder eine Anleitung mit den selben Rahmenbedingungen wie davor auch. Ich will weiterhin bei SSH bleiben.
