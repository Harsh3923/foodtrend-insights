from django.core.management.base import BaseCommand
from posts.reddit_json_ingest import ingest_reddit_json
from posts.term_matcher import run_term_matching
from posts.models import Post

class Command(BaseCommand):
    help = "Ingest posts from Reddit public JSON endpoints and run term matching."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)
        parser.add_argument("--sleep", type=float, default=2.0)
        parser.add_argument("--subs", nargs="*", default=None)

    def handle(self, *args, **options):
        limit = options["limit"]
        sleep = options["sleep"]
        subs = options["subs"]

        before_ids = set(Post.objects.values_list("id", flat=True))
        ingest_reddit_json(subreddits=subs, limit=limit, sleep_seconds=sleep)
        after_ids = set(Post.objects.values_list("id", flat=True))

        new_ids = after_ids - before_ids
        new_posts_qs = Post.objects.filter(id__in=new_ids)

        links = run_term_matching(posts_qs=new_posts_qs)

        self.stdout.write(
            self.style.SUCCESS(f"Done. New posts: {len(new_ids)}, term links created: {links}")
        )