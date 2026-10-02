# Product Requirements Document (PRD)

**Project:** PocketForge — Target-Aware Molecule Generator
_(working name; rename freely)_

**Owner:** Ahmed Hassan
**Context:** Pak-Angels Cohort 11 — Final Hackathon
**Document status:** Final — decisions locked; build in progress (P0)
**Last updated:** 3 Oct 2026
**Companion docs:** `testinglog.md` (how to test each phase) · `roadmap.md` (after-hackathon refinement & launch)

> **Framing.** The system spec this is based on describes a full enterprise SBDD platform. This PRD defines a tight, demoable **MVP**: one target, a pretrained model, in-silico scoring, a CrewAI-orchestrated pipeline, and a Streamlit dashboard. The enterprise build lives in `roadmap.md`.

---

## 0. Locked decisions

| Decision | Choice |
|---|---|
| **Generative model** | **DiffSBDD** (pretrained) — target-aware 3D diffusion; constraint/inpainting support. |
| **Demo target** | **SARS-CoV-2 main protease (Mpro / 3CLpro)** — PDB **6LU7**, reference ligand **N3**. Published DiffSBDD/TargetDiff results exist for 3CLpro (baseline to check our output against); real drug anchor = nirmatrelvir. |
| **Multi-agent framework** | **CrewAI** — agents that call the scientific tools; orchestrates the pipeline. |
| **Human-in-the-loop control** | **Forbid-substructure** — user flags an unwanted group; matching candidates are removed and the set re-ranked. |
| **Dev / testing compute** | **Google Colab (T4 GPU)** — free, where generation + docking are built and tested. |
| **Deployment** | **Hugging Face Space (Streamlit SDK) on a T4 GPU**, synced from **GitHub** (source of truth). |

---

## 1. Problem & Vision

**Problem.** For a given protein target (the biological "lock"), finding a small molecule (the "key") that binds tightly, is drug-like, is safe, and is actually makeable is slow and expensive.

**Vision (long-term).** An AI system that takes a 3D binding pocket and generates novel candidate molecules shaped to fit it, scoring them for binding, drug-likeness, safety, and synthesizability, with a chemist steering the search. Full build path: `roadmap.md`.

**Hackathon thesis.**
> _"Given the SARS-CoV-2 main protease pocket, we generate novel, valid, drug-like molecules that plausibly bind it — end to end, in silico, with a human able to steer generation — and our numbers line up with published results for the same target."_

A working, trustworthy slice on this one target is the goal. Breadth is not.

---

## 2. Users

| User | What they need from the MVP |
|---|---|
| **Judge / mentor** | A working demo: pocket in → ranked molecules out, with metrics they can trust and a 3D view. |
| **Medicinal chemist (simulated role)** | Forbid an unwanted substructure and see generation/filtering respond. |
| **Team testers (new to bioinfo)** | Plain-language, phase-by-phase testing guidance (`testinglog.md`). |

---

## 3. Scope

Scope creep is the #1 hackathon killer. This section is the firewall.

### 3.1 In scope (MVP — must demo)
1. **Target ingestion** — load Mpro (6LU7); define the pocket from reference ligand N3.
2. **Generation** — pretrained **DiffSBDD** produces candidate molecules conditioned on the pocket.
3. **Evaluation & ranking** — per candidate: validity, **QED**, **SA score**, **docking score** (Vina/smina), **PoseBusters** pass/fail; combine into a ranked list.
4. **Human-in-the-loop** — **forbid-substructure**: flag an unwanted group; remove matches; re-rank.
5. **Orchestration** — a **CrewAI** crew coordinates the stages (agents call the scientific tools).
6. **Dashboard** — a **Streamlit** app: select target → generate → ranked table (SMILES + metrics) + a **3D viewer** (py3Dmol) showing the molecule in the pocket.
7. **Double-check** — compare our set's Vina/QED/SA against **published 3CLpro numbers**; dock N3 as a baseline.

### 3.2 Out of scope
- Training/fine-tuning a model from scratch.
- Full ADMET suite; molecular dynamics; retrosynthesis beyond SA score.
- Multi-target selectivity / off-target panels.
- Microservices, Kubernetes, audit logging, multi-user isolation.
- Any **wet-lab** validation (the MVP is 100% in silico / dry lab — see `testinglog.md` §9).

