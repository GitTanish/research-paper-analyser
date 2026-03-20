import os
import json
import tempfile
import streamlit as st
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Research Paper Analyzer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap');

/* ── BASE COLORS ── */
:root{
  --bg:#f7f5e6;
  --ink:#0d0d0d;
  --ink2:#1a1a1a;
  --muted:#3a3a3a;
  --subtle:#555;
  --faint:#777;
  --yellow:#ffe94d;
  --surface:#fff;
  --surface2:#f0ede0;
  --border:#000;
}

/* Reset & Base Streamlit Overrides */
.stApp {
    background: var(--bg) !important;
    color: var(--ink) !important;
}

/* Force Streamlit text elements to be dark */
.stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6, .stApp span, label, .stMarkdown p {
    color: var(--ink) !important;
}

[data-testid="stSidebar"] {
    background: var(--bg) !important;
    border-right: 2.5px solid var(--border) !important;
}

.stApp, .stMarkdown, .stButton, .stTextInput, .stTextArea, .stSelectbox, .stMetric, .stTabs, label {
    font-family: 'Space Grotesk', sans-serif !important;
}

/* Neo-brutalist Utils */
.nb-card {
    background: var(--surface);
    border: 2.5px solid var(--border);
    box-shadow: 4px 4px 0 var(--border);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    transition: all 0.1s ease;
}
.nb-card:hover { transform: translate(2px, 2px); box-shadow: 2px 2px 0 var(--border); }

.nb-pill {
    display: inline-block;
    background: var(--yellow);
    border: 2px solid var(--border);
    border-radius: 4px;
    padding: 2px 10px;
    font-size: 0.75rem;
    font-weight: 700;
    font-family: 'Space Mono', monospace !important;
    margin-bottom: 0.5rem;
    color: var(--ink) !important;
}

/* Hero */
.hero {
    padding: 0;
    margin-bottom: 2rem;
}
.hero h1 {
    font-size: 3.5rem !important;
    font-weight: 800 !important;
    line-height: 1 !important;
    letter-spacing: -0.04em !important;
    margin-bottom: 1rem !important;
    color: var(--ink) !important;
}
.hero h1 span { text-decoration: underline; text-decoration-thickness: 4px; }

.hero-sub {
    font-size: 1.1rem;
    color: var(--muted);
    max-width: 600px;
    margin-bottom: 2rem;
    font-weight: 500;
}

