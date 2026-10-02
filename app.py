"""
app.py — PocketForge Streamlit dashboard.

P0 BASELINE: this is the runnable shell. It lays out the dashboard and shows
each pipeline stage as a placeholder, so we can deploy it green on the HF T4
Space and confirm the GitHub -> HF sync works BEFORE adding any DiffSBDD code.

Later phases wire the real work in:
  P1  target_prep   -> load 6LU7, extract the Mpro pocket from N3
  P2  generator     -> DiffSBDD generates candidates (GPU)
  P3  evaluator     -> QED / SA / docking / PoseBusters, then rank
  P4  orchestrator  -> CrewAI coordinates the agents; forbid-substructure control
"""

import streamlit as st

import config

# ── Page setup ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="PocketForge", page_icon="🧬", layout="wide")

st.title("🧬 PocketForge")
st.caption("Target-aware molecule generator — Pak-Angels Cohort 11")

# ── Sidebar: run controls ────────────────────────────────────────────────────
with st.sidebar:
    st.header("Run")
    st.write(f"**Target:** {config.TARGET_NAME}")
    st.write(f"**PDB:** {config.TARGET_PDB_ID}  ·  **Reference ligand:** {config.REFERENCE_LIGAND}")
    st.write(f"**Candidates to generate:** {config.N_CANDIDATES}")

    # Human-in-the-loop control (wired up in P4) — shown now so the layout is final.
    forbid = st.text_input(
        "Forbid substructure (SMARTS)",
        placeholder="e.g. [N+](=O)[O-]  (nitro group)",
        help="Candidates containing this group will be removed and the set re-ranked. (Active from P4.)",
    )

    generate = st.button("Generate", type="primary", use_container_width=True)

# ── Main area ────────────────────────────────────────────────────────────────
if generate:
    # P2+ will replace this with a real generation + scoring pass.
    st.info("Generation is not wired in yet — this is the P0 baseline shell. "
            "DiffSBDD + scoring arrive in P2–P3.")

col_results, col_viewer = st.columns([3, 2])

with col_results:
    st.subheader("Ranked candidates")
    st.write("The ranked table of candidates (SMILES · QED · SA · docking · PoseBusters) "
             "will appear here once scoring is wired in (P3).")

with col_viewer:
    st.subheader("3D view")
    st.write("The selected molecule inside the Mpro pocket will render here (py3Dmol, P3).")

st.divider()
st.caption("P0 baseline · deploy green, commit, then build P1 (target prep).")
