from django.http import JsonResponse
from django.views.decorators.http import require_GET

from posts.models import Post
from posts.services.search import search_posts
from posts.services.trending import get_trending_terms
from posts.trending_cuisines import get_trending_cuisines


@require_GET
def api_trending_cuisines(request):
    days = int(request.GET.get("days", 7))
    limit = int(request.GET.get("limit", 12))
    results = get_trending_cuisines(days=days, limit=limit)
    return JsonResponse({"days": days, "limit": limit, "results": results})


@require_GET
def api_posts(request):
    limit = int(request.GET.get("limit", 20))
    qs = Post.objects.order_by("-created_utc")[:limit]

    results = [{
        "reddit_id": p.reddit_id,
        "subreddit": p.subreddit,
        "title": p.title,
        "created_utc": p.created_utc.isoformat(),
        "score": p.score,
        "num_comments": p.num_comments,
    } for p in qs]

    return JsonResponse({"limit": limit, "results": results})


@require_GET
def api_trends(request):
    days = int(request.GET.get("days", 7))
    limit = int(request.GET.get("limit", 20))
    results = get_trending_terms(days=days, limit=limit)
    return JsonResponse({"days": days, "limit": limit, "results": results})


@require_GET
def api_search(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse({"results": [], "error": "Missing q parameter"}, status=400)

    days = int(request.GET.get("days", 30))
    limit = int(request.GET.get("limit", 20))
    term = request.GET.get("term")  # optional exact Term.text

    results = search_posts(q=q, days=days, limit=limit, term_text=term)
    return JsonResponse({"q": q, "days": days, "limit": limit, "term": term, "results": results})