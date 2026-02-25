import re
from collections import Counter
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from posts.models import Post


WORD_RE = re.compile(r"[a-z0-9]+")

# Keep this list small at first; expand as you see junk.
STOPWORDS = {
    "the", "a", "an", "and", "or", "but","to", "of", "in", "on", "for", "with", "at", "by", "from",
    "is", "are", "was", "were", "be", "been", "being","best","also","used","something","now","get","want","add","had","konw","there"
    "it", "this", "that","have", "all","some", "not","like","about", "any", "these", "those","ideas","anyone","other","making,"
    "i", "you", "we", "they", "he", "she", "them", "us","make","time","out","has","use","think","then","over","still","things",
    "my", "your", "our", "their", "his", "her","what", "why", "how", "when", "where",
    "can", "could", "should", "would", "will", "just","really", "very", "more", "most", "less",
    "help", "need", "question", "advice","food", "cook", "cooking", "recipe", "recipes",
    "eat","amp","long","same","ate","there","into","good","one","way","taste","pan","high","oven",
    "making","looking","using","fresh","paste","anything","store","before","love","too","after","dry",
    "sure","trying","maybe","few","cooked","than","put","minutes","cup","thank","first","does",
    "getting","stock","well","wondering","wanted","top","another","lot","hot","added","suggestions","bit","which","day",
    "much","work","baking","dish","thanks","different","got","hours","usual","through","tried","heat","substitute","home",
    "until","cast","iron","here","take","only","bought","everything","else","little","com","easy","new","because","stove",
    "recommendations","done","never","cast iron","etc","freezer","fridge","week","great","since","start","simple",
    "bad","wasn","last","set","buy","https","didn","ingredients","tsp","found","every","next","year",
    "part","pot","ever","small","basically","frozen","canned","cut","style","hour","decided","instead",
    "texture","doesn","usually","stuff","keep","able","finish","look","everyone","always","people","try","please",
    "though","while","even","going","however","idea","prep","makes","spray","kitchen","bag","doing","freeze","kind","cooker",
    "chops","bottom","without","said","online","pans","pieces","turn","worth","enough","www","https www","dinner",
    "breakfast","seems","heavy","thinking",
}

def tokenize(text: str) -> list[str]:
    return WORD_RE.findall((text or "").lower())

def is_good_token(w: str) -> bool:
    if len(w) < 3:
        return False
    if w.isdigit():
        return False
    if w in STOPWORDS:
        return False
    return True

def generate_ngrams(tokens: list[str], n: int) -> list[str]:
    out = []
    for i in range(len(tokens) - n + 1):
        gram = tokens[i:i+n]
        # skip grams containing stopwords or bad tokens
        if any((not is_good_token(w)) for w in gram):
            continue
        out.append(" ".join(gram))
    return out


class Command(BaseCommand):
    help = "Extract candidate food terms (unigrams/bigrams/trigrams) from recent posts."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=14, help="Lookback window in days.")
        parser.add_argument("--limit-posts", type=int, default=800, help="Max posts to scan.")
        parser.add_argument("--top", type=int, default=60, help="How many candidates to print.")
        parser.add_argument("--min-count", type=int, default=3, help="Minimum frequency.")
        parser.add_argument("--max-ngram", type=int, default=2, choices=[1, 2, 3], help="Max n-gram length.")
        parser.add_argument("--include-engagement", action="store_true", help="Weight counts by engagement.")

    def handle(self, *args, **opts):
        days = opts["days"]
        limit_posts = opts["limit_posts"]
        top = opts["top"]
        min_count = opts["min_count"]
        max_ngram = opts["max_ngram"]
        include_engagement = opts["include_engagement"]

        now = timezone.now()
        start = now - timedelta(days=days)

        qs = (
            Post.objects
            .filter(created_utc__gte=start)
            .only("title", "body", "score", "num_comments", "created_utc")
            .order_by("-created_utc")[:limit_posts]
        )

        counts = Counter()

        scanned = 0
        for p in qs.iterator():
            scanned += 1
            tokens = tokenize(f"{p.title} {p.body}")
            tokens = [w for w in tokens if is_good_token(w)]
            if not tokens:
                continue

            # Optional engagement weight (keeps it light + interpretable)
            weight = 1
            if include_engagement:
                score = int(p.score or 0)
                comments = int(p.num_comments or 0)
                weight = 1 + min(5, (score // 50) + (comments // 25))  # capped

            # unigrams
            for w in tokens:
                counts[w] += weight

            # bigrams/trigrams
            if max_ngram >= 2:
                for g in generate_ngrams(tokens, 2):
                    counts[g] += weight
            if max_ngram >= 3:
                for g in generate_ngrams(tokens, 3):
                    counts[g] += weight

        # Filter and show results
        candidates = [(term, c) for term, c in counts.items() if c >= min_count]
        candidates.sort(key=lambda x: x[1], reverse=True)

        self.stdout.write(self.style.SUCCESS(
            f"Scanned {scanned} posts from last {days} days. Candidates (min_count={min_count}):"
        ))

        for term, c in candidates[:top]:
            self.stdout.write(f"{c:>5}  {term}")