import math
import re
from datetime import timedelta
from django.utils import timezone

from posts.models import Post, PostTerm, Term

_WORD_RE = re.compile(r"[a-z0-9]+")

def _tokens(s: str) -> set[str]:
    return set(_WORD_RE.findall((s or "").lower()))

def search_posts(
    q: str,
    days: int = 30,
    limit: int = 20,
    half_life_days: float = 7.0,
    term_text: str | None = None,
):
    """
    Ranked search:
      - token overlap in title/body
      - engagement (score/comments)
      - recency decay
    """
    now = timezone.now()
    start = now - timedelta(days=days)

    query_tokens = _tokens(q)
    if not query_tokens:
        return []

    posts_qs = Post.objects.filter(created_utc__gte=start).only(
        "id", "reddit_id", "title", "body", "created_utc",
        "score", "num_comments", "subreddit"
    )

    # Optional term filter (exact Term.text)
    if term_text:
        try:
            term_text = (term_text or "").strip()
            term = Term.objects.get(text__iexact=term_text, is_active=True)
        except Term.DoesNotExist:
            return []

        post_ids = PostTerm.objects.filter(term=term).values_list("post_id", flat=True)
        posts_qs = posts_qs.filter(id__in=post_ids)

    def decay(age_days: float) -> float:
        return math.exp(-math.log(2) * age_days / half_life_days)

    ranked = []

    for p in posts_qs.iterator():
        title_tokens = _tokens(p.title)
        body_tokens = _tokens(p.body)

        title_hits = len(query_tokens & title_tokens)
        body_hits = len(query_tokens & body_tokens)

        if title_hits == 0 and body_hits == 0:
            continue

        age_days = max(0.0, (now - p.created_utc).total_seconds() / 86400.0)
        rec = decay(age_days)

        score = p.score or 0
        comments = p.num_comments or 0
        engagement = math.log1p(score) + 0.5 * math.log1p(comments)

        text_score = (2.0 * title_hits) + (1.0 * body_hits)
        final = rec * (text_score + 0.2 * engagement)

        ranked.append({
            "reddit_id": p.reddit_id,
            "title": p.title,
            "subreddit": p.subreddit,
            "created_utc": p.created_utc.isoformat(),
            "score": score,
            "num_comments": comments,
            "rank_score": round(final, 6),
            "title_hits": title_hits,
            "body_hits": body_hits,
        })

    ranked.sort(key=lambda x: x["rank_score"], reverse=True)
    return ranked[:limit]