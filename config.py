"""
config.py — central constants for PocketForge.

Everything that might change in one place: the target, where files live, the
score thresholds we judge candidates against, and the model/LLM names. Import
from here rather than hard-coding values in the agents/tools, so a change is a
one-line edit instead of a hunt across files.
"""

from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
TARGETS_DIR = DATA_DIR / "targets"
PRECOMPUTED_DIR = DATA_DIR / "precomputed"
RESULTS_DIR = ROOT / "results"

# ── Demo target: SARS-CoV-2 main protease (Mpro / 3CLpro) ───────────────────
TARGET_NAME = "SARS-CoV-2 main protease (Mpro / 3CLpro)"
TARGET_PDB_ID = "6LU7"
TARGET_PDB_FILE = TARGETS_DIR / "6LU7.pdb"
REFERENCE_LIGAND = "N3"  # co-crystallised inhibitor; used to define the pocket

# Docking box around the pocket — set these from the N3 ligand's location in P1.
# Placeholders for now (centre x/y/z and box size in Angstroms).
POCKET_CENTER = (None, None, None)
POCKET_BOX_SIZE = (20.0, 20.0, 20.0)

# ── Generation ──────────────────────────────────────────────────────────────
GENERATIVE_MODEL = "DiffSBDD"          # pretrained; weights pulled from HF Hub
N_CANDIDATES = 100                      # how many molecules to generate per run
RANDOM_SEED = 42                        # fixed for reproducibility (NFR-3)

# ── Scoring thresholds (what "good" looks like — see testinglog.md) ─────────
QED_MIN = 0.50          # drug-likeness, 0-1 (higher is better)
SA_MAX = 5.0            # synthetic accessibility, ~1 easy -> 10 hard (lower is better)
REDOCK_RMSD_MAX = 2.0   # P1 gate: N3 must re-dock within this many Angstroms

# ── Orchestration / LLM (stretch) ───────────────────────────────────────────
LLM_PROVIDER = "groq"
LLM_MODEL = "openai/gpt-oss-120b"       # free tier; reasoning/coordination only
# The Groq API key is read from the environment (set as an HF Space secret),
# never stored here.
