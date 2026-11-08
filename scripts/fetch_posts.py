"""Fetch recent posts from the newsletter feeds into _data/posts.yml.

Feeds come from _data/projects.yml: any item with a `feed:` URL is read, and
its posts are labelled with that item's title. All posts go into one list,
newest first. If a feed can't be reached, the posts saved from it last time
are kept, so a Substack outage never empties the list on the site.
"""
import sys
from pathlib import Path
from time import strftime

import feedparser
import yaml
from curl_cffi import requests

PROJECTS = Path("_data/projects.yml")
POSTS = Path("_data/posts.yml")
PER_FEED = 5    # how many recent posts to read from each feed
KEEP = 10       # how many to save in total (the page decides how many to show)


def load(path):
    if path.exists():
        return yaml.safe_load(path.read_text(encoding="utf-8")) or []
    return []


def feeds():
    for group in load(PROJECTS):
        for item in group.get("items") or []:
            if item.get("feed"):
                yield item["feed"], item["title"]


# Headers a real Chrome on Windows sends when opening a feed.
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "application/rss+xml,*/*;q=0.8",
    "Accept-Language": "en-CA,en;q=0.9",
    "Cache-Control": "no-cache",
    "Referer": "https://www.google.com/",
}


def get(url):
    """Fetch a URL as Chrome would. Returns the response, or None on failure."""
    try:
        response = requests.get(url, impersonate="chrome", headers=HEADERS, timeout=30)
    except Exception as error:
        print(f"    {url}: could not connect ({error})")
        return None
    if response.status_code != 200:
        # These headers say who refused and why (e.g. a Cloudflare challenge).
        why = ", ".join(f"{k}={response.headers[k]}"
                        for k in ("server", "cf-mitigated", "cf-ray")
                        if k in response.headers)
        print(f"    {url}: the server answered {response.status_code} ({why or 'no details'})")
        return None
    return response


def from_feed(url, source):
    response = get(url)
    if response is None:
        return None
    parsed = feedparser.parse(response.content)
    posts = []
    for entry in parsed.entries[:PER_FEED]:
        when = entry.get("published_parsed") or entry.get("updated_parsed")
        posts.append({
            "title": entry.get("title", "Untitled"),
            "url": entry.get("link", ""),
            "date": strftime("%Y-%m-%d", when) if when else "",
            "source": source,
            "feed": url,
        })
    return posts


def from_archive(url, source):
    """Second route: Substack's own post list, which its website uses."""
    base = url.rsplit("/feed", 1)[0]
    response = get(f"{base}/api/v1/archive?sort=new&offset=0&limit={PER_FEED}")
    if response is None:
        return None
    try:
        items = response.json()
    except ValueError:
        print(f"    {base}: the post list wasn't readable")
        return None
    return [{
        "title": item.get("title") or "Untitled",
        "url": item.get("canonical_url") or "",
        "date": (item.get("post_date") or "")[:10],
        "source": source,
        "feed": url,
    } for item in items[:PER_FEED]]


def latest(url, source):
    """The newest posts, or None if Substack couldn't be reached by any route."""
    for route in (from_feed, from_archive):
        posts = route(url, source)
        if posts is not None:
            return posts
    return None


old = load(POSTS)
posts = []
failed = []
for url, source in feeds():
    found = latest(url, source)
    if found is None:
        failed.append(source)
        found = [p for p in old if p.get("feed") == url]
        print(f"{source}: unreachable, kept {len(found)} saved posts")
    elif not found:
        print(f"{source}: no posts yet")
    else:
        print(f"{source}: {len(found)} posts")
    posts.extend(found)

posts.sort(key=lambda p: p["date"], reverse=True)
text = yaml.safe_dump(posts[:KEEP], allow_unicode=True, sort_keys=False)
if not POSTS.exists() or POSTS.read_text(encoding="utf-8") != text:
    POSTS.write_text(text, encoding="utf-8")
    print("posts.yml updated")
else:
    print("no change")

# Exit code 2 tells update_posts.sh that some feeds failed (the posts file is
# still written, keeping the saved posts for those feeds).
if failed:
    print(f"could not fetch: {', '.join(failed)}")
    sys.exit(2)