### 3.3 Stretch goals (only if MVP is solid)
- **Scaffold-locking** via DiffSBDD inpainting (true generative steering).
- **Active-learning loop**: the CrewAI/Groq orchestrator re-prompts generation toward the weakest metric.
- **ADMET-lite**: Lipinski Rule-of-5 + PAINS flags (cheap with RDKit).

---

## 4. Requirements

### 4.1 Functional requirements

| # | Requirement | Priority |
|---|---|---|
| FR-1 | Load Mpro (6LU7); define the pocket from N3. | Must |
| FR-2 | Generate ≥100 candidates via DiffSBDD. | Must |
| FR-3 | Filter invalid molecules; report valid %. | Must |
| FR-4 | Compute QED, SA, docking per valid candidate. | Must |
| FR-5 | PoseBusters pose check; report pass rate. | Must |
| FR-6 | Rank by combined score; show top-N. | Must |
| FR-7 | 3D view of any candidate in the pocket. | Must |
| FR-8 | Forbid a substructure → remove matches → re-rank. | Must |
| FR-9 | CrewAI crew orchestrates the stages. | Must |
| FR-10 | Report novelty vs a known reference set. | Should |
| FR-11 | Compare output distribution to published 3CLpro results; dock N3 baseline. | Should |
| FR-12 | Export top candidates (SMILES + metrics) as CSV. | Should |
| FR-13 | Scaffold-locking / active-learning loop / ADMET-lite. | Could (stretch) |

### 4.2 Non-functional requirements

| # | Requirement | Target |
|---|---|---|
| NFR-1 | **Compute:** dev generation + docking on **Colab T4**; live demo on the **HF T4 Streamlit Space**. | Mandatory |
| NFR-2 | **Demo latency:** pocket → 100 candidates → ranked results within a judge's patience (~3–5 min). | High |
| NFR-3 | **Reproducible:** fixed seed; dependency versions frozen after the first green install. | High |
| NFR-4 | **Explainable numbers:** every metric shown has a plain-language meaning the team can defend. | High |
| NFR-5 | **Graceful failure:** junk/empty input → friendly message, no crash. | Medium |
| NFR-6 | **Demo insurance:** keep a backup screen recording of a good run for demo day. | High |

### 4.3 Data requirements
- **Target:** Mpro, **PDB 6LU7**, reference ligand **N3** (RCSB PDB).
- **Reference chemical set:** a ChEMBL slice / the model's training set, for novelty.
- **Baseline numbers:** published DiffSBDD / TargetDiff Vina/QED/SA for 3CLpro.
- All data sources free and public (RCSB PDB, ChEMBL, PubChem, CrossDocked).

---

## 5. Tools & Technologies

### 5.1 Core stack

| Layer | Tool | Why / notes |
|---|---|---|
| **Language** | Python **3.12** | CrewAI requires ≤3.12; pinned up front. |
| **Cheminformatics** | **RDKit** | SMILES validity, QED, SA, Lipinski/PAINS, SMARTS matching (forbid-substructure), 2D/3D. |
| **Protein / pocket prep** | Open Babel, PDBFixer / `reduce`, Meeko | Clean protein, add hydrogens, convert to `.pdbqt`. |
| **Generative model** | **DiffSBDD** (pretrained) | Target-aware 3D diffusion; weights pulled from HF Hub at startup. |
| **Docking** | **AutoDock Vina** / **smina** | CPU, free, standard. kcal/mol binding score. |
| **3D pose validity** | **PoseBusters** | Catches physically broken molecules. Credibility filter. |
| **3D visualization** | **py3Dmol** | Molecule inside the pocket, in the UI. |
| **Orchestration** | **CrewAI** | Agents call the scientific tools; coordinates the pipeline. CPU-only (calls Groq over the network). |
| **LLM (for agents)** | **Groq** (`openai/gpt-oss-120b`) | Fast, free tier. Reasoning/coordination only — not the generator. |
| **UI** | **Streamlit** | The dashboard: ranked table, metrics, 3D view, forbid-substructure control. |
| **Dev / testing compute** | **Google Colab (T4 GPU)** | Build and test generation + docking here. |
| **Deployment** | **HF Space (Streamlit SDK) on T4 GPU** | Live demo; synced from GitHub. |
| **Version control** | **GitHub** (source of truth) | Commit a running baseline, then commit after each working step. |

