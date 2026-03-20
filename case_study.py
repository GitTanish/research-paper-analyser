"""
Case Study: AI Research Paper Analyzer
Architecture, Design Decisions, and Technology Stack.
"""

CASE_STUDY_MD = """
# Case Study: AI Research Paper Analyzer

## 1. Executive Summary
The Research Paper Analyzer is a multi-agent system designed to transform dense academic papers into structured, high-quality research briefs. It leverages a specialized ensemble of AI agents to overcome common limitations of single-prompt AI models.

## 2. Architecture & Design Decisions

### Multi-Agent Orchestration (CrewAI)
Instead of a single monolithic prompt, we use a decentralized "crew" of experts.
- **Boss Agent**: Orchestrates the workflow and synthesizes final outputs.
- **Specialized Specialists**: Analyst, Summarizer, Citation Extractor, and Insights Agent.
- **Review Agent**: Peer reviews every output; rejects and retries if score < 7.0.

### Model Rotation Architecture (Resilience)
Implements a **"rotate-first, sleep-last"** TPM management system. 
When a Groq rate limit is hit, the system instantly hot-swaps the agent's LLM to a backup model (e.g., Kimi-K2 or Qwen3) to maintain zero-latency throughput.

### Neo-Brutalist UI
A custom-themed Streamlit interface using bold typography, high-contrast colors (Yellow/Black/Cream), and modern CSS to provide a premium research laboratory feel.

## 3. Technology Stack
- **Orchestration**: CrewAI
- **Inference**: Groq (LPU)
- **Primary Models**: Llama-4-Scout-17b, Kimi-K2, Qwen3, GPT-OSS-120b
- **UI**: Streamlit + Custom CSS
- **Environment**: uv (fast dependency management)

## 4. Why It Is "The Best"
1. **Zero Hallucination**: Strict JSON binding and peer review verification.
2. **Infinite Throughput**: Seamless model rotation bypasses rate limits mid-task.
3. **Resilient API Handling**: Secure .env loading and internal sanitization.
4. **Speed**: Processes complex papers into briefs in seconds using Groq LPUs.
"""

if __name__ == "__main__":
    print(CASE_STUDY_MD)