.hero-stats {
    display: flex;
    gap: 1.5rem;
    margin-top: 1.5rem;
    margin-bottom: 2rem;
}
.stat { display: flex; flex-direction: column; }
.stat-num {
    font-size: 1.6rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: var(--ink);
}
.stat-label {
    font-size: 0.72rem;
    font-weight: 700;
    font-family: 'Space Mono', monospace;
    color: var(--subtle);
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

/* Sidebar Inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] {
    background: var(--surface) !important;
    border: 2.5px solid var(--border) !important;
    border-radius: 0px !important;
    box-shadow: 3px 3px 0 var(--border) !important;
    color: var(--ink) !important;
    font-family: 'Space Mono', monospace !important;
}

/* Buttons */
div.stButton > button {
    background: var(--yellow) !important;
    color: var(--ink) !important;
    border: 2.5px solid var(--border) !important;
    border-radius: 0px !important;
    box-shadow: 4px 4px 0 var(--ink) !important;
    font-weight: 800 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0.75rem 1.5rem !important;
    transition: all 0.1s ease !important;
    width: 100%;
}
div.stButton > button:hover {
    transform: translate(2px, 2px) !important;
    box-shadow: 2px 2px 0 var(--ink) !important;
    background: #ffd700 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 2.5px solid var(--border) !important;
    gap: 0px !important;
}
.stTabs [data-baseweb="tab"] {
    border: 2.5px solid transparent !important;
    border-bottom: none !important;
    background: transparent !important;
    color: var(--subtle) !important;
    padding: 8px 25px !important;
    font-weight: 700 !important;
    margin-bottom: -2.5px !important;
}
.stTabs [aria-selected="true"] {
    background: var(--yellow) !important;
    border: 2.5px solid var(--border) !important;
    border-bottom: 2.5px solid var(--yellow) !important;
    color: var(--ink) !important;
}

/* Results Display */
.score-card {
    background: var(--surface);
    border: 2.5px solid var(--border);
    box-shadow: 4px 4px 0 var(--border);
    padding: 1rem;
    text-align: center;
}
.sc-score {
    font-size: 2.5rem;
    font-weight: 800;
    line-height: 1;
    color: var(--ink) !important;
}

.result-card-head {
    background: var(--bg);
    border: 2.5px solid var(--border);
    border-bottom: none;
    padding: 0.75rem 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 800;
    color: var(--ink) !important;
}
.result-card-body {
    background: var(--surface);
    border: 2.5px solid var(--border);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 4px 4px 0 var(--border);
    color: var(--ink) !important;
}

.agent-log {
    background: var(--surface);
    border: 2.5px solid var(--border);
    padding: 1rem;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.8rem;
    max-height: 300px;
    overflow-y: auto;
    color: var(--ink) !important;
}

/* Streamlit internal overrides */
header[data-testid="stHeader"] {
    background-color: rgba(247, 245, 230, 0.8) !important;
    color: var(--ink) !important;
}
header[data-testid="stHeader"] button {
    color: var(--ink) !important;
}
#MainMenu {
    color: var(--ink) !important;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar Configuration Values ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='font-size:1.2rem; font-weight:800; margin-bottom:1rem;'>🔬 ResearchAI <span class='nb-pill'>BETA</span></div>", unsafe_allow_html=True)
    
    st.markdown("### ⚙️ CONFIGURATION")
    threshold = st.slider("Min Score", 5.0, 9.0, 7.0, 0.5)
    max_retries = st.slider("Max Retries", 1, 3, 2)
    
    st.markdown("<hr style='border:1.25px solid #000; margin:1.5rem 0;'>", unsafe_allow_html=True)

# ── Header & Hero ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
    <div class="hero-tag">MULTI-AGENT · CREWAI · GROQ</div>
    <h1>Research Paper<br><span>Analyzer</span></h1>
    <p class="hero-sub">
        6 specialized AI agents extract, summarize, and critique academic papers — with automated quality control and retry loops.
    </p>
    <div class="hero-stats">
      <div class="stat"><span class="stat-num">6</span><span class="stat-label">Agents</span></div>
      <div class="stat"><span class="stat-num">{threshold:.1f}</span><span class="stat-label">Min Score</span></div>
      <div class="stat"><span class="stat-num">{max_retries}×</span><span class="stat-label">Max Retry</span></div>
      <div class="stat"><span class="stat-num">~90s</span><span class="stat-label">Avg Time</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar API Key Handling ──────────────────────────────────────────────────
with st.sidebar:
    # Load API Key from environment and sanitize
    raw_key = os.getenv("GROQ_API_KEY")
    groq_key = raw_key.strip().strip('"').strip("'") if raw_key else None
    
    if groq_key:
        masked_key = f"{groq_key[:4]}...{groq_key[-4:]}"
        st.success(f"✅ Key loaded: `{masked_key}`")
        if not groq_key.startswith("gsk_"):
             st.warning("⚠️ Key doesn't start with `gsk_`. Check `.env` format.")
    else:
        st.error("❌ GROQ_API_KEY not found in .env")

    st.markdown("<hr style='border:1.25px solid #000; margin:1.5rem 0;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#333; font-weight:700;">
        BUILT WITH CREWAI · GROQ · STREAMLIT
    </div>
    """, unsafe_allow_html=True)

# ── Main content ───────────────────────────────────────────────────────────────
if not groq_key:
    st.error("👈 Please add a valid `GROQ_API_KEY` to the `.env` file.")
    st.stop()

# Set API key in env for CrewAI/LiteLLM
os.environ["GROQ_API_KEY"] = groq_key

# Input section
input_method = st.radio(
    "Input Method",
    ["📎 Upload PDF", "🔗 arXiv / PDF URL", "📋 Paste Text"],
    horizontal=True,
)

paper_text = ""
paper_source = ""

if input_method == "📎 Upload PDF":
    uploaded = st.file_uploader("Upload research paper PDF", type=["pdf"])
    if uploaded:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name
        try:
            from pdf_utils import extract_text_from_pdf
            with st.spinner("Extracting text from PDF..."):
                paper_text = extract_text_from_pdf(tmp_path)
            paper_source = uploaded.name
            st.success(f"✅ Extracted {len(paper_text):,} characters from {uploaded.name}")
        except Exception as e:
            st.error(f"PDF extraction failed: {e}")

elif input_method == "🔗 arXiv / PDF URL":
    url = st.text_input("PDF or arXiv URL", placeholder="https://arxiv.org/abs/2303.08774")
    if url and st.button("Fetch PDF"):
        try:
            from pdf_utils import fetch_pdf_from_url
            with st.spinner("Downloading and extracting..."):
                paper_text = fetch_pdf_from_url(url)
            paper_source = url
            st.success(f"✅ Fetched {len(paper_text):,} characters")
        except Exception as e:
            st.error(f"Failed to fetch PDF: {e}")

elif input_method == "📋 Paste Text":
    paper_text = st.text_area(
        "Paste paper text here",
        height=250,
        placeholder="Paste the full text of the research paper...",
    )
    paper_source = "Pasted text"

# ── Analyze button ─────────────────────────────────────────────────────────────
if paper_text:
    word_count = len(paper_text.split())
    st.caption(f"📄 {word_count:,} words · {len(paper_text):,} chars loaded")

    col1, col2 = st.columns([1, 4])
    with col1:
        analyze = st.button("🚀 Analyze Paper", use_container_width=True)

    if analyze:
        # Status log
        st.markdown("### 🔄 Agent Pipeline")
        log_placeholder = st.empty()
        log_lines = []

        def status_callback(msg: str):
            emoji_map = {"✅": "ok", "❌": "err", "🔄": "info", "📄": "info",
                         "📝": "info", "📚": "info", "💡": "info", "🧠": "info", "🔍": "info"}
            css_cls = next((v for k, v in emoji_map.items() if msg.startswith(k)), "")
            log_lines.append(f'<div class="log-line {css_cls}">{msg}</div>')
            log_placeholder.markdown(
                f'<div class="agent-log">{"".join(log_lines)}</div>',
                unsafe_allow_html=True,
            )

        try:
            from pdf_utils import truncate_for_context
            from crew import run_full_pipeline

            trimmed = truncate_for_context(paper_text, max_chars=12000)
            results = run_full_pipeline(trimmed, status_callback=status_callback)

            st.session_state["results"] = results
            st.session_state["paper_source"] = paper_source

        except Exception as e:
            st.error(f"Pipeline error: {e}")
            st.exception(e)

# ── Results display ────────────────────────────────────────────────────────────
if "results" in st.session_state:
    results = st.session_state["results"]
    source = st.session_state.get("paper_source", "")

    st.markdown("<hr style='border:2.5px solid #000; margin:2rem 0;'>", unsafe_allow_html=True)
    st.markdown("## 📋 RESEARCH BRIEF")

    # Quality scores overview
    def get_score(key):
        r = results.get(key, {}).get("review", {})
        return r.get("score", 0)

    scores = {
        "Analysis": get_score("analysis"),
        "Summary": get_score("summary"),
        "Citations": get_score("citations"),
        "Insights": get_score("insights"),
    }

    cols = st.columns(4)
    for i, (k, v) in enumerate(scores.items()):
        status = "APPROVED" if v >= threshold else "RETRYING"
        with cols[i]:
            st.markdown(f"""
            <div class="score-card">
                <div style="font-family:'Space Mono',monospace; font-size:0.65rem; font-weight:700; color:#333; text-transform:uppercase;">{k}</div>
                <div class="sc-score">{v:.1f}</div>
                <div style="background:#0d0d0d; color:#ffe94d; font-family:'Space Mono',monospace; font-size:0.6rem; font-weight:700; padding:2px 6px; margin-top:8px; display:inline-block;">{status}</div>
            </div>
            """, unsafe_allow_html=True)

    # Tabs for different sections
    tabs = st.tabs(["📄 FULL BRIEF", "🔬 ANALYSIS", "📝 SUMMARY", "📚 CITATIONS", "💡 INSIGHTS", "🔢 RAW JSON"])

    with tabs[0]:
        final_brief = results.get("final_brief", "")
        st.markdown(f'<div class="result-card-body">{final_brief}</div>', unsafe_allow_html=True)
        st.download_button(
            "⬇️ Download Research Brief (.md)",
            data=final_brief,
            file_name="research_brief.md",
            mime="text/markdown",
        )

    with tabs[1]:
        parsed = results.get("analysis", {}).get("parsed", {})
        if "raw_output" in parsed:
            st.markdown(f'<div class="result-card-body"><pre>{parsed["raw_output"]}</pre></div>', unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="result-card-head">
                <div>01 &nbsp; PAPER METADATA</div>
                <div class="nb-pill" style="margin:0">PASS</div>
            </div>
            <div class="result-card-body">
                <h3 style="margin-top:0;">{parsed.get('title', 'Unknown Title')}</h3>
                <div style="display:flex; gap:20px; margin-bottom:15px;">
                    <div><small style="display:block; font-family:'Space Mono',monospace; color:#888;">AUTHORS</small><b>{", ".join(parsed.get("authors", [])) or "N/A"}</b></div>
                    <div><small style="display:block; font-family:'Space Mono',monospace; color:#888;">YEAR</small><b>{parsed.get("year", "N/A")}</b></div>
                    <div><small style="display:block; font-family:'Space Mono',monospace; color:#888;">VENUE</small><b>{parsed.get("venue", "N/A")}</b></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            for field, label in [
                ("problem_statement", "🎯 Problem Statement"),
                ("hypothesis", "💭 Hypothesis"),
                ("methodology", "🔧 Methodology"),
                ("experiments", "🧪 Experiments"),
                ("limitations", "⚠️ Limitations"),
            ]:
                if parsed.get(field):
                    st.markdown(f'<div class="result-card-head">{label}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="result-card-body">{parsed[field]}</div>', unsafe_allow_html=True)

            findings = parsed.get("key_findings", [])
            if findings:
                st.markdown(f'<div class="result-card-head">📊 Key Findings</div>', unsafe_allow_html=True)
                findings_html = "".join([f"<li>{f}</li>" for f in findings])
                st.markdown(f'<div class="result-card-body"><ul>{findings_html}</ul></div>', unsafe_allow_html=True)

    with tabs[2]:
        parsed = results.get("summary", {}).get("parsed", {})
        summary_text = parsed.get("summary", results.get("summary", {}).get("output", ""))
        wc = parsed.get("word_count", len(summary_text.split()))
        st.markdown(f"""
        <div class="result-card-head">
            <div>02 &nbsp; EXECUTIVE SUMMARY</div>
            <div class="nb-pill" style="margin:0">{wc} WORDS</div>
        </div>
        <div class="result-card-body">
            <p style="font-size:1.1rem; line-height:1.6;">{summary_text}</p>
        </div>
        """, unsafe_allow_html=True)

    with tabs[3]:
        parsed = results.get("citations", {}).get("parsed", {})
        refs = parsed.get("references", [])
        total = parsed.get("total_references", len(refs))
        st.markdown(f"""
        <div class="result-card-head">
            <div>03 &nbsp; CITATIONS & REFERENCES</div>
            <div class="nb-pill" style="margin:0">{total} REFS</div>
        </div>
        <div class="result-card-body">
        """, unsafe_allow_html=True)
        
        for ref in refs:
             st.markdown(f"""
             <div style="display:flex; gap:10px; padding:8px 0; border-bottom:1.5px solid #e8e6d8;">
                <span style="font-family:'Space Mono',monospace; color:#333;">[{ref.get('index', '?')}]</span>
                <span>{ref.get('full_reference', ref.get('title', 'Unknown'))}</span>
             </div>
             """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[4]:
        parsed = results.get("insights", {}).get("parsed", {})
        st.markdown(f"""
        <div class="result-card-head">
            <div>04 &nbsp; KEY INSIGHTS</div>
            <div class="nb-pill" style="margin:0">INSIGHTS</div>
        </div>
        <div class="result-card-body">
        """, unsafe_allow_html=True)
        
        takeaways = parsed.get("practical_takeaways", [])
        for t in takeaways:
            st.markdown(f"**{t.get('takeaway', '')}**")
            st.caption(t.get("explanation", ""))
            st.markdown("<br>", unsafe_allow_html=True)
            
        st.markdown(f"### 🌍 Field Implications")
        st.write(parsed.get("field_implications", ""))
        
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[5]:
        st.json({k: v for k, v in results.items() if k != "final_brief"})
