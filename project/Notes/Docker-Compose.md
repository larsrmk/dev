# PowerShell commands PGAdmin

#### Verzeichnis
```
cd D:\dev\notebook
```
---
#### Container starten
```plain Text
docker compose up -d
```
---
#### Container stoppen
```
docker compose down
```
---
#### Laufenden Services auflisten
```
docker compose ps
```
---
#### Verbindung zur Datenbank prüfen
```
docker exec -it pgadmin ping postgres_db
```
---
#### Logs PGAdmin
```
docker compose logs pgadmin
```
---
#### LOGS PostgresDB
```
docker compose logs postgres_db
```
---
#### Docker Compose Version anzeigen
```
docker-compose version
```
```
docker info
```
```

```