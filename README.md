---
# ── Hugging Face Space configuration ──
# This YAML header tells the HF Space how to run the app.
# The T4 GPU hardware is NOT set here — set it in the Space's Settings → Hardware.
title: PocketForge
emoji: 🧬
colorFrom: blue
colorTo: indigo
sdk: streamlit
app_file: app.py
python_version: "3.12"
pinned: false
---

# PocketForge — Target-Aware Molecule Generator

Generate novel, drug-like small molecules that fit the **SARS-CoV-2 main protease (Mpro / 3CLpro)** binding pocket, score them, and rank them — a Pak-Angels Cohort 11 final-hackathon MVP.

See `PRD.md`, `testinglog.md`, and `roadmap.md` (kept outside this repo) for the full plan.

## Status
**P0 — baseline.** This is the runnable shell: the Streamlit dashboard loads and shows the pipeline stages as placeholders. DiffSBDD generation, docking, and scoring are added in later phases (P1–P4).

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
GitHub is the source of truth. Pushing to `main` triggers `.github/workflows/sync-to-hf.yml`, which pushes the repo to the Hugging Face Space. The Space runs Streamlit on a **T4 GPU** (set in Space Settings → Hardware).

## File index
| File | What it does |
|---|---|
| `app.py` | Streamlit dashboard (UI shell for now; runs a full pass in later phases). |
| `config.py` | Central constants — target, pocket box, score thresholds, model + LLM names. |
| `requirements.txt` | Python dependencies (freeze exact versions after the first green install). |
| `.python-version` | Pins Python 3.12 (CrewAI needs ≤3.12). |
| `.gitignore` | Keeps results, caches, and secrets out of git. |
| `agents/` | One file per agent — added in P1–P4. |
| `tools/` | Deterministic scientific tools the agents call — added in P1–P3. |
| `data/targets/6LU7.pdb` | Demo target structure (add in P0/P1). |
| `data/precomputed/` | Cached results for the backup demo (added in P5). |
| `.github/workflows/sync-to-hf.yml` | Pushes the repo to the HF Space on each commit to `main`. |
