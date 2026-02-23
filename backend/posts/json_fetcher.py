import requests
from datetime import datetime, timezone
from .models import Post


HEADERS = {
    "User-Agent": "foodtrendinsights/1.0 by Harsh"
}

def fetch_subreddit(subreddit_name: str, limit: int = 25):
    url = f"https://api.reddit.com/r/{subreddit_name}/hot?limit={limit}"
    response = requests.get(
    url,
    headers=HEADERS,
    timeout=10,
    )

    

    if response.status_code != 200:
        print(f"Failed to fetch r/{subreddit_name}")
        return

    data = response.json()

    for item in data["data"]["children"]:
        post_data = item["data"]

        Post.objects.update_or_create(
            reddit_id=post_data["id"],
            defaults={
                "subreddit": subreddit_name,
                "title": post_data.get("title", ""),
                "body": post_data.get("selftext", ""),
                "created_utc": datetime.fromtimestamp(
                    post_data["created_utc"], tz=timezone.utc
                ),
                "score": post_data.get("score", 0),
                "num_comments": post_data.get("num_comments", 0),
            },
        )

    print(f"Fetched posts from r/{subreddit_name}")


def fetch_reddit_data():
    subreddits = ["food", "Cooking", "recipes"]

    for sub in subreddits:
        fetch_subreddit(sub)

    print("JSON ingestion completed.")