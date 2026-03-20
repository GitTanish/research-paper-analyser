from typing import Optional
from crewai import Task


def create_analysis_task(agent, paper_text: str, feedback: Optional[str] = None) -> Task:
    description = f"""
Analyze the following research paper and extract structured information.

PAPER TEXT:
{paper_text[:8000]}  

Return a JSON object with EXACTLY these fields:
{{
  "title": "paper title",
  "authors": ["author1", "author2"],
  "year": "publication year or 'Unknown'",
  "venue": "journal/conference or 'Unknown'",
  "problem_statement": "what problem does this paper solve",
  "hypothesis": "the main hypothesis or research question",
  "methodology": "detailed description of the approach/method used",
  "experiments": "what experiments or studies were conducted",
  "key_findings": ["finding 1", "finding 2", "finding 3"],
  "limitations": "known limitations mentioned in the paper"
}}

Be precise and faithful to the source text. Do not hallucinate details not present in the paper.
"""
    if feedback:
        description += f"\n\nPRIOR FEEDBACK TO INCORPORATE:\n{feedback}"

    return Task(
        description=description,
        expected_output="A valid JSON object with all required fields populated from the paper.",
        agent=agent,
    )


def create_review_task(agent, content: str, content_type: str, attempt: int = 1) -> Task:
    return Task(
        description=f"""
Review the following {content_type} output (attempt {attempt}/3).

CONTENT TO REVIEW:
{content}

Evaluate strictly on:
1. Accuracy - does it faithfully represent source material? (0-10)
2. Completeness - are all required fields/sections present? (0-10)
3. Clarity - is it clear and well-structured? (0-10)

Return a JSON object:
{{
  "score": <average of three scores, float>,
  "accuracy_score": <0-10>,
  "completeness_score": <0-10>,
  "clarity_score": <0-10>,
  "approved": <true if score >= 7.0, false otherwise>,
  "feedback": "specific, actionable feedback for improvement if not approved",
  "strengths": "what was done well"
}}
""",
        expected_output="A JSON review object with score, approval status, and feedback.",
        agent=agent,
    )


def create_summary_task(agent, analysis: str, feedback: Optional[str] = None) -> Task:
    description = f"""
Based on the following research analysis, write an executive summary.

ANALYSIS:
{analysis}

Requirements:
- EXACTLY 150-200 words (count carefully)
- Written for a non-specialist audience (no jargon without explanation)
- Cover: (1) the problem being solved, (2) the approach/method, (3) key results
- Professional, clear, engaging tone
- Do NOT use bullet points — write flowing prose paragraphs

Return a JSON object:
{{
  "summary": "your 150-200 word executive summary here",
  "word_count": <actual word count as integer>
}}
"""
    if feedback:
        description += f"\n\nPRIOR FEEDBACK TO INCORPORATE:\n{feedback}"

    return Task(
        description=description,
        expected_output="A JSON object with the executive summary and its word count.",
        agent=agent,
    )


def create_citation_task(agent, paper_text: str, feedback: Optional[str] = None) -> Task:
    description = f"""
Extract all citations and references from the following research paper text.

PAPER TEXT:
{paper_text[:8000]}

Return a JSON object:
{{
  "total_references": <count>,
  "references": [
    {{
      "index": 1,
      "citation_key": "[1] or (Author, Year) format found in paper",
      "full_reference": "full reference text as found in the paper",
      "authors": "authors if extractable",
      "year": "year if extractable",
      "title": "title if extractable"
    }}
  ],
  "key_related_works": ["most important 3-5 cited works with brief reason why they matter"]
}}

Extract as many references as you can find. If the references section is truncated, extract what is available.
"""
    if feedback:
        description += f"\n\nPRIOR FEEDBACK TO INCORPORATE:\n{feedback}"

    return Task(
        description=description,
        expected_output="A JSON object with all extracted references and key related works.",
        agent=agent,
    )


def create_insights_task(agent, analysis: str, summary: str, feedback: Optional[str] = None) -> Task:
    description = f"""
Based on the research analysis and summary below, generate key insights and practical implications.

ANALYSIS:
{analysis}

SUMMARY:
{summary}

Return a JSON object:
{{
  "practical_takeaways": [
    {{"takeaway": "specific actionable insight", "explanation": "why this matters"}}
  ],
  "field_implications": "how this advances the field in 2-3 sentences",
  "potential_applications": ["application 1", "application 2", "application 3"],
  "open_questions": ["what questions does this research leave unanswered"],
  "who_should_read_this": "which professionals or researchers would benefit most from this paper"
}}

Be specific and concrete. Avoid vague statements like 'this is important for AI'.
"""
    if feedback:
        description += f"\n\nPRIOR FEEDBACK TO INCORPORATE:\n{feedback}"

    return Task(
        description=description,
        expected_output="A JSON object with practical takeaways, implications, and applications.",
        agent=agent,
    )


def create_combine_task(agent, analysis: str, summary: str, citations: str, insights: str) -> Task:
    return Task(
        description=f"""
Combine all approved agent outputs into a final, polished research brief.

ANALYSIS DATA:
{analysis}

EXECUTIVE SUMMARY:
{summary}

CITATIONS DATA:
{citations}

KEY INSIGHTS:
{insights}

Produce a well-structured markdown research brief with these sections:
1. # Paper Metadata (title, authors, year, venue)
2. # Research Analysis (problem, hypothesis, methodology, experiments, findings, limitations)
3. # Executive Summary
4. # Citations & References (formatted list)
5. # Key Insights & Practical Implications
6. # Conclusion (2-3 sentence wrap-up)

Make it professional, readable, and comprehensive. Use markdown formatting throughout.
""",
        expected_output="A complete markdown-formatted research brief combining all agent outputs.",
        agent=agent,
    )
