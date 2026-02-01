from django.urls import path
from . import views

urlpatterns = [
    path("manifest/", views.mcp_manifest, name="mcp-manifest"),
    path("tools/list/", views.mcp_tools_list, name="mcp-tools-list"),
    path("tools/call/", views.mcp_tools_call, name="mcp-tools-call"),
    path("resources/list/", views.mcp_resources_list, name="mcp-resources-list"),
    path("resources/read/", views.mcp_resources_read, name="mcp-resources-read"),
]
