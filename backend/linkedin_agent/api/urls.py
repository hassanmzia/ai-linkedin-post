from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

router = DefaultRouter()
router.register(r"templates", views.PostTemplateViewSet, basename="template")
router.register(r"projects", views.PostProjectViewSet, basename="project")
router.register(r"runs", views.AgentRunViewSet, basename="run")
router.register(r"analytics", views.PostAnalyticsViewSet, basename="analytics")
router.register(r"hashtags", views.SavedHashtagViewSet, basename="hashtag")
router.register(r"calendar", views.ContentCalendarViewSet, basename="calendar")

urlpatterns = [
    # Auth
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", views.me_view, name="me"),
    # Config
    path("config/", views.APIConfigView.as_view(), name="api-config"),
    # Dashboard
    path("dashboard/", views.dashboard_stats, name="dashboard"),
    # CRUD routes
    path("", include(router.urls)),
]
