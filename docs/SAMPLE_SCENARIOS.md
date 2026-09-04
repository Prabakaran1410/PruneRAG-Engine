# Sample Scenario Matrix

Generate all uploadable PDFs with:

```powershell
py -3 scripts/create_sample_pdf.py
```

Upload one scenario at a time. Restart the API between scenarios when isolated counts are needed.

| File | Scenario | Query | Expected signal |
| --- | --- | --- | --- |
| `quarterly_report.pdf` | Normal factual retrieval | `What was Q3 revenue and adjusted EBITDA?` | Correct financial values and source page |
| `exact_keyword_policy.pdf` | Exact IDs and terminology | `What is control ACME-LOG-117?` | Exact control ID and 400-day retention |
| `duplicate_sections.pdf` | Similarity deduplication | `What happened to the payments queue?` | Duplicate passages collapse during pruning |
| `long_handbook.pdf` | Token budget slicing | `What is the priority one escalation procedure?` | Lower after-pruning tokens with budget `100` or `200` |

For each scenario record indexed chunks, retrieved candidates, threshold-passing chunks, context chunks, tokens before/after pruning, latency, and source correctness.
