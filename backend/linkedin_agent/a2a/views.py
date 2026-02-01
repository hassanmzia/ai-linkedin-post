"""
Agent-to-Agent (A2A) Protocol implementation.
Enables inter-agent communication following the A2A specification.
Each agent (Supervisor, Researcher, Writer, Critic) is exposed as an
A2A-compatible endpoint that can be called by other agents or external systems.
"""

import json
import uuid
import logging
from datetime import datetime, timezone

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

# A2A Agent Cards - describe each agent's capabilities
AGENT_CARDS = {
    "supervisor": {
        "name": "LinkedIn Post Supervisor",
        "description": "Orchestrates the multi-agent LinkedIn post creation workflow. "
                       "Makes routing decisions based on current state.",
        "url": "/a2a/agents/supervisor/",
        "version": "1.0.0",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "stateTransitionHistory": True,
        },
        "skills": [
            {
                "id": "route-workflow",
                "name": "Route Workflow",
                "description": "Decide next step in the post creation workflow",
                "inputModes": ["application/json"],
                "outputModes": ["application/json"],
            }
        ],
    },
    "researcher": {
        "name": "LinkedIn Post Researcher",
        "description": "Researches topics using web search (Tavily) and AI summarization. "
                       "Finds trends, data, and insights for LinkedIn post creation.",
        "url": "/a2a/agents/researcher/",
        "version": "1.0.0",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "stateTransitionHistory": False,
        },
        "skills": [
            {
                "id": "research-topic",
                "name": "Research Topic",
                "description": "Research a topic and return summarized findings",
                "inputModes": ["text/plain", "application/json"],
                "outputModes": ["application/json"],
            }
        ],
    },
    "writer": {
        "name": "LinkedIn Post Writer",
        "description": "Creates and revises LinkedIn posts based on research findings "
                       "and critique feedback. Supports multiple tones and styles.",
        "url": "/a2a/agents/writer/",
        "version": "1.0.0",
        "capabilities": {
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionHistory": False,
        },
        "skills": [
            {
                "id": "write-post",
                "name": "Write Post",
                "description": "Write or revise a LinkedIn post",
                "inputModes": ["application/json"],
                "outputModes": ["text/plain", "application/json"],
            }
        ],
    },
    "critic": {
        "name": "LinkedIn Post Critic",
        "description": "Evaluates LinkedIn post drafts against quality criteria including "
                       "hook strength, clarity, value, structure, engagement, and tone.",
        "url": "/a2a/agents/critic/",
        "version": "1.0.0",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "stateTransitionHistory": False,
        },
        "skills": [
            {
                "id": "critique-post",
                "name": "Critique Post",
                "description": "Review and critique a LinkedIn post draft",
                "inputModes": ["text/plain", "application/json"],
                "outputModes": ["application/json"],
            }
        ],
    },
    "evaluator": {
        "name": "LinkedIn Post Evaluator",
        "description": "Evaluates the groundedness of LinkedIn posts by verifying "
                       "claims against research findings. Uses a more powerful model.",
        "url": "/a2a/agents/evaluator/",
        "version": "1.0.0",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "stateTransitionHistory": False,
        },
        "skills": [
            {
                "id": "evaluate-groundedness",
                "name": "Evaluate Groundedness",
                "description": "Check if post claims are supported by research",
                "inputModes": ["application/json"],
                "outputModes": ["application/json"],
            }
        ],
    },
}


@csrf_exempt
@require_http_methods(["GET"])
def a2a_agent_card(request, agent_name):
    """Return the A2A agent card for a specific agent."""
    card = AGENT_CARDS.get(agent_name)
    if not card:
        return JsonResponse({"error": f"Unknown agent: {agent_name}"}, status=404)
    return JsonResponse(card)


@csrf_exempt
@require_http_methods(["GET"])
def a2a_agents_list(request):
    """List all available A2A agents."""
    return JsonResponse({"agents": list(AGENT_CARDS.values())})