### 5.2 Key reference datasets (all free)
- **RCSB PDB** — 6LU7 (Mpro + N3).
- **CrossDocked2020 / PDBbind** — the benchmark sets for the baseline comparison.
- **ChEMBL / PubChem** — known-molecule reference for novelty.

### 5.3 Architecture
A CrewAI crew over a scientific pipeline, behind a Streamlit dashboard:

```
[ 6LU7 .pdb ] → target-prep agent (RDKit/OpenBabel) → [ Mpro pocket (from N3) ]
      → generation agent (DiffSBDD) → [ raw candidates ]
      → evaluation agent (RDKit QED+SA, Vina docking, PoseBusters, forbid-substructure) → [ ranked candidates ]
      → Streamlit dashboard (table + 3D viewer + forbid-substructure control)
      → (stretch) orchestrator agent re-prompts weak batches
```

### 5.3.1 Multi-agent patterns used (for the pitch)
- **Sequential (pipeline)** — the backbone: target prep → generate → evaluate → rank → display.
- **Parallel** — inside evaluation: QED, SA, docking, PoseBusters run independently on the same candidates, then **merge** into one ranked list.
- **Hierarchical / Supervisor + Magentic** — the stretch orchestrator: reads metrics, decides the weakest objective, re-prompts generation (active-learning loop).
- **Overall = Hybrid.**

The science stays in deterministic **tools**; the **CrewAI agents** handle reasoning/coordination and call those tools. Build the pipeline first (P0–P3), then add the CrewAI layer.

### 5.4 Deployment — GitHub source → HF T4 Streamlit Space

- **Source of truth:** GitHub. **Deployment:** a Hugging Face Space running the **Streamlit SDK** on a **T4 GPU**, so DiffSBDD runs live on the Space. Dev and pre-compute run on **Colab T4**.
- **Sync:** a **GitHub Action** pushes the repo to the Space on every commit to `main` (uses an HF access token stored as a GitHub secret). The Space declares `sdk: streamlit` + `app_file` + `python_version` in its `README.md` YAML header; the **T4 hardware is set in the Space's Settings**.
- **File handling:** small result files (SMILES + metrics as CSV/JSON, 3D poses as SDF/PDB) live in GitHub. **Model weights and large datasets are not committed** — they load from **HF Hub** at Space startup.

### 5.5 Secrets & API keys
- The core pipeline uses no API tokens; only the **CrewAI/Groq orchestrator** does.
- **Groq API key** → **HF Space secret** (Settings → Variables and secrets), read as an env var.
- **HF access token** (for the GitHub Action to push to the Space) → **GitHub Actions secret**.
- Locally, use a git-ignored `.streamlit/secrets.toml`. **Never commit keys.** If a key is ever committed, rotate it immediately.

### 5.6 Repository & deployment file structure
Modular — each agent in its own file, science kept in `tools/`, Python pinned to 3.12.

```
pocketforge/
├── README.md               # HF Space YAML header (sdk, app_file, python_version) + readme
├── requirements.txt        # deps (freeze exact versions after the first green install)
├── .python-version         # 3.12  — CrewAI needs ≤3.12
├── .gitignore              # results/, __pycache__/, .streamlit/secrets.toml, venv/
├── config.py               # target=6LU7, pocket box, thresholds, model + LLM names
├── app.py                  # Streamlit dashboard (UI + runs a pass, shows results)
├── agents/
│   ├── __init__.py
│   ├── target_prep.py      # load PDB, extract Mpro pocket from N3
│   ├── generator.py        # DiffSBDD wrapper (GPU; weights from HF Hub at startup)
│   ├── evaluator.py        # runs the scoring tools, builds the ranking
│   └── orchestrator.py     # (stretch) CrewAI/Groq manager — active-learning loop
├── tools/
│   ├── __init__.py
│   ├── chem_tools.py       # RDKit: validity, QED, SA, forbid-substructure (SMARTS)
│   ├── docking_tools.py    # Vina/smina wrapper
│   └── pose_tools.py       # PoseBusters checks
├── data/
│   ├── targets/6LU7.pdb    # demo target (small — OK in git)
│   └── precomputed/mpro_demo.json   # cached results for the backup demo (NFR-6)
└── .github/workflows/sync-to-hf.yml # Action: push repo → HF Space (uses HF token secret)
```

