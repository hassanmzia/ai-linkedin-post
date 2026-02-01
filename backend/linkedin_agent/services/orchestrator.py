"""
Orchestrator service - bridges Django models with the agent workflow.
Handles running agents, persisting state, and publishing real-time updates.
"""

import json
import logging
import time
from datetime import datetime, timezone

import redis
from django.conf import settings

from linkedin_agent.api.models import (
    PostProject, AgentRun, AgentStep, ResearchFinding, PostDraft, APIConfiguration,
)
from linkedin_agent.agents.workflow import LinkedInPostWorkflow

logger = logging.getLogger(__name__)


def get_redis_client():
    url = getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6452/0")
    return redis.from_url(url)


def publish_step(run_id: str, data: dict):
    """Publish agent step to Redis pub/sub for real-time WebSocket delivery."""
    try:
        r = get_redis_client()
        r.publish(f"agent_run:{run_id}", json.dumps(data, default=str))
    except Exception as e:
        logger.warning(f"Redis publish error: {e}")


def run_post_generation(project_id: str, user_id: int) -> dict:
    """Execute the multi-agent workflow for a project."""
    project = PostProject.objects.get(id=project_id)
    config = APIConfiguration.objects.get(user_id=user_id)

    if not config.openai_api_key:
        raise ValueError("OpenAI API key not configured. Go to Settings to add your key.")

    # Create agent run
    run = AgentRun.objects.create(
        project=project,
        status="running",
        started_at=datetime.now(timezone.utc),
    )

    project.status = "researching"
    project.save(update_fields=["status"])

    step_data_buffer = []

    def on_step(data):
        """Callback for each agent step."""
        step_data_buffer.append(data)
        agent_name = data.get("agent", "unknown")

        # Update project status based on agent
        status_map = {
            "supervisor": project.status,
            "researcher": "researching",
            "writer": "writing",
            "critic": "reviewing",
        }
        new_status = status_map.get(agent_name, project.status)
        if new_status != project.status:
            project.status = new_status
            project.save(update_fields=["status"])

        # Persist step
        AgentStep.objects.create(
            run=run,
            agent_name=agent_name if agent_name != "critic" else "critic",
            step_number=data.get("step", 0),
            output_data=data,
            decision=data.get("decision", data.get("task", "")),
            duration_ms=data.get("duration_ms"),
        )

        # Publish for WebSocket
        publish_step(str(run.id), {
            "type": "agent_step",
            "run_id": str(run.id),
            "project_id": str(project.id),
            **data,
        })

    try:
        # Build workflow
        workflow = LinkedInPostWorkflow(
            openai_api_key=config.openai_api_key,
            openai_base_url=config.openai_base_url,
            model_name=config.openai_model,
            eval_model_name=config.openai_eval_model,
            tavily_api_key=config.tavily_api_key,
            max_revisions=settings.AGENT_CONFIG.get("MAX_REVISIONS", 5),
            on_step=on_step,
        )

        # Template instructions
        template_instructions = ""
        if project.template:
            template_instructions = project.template.structure_prompt

        # Run the workflow
        result = workflow.run(
            topic=project.topic,
            tone=project.tone,
            target_audience=project.target_audience,
            word_count_min=project.target_word_count_min,
            word_count_max=project.target_word_count_max,
            language=project.language,
            include_hashtags=project.include_hashtags,
            include_cta=project.include_cta,
            include_emoji=project.include_emoji,
            template_instructions=template_instructions,
        )

        # Save research findings
        for i, finding in enumerate(result.get("research_findings", [])):
            ResearchFinding.objects.create(
                project=project,
                run=run,
                query=project.topic,
                summary=finding,
                sources=[],
            )

        # Save final draft
        draft = PostDraft.objects.create(
            project=project,
            run=run,
            version=result.get("revision_number", 1),
            content=result.get("draft", ""),
            is_approved="APPROVED" in result.get("critique_notes", "").upper(),
        )

        # Run groundedness evaluation
        try:
            eval_result = workflow.evaluate_groundedness(
                draft=result.get("draft", ""),
                research_findings=result.get("research_findings", []),
            )
            project.groundedness_score = eval_result.get("score", -1)
            project.groundedness_report = eval_result

            publish_step(str(run.id), {
                "type": "evaluation_complete",
                "run_id": str(run.id),
                "project_id": str(project.id),
                "groundedness_score": eval_result.get("score"),
                "report": eval_result,
            })
        except Exception as e:
            logger.warning(f"Groundedness evaluation failed: {e}")

        # Finalize
        project.final_post = result.get("draft", "")
        project.status = "approved"
        project.save()

        run.status = "completed"
        run.total_revisions = result.get("revision_number", 0)
        run.completed_at = datetime.now(timezone.utc)
        run.save()

        publish_step(str(run.id), {
            "type": "workflow_complete",
            "run_id": str(run.id),
            "project_id": str(project.id),
            "status": "completed",
            "final_post": result.get("draft", ""),
            "revisions": result.get("revision_number", 0),
            "groundedness_score": project.groundedness_score,
        })

        return {
            "run_id": str(run.id),
            "status": "completed",
            "final_post": result.get("draft", ""),
            "revisions": result.get("revision_number", 0),
            "groundedness_score": project.groundedness_score,
        }

    except Exception as e:
        logger.error(f"Workflow failed: {e}", exc_info=True)
        project.status = "failed"
        project.save(update_fields=["status"])
        run.status = "failed"
        run.error_message = str(e)
        run.completed_at = datetime.now(timezone.utc)
        run.save()

        publish_step(str(run.id), {
            "type": "workflow_error",
            "run_id": str(run.id),
            "project_id": str(project.id),
            "error": str(e),
        })

        raise
