"""
Model Context Protocol (MCP) Server implementation.
Exposes LinkedIn Post Agent capabilities as MCP tools that can be
consumed by any MCP-compatible client (Claude Desktop, etc.).

Follows the MCP specification for tool discovery and invocation.
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

# MCP Tool definitions - expose agent capabilities as tools
MCP_TOOLS = [
    {
        "name": "generate_linkedin_post",
        "description": "Generate a professional LinkedIn post using a multi-agent AI system. "
                       "Uses Supervisor, Researcher, Writer, and Critic agents to produce "
                       "high-quality, research-backed LinkedIn content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic or prompt for the LinkedIn post"
                },
                "tone": {
                    "type": "string",
                    "enum": ["professional", "casual", "inspirational", "educational",
                             "storytelling", "controversial", "humorous"],
                    "description": "The tone of the post",
                    "default": "professional"
                },
                "target_audience": {
                    "type": "string",
                    "description": "The target audience for the post",
                    "default": "tech professionals"
                },
                "word_count_min": {"type": "integer", "default": 150},
                "word_count_max": {"type": "integer", "default": 300},
                "include_hashtags": {"type": "boolean", "default": True},
                "include_cta": {"type": "boolean", "default": True},
            },
            "required": ["topic"]
        }
    },
    {
        "name": "research_topic",
        "description": "Research a topic using web search and AI summarization. "
                       "Returns key findings, trends, and data points.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The research query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of search results",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "evaluate_post_groundedness",
        "description": "Evaluate how well a LinkedIn post is grounded in research findings. "
                       "Returns a score (0-5) and detailed analysis.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "post_content": {
                    "type": "string",
                    "description": "The LinkedIn post to evaluate"
                },
                "research_findings": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Research findings to check against"
                }
            },
            "required": ["post_content", "research_findings"]
        }
    },
    {
        "name": "critique_post",
        "description": "Get a detailed critique of a LinkedIn post draft based on "
                       "hook strength, clarity, value, structure, engagement potential, and tone.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "post_content": {
                    "type": "string",
                    "description": "The LinkedIn post to critique"
                },
                "tone": {
                    "type": "string",
                    "description": "Expected tone of the post",
                    "default": "professional"
                },
                "target_audience": {
                    "type": "string",
                    "description": "Target audience",
                    "default": "professionals"
                }
            },
            "required": ["post_content"]
        }
    },
    {
        "name": "list_post_templates",
        "description": "List available LinkedIn post templates with their tone and structure.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        }
    },
    {
        "name": "generate_hashtags",
        "description": "Generate relevant LinkedIn hashtags for a given post or topic.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Post content or topic to generate hashtags for"
                },
                "count": {
                    "type": "integer",
                    "description": "Number of hashtags to generate",
                    "default": 5
                }
            },
            "required": ["content"]
        }
    },
]

# MCP Resources - data the server exposes
MCP_RESOURCES = [
    {
        "uri": "linkedin-agent://templates",
        "name": "Post Templates",
        "description": "Available LinkedIn post templates",
        "mimeType": "application/json"
    },
    {
        "uri": "linkedin-agent://recent-posts",
        "name": "Recent Posts",
        "description": "Recently generated LinkedIn posts",
        "mimeType": "application/json"
    },
]


@csrf_exempt
@require_http_methods(["GET"])
def mcp_manifest(request):
    """MCP server manifest - describes capabilities."""
    return JsonResponse({
        "name": "linkedin-post-agent",
        "version": "1.0.0",
        "description": "Multi-Agent LinkedIn Post Creator with research, writing, critique, and evaluation capabilities.",
        "protocol_version": "2024-11-05",
        "capabilities": {
            "tools": {"listChanged": False},
            "resources": {"subscribe": False, "listChanged": False},
            "prompts": {"listChanged": False},
        },
    })


@csrf_exempt
@require_http_methods(["GET"])
def mcp_tools_list(request):
    """List available MCP tools."""
    return JsonResponse({"tools": MCP_TOOLS})


@csrf_exempt
@require_http_methods(["POST"])
def mcp_tools_call(request):
    """Execute an MCP tool call."""
    try:
        body = json.loads(request.body)
        tool_name = body.get("name")
        arguments = body.get("arguments", {})

        handler = TOOL_HANDLERS.get(tool_name)
        if not handler:
            return JsonResponse(
                {"error": f"Unknown tool: {tool_name}"},
                status=404
            )

        result = handler(arguments, request)
        return JsonResponse({
            "content": [{"type": "text", "text": json.dumps(result, default=str)}],
            "isError": False,
        })

    except Exception as e:
        logger.error(f"MCP tool call error: {e}", exc_info=True)
        return JsonResponse({
            "content": [{"type": "text", "text": str(e)}],
            "isError": True,
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def mcp_resources_list(request):
    """List available MCP resources."""
    return JsonResponse({"resources": MCP_RESOURCES})


@csrf_exempt
@require_http_methods(["POST"])
def mcp_resources_read(request):
    """Read an MCP resource."""
    try:
        body = json.loads(request.body)
        uri = body.get("uri", "")

        if uri == "linkedin-agent://templates":
            from linkedin_agent.api.models import PostTemplate
            templates = list(PostTemplate.objects.filter(is_system=True).values(
                "id", "name", "tone", "category", "description"
            ))
            return JsonResponse({
                "contents": [{"uri": uri, "mimeType": "application/json",
                              "text": json.dumps(templates, default=str)}]
            })

        if uri == "linkedin-agent://recent-posts":
            from linkedin_agent.api.models import PostProject
            posts = list(PostProject.objects.filter(
                status__in=["approved", "published"]
            ).order_by("-created_at")[:10].values(
                "id", "title", "topic", "tone", "final_post",
                "groundedness_score", "created_at"
            ))
            return JsonResponse({
                "contents": [{"uri": uri, "mimeType": "application/json",
                              "text": json.dumps(posts, default=str)}]
            })

        return JsonResponse({"error": f"Unknown resource: {uri}"}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# --- Tool Handler Implementations ---

def _handle_generate_post(args, request):
    """Handle generate_linkedin_post tool."""
    from linkedin_agent.api.models import PostProject, APIConfiguration
    from linkedin_agent.agents.workflow import LinkedInPostWorkflow

    # Use system config or request user config
    config = None
    if request.user.is_authenticated:
        config = APIConfiguration.objects.filter(user=request.user).first()

    if not config or not config.openai_api_key:
        return {"error": "API key not configured. Please configure OpenAI API key in settings."}

    workflow = LinkedInPostWorkflow(
        openai_api_key=config.openai_api_key,
        openai_base_url=config.openai_base_url,
        model_name=config.openai_model,
        tavily_api_key=config.tavily_api_key,
    )

    result = workflow.run(
        topic=args["topic"],
        tone=args.get("tone", "professional"),
        target_audience=args.get("target_audience", "tech professionals"),
        word_count_min=args.get("word_count_min", 150),
        word_count_max=args.get("word_count_max", 300),
        include_hashtags=args.get("include_hashtags", True),
        include_cta=args.get("include_cta", True),
    )

    return {
        "post": result.get("draft", ""),
        "revisions": result.get("revision_number", 0),
        "research_findings": result.get("research_findings", []),
    }


def _handle_research(args, request):
    """Handle research_topic tool."""
    from linkedin_agent.api.models import APIConfiguration
    from langchain_tavily import TavilySearch

    config = None
    if request.user.is_authenticated:
        config = APIConfiguration.objects.filter(user=request.user).first()

    if not config or not config.tavily_api_key:
        return {"error": "Tavily API key not configured."}

    tool = TavilySearch(
        max_results=args.get("max_results", 5),
        topic="general",
        search_depth="basic",
        api_key=config.tavily_api_key,
    )
    results = tool.invoke({"query": args["query"]})
    return {"results": results}


def _handle_evaluate(args, request):
    """Handle evaluate_post_groundedness tool."""
    from linkedin_agent.api.models import APIConfiguration
    from linkedin_agent.agents.workflow import LinkedInPostWorkflow

    config = None
    if request.user.is_authenticated:
        config = APIConfiguration.objects.filter(user=request.user).first()

    if not config or not config.openai_api_key:
        return {"error": "OpenAI API key not configured."}

    workflow = LinkedInPostWorkflow(
        openai_api_key=config.openai_api_key,
        openai_base_url=config.openai_base_url,
        eval_model_name=config.openai_eval_model,
    )
    return workflow.evaluate_groundedness(
        draft=args["post_content"],
        research_findings=args["research_findings"],
    )


def _handle_critique(args, request):
    """Handle critique_post tool."""
    from linkedin_agent.api.models import APIConfiguration
    from linkedin_agent.agents.prompts import CRITIC_PROMPT
    from langchain_openai import ChatOpenAI

    config = None
    if request.user.is_authenticated:
        config = APIConfiguration.objects.filter(user=request.user).first()

    if not config or not config.openai_api_key:
        return {"error": "OpenAI API key not configured."}

    llm_kwargs = {"model": config.openai_model, "temperature": 0, "api_key": config.openai_api_key}
    if config.openai_base_url:
        llm_kwargs["base_url"] = config.openai_base_url
    llm = ChatOpenAI(**llm_kwargs)

    prompt = CRITIC_PROMPT.format(
        main_task="",
        draft=args["post_content"],
        tone=args.get("tone", "professional"),
        target_audience=args.get("target_audience", "professionals"),
        word_count_min=150,
        word_count_max=300,
    )
    response = llm.invoke(prompt)
    return {"critique": response.content}


def _handle_list_templates(args, request):
    """Handle list_post_templates tool."""
    from linkedin_agent.api.models import PostTemplate
    templates = list(PostTemplate.objects.filter(is_system=True).values(
        "name", "tone", "category", "description", "structure_prompt"
    ))
    return {"templates": templates}


def _handle_generate_hashtags(args, request):
    """Handle generate_hashtags tool."""
    from linkedin_agent.api.models import APIConfiguration
    from linkedin_agent.agents.prompts import HASHTAG_GENERATOR_PROMPT
    from langchain_openai import ChatOpenAI

    config = None
    if request.user.is_authenticated:
        config = APIConfiguration.objects.filter(user=request.user).first()

    if not config or not config.openai_api_key:
        return {"error": "OpenAI API key not configured."}

    llm_kwargs = {"model": config.openai_model, "temperature": 0.3, "api_key": config.openai_api_key}
    if config.openai_base_url:
        llm_kwargs["base_url"] = config.openai_base_url
    llm = ChatOpenAI(**llm_kwargs)

    prompt = HASHTAG_GENERATOR_PROMPT.format(
        post_content=args["content"],
        topic=args["content"][:100],
        category="general",
    )
    response = llm.invoke(prompt)
    try:
        hashtags = json.loads(response.content)
    except json.JSONDecodeError:
        hashtags = [tag.strip() for tag in response.content.split(",")]
    return {"hashtags": hashtags[:args.get("count", 5)]}


TOOL_HANDLERS = {
    "generate_linkedin_post": _handle_generate_post,
    "research_topic": _handle_research,
    "evaluate_post_groundedness": _handle_evaluate,
    "critique_post": _handle_critique,
    "list_post_templates": _handle_list_templates,
    "generate_hashtags": _handle_generate_hashtags,
}
