"""Celery tasks for async agent execution."""

from celery import shared_task
from linkedin_agent.services.orchestrator import run_post_generation


@shared_task(bind=True, max_retries=1, time_limit=600)
def generate_post_task(self, project_id: str, user_id: int):
    """Async task to run the multi-agent post generation workflow."""
    try:
        result = run_post_generation(project_id, user_id)
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)


@shared_task(bind=True, max_retries=1, time_limit=300)
def evaluate_post_task(self, project_id: str, user_id: int):
    """Async task to evaluate groundedness of a post."""
    from linkedin_agent.api.models import PostProject, APIConfiguration
    from linkedin_agent.agents.workflow import LinkedInPostWorkflow

    project = PostProject.objects.get(id=project_id)
    config = APIConfiguration.objects.get(user_id=user_id)

    workflow = LinkedInPostWorkflow(
        openai_api_key=config.openai_api_key,
        openai_base_url=config.openai_base_url,
        model_name=config.openai_model,
        eval_model_name=config.openai_eval_model,
        tavily_api_key=config.tavily_api_key,
    )

    findings = list(project.findings.values_list("summary", flat=True))
    result = workflow.evaluate_groundedness(
        draft=project.final_post,
        research_findings=findings,
    )

    project.groundedness_score = result.get("score", -1)
    project.groundedness_report = result
    project.save(update_fields=["groundedness_score", "groundedness_report"])

    return result
