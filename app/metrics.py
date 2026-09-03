import time

INPUT_COST_PER_1M = 0.075
OUTPUT_COST_PER_1M = 0.30


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split())) if text.strip() else 0


def calculate_rag_metrics(prompt_text: str, completion_text: str, unpruned_token_count: int, start_time: float) -> dict:
    input_tokens = estimate_tokens(prompt_text)
    output_tokens = estimate_tokens(completion_text)
    raw_cost = (unpruned_token_count / 1_000_000) * INPUT_COST_PER_1M
    actual_cost = (input_tokens / 1_000_000) * INPUT_COST_PER_1M + (output_tokens / 1_000_000) * OUTPUT_COST_PER_1M
    return {
        "latency_ms": round((time.time() - start_time) * 1000, 2),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "baseline_tokens": unpruned_token_count,
        "tokens_saved": max(0, unpruned_token_count - input_tokens),
        "pruning_reduction_pct": round(max(0, unpruned_token_count - input_tokens) / max(1, unpruned_token_count) * 100, 1),
        "cost_saved_usd": round(max(0.0, raw_cost - actual_cost), 6),
    }