# 🔬 AI Research Paper Analyzer

A **multi-agent system** built with CrewAI and Groq that automatically reads, analyzes, and summarizes academic research papers — with automated quality control and iterative improvement.

Built as a technical assignment for **Vilambo Private Limited**.

---

## 🏗️ Architecture

```
Input (PDF / URL / Text)
         │
         ▼
┌─────────────────────┐
│   Boss Agent        │  ← Orchestrator: coordinates all agents,
│   (Orchestrator)    │    combines final outputs
└─────────┬───────────┘
          │ delegates
          ▼
┌─────────────────────┐     ┌────────────────────┐
│  Paper Analyzer     │────▶│   Review Agent     │ score ≥ 7 → ✅
│  Agent              │     │  (Quality Control) │ score < 7 → 🔄 retry (max 2x)
└─────────────────────┘     └────────────────────┘
          │ (if approved)
          ▼
┌─────────────────────┐     ┌────────────────────┐
│  Summary Generator  │────▶│   Review Agent     │
│  Agent              │     │                    │
└─────────────────────┘     └────────────────────┘
          │
┌─────────────────────┐     ┌────────────────────┐
│  Citation Extractor │────▶│   Review Agent     │
│  Agent              │     │                    │
└─────────────────────┘     └────────────────────┘
          │
┌─────────────────────┐     ┌────────────────────┐
│  Key Insights       │────▶│   Review Agent     │
│  Agent (Bonus)      │     │                    │
└─────────────────────┘     └────────────────────┘
          │ (all approved)
          ▼
┌─────────────────────┐
│  Boss Agent         │  ← Combines all outputs
│  (Combiner)         │
└─────────────────────┘
          │
          ▼
  📋 Complete Research Brief
  (Markdown + JSON)
```

### Smart Model Rotation (TPM Management)

The system automatically rotates between high-performance models on Groq to bypass Token Per Minute (TPM) limits without waiting.

| Layer | Primary Model | Backup Rotation | Role |
| :--- | :--- | :--- | :--- |
| **Main Pipeline** | **Llama-4-Scout-17b** | `Kimi-K2`, `Qwen3`, `GPT-OSS-120b` | Research Analysis & Synthesis |
| **Reviewer** | **Llama-3.1-8b** | `Llama-3.3-70b` | Quality Audit & Scorecard |

---

---

## ⚙️ Setup

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/research-paper-analyzer.git
cd research-paper-analyzer
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your Groq API key

```bash
cp .env.example .env
# Edit .env and add your key:
# GROQ_API_KEY=gsk_your_key_here
```

Get a free Groq API key at [console.groq.com](https://console.groq.com).

---

## 🚀 Usage

### Option A: Streamlit UI (Recommended)

```bash
streamlit run app.py
```

Open `http://localhost:8501` — upload a PDF, paste a URL, or paste text directly.

### Option B: CLI

```bash
# From a PDF
python main.py --pdf path/to/paper.pdf

# From an arXiv URL (auto-converted to PDF download)
python main.py --url https://arxiv.org/abs/2303.08774

# From plain text
python main.py --text paper.txt

# With custom output path and JSON dump
python main.py --pdf paper.pdf --output brief.md --json-output results.json
```

---

## 📤 Output

The system generates a structured **Research Brief** containing:

1. **Paper Metadata** — title, authors, year, venue
2. **Research Analysis** — problem, hypothesis, methodology, experiments, findings, limitations
3. **Executive Summary** — 150-200 word overview for non-specialists
4. **Citations & References** — all references extracted and organized
5. **Key Insights** — practical takeaways, applications, open questions

Each section includes a **quality score (1-10)** from the Review Agent.

---

## 📁 Project Structure

```
research-paper-analyzer/
├── app.py           # Streamlit UI
├── main.py          # CLI entry point
├── agents.py        # CrewAI agent definitions
├── tasks.py         # Task definitions for each agent
├── crew.py          # Pipeline orchestration + review/retry logic
├── pdf_utils.py     # PDF extraction and URL fetching
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🎯 High-Throughput Architecture

- **Neo-Brutalist UI**: Premium, high-contrast Streamlit interface for professional research visualization.
- **Rotate-First, Sleep-Last**: If a model hits a TPM limit, the agent instantly hot-swaps to the next model in the pool (e.g., Moonshot's `Kimi-K2`).
- **Secure API Management**: Internal sanitization of `.env` keys with masking in the UI for security and reliability.
- **Hybrid Truncation**: Intelligently preserves Paper Head (Abstract/Intro) and Tail (Conclusion/References) to maximize context usage.

---

## 🔧 Tested With

- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
- [GPT-4 Technical Report](https://arxiv.org/abs/2303.08774)
- [LangGraph paper](https://arxiv.org/abs/2401.12794)
