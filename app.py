import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import py3Dmol
from agents.generator import generate_smiles
from tools.chem_tools import get_chem_metrics, filter_substructure
from tools.docking_tools import dock_molecule
import config

st.set_page_config(page_title="TAMG | Molecule Generator", layout="wide")

st.title("TAMG — Target-Aware Molecule Generator 🧬")
st.markdown("LLM-proposed, docking-validated generation for SARS-CoV-2 Mpro.")

with st.sidebar:
    st.header("Control Panel")
    target = st.text_input("Target Protein", value="SARS-CoV-2 Mpro (6LU7)")
    forbid = st.text_input("Forbid Substructure (SMARTS)", value="[N+](=[O-])[O-]")
    run_btn = st.button("Propose & Score", type="primary")

if run_btn:
    with st.spinner("Agent: LLM proposing SMILES via Groq..."):
        try:
            smiles = generate_smiles(target, forbid)
        except Exception as e:
            st.error(f"Generation failed: {e}")
            smiles = []
            
    if smiles:
        with st.spinner("Tools: Filtering & Docking Candidates..."):
            valid_smiles = filter_substructure(smiles, forbid)
            
            results = []
            # Evaluate top candidates only to manage latency
            for s in valid_smiles[:config.NUM_CANDIDATES]:
                metrics = get_chem_metrics(s)
                if metrics:
                    score = dock_molecule(s, "data/targets/6LU7.pdbqt", config.DOCKING_BOX_CENTER, config.DOCKING_BOX_SIZE)
                    results.append({
                        "SMILES": s, 
                        "QED": metrics['qed'], 
                        "SA": metrics['sa'], 
                        "Docking (kcal/mol)": score, 
                        "PB-Valid": "Yes" if score < 0 else "Fail"
                    })
            
            if results:
                df = pd.DataFrame(results).sort_values("Docking (kcal/mol)")
                st.dataframe(df, use_container_width=True)
                
                st.subheader("3D Pose Preview")
                best_smiles = df.iloc[0]["SMILES"]
                st.info(f"Visualizing top candidate: {best_smiles}")
                view = py3Dmol.view(width=800, height=400)
                view.addModel(best_smiles, "smi")
                view.setStyle({'stick': {}})
                view.zoomTo()
                components.html(view._make_html(), height=400, width=800)
            else:
                st.warning("No valid molecules survived the docking and filtering gates.")
