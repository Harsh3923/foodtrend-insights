# posts/term_matcher.py

import re
from django.db import transaction
from django.utils import timezone

from posts.models import Post, Term, PostTerm

_WORD_RE = re.compile(r"[a-z0-9]+")

STOP_TERMS = {
    "food", "cook", "cooking", "recipe", "recipes",
    "help", "need", "best", "easy", "good", "question",
    "dinner", "lunch", "breakfast", "meal", "meals",
    "cutting",  # you asked to add this
}

def _tokens(text: str) -> list[str]:
    return _WORD_RE.findall((text or "").lower())

def _norm(text: str) -> str:
    return " ".join(_tokens(text))

def _term_ok(t: str) -> bool:
    t = (t or "").strip().lower()
    if len(t) < 3:
        return False
    if t in STOP_TERMS:
        return False
    if t.isdigit():
        return False
    return True

def _build_term_index():
    """
    Build term index for fast matching.
    - single_terms: dict[word -> term_id]
    - phrase_terms: list[(normalized_phrase, term_id)] longest-first
    """
    single_terms: dict[str, int] = {}
    phrase_terms: list[tuple[str, int]] = []

    for term in Term.objects.filter(is_active=True).only("id", "text"):
        raw = (term.text or "").strip()
        if not raw:
            continue
        if not _term_ok(raw):
            continue

        if " " in raw:
            phrase_terms.append((_norm(raw), term.id))
        else:
            single_terms[raw.lower()] = term.id

    phrase_terms.sort(key=lambda x: len(x[0]), reverse=True)
    return single_terms, phrase_terms

@transaction.atomic
def run_term_matching(posts_qs=None, limit: int | None = 500, force: bool = False):
    """
    Best long-term behavior:
    - By default, only matches posts where term_matched_at is NULL (never processed).
    - Sets post.term_matched_at when processed.
    - If force=True, it will re-process posts (useful when you updated STOP_TERMS/Terms).
    - Uses limit to keep it fast (defaults to latest 500).
    """
    single_terms, phrase_terms = _build_term_index()

    posts = posts_qs if posts_qs is not None else Post.objects.all()

    if not force:
        posts = posts.filter(term_matched_at__isnull=True)

    posts = posts.order_by("-created_utc")
    if limit is not None:
        posts = posts[:limit]

    created_links = 0
    processed_posts = 0
    now = timezone.now()

    for post in posts.iterator():
        processed_posts += 1

        hay = _norm(f"{post.title} {post.body}")
        if not hay:
            post.term_matched_at = now
            post.save(update_fields=["term_matched_at"])
            continue

        tok_set = set(hay.split())
        matched_term_ids: set[int] = set()

        # Phrase matches (space-normalized boundaries)
        padded = f" {hay} "
        for phrase_norm, term_id in phrase_terms:
            if f" {phrase_norm} " in padded:
                matched_term_ids.add(term_id)

        # Single word matches (set intersection)
        if single_terms:
            for w in (tok_set & set(single_terms.keys())):
                matched_term_ids.add(single_terms[w])

        # Create links
        for term_id in matched_term_ids:
            _, created = PostTerm.objects.get_or_create(post=post, term_id=term_id)
            if created:
                created_links += 1

        # Mark as processed (even if no terms matched)
        post.term_matched_at = now
        post.save(update_fields=["term_matched_at"])

    print(f"Processed {processed_posts} posts. Created {created_links} term links.")
    return created_links