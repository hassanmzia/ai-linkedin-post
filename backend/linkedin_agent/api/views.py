"""REST API views for the LinkedIn Post Agent."""

from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Avg, Sum, Count, Q

from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    APIConfiguration, PostTemplate, PostProject, AgentRun,
    PostAnalytics, SavedHashtag, ContentCalendar,
)
from .serializers import (
    UserSerializer, RegisterSerializer, APIConfigurationSerializer,
    PostTemplateSerializer, PostProjectListSerializer, PostProjectDetailSerializer,
    PostProjectCreateSerializer, AgentRunSerializer, PostAnalyticsSerializer,
    SavedHashtagSerializer, ContentCalendarSerializer, DashboardStatsSerializer,
)
from .tasks import generate_post_task, evaluate_post_task


# --- Auth ---

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": UserSerializer(user).data,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    return Response(UserSerializer(request.user).data)


# --- API Configuration ---

class APIConfigView(generics.RetrieveUpdateAPIView):
    serializer_class = APIConfigurationSerializer

    def get_object(self):
        obj, _ = APIConfiguration.objects.get_or_create(user=self.request.user)
        return obj


# --- Templates ---

class PostTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = PostTemplateSerializer

    def get_queryset(self):
        return PostTemplate.objects.filter(
            Q(is_system=True) | Q(user=self.request.user)
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# --- Projects ---

class PostProjectViewSet(viewsets.ModelViewSet):
    filterset_fields = ["status", "tone", "is_favorite"]
    search_fields = ["title", "topic", "tags"]
    ordering_fields = ["created_at", "updated_at", "groundedness_score"]

    def get_queryset(self):
        return PostProject.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return PostProjectCreateSerializer
        if self.action in ("retrieve",):
            return PostProjectDetailSerializer
        return PostProjectListSerializer

    @action(detail=True, methods=["post"])
    def generate(self, request, pk=None):
        """Trigger the multi-agent workflow for this project."""
        project = self.get_object()
        if project.status in ("researching", "writing", "reviewing"):
            return Response(
                {"error": "A generation is already in progress."},
                status=status.HTTP_409_CONFLICT,
            )

        project.status = "draft"
        project.save(update_fields=["status"])

        task = generate_post_task.delay(str(project.id), request.user.id)
        return Response({
            "message": "Post generation started",
            "task_id": task.id,
            "project_id": str(project.id),
        })

    @action(detail=True, methods=["post"])
    def regenerate(self, request, pk=None):
        """Regenerate with optional user feedback."""
        project = self.get_object()
        feedback = request.data.get("feedback", "")
        if feedback:
            project.topic = f"{project.topic}\n\nAdditional instructions: {feedback}"
            project.save(update_fields=["topic"])

        project.status = "draft"
        project.final_post = ""
        project.groundedness_score = None
        project.groundedness_report = None
        project.save()

        task = generate_post_task.delay(str(project.id), request.user.id)
        return Response({
            "message": "Regeneration started",
            "task_id": task.id,
        })

    @action(detail=True, methods=["post"])
    def evaluate(self, request, pk=None):
        """Evaluate groundedness of the current post."""
        project = self.get_object()
        if not project.final_post:
            return Response(
                {"error": "No final post to evaluate."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task = evaluate_post_task.delay(str(project.id), request.user.id)
        return Response({"message": "Evaluation started", "task_id": task.id})

    @action(detail=True, methods=["post"])
    def toggle_favorite(self, request, pk=None):
        project = self.get_object()
        project.is_favorite = not project.is_favorite
        project.save(update_fields=["is_favorite"])
        return Response({"is_favorite": project.is_favorite})

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        project = self.get_object()
        project.status = "published"
        project.published_at = timezone.now()
        project.save(update_fields=["status", "published_at"])
        return Response({"status": "published"})

    @action(detail=True, methods=["post"])
    def update_post(self, request, pk=None):
        """Manually edit the final post."""
        project = self.get_object()
        new_content = request.data.get("content", "")
        if new_content:
            project.final_post = new_content
            project.save(update_fields=["final_post"])
        return Response({"final_post": project.final_post})


# --- Agent Runs ---

class AgentRunViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AgentRunSerializer

    def get_queryset(self):
        return AgentRun.objects.filter(
            project__user=self.request.user
        ).select_related("project").prefetch_related("steps", "findings", "drafts")


# --- Analytics ---

class PostAnalyticsViewSet(viewsets.ModelViewSet):
    serializer_class = PostAnalyticsSerializer

    def get_queryset(self):
        return PostAnalytics.objects.filter(project__user=self.request.user)


# --- Hashtags ---

class SavedHashtagViewSet(viewsets.ModelViewSet):
    serializer_class = SavedHashtagSerializer

    def get_queryset(self):
        return SavedHashtag.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# --- Content Calendar ---

class ContentCalendarViewSet(viewsets.ModelViewSet):
    serializer_class = ContentCalendarSerializer
    filterset_fields = ["is_completed", "scheduled_date"]

    def get_queryset(self):
        qs = ContentCalendar.objects.filter(user=self.request.user)
        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")
        if start:
            qs = qs.filter(scheduled_date__gte=start)
        if end:
            qs = qs.filter(scheduled_date__lte=end)
        return qs


# --- Dashboard ---

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    user = request.user
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    projects = PostProject.objects.filter(user=user)

    stats = {
        "total_projects": projects.count(),
        "published_posts": projects.filter(status="published").count(),
        "avg_groundedness": projects.filter(
            groundedness_score__isnull=False
        ).aggregate(avg=Avg("groundedness_score"))["avg"],
        "total_revisions": AgentRun.objects.filter(
            project__user=user
        ).aggregate(total=Sum("total_revisions"))["total"] or 0,
        "posts_this_week": projects.filter(created_at__gte=week_ago).count(),
        "posts_this_month": projects.filter(created_at__gte=month_ago).count(),
        "top_tones": list(
            projects.values("tone")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        ),
        "recent_projects": PostProjectListSerializer(
            projects[:5], many=True
        ).data,
    }

    return Response(stats)
