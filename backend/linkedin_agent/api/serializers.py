from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    APIConfiguration, PostTemplate, PostProject, AgentRun, AgentStep,
    ResearchFinding, PostDraft, PostAnalytics, SavedHashtag, ContentCalendar,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "date_joined"]
        read_only_fields = ["id", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password_confirm", "first_name", "last_name"]

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        APIConfiguration.objects.create(user=user)
        return user


class APIConfigurationSerializer(serializers.ModelSerializer):
    openai_api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    tavily_api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    has_openai_key = serializers.SerializerMethodField()
    has_tavily_key = serializers.SerializerMethodField()

    class Meta:
        model = APIConfiguration
        fields = [
            "openai_base_url", "openai_model", "openai_eval_model",
            "openai_api_key", "tavily_api_key",
            "has_openai_key", "has_tavily_key",
            "updated_at",
        ]

    def get_has_openai_key(self, obj):
        return bool(obj.openai_api_key)

    def get_has_tavily_key(self, obj):
        return bool(obj.tavily_api_key)


class PostTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostTemplate
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class AgentStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentStep
        fields = "__all__"


class ResearchFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResearchFinding
        fields = "__all__"


class PostDraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostDraft
        fields = "__all__"


class AgentRunSerializer(serializers.ModelSerializer):
    steps = AgentStepSerializer(many=True, read_only=True)
    findings = ResearchFindingSerializer(many=True, read_only=True)
    drafts = PostDraftSerializer(many=True, read_only=True)

    class Meta:
        model = AgentRun
        fields = "__all__"


class PostProjectListSerializer(serializers.ModelSerializer):
    draft_count = serializers.SerializerMethodField()
    latest_draft_preview = serializers.SerializerMethodField()

    class Meta:
        model = PostProject
        fields = [
            "id", "title", "topic", "status", "tone", "target_audience",
            "is_favorite", "tags", "final_post", "groundedness_score",
            "scheduled_at", "published_at", "created_at", "updated_at",
            "draft_count", "latest_draft_preview",
        ]

    def get_draft_count(self, obj):
        return obj.drafts.count()

    def get_latest_draft_preview(self, obj):
        draft = obj.drafts.order_by("-version").first()
        if draft:
            return draft.content[:200]
        return ""


class PostProjectDetailSerializer(serializers.ModelSerializer):
    runs = AgentRunSerializer(many=True, read_only=True)
    drafts = PostDraftSerializer(many=True, read_only=True)
    findings = ResearchFindingSerializer(many=True, read_only=True)
    template_detail = PostTemplateSerializer(source="template", read_only=True)

    class Meta:
        model = PostProject
        fields = "__all__"
        read_only_fields = ["id", "user", "created_at", "updated_at"]


class PostProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostProject
        fields = [
            "title", "topic", "template", "tone", "target_audience",
            "target_word_count_min", "target_word_count_max",
            "include_hashtags", "include_cta", "include_emoji", "language",
            "tags",
        ]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class PostAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostAnalytics
        fields = "__all__"
        read_only_fields = ["id", "recorded_at"]


class SavedHashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedHashtag
        fields = "__all__"
        read_only_fields = ["user", "usage_count"]


class ContentCalendarSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source="project.title", read_only=True, default="")

    class Meta:
        model = ContentCalendar
        fields = "__all__"
        read_only_fields = ["id", "user", "created_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class GeneratePostSerializer(serializers.Serializer):
    """Input serializer for triggering post generation."""
    project_id = serializers.UUIDField()


class RegeneratePostSerializer(serializers.Serializer):
    """Input for regenerating with feedback."""
    project_id = serializers.UUIDField()
    feedback = serializers.CharField(required=False, allow_blank=True, default="")


class EvaluatePostSerializer(serializers.Serializer):
    """Input for evaluating groundedness."""
    project_id = serializers.UUIDField()


class DashboardStatsSerializer(serializers.Serializer):
    total_projects = serializers.IntegerField()
    published_posts = serializers.IntegerField()
    avg_groundedness = serializers.FloatField(allow_null=True)
    total_revisions = serializers.IntegerField()
    posts_this_week = serializers.IntegerField()
    posts_this_month = serializers.IntegerField()
    top_tones = serializers.ListField()
    recent_projects = PostProjectListSerializer(many=True)
