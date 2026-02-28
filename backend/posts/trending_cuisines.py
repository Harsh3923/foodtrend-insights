import math
from datetime import timedelta
from django.utils import timezone

from posts.models import PostTerm

def _decay_weight(age_days: float, half_life_days: float) -> float:
    return math.exp(-math.log(2) * age_days / half_life_days)

def get_trending_cuisines(
    days: int = 7,
    limit: int = 20,
    half_life_days: float = 2.5,
    a: float = 0.25,
    b: float = 0.15,
):
    """
    Cuisine-level trending using the SAME scoring logic as get_trending_terms(),
    but grouped by Term.cultural_origin.
    """
    now = timezone.now()
    window_start = now - timedelta(days=days)
    last_24h_start = now - timedelta(hours=24)
    prev_24h_start = now - timedelta(hours=48)

    qs = (
        PostTerm.objects
        .select_related("term", "post")
        .filter(post__created_utc__gte=window_start, term__is_active=True)
        .only(
            "term_id", "post_id",
            "post__created_utc", "post__score", "post__num_comments",
            "term__cultural_origin"
        )
    )

    by_origin = {}

    for pt in qs.iterator():
        origin = pt.term.cultural_origin or "other"
        post = pt.post
        created = post.created_utc

        age_days = max(0.0, (now - created).total_seconds() / 86400.0)
        decay = _decay_weight(age_days, half_life_days)

        score = post.score or 0
        comments = post.num_comments or 0

        contrib = decay * (1.0 + a * math.log1p(score) + b * math.log1p(comments))

        if origin not in by_origin:
            by_origin[origin] = {
                "origin": origin,
                "trend_score": 0.0,
                "mentions": 0,
                "recent_24h": 0,
                "prev_24h": 0,
                "unique_terms": set(),
                "unique_subreddits": set(),
            }

        bucket = by_origin[origin]
        bucket["trend_score"] += contrib
        bucket["mentions"] += 1
        bucket["unique_terms"].add(pt.term_id)
        bucket["unique_subreddits"].add(post.subreddit)

        if created >= last_24h_start:
            bucket["recent_24h"] += 1
        elif created >= prev_24h_start:
            bucket["prev_24h"] += 1

    results = []
    for origin, data in by_origin.items():
        recent = data["recent_24h"]
        prev = data["prev_24h"]
        spike = (recent + 1) / (prev + 1)

        results.append({
            "origin": origin,
            "trend_score": round(data["trend_score"], 4),
            "mentions": data["mentions"],
            "recent_24h": recent,
            "prev_24h": prev,
            "spike": round(spike, 4),
            "unique_terms": len(data["unique_terms"]),
            "subreddit_spread": len(data["unique_subreddits"]),  # diffusion metric
        })

    results.sort(key=lambda x: x["trend_score"], reverse=True)
    return results[:limit]