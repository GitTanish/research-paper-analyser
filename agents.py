from crewai import Agent, LLM

# ── Model rotation lists ───────────────────────────────────────────────────────
# Rotate through these when TPM is exhausted instead of sleeping.
# Models are listed highest-quality first. All available on Groq free tier.
MAIN_MODELS = [
    "groq/meta-llama/llama-4-scout-17b-16e-instruct",  # 30K TPM, 500K TPD
    "groq/moonshotai/kimi-k2-instruct",                 # 10K TPM, 300K TPD — strong coder
    "groq/qwen/qwen3-32b",                              # 6K TPM, 500K TPD — excellent reasoning
    "groq/openai/gpt-oss-120b",                         # 8K TPM, 200K TPD — GPT-class quality
]

# For the fast review agent — prioritise high RPD so it rarely blocks
REVIEW_MODELS = [
    "groq/llama-3.1-8b-instant",                        # 6K TPM, 500K TPD, 14.4K RPD
    "groq/llama-3.3-70b-versatile",                     # 12K TPM, 100K TPD
]


def get_llm(model: str = MAIN_MODELS[0]):
    """Return a CrewAI LLM instance for the given model."""
    return LLM(model=model, temperature=0.2, max_tokens=4096)


def get_fast_llm(model: str = REVIEW_MODELS[0]):
    """Return a CrewAI LLM instance for the review/fast agent."""
    return LLM(model=model, temperature=0.1, max_tokens=1024)


def create_boss_agent():
    return Agent(
        role="Research Orchestrator",
        goal=(
            "Coordinate the full research paper analysis pipeline. "
            "Delegate tasks to specialized agents, monitor quality, and "
            "combine all approved outputs into a comprehensive research brief."
        ),
        backstory=(
            "You are a senior research director with 20 years of academic experience. "
            "You know how to decompose complex analysis tasks, ensure quality standards, "
            "and synthesize information from multiple expert sources into clear, actionable reports."
        ),
        llm=get_llm(),
        verbose=True,
        allow_delegation=True,
    )


def create_paper_analyzer_agent():
    return Agent(
        role="Research Paper Analyst",
        goal=(
            "Extract and structure the core academic content from research papers: "
            "problem statement, hypothesis, methodology, experiments, and key findings."
        ),
        backstory=(
            "You are a PhD-level research scientist who has reviewed thousands of academic papers. "
            "You excel at identifying the research question, dissecting methodology, and extracting "
            "statistically significant findings. You output clean, structured JSON."
        ),
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
    )


def create_summary_agent():
    return Agent(
        role="Executive Summary Writer",
        goal=(
            "Write a clear, precise executive summary (150-200 words) that captures "
            "the paper's problem, approach, and results for a non-specialist audience."
        ),
        backstory=(
            "You are a science communicator and technical writer who bridges the gap between "
            "dense academic prose and clear executive communication. You write for busy decision-makers "
            "who need the essence of a paper in under two minutes."
        ),
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
    )


def create_citation_agent():
    return Agent(
        role="Citation and Reference Extractor",
        goal=(
            "Identify, extract, and organize all citations, references, and related works "
            "mentioned in the research paper into a clean structured list."
        ),
        backstory=(
            "You are a research librarian and bibliographer with expertise in academic citation formats "
            "(APA, MLA, IEEE, arXiv). You can identify inline citations, reference lists, and key "
            "related works even in complex multi-column academic PDFs."
        ),
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
    )


def create_insights_agent():
    return Agent(
        role="Key Insights and Implications Analyst",
        goal=(
            "Identify practical takeaways, real-world applications, limitations, "
            "and future research directions from the paper."
        ),
        backstory=(
            "You are a technology strategist and innovation consultant who reads research papers "
            "to identify what matters in the real world. You spot gaps, opportunities, and "
            "implications that pure academics often miss."
        ),
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
    )


def create_review_agent():
    return Agent(
        role="Quality Review and Validation Agent",
        goal=(
            "Review each agent's output for accuracy, completeness, and clarity. "
            "Score outputs on a 1-10 scale and provide specific feedback for improvement. "
            "Approve outputs scoring >= 7, reject and request revision for scores < 7."
        ),
        backstory=(
            "You are a rigorous peer reviewer and quality assurance specialist. "
            "You have high standards: you check that analysis matches source material, "
            "summaries are within word limits, citations are properly formatted, and "
            "insights are genuinely actionable. You are fair but uncompromising."
        ),
        llm=get_fast_llm(),
        verbose=True,
        allow_delegation=False,
    )
