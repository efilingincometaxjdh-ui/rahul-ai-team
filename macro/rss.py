import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

DEFAULT_FEEDS = (
    "https://www.federalreserve.gov/feeds/press_all.xml",
)


def fetch_feed(url, timeout=15):
    request = urllib.request.Request(url, headers={"User-Agent": "Rahul-AI-Team-Agent03/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        root = ET.fromstring(response.read())

    items = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        published = (item.findtext("pubDate") or "").strip()
        if title:
            items.append({"title": title, "url": link, "published": published, "source": url})
    return items


def collect_headlines(feeds=DEFAULT_FEEDS, limit=25):
    headlines, errors = [], []
    for feed in feeds:
        try:
            headlines.extend(fetch_feed(feed))
        except Exception as error:
            errors.append(f"{feed}: {error}")

    unique = []
    seen = set()
    for item in headlines:
        key = item["title"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique[:limit], errors
