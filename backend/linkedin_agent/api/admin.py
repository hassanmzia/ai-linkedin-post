from django.contrib import admin
from .models import (
    APIConfiguration, PostTemplate, PostProject, AgentRun, AgentStep,
    ResearchFinding, PostDraft, PostAnalytics, SavedHashtag, ContentCalendar,
)

admin.site.site_header = "LinkedIn Post Agent Admin"

@admin.register(APIConfiguration)
class APIConfigurationAdmin(admin.ModelAdmin):
    list_display = ["user", "openai_model", "updated_at"]

@admin.register(PostTemplate)
class PostTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "tone", "category", "is_system", "created_at"]
    list_filter = ["tone", "category", "is_system"]

@admin.register(PostProject)
class PostProjectAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "status", "tone", "groundedness_score", "created_at"]
    list_filter = ["status", "tone"]
    search_fields = ["title", "topic"]

@admin.register(AgentRun)
class AgentRunAdmin(admin.ModelAdmin):
    list_display = ["id", "project", "status", "total_revisions", "created_at"]
    list_filter = ["status"]

@admin.register(AgentStep)
class AgentStepAdmin(admin.ModelAdmin):
    list_display = ["agent_name", "step_number", "decision", "duration_ms", "created_at"]
    list_filter = ["agent_name"]

@admin.register(ResearchFinding)
class ResearchFindingAdmin(admin.ModelAdmin):
    list_display = ["project", "query", "created_at"]

@admin.register(PostDraft)
class PostDraftAdmin(admin.ModelAdmin):
    list_display = ["project", "version", "word_count", "is_approved", "created_at"]

@admin.register(PostAnalytics)
class PostAnalyticsAdmin(admin.ModelAdmin):
    list_display = ["project", "impressions", "likes", "comments", "shares", "recorded_at"]

@admin.register(SavedHashtag)
class SavedHashtagAdmin(admin.ModelAdmin):
    list_display = ["user", "tag", "category", "usage_count"]

@admin.register(ContentCalendar)
class ContentCalendarAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "scheduled_date", "is_completed"]
    list_filter = ["is_completed"]
