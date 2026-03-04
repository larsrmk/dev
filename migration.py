#!/usr/bin/env python3
import os, re, ssl, time, urllib.request, urllib.parse, urllib.error
from html.parser import HTMLParser
from collections import deque
from pathlib import Path

# ── Konfiguration ─────────────────────────────────────────────────────
START_URL  = "http://intern.example.com"  # ← anpassen
OUTPUT_DIR = "site_mirror"
DELAY      = 0.2
MAX_PAGES  = 1000
HEADERS    = {"User-Agent": "Mozilla/5.0 (compatible; SiteMirror/1.0)"}

# ── FIX 1: SSL-Zertifikatsprüfung deaktivieren (intern/selbstsigniert) ──
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# ── HTML-Parser ────────────────────────────────────────────────────────
class LinkExtractor(HTMLParser):
    TAG_ATTRS = {
        "a": ["href"], "link": ["href"], "script": ["src"],
        "img": ["src", "data-src"], "source": ["src", "srcset"],
        "iframe": ["src"], "form": ["action"], "video": ["src"],
    }
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.links = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        for attr in self.TAG_ATTRS.get(tag, []):
            val = d.get(attr, "")
            if not val or val.startswith(("javascript:", "mailto:", "#", "")):
                continue
            if attr == "srcset":
                for part in val.split(","):
                    raw = part.strip().split()[0]
                    self._add(raw, tag == "a")
            else:
                self._add(val, tag == "a")

    def _add(self, href, is_page):
        abs_url = urllib.parse.urljoin(self.base_url, href.strip()).split("#")[0]
        if abs_url:
            self.links.append((abs_url, is_page))

# ── Hilfsfunktionen ────────────────────────────────────────────────────
def url_to_local_path(url, output_dir):
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.rstrip("/") or "/index"
    # FIX 2: Query-String sicher in Dateinamen kodieren
    if parsed.query:
        safe_q = parsed.query.replace("/", "_").replace("?", "_")[:50]
        path += "_" + safe_q
    if not Path(path).suffix:
        path += ".html"
    return os.path.join(output_dir, parsed.netloc, path.lstrip("/"))

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    # FIX 1: SSL_CTX übergeben
    with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as resp:
        final_url = resp.geturl()          # Redirects folgen
        ctype = resp.headers.get_content_type() or ""
        return resp.read(), ctype, final_url

def rewrite_html(html, page_url, rel_map):
    def replace(m):
        attr, q, val = m.group(1), m.group(2), m.group(3)
        abs_url = urllib.parse.urljoin(page_url, val.split("#")[0])
        local = rel_map.get(abs_url)
        return f'{attr}={q}{local}{q}' if local else m.group(0)
    return re.sub(
        r'((?:href|src|action))\s*=\s*(["\'])([^"\'>\s]+)\2',
        replace, html, flags=re.IGNORECASE
    )

def rewrite_css(css, css_url, rel_map):
    def replace(m):
        raw = m.group(1).strip("'\"")
        abs_url = urllib.parse.urljoin(css_url, raw)
        local = rel_map.get(abs_url)
        return f"url('{local}')" if local else m.group(0)
    return re.sub(r'url\\(([^)]+)\\)', replace, css)

# ── Haupt-Crawler ───────────────────────────────────────────────────────
def mirror(start_url, output_dir):
    base_domain = urllib.parse.urlparse(start_url).netloc
    visited, downloaded = set(), {}
    queue = deque([start_url])
    count = 0

    # FIX 3: Verbindungstest VOR dem Crawl
    print(f"[mirror] Teste Verbindung zu {start_url} ...")
    try:
        _, _, _ = fetch(start_url)
        print("[mirror] ✓ Verbindung OK\n")
    except Exception as e:
        print(f"[mirror] ✗ Verbindung fehlgeschlagen: {e}")
        print("  → Prüfe URL, Netzwerk oder VPN-Verbindung!")
        return

    print(f"[mirror] Ausgabe: {os.path.abspath(output_dir)}\n")

    # Phase 1: Crawlen
    while queue and count < MAX_PAGES:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        if urllib.parse.urlparse(url).netloc != base_domain:
            continue

        try:
            content, ctype, final_url = fetch(url)
            # FIX 4: Redirect-Ziel auch als besucht markieren
            if final_url != url:
                visited.add(final_url)
            count += 1
        except Exception as e:
            print(f"  [FEHLER] {url}: {e}")
            continue

        local_path = url_to_local_path(url, output_dir)

        # FIX 5: Sicherstellen dass dirname nicht leer ist
        dir_name = os.path.dirname(local_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        else:
            os.makedirs(output_dir, exist_ok=True)
            local_path = os.path.join(output_dir, local_path)

        downloaded[url] = local_path

        if "text/html" in ctype:
            html_text = content.decode("utf-8", errors="replace")
            parser = LinkExtractor(url)
            try:
                parser.feed(html_text)
            except Exception:
                pass
            for link, _ in parser.links:
                if urllib.parse.urlparse(link).netloc == base_domain and link not in visited:
                    queue.append(link)

        elif "text/css" in ctype:
            css_text = content.decode("utf-8", errors="replace")
            for m in re.finditer(r'url\\(([^)]+)\\)', css_text):
                raw = m.group(1).strip("'\"")
                abs_url = urllib.parse.urljoin(url, raw)
                if urllib.parse.urlparse(abs_url).netloc == base_domain and abs_url not in visited:
                    queue.append(abs_url)

        with open(local_path, "wb") as f:
            f.write(content)

        print(f"  [{count:4d}] {url}")
        time.sleep(DELAY)

    # Phase 2: Links umschreiben
    print(f"\n[mirror] Schreibe {len(downloaded)} Dateien um ...")
    for url, local_path in downloaded.items():
        if not os.path.exists(local_path):
            continue
        this_dir = os.path.dirname(local_path)
        rel_map = {
            u: os.path.relpath(p, this_dir).replace("\\", "/")
            for u, p in downloaded.items()
        }
        try:
            if local_path.endswith(".html"):
                with open(local_path, "r", encoding="utf-8", errors="replace") as f:
                    data = f.read()
                data = rewrite_html(data, url, rel_map)
                with open(local_path, "w", encoding="utf-8") as f:
                    f.write(data)
            elif local_path.endswith(".css"):
                with open(local_path, "r", encoding="utf-8", errors="replace") as f:
                    data = f.read()
                data = rewrite_css(data, url, rel_map)
                with open(local_path, "w", encoding="utf-8") as f:
                    f.write(data)
        except Exception as e:
            print(f"  [REWRITE-FEHLER] {local_path}: {e}")

    index = os.path.join(output_dir, base_domain, "index.html")
    print(f"\n[mirror] ✓ Fertig! {count} Dateien gespeichert.")
    print(f"[mirror] Einstieg: {os.path.abspath(index)}")

if __name__ == "__main__":
    mirror(START_URL, OUTPUT_DIR)