---

## 6. Finance — MVP / Hackathon budget

This PRD covers the hackathon MVP budget only. The post-hackathon wet-lab + production budget lives in `roadmap.md`.

> _Not financial advice. Rough planning ranges that vary by vendor, region, and time. Treat as orientation, not quotes._

| Item | Cost |
|---|---|
| Dev GPU — Colab T4 (generation + docking while building) | Free |
| Deployment GPU — HF T4 Streamlit Space ($0.40/GPU-hr, billed hourly while running) | ~$5–15 across the hackathon |
| DiffSBDD weights | Free (public download) |
| RDKit / Vina / PoseBusters | Free (open-source) |
| Datasets (6LU7, ChEMBL, CrossDocked) | Free (public) |
| Groq (orchestrator) | Free tier |
| GitHub hosting | Free |

**Realistic total: ~$5–15** — all dev and pre-compute on free Colab T4; the HF T4 covers the testing and demo hours.
_(Rough PKR reference at ~280 PKR/USD: ~PKR 1,400–4,200. Rate moves — illustration only.)_

**The real MVP budget is TIME:** ~20% setup & target prep · 25% first working generation run · 30% scoring + filtering + ranking · 15% Streamlit dashboard · 10% demo prep. Protect the last 10%.

---

## 7. Roadmap (hackathon build)

Step-by-step; commit after each green step. The post-hackathon roadmap lives in `roadmap.md`.

| Phase | Goal | "Done" means | Test gate (`testinglog.md`) |
|---|---|---|---|
| **P0 — Baseline** | Repo + empty app deploys | Scaffold committed; Streamlit shell deploys green on the HF T4 Space via GitHub sync; Colab T4 environment imports; 6LU7 + N3 + DiffSBDD weights in hand | Phase 0 checks pass |
| **P1 — Target prep** | Mpro pocket extracted | Pocket defined from N3; N3 re-docks with RMSD < 2.0 Å | Phase 1 checks pass |
| **P2 — Generation** | DiffSBDD runs on the pocket | ≥100 candidates generated | Phase 2 checks pass |
| **P3 — Evaluation** | Candidates scored & ranked | QED, SA, Vina, PoseBusters computed; top-N ranked; compared to published 3CLpro baseline | Phase 3 checks pass |
| **P4 — HITL + dashboard** | CrewAI + Streamlit live | Select→generate→ranked table + 3D view; forbidding a group re-ranks | Phase 4 checks pass |
| **P5 — Demo polish** | End-to-end + backup | Clean run-through; backup recording saved | Phase 5 checks pass |
| **S — Stretch** | Scaffold-locking / active-learning / ADMET-lite | Only after P0–P5 are green | Stretch checks |

**Golden rule:** start from a baseline that runs, commit it, then move one phase at a time. Don't start a phase until the previous gate is green.

---

## 8. Success criteria

1. Live run: Mpro pocket → generated molecules → ranked results with a 3D view.
2. Some candidates are valid, drug-like (QED), PB-valid, and dock near/better than N3 — and in the ballpark of published 3CLpro results.
3. The team can explain every number a judge points at.
4. Forbidding a substructure visibly changes the output.
5. Candidates are novel (not memorized known drugs).

---

## 9. Risks & assumptions

| Risk | Likelihood | Mitigation |
|---|---|---|
| DiffSBDD repo is hard to install / version hell | High | Nail the environment in P0 on Colab T4; freeze versions after first green install. |
| Generated molecules invalid or physically broken | Medium | Expected — PoseBusters + RDKit filters are the point; report pass rates honestly. |
| Docking too slow for live demo | Medium | Dock only top candidates after cheap RDKit filters; pre-compute for 6LU7. |
| Python 3.14 vs CrewAI's 3.12 | Medium | Pin 3.12 in `.python-version` and the Space config from the start. |
| Scope creep toward the enterprise spec | High | §3.2 is the firewall. |
| Team unfamiliar with bioinfo metrics | High | `testinglog.md` glossary + per-phase "what good looks like". |
| Cold start / network at demo time | Medium | Backup screen recording (NFR-6). |
