# 1. Konfiguration
$confluenceUrl = "https://DEINE_CONFLUENCE_URL/display/SPACE/SEITE"
$exportCssPath = "C:\Pfad\zu\deinem\Export\styles\site.css" # Die Datei wird überschrieben!

# 2. Lade den HTML-Quelltext der Seite herunter
$html = Invoke-WebRequest -Uri $confluenceUrl -UseBasicParsing

# 3. Suche alle <link rel="stylesheet"> Tags und extrahiere die href-Pfade
$cssLinks = $html.Content -split '<link' | 
    Where-Object { $_ -match 'rel="stylesheet"' -and $_ -match 'href="([^"]+)"' } | 
    ForEach-Object { $matches[1] }

# 4. Leere die vorhandene site.css im Export-Ordner
Clear-Content -Path $exportCssPath -ErrorAction SilentlyContinue

Write-Host "Lade CSS-Dateien herunter und bündele sie..."

# 5. Lade jedes CSS herunter und hänge es an die site.css an
foreach ($link in $cssLinks) {
    # Mache relative Links (die mit / anfangen) zu absoluten URLs
    if ($link -match "^/") {
        $baseUrl = ([System.Uri]$confluenceUrl).GetLeftPart('Authority')
        $fullUrl = $baseUrl + $link
    } else {
        $fullUrl = $link
    }
    
    try {
        # CSS herunterladen
        $cssContent = (Invoke-WebRequest -Uri $fullUrl -UseBasicParsing).Content
        
        # CSS an die site.css anhängen
        Add-Content -Path $exportCssPath -Value "/* --- Source: $link --- */"
        Add-Content -Path $exportCssPath -Value $cssContent
        Add-Content -Path $exportCssPath -Value ""
        
        Write-Host "Erfolgreich hinzugefügt: $link"
    } catch {
        Write-Host "Fehler beim Laden von: $fullUrl" -ForegroundColor Red
    }
}

Write-Host "Fertig! Die Datei site.css wurde aktualisiert." -ForegroundColor Green
