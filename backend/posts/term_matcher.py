import re
from posts.models import Post, Term, PostTerm

def run_term_matching():
    terms = Term.objects.filter(is_active=True)
    posts = Post.objects.all()

    created_links = 0

    for post in posts:
        content = f"{post.title} {post.body}".lower()

        for term in terms:
            pattern = r"\b" + re.escape(term.text.lower()) + r"\b"

            if re.search(pattern, content):
                _, created = PostTerm.objects.get_or_create(
                    post=post,
                    term=term
                )
                if created:
                    created_links += 1

    print(f"Created {created_links} term links.")