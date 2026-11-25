# Contract Comparison Agent (prototype)

Compares a supplier's contract with the company's gold-standard clauses and tracks every change between contract versions, with lawyer review of each point and export to Word.

**Stack:** Python · Streamlit · Azure OpenAI · MongoDB (gold-standard clause store) · python-docx · ReportLab
**Role:** Lead developer: design and implementation
**Status:** Prototype that proved the value with the legal team; its production backend is [contract-comparison-api](https://github.com/lucasboliveirasipp/contract-comparison-api)

> Built at a large Brazilian insurer. The company is replaced by the fictional **Acme Seguros**, and every name, document and data point here is fictional. Code, prompts and UI are in Portuguese, written for Brazilian business teams.

## Problem

Lawyers reviewed supplier contracts clause by clause against the approved wording for liability, confidentiality, data protection, termination and so on. When a supplier sent a modified version back, they also had to find every change by hand. Both tasks were slow and error-prone on long contracts.

## What I built

1. **Gold standard vs supplier draft:** finds the relevant standard clauses with a tiered theme search (exact title, partial title, body text, full-text index), compares them with the supplier's wording and classifies the impact of every difference from the company's point of view, with a suggested response.
2. **Original vs modified:** lists every change between two versions, with a summary.
3. **Analysis chat:** follow-up questions about the analysis just produced.
4. **Human in the loop:** lawyers accept, reject or edit each point, and their feedback is stored with the analysis.
5. **Export** of the reviewed analysis to Word (with comments) or PDF.

## Design decisions

- **The model proposes, the lawyer decides.** Each point is reviewed before export, so the tool speeds up review without replacing legal judgement.
- **Prototype first.** A Streamlit app talking straight to Azure OpenAI and MongoDB fixed the output format with real users before any backend work. The production version then moved prompts and the clause index behind the company's AI gateway.

Full write-up with trade-offs (both phases): [docs/CASE_STUDY.md](docs/CASE_STUDY.md)

## Run it

```bash
python -m venv .venv && .venv\Scripts\activate   # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                               # Azure OpenAI + MongoDB
streamlit run streamlit_app.py
```

Needs a MongoDB collection with your own gold-standard clauses, and sample contracts to compare.

---
Part of my [AI engineering portfolio](https://github.com/lucasboliveirasipp).
