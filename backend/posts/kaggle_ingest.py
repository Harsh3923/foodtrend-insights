import os
import csv
from datetime import datetime, timezone
from posts.models import Post


def ingest_kaggle_data():
    file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "food.csv"
    )

    if not os.path.exists(file_path):
        print("CSV file not found.")
        return

    created_count = 0

    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            post_id = row.get("id")

            # Skip duplicates
            if Post.objects.filter(reddit_id=post_id).exists():
                continue

            created_date = None
            if row.get("timestamp"):
                try:
                    created_date = datetime.strptime(
                        row["timestamp"],
                        "%Y-%m-%d %H:%M:%S"
                    ).replace(tzinfo=timezone.utc)
                except Exception as e:
                    print("Timestamp parse failed:", e)
                    continue
            else:
                continue



            Post.objects.create(
                reddit_id=post_id,
                subreddit="food",  # Since dataset is r/Food
                title=row.get("title", ""),
                body=row.get("body", ""),
                created_utc=created_date,
                score=int(row.get("score", 0)),
                num_comments=int(row.get("comms_num", 0))
            )

            created_count += 1

    print(f"Ingestion complete. {created_count} posts inserted.")