@csrf_exempt
@require_http_methods(["POST"])
def a2a_agent_invoke(request, agent_name):
    """
    Invoke an A2A agent with a task.
    Follows the A2A task lifecycle: submitted -> working -> completed/failed.
    """
    if agent_name not in AGENT_CARDS:
        return JsonResponse({"error": f"Unknown agent: {agent_name}"}, status=404)

    try:
        body = json.loads(request.body)
        task_id = body.get("id", str(uuid.uuid4()))
        message = body.get("message", {})

        # Create A2A task response
        task = {
            "id": task_id,
            "status": {
                "state": "working",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "artifacts": [],
        }

        handler = A2A_HANDLERS.get(agent_name)
        if handler:
            result = handler(message, request)
            task["status"]["state"] = "completed"
            task["artifacts"] = [
                {
                    "name": f"{agent_name}_output",
                    "parts": [{"type": "application/json", "data": result}],
                }
            ]
        else:
            task["status"]["state"] = "failed"
            task["status"]["message"] = f"No handler for agent: {agent_name}"

        task["status"]["timestamp"] = datetime.now(timezone.utc).isoformat()
        return JsonResponse({"jsonrpc": "2.0", "result": task})

    except Exception as e:
        logger.error(f"A2A invoke error for {agent_name}: {e}", exc_info=True)
        return JsonResponse({
            "jsonrpc": "2.0",
            "error": {"code": -32000, "message": str(e)},
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def a2a_task_status(request, task_id):
    """Check the status of an A2A task."""
    # For synchronous execution, tasks complete immediately
    return JsonResponse({
        "jsonrpc": "2.0",
        "result": {
            "id": task_id,
            "status": {"state": "completed"},
        }
    })


# --- A2A Agent Handlers ---

def _a2a_supervisor(message, request):
    """Supervisor agent handler for A2A."""
    data = message.get("parts", [{}])[0].get("data", {})
    from linkedin_agent.agents.workflow import LinkedInPostWorkflow
    from linkedin_agent.api.models import APIConfiguration

    config = APIConfiguration.objects.filter(user=request.user).first() if request.user.is_authenticated else None
    if not config:
        return {"error": "No API configuration found"}

    # Mimic supervisor decision logic
    research = data.get("research_findings", [])
    revision = data.get("revision_number", 0)
    has_research = len(research) > 0
    has_draft = bool(data.get("draft", "").strip())
    critique = data.get("critique_notes", "")

    if "APPROVED" in critique.upper() and has_draft:
        return {"next_step": "END", "task_description": "Draft approved"}
    elif not has_research:
        return {"next_step": "researcher", "task_description": f"Research: {data.get('main_task', '')}"}
    elif has_research and not has_draft:
        return {"next_step": "writer", "task_description": "Write first draft"}
    elif critique and "APPROVED" not in critique.upper() and revision < 5:
        return {"next_step": "writer", "task_description": "Revise based on feedback"}
    else:
        return {"next_step": "END", "task_description": "Finalizing"}


def _a2a_researcher(message, request):
    """Researcher agent handler for A2A."""
    data = message.get("parts", [{}])[0].get("data", {})
    query = data.get("query", data.get("topic", ""))

    from linkedin_agent.api.models import APIConfiguration
    config = APIConfiguration.objects.filter(user=request.user).first() if request.user.is_authenticated else None
    if not config or not config.tavily_api_key:
        return {"findings": f"General research on: {query}"}

    from langchain_tavily import TavilySearch
    from langchain_openai import ChatOpenAI

    tool = TavilySearch(max_results=5, topic="general", search_depth="basic", api_key=config.tavily_api_key)
    results = tool.invoke({"query": query})

    llm_kwargs = {"model": config.openai_model, "temperature": 0, "api_key": config.openai_api_key}
    if config.openai_base_url:
        llm_kwargs["base_url"] = config.openai_base_url
    llm = ChatOpenAI(**llm_kwargs)

    summary_prompt = f"Summarize key findings (5-7 bullet points) about '{query}':\n{json.dumps(results[:3], default=str)}"
    response = llm.invoke(summary_prompt)

    return {"findings": response.content, "sources": results[:3]}


def _a2a_writer(message, request):
    """Writer agent handler for A2A."""
    data = message.get("parts", [{}])[0].get("data", {})

    from linkedin_agent.api.models import APIConfiguration
    from linkedin_agent.agents.prompts import WRITER_PROMPT
    from langchain_openai import ChatOpenAI

    config = APIConfiguration.objects.filter(user=request.user).first() if request.user.is_authenticated else None
    if not config or not config.openai_api_key:
        return {"error": "No API configuration found"}

    llm_kwargs = {"model": config.openai_model, "temperature": 0, "api_key": config.openai_api_key}
    if config.openai_base_url:
        llm_kwargs["base_url"] = config.openai_base_url
    llm = ChatOpenAI(**llm_kwargs)

    research = data.get("research_findings", [])
    prompt = WRITER_PROMPT.format(
        main_task=data.get("main_task", ""),
        research_findings="\n\n".join(research) if research else "No research.",
        draft=data.get("draft", ""),
        critique_notes=data.get("critique_notes", ""),
        tone=data.get("tone", "professional"),
        target_audience=data.get("target_audience", "professionals"),
        word_count_min=data.get("word_count_min", 150),
        word_count_max=data.get("word_count_max", 300),
        language=data.get("language", "English"),
        include_hashtags=data.get("include_hashtags", True),
        include_cta=data.get("include_cta", True),
        include_emoji=data.get("include_emoji", False),
        template_instructions=data.get("template_instructions", ""),
    )

    response = llm.invoke(prompt)
    return {"draft": response.content, "word_count": len(response.content.split())}


def _a2a_critic(message, request):
    """Critic agent handler for A2A."""
    data = message.get("parts", [{}])[0].get("data", {})

    from linkedin_agent.api.models import APIConfiguration
    from linkedin_agent.agents.prompts import CRITIC_PROMPT
    from langchain_openai import ChatOpenAI

    config = APIConfiguration.objects.filter(user=request.user).first() if request.user.is_authenticated else None
    if not config or not config.openai_api_key:
        return {"error": "No API configuration found"}

    llm_kwargs = {"model": config.openai_model, "temperature": 0, "api_key": config.openai_api_key}
    if config.openai_base_url:
        llm_kwargs["base_url"] = config.openai_base_url
    llm = ChatOpenAI(**llm_kwargs)

    prompt = CRITIC_PROMPT.format(
        main_task=data.get("main_task", ""),
        draft=data.get("draft", ""),
        tone=data.get("tone", "professional"),
        target_audience=data.get("target_audience", "professionals"),
        word_count_min=data.get("word_count_min", 150),
        word_count_max=data.get("word_count_max", 300),
    )

    response = llm.invoke(prompt)
    approved = "APPROVED" in response.content.upper()
    return {"critique": response.content, "approved": approved}


def _a2a_evaluator(message, request):
    """Evaluator agent handler for A2A."""
    data = message.get("parts", [{}])[0].get("data", {})

    from linkedin_agent.api.models import APIConfiguration
    from linkedin_agent.agents.workflow import LinkedInPostWorkflow

    config = APIConfiguration.objects.filter(user=request.user).first() if request.user.is_authenticated else None
    if not config or not config.openai_api_key:
        return {"error": "No API configuration found"}

    workflow = LinkedInPostWorkflow(
        openai_api_key=config.openai_api_key,
        openai_base_url=config.openai_base_url,
        eval_model_name=config.openai_eval_model,
    )
    return workflow.evaluate_groundedness(
        draft=data.get("draft", ""),
        research_findings=data.get("research_findings", []),
    )


A2A_HANDLERS = {
    "supervisor": _a2a_supervisor,
    "researcher": _a2a_researcher,
    "writer": _a2a_writer,
    "critic": _a2a_critic,
    "evaluator": _a2a_evaluator,
}
