# PruneRAG Validation Runbook

This runbook validates document processing, retrieval quality, pruning behavior, and concurrent performance in local mode.

## 1. Start the application

```powershell
py -3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
py -3 -m streamlit run ui/app.py --server.port 8501
```

Generate the supplied test document:

```powershell
py -3 scripts/create_sample_pdf.py
```

Open `http://localhost:8501`, upload `sample_data/quarterly_report.pdf`, and click **Index document**.

## 2. Validate document processing

The UI should show pages parsed, context chunks, and estimated tokens immediately after indexing. The API should report the same result:

```powershell
curl.exe -X POST -F "file=@sample_data/quarterly_report.pdf" http://localhost:8000/api/v1/ingest
```

Pass criteria:

- HTTP `200`
- At least one page and one chunk indexed
- Estimated tokens greater than zero

## 3. Validate optimization

Ask these questions one at a time in the UI:

- `What was Q3 revenue and adjusted EBITDA?`
- `Which cost optimization actions reduced spending?`
- `What are the Q4 revenue expectations and risks?`

Review **Optimization trace** after each answer. It reports:

```text
Indexed -> Retrieved -> Relevant -> Sent to LLM
```

Pass criteria:

- Sources identify the expected page
- Relevant chunks are fewer than or equal to retrieved chunks
- Tokens after pruning are fewer than or equal to tokens before pruning
- The answer is grounded in the displayed source content
- Latency is below `500 ms` in local fallback mode for a small document

For a direct API check:

```powershell
$body = @{ query = "What was Q3 revenue and adjusted EBITDA?"; enable_pruning = $true } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/query -ContentType application/json -Body $body | ConvertTo-Json -Depth 8
```

## 4. Compare pruning impact

Run the same question with pruning enabled and disabled. Compare `metrics.input_tokens`, `metrics.tokens_saved`, and `pipeline.tokens_after_pruning`.

```powershell
$query = @{ query = "What are the Q3 customer and product metrics?"; enable_pruning = $true; max_context_tokens = 200 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/query -ContentType application/json -Body $query | ConvertTo-Json -Depth 8
```

For a meaningful reduction test, use a document with repeated or overlapping sections and a lower context budget. A single small report may legitimately show `0%` reduction because it has only one relevant passage.

## 5. Measure performance

Run the functional suite:

```powershell
py -3 -m pytest -q
```

Run a headless Locust test for two minutes with ten concurrent users:

```powershell
locust -f tests/locustfile.py --headless --users 10 --spawn-rate 2 --run-time 2m --host http://localhost:8000
```

Record requests per second, median latency, p95 latency, failure count, and API error rate. A useful baseline is zero failures, p95 below `500 ms`, and stable throughput as users increase from 1 to 10. Run each scenario three times and compare medians; the first run may include model or OS cache warm-up.

## 6. Optional dense mode

Set `PRUNERAG_ENABLE_DENSE=true` before starting the API to enable `all-MiniLM-L6-v2`. The first query downloads/loads model weights and is not a representative latency sample. Warm up once, then repeat the performance test.