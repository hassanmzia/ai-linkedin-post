from django.urls import path
from . import views

urlpatterns = [
    path("agents/", views.a2a_agents_list, name="a2a-agents-list"),
    path("agents/<str:agent_name>/", views.a2a_agent_card, name="a2a-agent-card"),
    path("agents/<str:agent_name>/invoke/", views.a2a_agent_invoke, name="a2a-agent-invoke"),
    path("tasks/<str:task_id>/", views.a2a_task_status, name="a2a-task-status"),
]
