"""Fetch recent posts from the newsletter feeds into _data/posts.yml.

Feeds come from _data/projects.yml: any item with a `feed:` URL is read, and
its posts are labelled with that item's title. All posts go into one list,
newest first. If a feed can't be reached, the posts saved from it last time
are kept, so a Substack outage never empties the list on the site.
"""
from pathlib import Path
from time import strftime

import feedparser
import yaml

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


def latest(url, source):
    parsed = feedparser.parse(url, agent="seangrogan.github.io feed reader")
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


old = load(POSTS)
posts = []
for url, source in feeds():
    found = latest(url, source)
    if found:
        print(f"{source}: {len(found)} posts")
    else:
        found = [p for p in old if p.get("feed") == url]
        print(f"{source}: unreachable, kept {len(found)} saved posts")
    posts.extend(found)

posts.sort(key=lambda p: p["date"], reverse=True)
text = yaml.safe_dump(posts[:KEEP], allow_unicode=True, sort_keys=False)
if not POSTS.exists() or POSTS.read_text(encoding="utf-8") != text:
    POSTS.write_text(text, encoding="utf-8")
    print("posts.yml updated")
else:
    print("no change")
