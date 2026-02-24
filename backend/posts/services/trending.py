import math
from datetime import timedelta
from django.db.models import F
from django.utils import timezone

from posts.models import PostTerm, Term


def _decay_weight(age_days: float, half_life_days: float) -> float:
    # Exponential decay: weight halves every `half_life_days`
    # exp(-ln(2) * age / half_life)
    return math.exp(-math.log(2) * age_days / half_life_days)


def get_trending_terms(
    days: int = 7,
    limit: int = 20,
    half_life_days: float = 2.5,
    a: float = 0.25,
    b: float = 0.15,
):
    """
    Returns ranked terms with:
      - trend_score (mentions + engagement + recency)
      - mentions in window
      - spike ratio (last 24h vs prev 24h)
    """
    now = timezone.now()
    window_start = now - timedelta(days=days)
    last_24h_start = now - timedelta(hours=24)
    prev_24h_start = now - timedelta(hours=48)

    # Pull matches in the window
    qs = (
        PostTerm.objects
        .select_related("term", "post")
        .filter(post__created_utc__gte=window_start, term__is_active=True)
        .only(
            "term_id", "post_id",
            "post__created_utc", "post__score", "post__num_comments",
            "term__text"
        )
    )

    # Aggregate in Python (SQLite-friendly; avoids DB-specific funcs)
    by_term = {}

    for pt in qs.iterator():
        term_id = pt.term_id
        term_text = pt.term.text

        post = pt.post
        created = post.created_utc
        age_days = max(0.0, (now - created).total_seconds() / 86400.0)
        decay = _decay_weight(age_days, half_life_days)

        score = post.score or 0
        comments = post.num_comments or 0

        engagement = math.log1p(score) + 0.5 * math.log1p(comments)
        contrib = decay * (1.0 + a * math.log1p(score) + b * math.log1p(comments))

        if term_id not in by_term:
            by_term[term_id] = {
                "term": term_text,
                "trend_score": 0.0,
                "mentions": 0,
                "recent_24h": 0,
                "prev_24h": 0,
            }

        bucket = by_term[term_id]
        bucket["trend_score"] += contrib
        bucket["mentions"] += 1

        if created >= last_24h_start:
            bucket["recent_24h"] += 1
        elif created >= prev_24h_start:
            bucket["prev_24h"] += 1

    # Add spike ratio + sort
    results = []
    for term_id, data in by_term.items():
        recent = data["recent_24h"]
        prev = data["prev_24h"]
        spike = (recent + 1) / (prev + 1)  # smoothing

        results.append({
            "term_id": term_id,
            "term": data["term"],
            "trend_score": round(data["trend_score"], 4),
            "mentions": data["mentions"],
            "recent_24h": recent,
            "prev_24h": prev,
            "spike": round(spike, 4),
        })

    results.sort(key=lambda x: x["trend_score"], reverse=True)
    return results[:limit]