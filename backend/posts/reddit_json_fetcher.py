import time
import requests
from datetime import datetime, timezone
from django.db import transaction
from posts.models import Post

DEFAULT_SUBREDDITS = ["food", "Cooking", "recipes"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

def _parse_created_utc(created_utc_value) -> datetime:
    return datetime.fromtimestamp(float(created_utc_value), tz=timezone.utc)

@transaction.atomic
def ingest_from_subreddit(subreddit: str, limit: int = 50) -> int:
    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
    r = requests.get(url, headers=HEADERS, timeout=20)

    if r.status_code != 200:
        # Reddit sometimes returns an HTML block page. Print first 120 chars to confirm.
        snippet = (r.text or "")[:120].replace("\n", " ")
        print(f"[{subreddit}] HTTP {r.status_code} | {snippet}")
        return 0

    data = r.json()
    children = data.get("data", {}).get("children", [])

    inserted = 0
    for item in children:
        d = item.get("data", {})
        reddit_id = d.get("id")
        if not reddit_id:
            continue

        if Post.objects.filter(reddit_id=reddit_id).exists():
            continue

        created_dt = _parse_created_utc(d.get("created_utc", time.time()))

        Post.objects.create(
            reddit_id=reddit_id,
            subreddit=subreddit,
            title=d.get("title", "") or "",
            body=d.get("selftext", "") or "",
            created_utc=created_dt,
            score=int(d.get("score", 0) or 0),
            num_comments=int(d.get("num_comments", 0) or 0),
        )
        inserted += 1

    print(f"[{subreddit}] inserted {inserted}")
    return inserted

def ingest_reddit_json(subreddits=None, limit: int = 50, sleep_seconds: float = 2.0) -> int:
    subreddits = subreddits or DEFAULT_SUBREDDITS
    total = 0
    for sr in subreddits:
        total += ingest_from_subreddit(sr, limit=limit)
        time.sleep(sleep_seconds)
    print(f"Total inserted: {total}")
    return total