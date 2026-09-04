# PruneRAG Engine

A zero-cost local RAG benchmark for PDF question answering, hybrid retrieval, and dynamic context pruning.

## Quick start

1. Create an environment and install dependencies:

   ```powershell
   py -3 -m venv .venv
   .\\.venv\\Scripts\\Activate.ps1
   pip install -r requirements.txt
   ```

2. Start the API:

   ```powershell
   uvicorn app.main:app --reload
   ```

3. In a second terminal, start the dashboard:

   ```powershell
   streamlit run ui/app.py
   ```

Open `http://localhost:8501`. The system works in local fallback mode without a Gemini key. Set `GEMINI_API_KEY` to enable Gemini 1.5 Flash when available.

## Tests and benchmark

```powershell
py -3 -m pytest
locust -f tests/locustfile.py --host=http://localhost:8000
```

For a complete validation procedure, see [docs/RUNBOOK.md](docs/RUNBOOK.md). Generate the included sample document with `py -3 scripts/create_sample_pdf.py`, then upload `sample_data/quarterly_report.pdf` in the dashboard.
Additional scenario documents and expected results are listed in [docs/SAMPLE_SCENARIOS.md](docs/SAMPLE_SCENARIOS.md). The generator creates PDFs for every `.txt` file in `sample_data/`.

Qdrant is included in `docker-compose.yml` for the next retrieval milestone. The current MVP uses an in-process hybrid fallback so development does not require Docker or a model download.
