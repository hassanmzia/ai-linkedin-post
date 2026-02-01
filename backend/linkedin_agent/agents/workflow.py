"""
Multi-Agent LinkedIn Post Creator Workflow.
Faithfully ported from the Jupyter notebook with enhancements for production use.
"""

import json
import time
import logging
from typing import TypedDict, Annotated, List, Optional, Callable
import operator

from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, END

from .prompts import (
    SUPERVISOR_PROMPT, RESEARCHER_PROMPT, WRITER_PROMPT,
    CRITIC_PROMPT, GROUNDEDNESS_PROMPT,
)

logger = logging.getLogger(__name__)


class ResearchState(TypedDict):
    """State for the research workflow - matches notebook exactly."""
    main_task: str
    research_findings: Annotated[List[str], operator.add]
    draft: str
    critique_notes: str
    revision_number: int
    next_step: str
    current_sub_task: str
    # Enhanced fields
    tone: str
    target_audience: str
    word_count_min: int
    word_count_max: int
    language: str
    include_hashtags: bool
    include_cta: bool
    include_emoji: bool
    template_instructions: str
    max_revisions: int


class LinkedInPostWorkflow:
    """Encapsulates the entire multi-agent workflow from the notebook."""

    def __init__(
        self,
        openai_api_key: str,
        openai_base_url: str = "",
        model_name: str = "gpt-4o-mini",
        eval_model_name: str = "gpt-4o",
        tavily_api_key: str = "",
        max_revisions: int = 5,
        on_step: Optional[Callable] = None,
    ):
        self.on_step = on_step  # callback for real-time updates
        self.max_revisions = max_revisions
        self.step_counter = 0

        # Primary LLM
        llm_kwargs = {
            "model": model_name,
            "temperature": 0,
            "max_tokens": 4096,
            "api_key": openai_api_key,
        }
        if openai_base_url:
            llm_kwargs["base_url"] = openai_base_url
        self.llm = ChatOpenAI(**llm_kwargs)

        # Eval LLM
        eval_kwargs = {
            "model": eval_model_name,
            "temperature": 0,
            "max_tokens": 4096,
            "api_key": openai_api_key,
        }
        if openai_base_url:
            eval_kwargs["base_url"] = openai_base_url
        self.eval_llm = ChatOpenAI(**eval_kwargs)

        # Tavily search tool
        self.tavily_tool = None
        if tavily_api_key:
            self.tavily_tool = TavilySearch(
                max_results=5,
                topic="general",
                include_answer=False,
                include_raw_content=False,
                search_depth="basic",
                api_key=tavily_api_key,
            )

        # Build the graph
        self.app = self._build_graph()

    def _emit_step(self, agent_name: str, data: dict):
        self.step_counter += 1
        if self.on_step:
            self.on_step({
                "step": self.step_counter,
                "agent": agent_name,
                **data,
            })

    def _supervisor_node(self, state: ResearchState) -> dict:
        """Supervisor decides the next step - deterministic first, LLM fallback."""
        start = time.time()
        research = state.get("research_findings", [])
        revision = state.get("revision_number", 0)
        has_research = len(research) > 0
        has_draft = bool(state.get("draft", "").strip())
        critique = state.get("critique_notes", "")
        max_rev = state.get("max_revisions", self.max_revisions)

        decision = None

        # Deterministic decision logic (from notebook)
        if "APPROVED" in critique.upper() and has_draft:
            decision = {"next_step": "END", "task_description": "Draft approved and complete"}
        elif not has_research:
            decision = {"next_step": "researcher", "task_description": f"Research the topic: {state.get('main_task', '')}"}
        elif has_research and not has_draft:
            decision = {"next_step": "writer", "task_description": "Write the first draft based on research findings"}
        elif has_draft and not critique:
            decision = {"next_step": "writer", "task_description": "Prepare draft for critique"}
        elif critique and "APPROVED" not in critique.upper() and revision < max_rev:
            decision = {"next_step": "writer", "task_description": "Revise the draft based on critique feedback"}
        elif revision >= max_rev:
            decision = {"next_step": "END", "task_description": "Maximum revisions reached, finalizing"}

        # LLM fallback
        if not decision:
            try:
                research_text = "\n---\n".join(research) if research else "No research yet."
                prompt = SUPERVISOR_PROMPT.format(
                    main_task=state.get("main_task", ""),
                    research_findings=research_text,
                    draft=state.get("draft", "No draft yet."),
                    critique_notes=critique or "No critique yet.",
                    revision_number=revision,
                    tone=state.get("tone", "professional"),
                    target_audience=state.get("target_audience", "professionals"),
                    word_count_min=state.get("word_count_min", 150),
                    word_count_max=state.get("word_count_max", 300),
                    language=state.get("language", "English"),
                    max_revisions=max_rev,
                )
                response = self.llm.invoke(prompt)
                text = response.content.strip()
                if text.startswith("```"):
                    lines = text.split("\n")
                    text = "\n".join([l for l in lines if not l.strip().startswith("```")])
                decision = json.loads(text.strip())
            except Exception as e:
                logger.warning(f"Supervisor LLM fallback error: {e}")
                decision = {"next_step": "writer", "task_description": "Continue with draft creation"}

        duration = int((time.time() - start) * 1000)
        self._emit_step("supervisor", {
            "decision": decision["next_step"],
            "task": decision["task_description"],
            "duration_ms": duration,
        })

        return {
            "next_step": decision["next_step"],
            "current_sub_task": decision["task_description"],
        }

    def _research_node(self, state: ResearchState) -> dict:
        """Research node that gathers information via Tavily."""
        start = time.time()
        sub_task = state.get("current_sub_task", state.get("main_task"))
        findings = f"Research on {sub_task} - general information gathered"
        sources = []

        if self.tavily_tool:
            try:
                search_response = self.tavily_tool.invoke({"query": sub_task})
                results = search_response if isinstance(search_response, list) else search_response.get("results", [])

                formatted_results = []
                for result in results[:3]:
                    if isinstance(result, dict):
                        title = result.get("title", "Untitled")
                        url = result.get("url", "N/A")
                        content = result.get("content", "")
                        formatted_results.append(f"**{title}**\nSource: {url}\n{content[:300]}...")
                        sources.append({"title": title, "url": url})

                if formatted_results:
                    raw_output = "\n---\n".join(formatted_results)
                    audience = state.get("target_audience", "professionals")
                    summary_prompt = (
                        f"Based on these search results about '{sub_task}' for an audience of {audience}, "
                        f"provide a concise summary of key findings (5-7 bullet points):\n{raw_output}\n"
                        f"Format as clear bullet points with the most important information."
                    )
                    summary_response = self.llm.invoke(summary_prompt)
                    findings = summary_response.content
            except Exception as e:
                logger.error(f"Research error: {e}")
                findings = f"Research on {sub_task} - information gathered from web sources."

        duration = int((time.time() - start) * 1000)
        self._emit_step("researcher", {
            "query": sub_task,
            "findings_preview": findings[:200],
            "sources": sources,
            "duration_ms": duration,
        })

        return {"research_findings": [findings]}

    def _write_node(self, state: ResearchState) -> dict:
        """Writer node that creates or revises draft."""
        start = time.time()
        research = state.get("research_findings", [])
        research_text = "\n\n".join(research) if research else "No research available."

        prompt = WRITER_PROMPT.format(
            main_task=state.get("main_task", ""),
            research_findings=research_text,
            draft=state.get("draft", ""),
            critique_notes=state.get("critique_notes", ""),
            tone=state.get("tone", "professional"),
            target_audience=state.get("target_audience", "professionals"),
            word_count_min=state.get("word_count_min", 150),
            word_count_max=state.get("word_count_max", 300),
            language=state.get("language", "English"),
            include_hashtags=state.get("include_hashtags", True),
            include_cta=state.get("include_cta", True),
            include_emoji=state.get("include_emoji", False),
            template_instructions=state.get("template_instructions", ""),
        )

        try:
            response = self.llm.invoke(prompt)
            draft = response.content if response.content else "Draft in progress..."
        except Exception as e:
            logger.error(f"Writer error: {e}")
            draft = "Error generating draft. Please try again."

        duration = int((time.time() - start) * 1000)
        revision = state.get("revision_number", 0) + 1
        self._emit_step("writer", {
            "revision": revision,
            "word_count": len(draft.split()),
            "draft_preview": draft[:200],
            "duration_ms": duration,
        })

        return {
            "draft": draft,
            "revision_number": revision,
        }

    def _critique_node(self, state: ResearchState) -> dict:
        """Critique node that reviews the draft."""
        start = time.time()
        draft = state.get("draft", "")
        revision_num = state.get("revision_number", 0)
        max_rev = state.get("max_revisions", self.max_revisions)

        # Safety checks (from notebook)
        if len(draft.strip()) < 100:
            critique = "APPROVED - Draft is minimal but acceptable."
        elif revision_num >= max_rev:
            critique = "APPROVED - Maximum revisions reached. The post is satisfactory."
        else:
            prompt = CRITIC_PROMPT.format(
                main_task=state.get("main_task", ""),
                draft=draft,
                tone=state.get("tone", "professional"),
                target_audience=state.get("target_audience", "professionals"),
                word_count_min=state.get("word_count_min", 150),
                word_count_max=state.get("word_count_max", 300),
            )
            try:
                response = self.llm.invoke(prompt)
                critique = response.content if response.content else "APPROVED"
            except Exception as e:
                logger.error(f"Critique error: {e}")
                critique = "APPROVED - Error in critique, proceeding with current draft."

        is_approved = "APPROVED" in critique.upper()
        duration = int((time.time() - start) * 1000)

        self._emit_step("critic", {
            "approved": is_approved,
            "feedback_preview": critique[:200],
            "duration_ms": duration,
        })

        if is_approved:
            return {"critique_notes": "APPROVED", "next_step": "END"}
        else:
            return {"critique_notes": critique, "next_step": "writer"}

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow - mirrors notebook exactly."""
        workflow = StateGraph(ResearchState)

        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("researcher", self._research_node)
        workflow.add_node("writer", self._write_node)
        workflow.add_node("critiquer", self._critique_node)

        workflow.set_entry_point("supervisor")

        workflow.add_edge("researcher", "supervisor")
        workflow.add_edge("writer", "critiquer")
        workflow.add_edge("critiquer", "supervisor")

        workflow.add_conditional_edges(
            "supervisor",
            lambda state: state.get("next_step", "researcher"),
            {
                "researcher": "researcher",
                "writer": "writer",
                "END": END,
            },
        )

        return workflow.compile()

    def run(self, topic: str, **kwargs) -> dict:
        """Execute the full workflow."""
        self.step_counter = 0
        initial_state = {
            "main_task": topic,
            "research_findings": [],
            "draft": "",
            "critique_notes": "",
            "revision_number": 0,
            "next_step": "",
            "current_sub_task": "",
            "tone": kwargs.get("tone", "professional"),
            "target_audience": kwargs.get("target_audience", "tech professionals"),
            "word_count_min": kwargs.get("word_count_min", 150),
            "word_count_max": kwargs.get("word_count_max", 300),
            "language": kwargs.get("language", "English"),
            "include_hashtags": kwargs.get("include_hashtags", True),
            "include_cta": kwargs.get("include_cta", True),
            "include_emoji": kwargs.get("include_emoji", False),
            "template_instructions": kwargs.get("template_instructions", ""),
            "max_revisions": kwargs.get("max_revisions", self.max_revisions),
        }

        result = self.app.invoke(initial_state)
        return result

    def stream(self, topic: str, **kwargs):
        """Stream the workflow execution step by step."""
        self.step_counter = 0
        initial_state = {
            "main_task": topic,
            "research_findings": [],
            "draft": "",
            "critique_notes": "",
            "revision_number": 0,
            "next_step": "",
            "current_sub_task": "",
            "tone": kwargs.get("tone", "professional"),
            "target_audience": kwargs.get("target_audience", "tech professionals"),
            "word_count_min": kwargs.get("word_count_min", 150),
            "word_count_max": kwargs.get("word_count_max", 300),
            "language": kwargs.get("language", "English"),
            "include_hashtags": kwargs.get("include_hashtags", True),
            "include_cta": kwargs.get("include_cta", True),
            "include_emoji": kwargs.get("include_emoji", False),
            "template_instructions": kwargs.get("template_instructions", ""),
            "max_revisions": kwargs.get("max_revisions", self.max_revisions),
        }

        for step_output in self.app.stream(initial_state):
            yield step_output

    def evaluate_groundedness(self, draft: str, research_findings: List[str]) -> dict:
        """Evaluate groundedness of the final post - from notebook's evaluation cell."""
        research_text = "\n\n".join(research_findings)
        prompt = GROUNDEDNESS_PROMPT.format(
            research_findings=research_text,
            draft=draft,
        )

        try:
            response = self.eval_llm.invoke(prompt)
            content = response.content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join([l for l in lines if not l.strip().startswith("```")])
            return json.loads(content.strip())
        except Exception as e:
            logger.error(f"Groundedness evaluation error: {e}")
            return {"score": -1, "notes": f"Evaluation failed: {str(e)}"}
