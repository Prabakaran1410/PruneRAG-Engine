import os
import requests
import streamlit as st

st.set_page_config(page_title="PruneRAG Engine", page_icon="P", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root { --ink:#17231f; --muted:#66736d; --paper:#f4f1e9; --mint:#c9e7d8; --coral:#e87961; --line:#d9d8cf; }
.stApp { background:var(--paper); color:var(--ink); }
[data-testid="stHeader"] { background:transparent; }
.block-container { max-width:1400px; padding:2.5rem 4rem 4rem; }
h1,h2,h3,p,button,label { font-family:'Space Grotesk',sans-serif; }
h1 { font-size:clamp(2rem,4vw,4.5rem); letter-spacing:0; line-height:1; margin:0; }
.eyebrow { color:var(--coral); font:500 0.75rem 'DM Mono',monospace; letter-spacing:0.08em; text-transform:uppercase; }
.subtle { color:var(--muted); }
.telemetry { border-top:2px solid var(--ink); padding:1rem 0 1.4rem; }
.telemetry .value { font:500 2rem 'DM Mono',monospace; color:var(--ink); }
.telemetry .label { color:var(--muted); font-size:.82rem; }
.source { border-left:3px solid var(--coral); background:#ebe9df; padding:.7rem 1rem; margin:.5rem 0; font-size:.86rem; }
.stButton button { border-radius:2px; border:1px solid var(--ink); background:var(--ink); color:white; }
.stChatMessage { background:transparent; border-bottom:1px solid var(--line); border-radius:0; }
</style>
""", unsafe_allow_html=True)

API_URL = os.getenv("PRUNERAG_API_URL", "http://localhost:8000")
if "messages" not in st.session_state:
    st.session_state.messages = []
if "metrics" not in st.session_state:
    st.session_state.metrics = {"latency_ms": 0, "input_tokens": 0, "baseline_tokens": 0, "tokens_saved": 0, "pruning_reduction_pct": 0, "cost_saved_usd": 0}

st.markdown('<div class="eyebrow">Local intelligence / telemetry console</div>', unsafe_allow_html=True)
st.title("PruneRAG Engine")
st.markdown('<p class="subtle">Ask your documents sharper questions. Watch the context get smaller without losing the signal.</p>', unsafe_allow_html=True)
st.write("")

chat_col, metric_col = st.columns([1.55, 1], gap="large")
with chat_col:
    st.markdown('<div class="eyebrow">01 / retrieval workspace</div>', unsafe_allow_html=True)
    upload = st.file_uploader("Upload a PDF", type=["pdf"], label_visibility="collapsed")
    if upload and st.button("Index document", use_container_width=False):
        try:
            response = requests.post(f"{API_URL}/api/v1/ingest", files={"file": (upload.name, upload.getvalue(), "application/pdf")}, timeout=60)
            response.raise_for_status()
            st.success(f"Indexed {response.json()['chunks_indexed']} context chunks")
        except requests.RequestException as exc:
            st.error(f"Backend unavailable: {exc}")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    prompt = st.chat_input("Ask about the indexed document")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        try:
            response = requests.post(f"{API_URL}/api/v1/query", json={"query": prompt, "enable_pruning": True}, timeout=90)
            response.raise_for_status()
            payload = response.json()
            st.session_state.metrics = payload["metrics"]
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
    st.caption("Metrics use a local token estimate for zero-cost development. Gemini is optional.")
