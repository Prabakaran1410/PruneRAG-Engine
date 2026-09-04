import os
import requests
import streamlit as st

st.set_page_config(page_title="PruneRAG Engine", page_icon="P", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root { --ink:#17231f; --muted:#66736d; --paper:#f4f1e9; --panel:#fbfaf5; --mint:#c9e7d8; --coral:#e87961; --blue:#82bde8; --line:#d9d8cf; }
.stApp { background:linear-gradient(135deg,#f4f1e9 0%,#f8f6ef 48%,#e8f0eb 100%); color:var(--ink); }
[data-testid="stHeader"] { background:transparent; }
.block-container { max-width:1400px; padding:2.5rem 4rem 4rem; }
h1,h2,h3,p,button,label,div { font-family:'Space Grotesk',sans-serif; }
h1 { font-size:clamp(2rem,4vw,4.5rem); letter-spacing:0; line-height:1; margin:0; }
.eyebrow { color:var(--coral); font:500 0.75rem 'DM Mono',monospace; letter-spacing:0.08em; text-transform:uppercase; }
.subtle, .stCaption, [data-testid="stCaptionContainer"] { color:var(--muted) !important; }
.stMarkdown, .stText, [data-testid="stMarkdownContainer"] { color:var(--ink); }
.stTextInput label, .stFileUploader label { color:var(--ink) !important; font-weight:600; }
.stTextInput input { background:var(--panel) !important; color:var(--ink) !important; border:1px solid var(--line) !important; border-radius:4px !important; }
.stTextInput input::placeholder { color:#89928d !important; }
.stFileUploader section { background:rgba(251,250,245,.8) !important; border:1px dashed #aebbb3 !important; border-radius:5px !important; }
.stFileUploader section * { color:var(--ink) !important; }
.telemetry { border-top:2px solid var(--ink); padding:1rem 0 1.4rem; }
.telemetry .value { font:500 2rem 'DM Mono',monospace; color:var(--ink); }
.telemetry .label { color:var(--muted); font-size:.82rem; }
.source { border-left:3px solid var(--coral); background:#ebe9df; padding:.7rem 1rem; margin:.5rem 0; font-size:.86rem; }
.process-grid { display:grid; grid-template-columns:repeat(3, 1fr); gap:.6rem; margin:1rem 0 1.4rem; }
.process-cell { border-top:2px solid var(--ink); padding:.65rem 0; }
.process-value { font:500 1.3rem 'DM Mono',monospace; }
.process-label { color:var(--muted); font-size:.75rem; }
.stButton button { border-radius:3px; border:1px solid var(--ink); background:var(--ink); color:white !important; font-weight:600; }
.stButton button:hover { border-color:var(--coral); background:#263731; }
.stChatMessage { background:rgba(251,250,245,.7); border-bottom:1px solid var(--line); border-radius:4px; }
.stChatMessage * { color:var(--ink) !important; }
.funnel-row { display:grid; grid-template-columns:7.2rem 1fr 2.5rem; align-items:center; gap:.6rem; margin:.5rem 0; color:var(--ink); font-size:.8rem; }
.funnel-track { height:1.1rem; background:#dfe5e1; border-radius:2px; overflow:hidden; }
.funnel-fill { height:100%; background:var(--blue); border-radius:2px; }
.funnel-count { font:500 .78rem 'DM Mono',monospace; text-align:right; }
</style>
""", unsafe_allow_html=True)

API_URL = os.getenv("PRUNERAG_API_URL", "http://localhost:8000")
if "messages" not in st.session_state:
    st.session_state.messages = []
if "metrics" not in st.session_state:
    st.session_state.metrics = {"latency_ms": 0, "input_tokens": 0, "baseline_tokens": 0, "tokens_saved": 0, "pruning_reduction_pct": 0, "cost_saved_usd": 0}
if "pipeline" not in st.session_state:
    st.session_state.pipeline = None
if "document" not in st.session_state:
    st.session_state.document = None

st.markdown('<div class="eyebrow">Local intelligence / telemetry console</div>', unsafe_allow_html=True)
st.title("PruneRAG Engine")
st.markdown('<p class="subtle">Ask your documents sharper questions. Watch the context get smaller without losing the signal.</p>', unsafe_allow_html=True)
st.write("")

chat_col, metric_col = st.columns([1.55, 1], gap="large")
with chat_col:
    st.markdown('<div class="eyebrow">01 / retrieval workspace</div>', unsafe_allow_html=True)
    upload = st.file_uploader("Upload a PDF", type=["pdf"], label_visibility="collapsed")
    if upload and st.button("Index document", width="content"):
        try:
            response = requests.post(f"{API_URL}/api/v1/ingest", files={"file": (upload.name, upload.getvalue(), "application/pdf")}, timeout=60)
            response.raise_for_status()
            st.session_state.document = response.json()
            st.success(f"Indexed {st.session_state.document['chunks_indexed']} context chunks")
        except requests.RequestException as exc:
            st.error(f"Backend unavailable: {exc}")
    if st.session_state.document:
        document = st.session_state.document
        st.markdown('<div class="eyebrow">Document processing</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="process-grid"><div class="process-cell"><div class="process-value">{document["pages_indexed"]}</div><div class="process-label">pages parsed</div></div><div class="process-cell"><div class="process-value">{document["chunks_indexed"]}</div><div class="process-label">context chunks</div></div><div class="process-cell"><div class="process-value">{document["estimated_tokens"]}</div><div class="process-label">estimated tokens</div></div></div>', unsafe_allow_html=True)
        st.caption("Document processing is complete. Ask a question below to measure retrieval and pruning.")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    with st.form("query_form", clear_on_submit=True):
        prompt = st.text_input("Ask a question", placeholder="e.g. What are the main findings in this document?")
        context_budget = st.number_input("Context token budget", min_value=100, max_value=8000, value=2000, step=100)
        submitted = st.form_submit_button("Run query", width="stretch")
    if submitted and prompt.strip():
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        try:
            response = requests.post(f"{API_URL}/api/v1/query", json={"query": prompt, "enable_pruning": True, "max_context_tokens": context_budget}, timeout=90)
            response.raise_for_status()
            payload = response.json()
            st.session_state.metrics = payload["metrics"]
            st.session_state.pipeline = payload.get("pipeline")
            with st.chat_message("assistant"):
                st.write(payload["answer"])
                for source in payload["sources"]:
                    st.markdown(f'<div class="source">{source["source"]} / page {source["page"]}</div>', unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": payload["answer"]})
        except requests.RequestException as exc:
            st.error(f"Backend unavailable: {exc}")

with metric_col:
    st.markdown('<div class="eyebrow">02 / live telemetry</div>', unsafe_allow_html=True)
    metrics = st.session_state.metrics
    cards = [
        ("Query latency", f"{metrics['latency_ms']} ms", "target < 500 ms"),
        ("Tokens processed", f"{metrics['input_tokens']}", f"baseline {metrics['baseline_tokens']}"),
        ("Pruning reduction", f"{metrics['pruning_reduction_pct']}%", f"{metrics['tokens_saved']} tokens saved"),
        ("Estimated savings", f"${metrics['cost_saved_usd']:.6f}", "per request"),
    ]
    for label, value, detail in cards:
        st.markdown(f'<div class="telemetry"><div class="value">{value}</div><div class="label">{label} / {detail}</div></div>', unsafe_allow_html=True)
    if st.session_state.pipeline:
        pipeline = st.session_state.pipeline
        st.markdown('<div class="eyebrow">03 / optimization trace</div>', unsafe_allow_html=True)
        stages = {
            "Indexed": pipeline["indexed_chunks"],
            "Retrieved": pipeline["retrieved_candidates"],
            "Relevant": pipeline["threshold_passed"],
            "Sent to LLM": pipeline["context_chunks"],
        }
        max_stage = max(stages.values()) or 1
        funnel_html = "".join(
            f'<div class="funnel-row"><span>{label}</span><div class="funnel-track"><div class="funnel-fill" style="width:{max(4, value / max_stage * 100)}%"></div></div><span class="funnel-count">{value}</span></div>'
            for label, value in stages.items()
        )
        st.markdown(funnel_html, unsafe_allow_html=True)
        before = pipeline["tokens_before_pruning"]
        after = pipeline["tokens_after_pruning"]
        reduction = round(max(0, before - after) / max(1, before) * 100, 1)
        st.markdown(f'<div class="source"><strong>{reduction}% context reduction</strong><br>{before} estimated tokens before pruning → {after} after pruning<br>Threshold {pipeline["relevance_threshold"]} / duplicate cutoff {pipeline["duplicate_similarity_threshold"]}</div>', unsafe_allow_html=True)
        with st.expander("Inspect processing stages"):
            st.json(pipeline)
    st.caption("Metrics use a local token estimate for zero-cost development. Gemini is optional.")
