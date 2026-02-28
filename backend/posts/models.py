from django.db import models

# Create your models here.
class Post(models.Model):
    """
    Raw Reddit post (no-username stored).
    """
    reddit_id = models.CharField(max_length=20, unique=True)
    subreddit = models.CharField(max_length=100)
    title = models.TextField()
    body = models.TextField(blank=True)
    created_utc = models.DateTimeField()
    score = models.IntegerField(default=0)
    num_comments = models.IntegerField(default=0)

    fetched_at = models.DateTimeField(auto_now_add=True)
    term_matched_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"[r/{self.subreddit}] {self.title[:60]}"
    

class Term(models.Model):
    ORIGINS = [
        ("american_canadian", "American/Canadian"),
        ("italian", "Italian"),
        ("mexican", "Mexican"),
        ("korean", "Korean"),
        ("japanese", "Japanese"),
        ("chinese", "Chinese"),
        ("indian", "Indian"),
        ("middle_eastern", "Middle Eastern"),
        ("southeast_asian", "Southeast Asian"),
        ("french", "French"),
        ("fusion", "Fusion"),
        ("other", "Other/Unclear"),
    ]

    text = models.CharField(max_length=80, unique=True)
    is_active = models.BooleanField(default=True)

    cultural_origin = models.CharField(
        max_length=32,
        choices=ORIGINS,
        default="other",
        db_index=True,
    )
    origin_confidence = models.FloatField(default=0.0)

    def __str__(self) -> str:
        return self.text
    
class PostTerm(models.Model):
    """
    which term appears in which posts.
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="term_links")
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="post_links")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "term")

    def __str__(self) -> str:
        return f"{self.term.text} in {self.post.reddit_id}"