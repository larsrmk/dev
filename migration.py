#!/usr/bin/env python3
"""
site_mirror.py – Vollständiger Website-Mirror (nur Python-Stdlib)
Lädt alle Unterseiten + Assets (CSS, JS, Bilder) und schreibt
alle Links für Offline-Nutzung um.
"""

import os
import re
import time
import urllib.request
import urllib.parse
import urllib.error
from html.parser import HTMLParser
from collections import deque
from pathlib import Path

# ── Konfiguration ───────────────────────────────────────────────
START_URL  = "http://intern.example.com"   # ← anpassen
OUTPUT_DIR = "site_mirror"
DELAY      = 0.3    # Sekunden zwischen Requests (Schonung des Servers)
MAX_PAGES  = 1000   # Sicherheitslimit

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SiteMirror/1.0)"}


# ── HTML-Parser: alle Link/Asset-URLs extrahieren ───────────────
class LinkExtractor(HTMLParser):
    TAG_ATTRS = {
        "a":      ["href"],
        "link":   ["href"],
        "script": ["src"],
        "img":    ["src", "data-src"],
        "source": ["src", "srcset"],
        "iframe": ["src"],
        "form":   ["action"],
        "video":  ["src"],
        "audio":  ["src"],
    }

    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.links = []  # Liste von (abs_url, is_page)

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        for attr in self.TAG_ATTRS.get(tag, []):
            val = attrs_dict.get(attr, "")
            if not val or val.startswith(("javascript:", "mailto:", "#", "")):
                continue
            if attr == "srcset":
                for part in val.split(","):
                    raw = part.strip().split()[0]
                    self._add(raw, is_page=False)
            else:
                self._add(val, is_page=(tag == "a"))

    def _add(self, href, is_page):
        abs_url = urllib.parse.urljoin(self.base_url, href.strip()).split("#")[0]
        if abs_url:
            self.links.append((abs_url, is_page))


# ── Hilfsfunktionen ─────────────────────────────────────────────
def url_to_local_path(url, output_dir):
    """URL → lokaler Dateipfad."""
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.rstrip("/") or "/index"
    if not Path(path).suffix:
        path += ".html"
    return os.path.join(output_dir, parsed.netloc, path.lstrip("/"))


def fetch(url):
    """HTTP-GET, gibt (bytes, content_type) zurück."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read(), (resp.headers.get_content_type() or "")


def rewrite_html(html, page_url, rel_map):
    """Ersetzt href/src/action im HTML durch lokale Pfade."""
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
    """Ersetzt url(...) in CSS durch lokale Pfade."""
    def replace(m):
        raw = m.group(1).strip("'\"")
        abs_url = urllib.parse.urljoin(css_url, raw)
        local = rel_map.get(abs_url)
        return f"url('{local}')" if local else m.group(0)

    return re.sub(r'url\\(([^)]+)\\)', replace, css)


# ── Haupt-Crawler ───────────────────────────────────────────────
def mirror(start_url, output_dir):
    base_domain = urllib.parse.urlparse(start_url).netloc
    visited, downloaded = set(), {}  # url → lokaler Pfad
    queue = deque([start_url])
    count = 0

    print(f"[mirror] Start : {start_url}")
    print(f"[mirror] Ausgabe: {os.path.abspath(output_dir)}\n")

    # ── Phase 1: Crawlen & Herunterladen ────────────────────────
    while queue and count < MAX_PAGES:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        # Nur interne URLs
        if urllib.parse.urlparse(url).netloc != base_domain:
            continue

        try:
            content, ctype = fetch(url)
            count += 1
        except Exception as e:
            print(f"  [FEHLER] {url}: {e}")
            continue

        local_path = url_to_local_path(url, output_dir)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        downloaded[url] = local_path

        # HTML → Links in Queue einstellen
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

        # CSS → url()-Referenzen in Queue einstellen
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

    # ── Phase 2: Links umschreiben ───────────────────────────────
    print(f"\n[mirror] Schreibe {len(downloaded)} Dateien um …")

    for url, local_path in downloaded.items():
        if not os.path.exists(local_path):
            continue

        this_dir = os.path.dirname(local_path)
        # Relativer Pfad vom aktuellen File zu jedem anderen File
        rel_map = {
            u: os.path.relpath(p, this_dir).replace("\\", "/")
            for u, p in downloaded.items()
        }

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

    index = os.path.join(output_dir, base_domain, "index.html")
    print(f"\n[mirror] ✓ Fertig! {count} Dateien gespeichert.")
    print(f"[mirror] Einstieg: {os.path.abspath(index)}")


if __name__ == "__main__":
    mirror(START_URL, OUTPUT_DIR)
