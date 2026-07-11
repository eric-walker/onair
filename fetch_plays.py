#!/usr/bin/env python3
"""Fetch recent plays from xmplaylist and save them as JSON files in ./data/.
Runs on a schedule via GitHub Actions (see .github/workflows/fetch-plays.yml).
Add or remove station slugs in SLUGS below."""

import json
import pathlib
import sys
import time

SLUGS = ["thespectrum", "siriusxmu"]

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 onair-personal-dashboard")


def get(url):
    """Fetch with cloudscraper if available (handles Cloudflare bot checks),
    otherwise plain urllib with a browser-like user agent."""
    try:
        import cloudscraper
        s = cloudscraper.create_scraper()
        r = s.get(url, headers={"User-Agent": UA, "Accept": "application/json"}, timeout=30)
        return r.status_code, r.text
    except ImportError:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode()


def main():
    out = pathlib.Path("data")
    out.mkdir(exist_ok=True)
    failures = 0

    for slug in SLUGS:
        try:
            code, text = get(f"https://xmplaylist.com/api/station/{slug}")
            payload = json.loads(text)
        except Exception as e:
            print(f"{slug}: FAILED ({e})")
            failures += 1
            continue

        if not isinstance(payload, dict):
            payload = {"results": payload}
        payload["fetched"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        (out / f"{slug}.json").write_text(json.dumps(payload))
        print(f"{slug}: ok ({code})")

    # Fail the workflow only if nothing succeeded
    sys.exit(1 if failures == len(SLUGS) else 0)


if __name__ == "__main__":
    main()
