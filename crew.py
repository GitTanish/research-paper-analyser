import re
import time
import json
import logging
from typing import Optional, List, Dict, Any
from crewai import Agent, Crew, Process

from agents import (
    create_boss_agent,
    create_paper_analyzer_agent,
    create_summary_agent,
    create_citation_agent,
    create_insights_agent,
    create_review_agent,
    get_llm,
    get_fast_llm,
    MAIN_MODELS,
    REVIEW_MODELS,
)
from tasks import (
    create_analysis_task,
    create_review_task,
    create_summary_task,
    create_citation_task,
    create_insights_task,
    create_combine_task,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

QUALITY_THRESHOLD = 7.0
MAX_RETRIES = 2


def parse_json_output(raw: str) -> dict:
    """Safely extract JSON from agent output which may have extra prose."""
    try:
        # Direct parse
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Try to find JSON block inside markdown fences
    patterns = [
        r"```json\s*([\s\S]*?)\s*```",
        r"```\s*([\s\S]*?)\s*```",
        r"(\{[\s\S]*\})",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
    logger.warning("Could not parse JSON from output, returning raw string in wrapper")
    return {"raw_output": raw}


def _parse_wait_time(err_str: str, default: float = 62.0) -> float:
    """Parse Groq's suggested wait time from a rate-limit error message."""
    match = re.search(r"try again in ([0-9.]+)s", err_str)
    return float(match.group(1)) + 2.0 if match else default


def _kickoff_with_tpm_retry(
    crew: Crew,
    agents: List[Agent],
    label: str,
    model_list: List[str],
    llm_factory,
    status_callback=None,
) -> object:
    """
    Run crew.kickoff() with rotate-first, sleep-last TPM handling.

    On a TPM rate-limit error:
      1. Try each model in model_list in order (rotate).
      2. If all models are exhausted, parse the wait time from the error and sleep.
      3. Non-TPM errors are re-raised immediately.
    """
    model_index = 0  # start with whichever model is already set on the agents

    while True:
        try:
            return crew.kickoff()
        except Exception as e:
            err_str = str(e)
            is_tpm = "rate_limit_exceeded" in err_str and "tokens" in err_str.lower()

            if not is_tpm:
                raise  # surface non-rate-limit errors immediately

            model_index += 1
            if model_index < len(model_list):
                next_model = model_list[model_index]
                short_name = next_model.split("/")[-1]
                msg = f"⚡ TPM limit on {label}. Rotating to {short_name}..."
                logger.warning(msg)
                if status_callback:
                    status_callback(msg)
                # Swap LLM on every agent in this crew in-place
                new_llm = llm_factory(next_model)
                for agent in agents:
                    agent.llm = new_llm
            else:
                # All models exhausted — fall back to sleeping
                wait_secs = _parse_wait_time(err_str)
                msg = f"⏳ All models at TPM limit for {label}. Sleeping {wait_secs:.0f}s..."
                logger.warning(msg)
                if status_callback:
                    status_callback(msg)
                time.sleep(wait_secs)
                # Reset to first model after sleep
                model_index = 0
                first_model = model_list[0]
                new_llm = llm_factory(first_model)
                for agent in agents:
                    agent.llm = new_llm


def run_agent_with_review(
    agent_task_fn,
    review_agent,
    content_type: str,
    task_kwargs: dict,
    status_callback=None,
) -> tuple[str, dict]:
    """
    Run an agent task and review it. Retry up to MAX_RETRIES if below quality threshold.
    Uses model rotation for TPM rate limits. Returns (raw_output_str, review_result_dict).
    """
    attempt = 0
    last_output = ""
    last_review = {}

    while attempt <= MAX_RETRIES:
        attempt += 1
        if status_callback:
            status_callback(f"🔄 Running {content_type} agent (attempt {attempt}/{MAX_RETRIES + 1})...")

        # Build and run the main agent task
        agent, task = agent_task_fn(**task_kwargs)
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False,
        )
        result = _kickoff_with_tpm_retry(
            crew=crew,
            agents=[agent],
            label=content_type,
            model_list=MAIN_MODELS,
            llm_factory=get_llm,
            status_callback=status_callback,
        )
        last_output = str(result)

        # Review the output
        if status_callback:
            status_callback(f"🔍 Reviewing {content_type} output...")

        review_task = create_review_task(review_agent, last_output, content_type, attempt)
        review_crew = Crew(
            agents=[review_agent],
            tasks=[review_task],
            process=Process.sequential,
            verbose=False,
        )
        review_result = _kickoff_with_tpm_retry(
            crew=review_crew,
            agents=[review_agent],
            label=f"{content_type} review",
            model_list=REVIEW_MODELS,
            llm_factory=get_fast_llm,
            status_callback=status_callback,
        )
        last_review = parse_json_output(str(review_result))

        score = last_review.get("score", 0)
        approved = last_review.get("approved", False)

        logger.info(f"{content_type} attempt {attempt}: score={score}, approved={approved}")

        if status_callback:
            status_callback(
                f"{'✅' if approved else '❌'} {content_type} score: {score:.1f}/10 "
                f"({'approved' if approved else 'needs revision'})"
            )

        if approved or attempt > MAX_RETRIES:
            break

        # Inject feedback for next attempt
        feedback = last_review.get("feedback", "")
        if feedback and "paper_text" in task_kwargs:
            task_kwargs["feedback"] = feedback

    return last_output, last_review


def _make_agent_task(agent_fn, task_fn, **kwargs):
    """Helper to create agent+task pair for run_agent_with_review."""
    agent = agent_fn()
    task = task_fn(agent, **kwargs)
    return agent, task


def run_full_pipeline(paper_text: str, status_callback=None) -> Dict[str, Any]:
    """
    Main pipeline: runs all agents with review/retry loop.
    Returns a dict with all outputs and the final brief.
    """
    review_agent = create_review_agent()
    results: Dict[str, Any] = {}

    # ── 1. Paper Analyzer ──────────────────────────────────────────────────
    if status_callback:
        status_callback("📄 Starting Paper Analysis...")

    analysis_output, analysis_review = run_agent_with_review(
        agent_task_fn=lambda **kw: _make_agent_task(
            create_paper_analyzer_agent, create_analysis_task, **kw
        ),
        review_agent=review_agent,
        content_type="Paper Analysis",
        task_kwargs={"paper_text": paper_text},
        status_callback=status_callback,
    )
    results["analysis"] = {
        "output": analysis_output,
        "parsed": parse_json_output(analysis_output),
        "review": analysis_review,
    }

    # ── 2. Summary Generator ───────────────────────────────────────────────
    if status_callback:
        status_callback("📝 Generating Executive Summary...")

    summary_output, summary_review = run_agent_with_review(
        agent_task_fn=lambda **kw: _make_agent_task(
            create_summary_agent, create_summary_task, **kw
        ),
        review_agent=review_agent,
        content_type="Executive Summary",
        task_kwargs={"analysis": analysis_output},
        status_callback=status_callback,
    )
    results["summary"] = {
        "output": summary_output,
        "parsed": parse_json_output(summary_output),
        "review": summary_review,
    }

    # ── 3. Citation Extractor ──────────────────────────────────────────────
    if status_callback:
        status_callback("📚 Extracting Citations...")

    citation_output, citation_review = run_agent_with_review(
        agent_task_fn=lambda **kw: _make_agent_task(
            create_citation_agent, create_citation_task, **kw
        ),
        review_agent=review_agent,
        content_type="Citations",
        task_kwargs={"paper_text": paper_text},
        status_callback=status_callback,
    )
    results["citations"] = {
        "output": citation_output,
        "parsed": parse_json_output(citation_output),
        "review": citation_review,
    }

    # ── 4. Key Insights Agent ──────────────────────────────────────────────
    if status_callback:
        status_callback("💡 Generating Key Insights...")

    insights_output, insights_review = run_agent_with_review(
        agent_task_fn=lambda **kw: _make_agent_task(
            create_insights_agent, create_insights_task, **kw
        ),
        review_agent=review_agent,
        content_type="Key Insights",
        task_kwargs={"analysis": analysis_output, "summary": summary_output},
        status_callback=status_callback,
    )
    results["insights"] = {
        "output": insights_output,
        "parsed": parse_json_output(insights_output),
        "review": insights_review,
    }

    # ── 5. Boss Agent combines everything ─────────────────────────────────
    if status_callback:
        status_callback("🧠 Boss Agent assembling final research brief...")

    boss = create_boss_agent()
    combine_task = create_combine_task(
        boss,
        analysis=analysis_output,
        summary=summary_output,
        citations=citation_output,
        insights=insights_output,
    )
    final_crew = Crew(
        agents=[boss],
        tasks=[combine_task],
        process=Process.sequential,
        verbose=False,
    )
    final_result = final_crew.kickoff()
    results["final_brief"] = str(final_result)

    if status_callback:
        status_callback("✅ Pipeline complete!")

    return results
