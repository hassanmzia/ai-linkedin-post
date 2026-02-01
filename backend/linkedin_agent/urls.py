from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("linkedin_agent.api.urls")),
    path("a2a/", include("linkedin_agent.a2a.urls")),
    path("mcp/", include("linkedin_agent.mcp.urls")),
]
