import uuid
from django.db import models
from django.contrib.auth.models import User


class APIConfiguration(models.Model):
    """Per-user API key configuration."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="api_config")
    openai_api_key = models.CharField(max_length=500, blank=True, default="")
    openai_base_url = models.CharField(max_length=500, blank=True, default="")
    openai_model = models.CharField(max_length=100, default="gpt-4o-mini")
    openai_eval_model = models.CharField(max_length=100, default="gpt-4o")
    tavily_api_key = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Config for {self.user.username}"


class PostTemplate(models.Model):
    """Reusable LinkedIn post templates."""
    TONE_CHOICES = [
        ("professional", "Professional"),
        ("casual", "Casual"),
        ("inspirational", "Inspirational"),
        ("educational", "Educational"),
        ("storytelling", "Storytelling"),
        ("controversial", "Controversial / Hot Take"),
        ("humorous", "Humorous"),
    ]
    CATEGORY_CHOICES = [
        ("tech", "Technology"),
        ("leadership", "Leadership"),
        ("career", "Career Growth"),
        ("startup", "Startup / Entrepreneurship"),
        ("ai_ml", "AI / Machine Learning"),
        ("productivity", "Productivity"),
        ("marketing", "Marketing"),
        ("custom", "Custom"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    tone = models.CharField(max_length=50, choices=TONE_CHOICES, default="professional")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="tech")
    structure_prompt = models.TextField(
        help_text="Custom structure instructions for the writer agent"
    )
    example_post = models.TextField(blank=True, default="")
    is_system = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="templates")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class PostProject(models.Model):
    """A LinkedIn post generation project / session."""
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("researching", "Researching"),
        ("writing", "Writing"),
        ("reviewing", "Reviewing"),
        ("approved", "Approved"),
        ("published", "Published"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects")
    title = models.CharField(max_length=500)
    topic = models.TextField(help_text="The main topic/prompt for LinkedIn post generation")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    template = models.ForeignKey(PostTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    tone = models.CharField(max_length=50, default="professional")
    target_audience = models.CharField(max_length=200, blank=True, default="")
    target_word_count_min = models.IntegerField(default=150)
    target_word_count_max = models.IntegerField(default=300)
    include_hashtags = models.BooleanField(default=True)
    include_cta = models.BooleanField(default=True)
    include_emoji = models.BooleanField(default=False)
    language = models.CharField(max_length=50, default="English")

    # Final output
    final_post = models.TextField(blank=True, default="")
    groundedness_score = models.FloatField(null=True, blank=True)
    groundedness_report = models.JSONField(null=True, blank=True)

    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    is_favorite = models.BooleanField(default=False)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.status})"


class AgentRun(models.Model):
    """Tracks a single agent workflow execution."""
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(PostProject, on_delete=models.CASCADE, related_name="runs")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_revisions = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class AgentStep(models.Model):
    """Individual step within an agent run."""
    AGENT_CHOICES = [
        ("supervisor", "Supervisor"),
        ("researcher", "Researcher"),
        ("writer", "Writer"),
        ("critic", "Critic"),
        ("evaluator", "Evaluator"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run = models.ForeignKey(AgentRun, on_delete=models.CASCADE, related_name="steps")
    agent_name = models.CharField(max_length=50, choices=AGENT_CHOICES)
    step_number = models.IntegerField()
    input_data = models.JSONField(default=dict, blank=True)
    output_data = models.JSONField(default=dict, blank=True)
    decision = models.CharField(max_length=200, blank=True, default="")
    duration_ms = models.IntegerField(null=True, blank=True)
    tokens_used = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["step_number"]


class ResearchFinding(models.Model):
    """Research findings collected during agent runs."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(PostProject, on_delete=models.CASCADE, related_name="findings")
    run = models.ForeignKey(AgentRun, on_delete=models.CASCADE, related_name="findings")
    query = models.TextField()
    summary = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    raw_results = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class PostDraft(models.Model):
    """Draft versions of the post."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(PostProject, on_delete=models.CASCADE, related_name="drafts")
    run = models.ForeignKey(AgentRun, on_delete=models.CASCADE, related_name="drafts")
    version = models.IntegerField()
    content = models.TextField()
    word_count = models.IntegerField(default=0)
    critique_notes = models.TextField(blank=True, default="")
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["version"]

    def save(self, *args, **kwargs):
        self.word_count = len(self.content.split())
        super().save(*args, **kwargs)


class PostAnalytics(models.Model):
    """Track post performance analytics (manual or via LinkedIn API)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(PostProject, on_delete=models.CASCADE, related_name="analytics")
    impressions = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    clicks = models.IntegerField(default=0)
    engagement_rate = models.FloatField(default=0.0)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at"]


class SavedHashtag(models.Model):
    """User's saved hashtag collections."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="hashtags")
    tag = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True, default="")
    usage_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ("user", "tag")
        ordering = ["-usage_count"]


class ContentCalendar(models.Model):
    """Content calendar for planning posts."""
    RECURRENCE_CHOICES = [
        ("none", "None"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("biweekly", "Bi-weekly"),
        ("monthly", "Monthly"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="calendar_entries")
    project = models.ForeignKey(PostProject, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, default="")
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField(null=True, blank=True)
    recurrence = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, default="none")
    is_completed = models.BooleanField(default=False)
    color = models.CharField(max_length=7, default="#3B82F6")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["scheduled_date", "scheduled_time"]
