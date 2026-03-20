# Bug Report — assignment-crewai

**Date:** 2026-03-20  
**Files audited:** `crew.py`, `tasks.py`, `agents.py`, `app.py`, `pdf_utils.py`

---

## BUG-001 · Infinite loop possible in `_kickoff_with_tpm_retry`

**File:** `crew.py` — lines 84–119  
**Severity:** High

After all models are exhausted and the code sleeps, it resets `model_index = 0` and retries.
If the very first model is *still* rate-limited after sleeping, the loop re-exhausts all models,
sleeps again, and repeats forever. There is no attempt counter or total timeout to break out.

```python
# Current — no exit condition
while True:
    try:
        return crew.kickoff()
    except Exception as e:
        ...
        time.sleep(wait_secs)
        model_index = 0   # resets unconditionally → infinite loop
```

**Fix:** Add a max sleep-cycle counter and raise after N total sleep cycles.

---

## BUG-002 · `score` cast to `float` on a value that may be a string

**File:** `crew.py` — line 188  
**Severity:** Medium

```python
status_callback(f"... {score:.1f}/10 ...")
```

`score` comes from `last_review.get("score", 0)`, which is raw LLM JSON output parsed by
`parse_json_output`. If the LLM returns `"score": "8"` (a string, which happens), this
`:.1f` format will raise `ValueError: Unknown format code 'f' for object of type 'str'`,
crashing the entire pipeline silently inside `run_agent_with_review`.

**Fix:** Cast explicitly: `score = float(last_review.get("score", 0))`

---

## BUG-003 · `approved` logic is split across agent and reviewer — can disagree

**File:** `crew.py` line 182 / `tasks.py` line 57  
**Severity:** Medium

The review task prompt tells the LLM to set `"approved": true if score >= 7.0`.
But the pipeline also independently checks `approved` from that same JSON:

```python
approved = last_review.get("approved", False)
if approved or attempt > MAX_RETRIES:
    break
```

If the LLM outputs `score: 7.5` but also `approved: false` (which happens when the LLM
disagrees with its own threshold), the item gets retried even though the score passes.
Conversely, `score: 5` + `approved: true` gets accepted. The `approved` field and the
`score` field are not cross-validated in code — the LLM's `approved` flag is blindly trusted.

**Fix:** Derive approval from score in code, not from the LLM's `approved` field:
```python
approved = float(last_review.get("score", 0)) >= QUALITY_THRESHOLD
```

---

## BUG-004 · Task truncates paper at 8000 chars but pipeline truncates at 12000

**File:** `tasks.py` lines 10, 102 / `app.py` line 329  
**Severity:** Medium

`run_full_pipeline` receives text already truncated to 12,000 chars by `truncate_for_context`.
Then `create_analysis_task` and `create_citation_task` re-truncate at 8,000 chars
(`paper_text[:8000]`). The summary and insights tasks use the full agent *output* string
(not the paper text), so they get the full 12K.

Result: the citation and analysis agents only ever see 8,000 chars of the paper regardless
of what context limit was set at the call site. The 12K truncation in `app.py` is silently
wasted — and the last 4,000 chars (often the conclusion + references) are always dropped.

**Fix:** Remove the hardcoded slice `[:8000]` in `tasks.py` and let the caller control length.

---

## BUG-005 · `fetch_pdf_from_url` hardcodes `/tmp/paper.pdf`

**File:** `pdf_utils.py` — line 63  
**Severity:** Medium (Windows-specific breakage)

```python
def fetch_pdf_from_url(url: str, save_path: str = "/tmp/paper.pdf") -> str:
```

`/tmp/` does not exist on Windows. Every URL-based PDF fetch will fail with
`FileNotFoundError` at the `open(save_path, "wb")` call on line 78 — silently raised
through Streamlit's `st.error`.

**Fix:** Use `tempfile.mktemp(suffix=".pdf")` as the default, same pattern used in `app.py`
line 268.

---

## BUG-006 · `extract_text_from_pdf` returns empty string silently

**File:** `pdf_utils.py` — lines 44–45  
**Severity:** Low

When `pdfplumber` raises a non-`ImportError` exception (e.g., corrupted PDF), the
`except Exception` block only prints to stdout and falls through to the PyPDF2 fallback.
If PyPDF2 also fails *silently* (e.g., returns pages with no text, which is common for
scanned PDFs), the function returns `text = ""` on line 45 with no error raised.

The caller in `app.py` then displays `✅ Extracted 0 characters` as a success, and the
pipeline runs on an empty string, wasting all API calls.

**Fix:** After both extraction attempts, raise if `text.strip()` is empty:
```python
if not text.strip():
    raise RuntimeError("No text could be extracted from this PDF (possibly scanned/image-only).")
```

---

## BUG-007 · `groq_key` scoped inside `with st.sidebar` but used outside it

**File:** `app.py` — lines 224, 248  
**Severity:** Low (works due to Python scoping, but fragile)

`groq_key` is assigned inside `with st.sidebar:` (line 224). It is then used on line 248
outside that block (`if not groq_key:`). This works because Python `with` blocks don't
create a new scope, but it is a readability and maintenance hazard — any refactor that
extracts the sidebar into a function would break the reference silently, producing a
`NameError` at runtime.

**Fix:** Assign `groq_key` before the `with st.sidebar:` block.

---

## Summary

| ID | File | Severity | One-liner |
|---|---|---|---|
| BUG-001 | `crew.py` | High | Infinite loop when all models stay rate-limited after sleep |
| BUG-002 | `crew.py` | Medium | `score` may be a string; `:.1f` format crashes the pipeline |
| BUG-003 | `crew.py` / `tasks.py` | Medium | LLM's `approved` field trusted over actual score value |
| BUG-004 | `tasks.py` | Medium | Paper hard-truncated at 8K inside tasks, overriding 12K caller limit |
| BUG-005 | `pdf_utils.py` | Medium | `/tmp/paper.pdf` hardcoded — breaks on Windows |
| BUG-006 | `pdf_utils.py` | Low | Empty extraction returns silently, pipeline runs on empty string |
| BUG-007 | `app.py` | Low | `groq_key` scoped inside sidebar block but relied upon outside it |
