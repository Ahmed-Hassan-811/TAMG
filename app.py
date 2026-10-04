import os
import re
import streamlit as st
import pandas as pd
from litellm import completion

from rdkit import Chem
from rdkit.Chem import QED, Descriptors, Lipinski, Crippen

# --- Real SA (synthetic accessibility) score from RDKit's contrib module ---
_SA_OK = True
try:
    import sys
    from rdkit.Chem import RDConfig
    sys.path.append(os.path.join(RDConfig.RDContribDir, "SA_Score"))
    import sascorer  # noqa: E402
except Exception:
    _SA_OK = False


# ---------------------------------------------------------------------------
# Error -> plain-language fix (shown in the UI when something breaks)
# ---------------------------------------------------------------------------
def explain_error(e):
    s = str(e).lower()
    if "no credits" in s or "openaiexception" in s or ("openai" in s and "credit" in s):
        return ("⚠️ Routed to OpenAI (no credits). In the sidebar **Select Model**, pick a model that "
                "starts with `groq/` — Groq is free.")
    if "ratelimit" in s or "rate limit" in s or "429" in s or "too many requests" in s:
        return ("⚠️ Groq free-tier rate limit hit. Wait ~30 seconds and retry, or lower "
                "**Candidates to propose** in the sidebar.")
    if "api key" in s or "authentication" in s or "401" in s or "invalid" in s and "key" in s:
        return "⚠️ API key problem — check `GROQ_API_KEY` in Streamlit Secrets (Manage app → Settings → Secrets)."
    if "not found" in s or "does not exist" in s or "decommission" in s:
        return "⚠️ That model is unavailable. Pick a `groq/` model from the dropdown."
    return f"⚠️ Unexpected error: {e}\n\nSee **🛠️ If something breaks** in the sidebar."


# ---------------------------------------------------------------------------
# Chemistry helpers (all real RDKit — no fake numbers)
# ---------------------------------------------------------------------------
def extract_smiles(text):
    """Pull candidate SMILES out of an LLM response: one token per line,
    stripped of numbering / markdown, kept only if RDKit can parse it."""
    found = []
    for raw in text.splitlines():
        line = raw.strip().strip("`").strip("*").strip()
        line = re.sub(r"^\s*\d+[\.\)]\s*", "", line)   # drop "1. " / "2) "
        if not line:
            continue
        token = line.split()[0]                          # SMILES have no spaces
        if Chem.MolFromSmiles(token):
            found.append(token)
    return found


def compile_forbidden(smarts_str):
    """Compile a comma-separated SMARTS list into (text, pattern) pairs."""
    pats = []
    for part in (smarts_str or "").split(","):
        part = part.strip()
        if not part:
            continue
        pat = Chem.MolFromSmarts(part)
        if pat is not None:
            pats.append((part, pat))
    return pats


def forbidden_hit(mol, pats):
    """Return the first forbidden SMARTS this molecule matches, else ''."""
    for text, pat in pats:
        if mol.HasSubstructMatch(pat):
            return text
    return ""


def compute_metrics(mol):
    mw = round(Descriptors.MolWt(mol), 1)
    logp = round(Crippen.MolLogP(mol), 2)
    hbd = Lipinski.NumHDonors(mol)
    hba = Lipinski.NumHAcceptors(mol)
    violations = sum([mw > 500, logp > 5, hbd > 5, hba > 10])   # Lipinski Rule of 5
    sa = round(sascorer.calculateScore(mol), 2) if _SA_OK else None
    return {
        "QED": round(QED.qed(mol), 3),
        "SA": sa,
        "MW": mw,
        "LogP": logp,
        "HBD": hbd,
        "HBA": hba,
        "Ro5": violations <= 1,
    }


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Target-Aware Molecule Generator (TAMG)", page_icon="🧬", layout="wide")
st.title("🧬 Target-Aware Molecule Generator (TAMG)")
st.markdown("LLM-proposed, RDKit-validated molecular candidates with substructure constraints.")

try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
    if "OPENAI_API_KEY" in st.secrets:   # optional, unused by default
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
except Exception:
    pass

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("🧬 Target & Structure Settings")
    target_protein = st.text_input("Target Protein", value="SARS-CoV-2 Mpro (6LU7)")
    forbid_substructures = st.text_input(
        "Forbid Substructures (SMARTS)",
        value="",
        placeholder="e.g. [#8]-[#8], C1OC1, [N;R0]=O",
        help="Comma-separated SMARTS. Any candidate matching one is dropped.",
    )

    st.markdown("---")
    st.header("⚙️ Model Configuration")
    # LiteLLM picks the provider from the text BEFORE the first '/'. Groq's model
    # id is 'openai/gpt-oss-120b', so the 'groq/' prefix is required to reach Groq.
    provider_option = st.selectbox(
        "Select Model",
        ("groq/openai/gpt-oss-120b", "groq/openai/gpt-oss-20b"),
        index=0,
        key="unique_tamg_model_selector",
    )
    temperature = st.slider("Temperature (Creativity)", 0.0, 1.0, 0.5)
    num_candidates = st.slider("Candidates to propose", 5, 50, 20)

    st.markdown("---")
    st.markdown("### API Key Status")
    st.text(f"Groq Key Set: {'Yes' if os.getenv('GROQ_API_KEY') else 'No'}")
    st.caption("SA score: " + ("available" if _SA_OK else "unavailable (SA column blank; not a blocker)"))

    # ---- In-UI troubleshooting flags ----
    with st.expander("🛠️ If something breaks"):
        st.markdown(
            "- **'no credits' / OpenAI error** → pick a model starting with `groq/` (free).\n"
            "- **RateLimitError (Groq)** → wait ~30s and retry, or lower *Candidates to propose*.\n"
            "- **'SA score: unavailable'** → the SA column is blank; everything else still works.\n"
            "- **'No valid molecules came back'** → raise *Temperature* and click again."
        )


def call_llm(messages):
    resp = completion(model=provider_option, messages=messages, temperature=temperature)
    return resp.choices[0].message.content


# ---------------------------------------------------------------------------
# Generate & validate
# ---------------------------------------------------------------------------
st.subheader("🧪 Generate & validate candidates")
st.caption("The LLM proposes molecules; RDKit then checks every one — validity, QED, SA, Lipinski, and your forbidden substructures.")

# The button only COMPUTES and stores results. Streamlit reruns the whole
# script on every interaction (e.g. sending a chat message), so if we rendered
# the table only inside this block it would vanish on the next rerun. Instead we
# save to st.session_state and render it below on every run.
if st.button("Generate & validate", type="primary"):
    pats = compile_forbidden(forbid_substructures)
    gen_prompt = (
        f"List {num_candidates} diverse, drug-like, synthesizable small-molecule SMILES "
        f"that could bind {target_protein or 'the target'}. "
        f"Output ONLY SMILES, one per line — no numbering, no prose, no markdown fences."
    )
    if forbid_substructures.strip():
        gen_prompt += f" Avoid molecules whose structure matches any of these SMARTS: {forbid_substructures}."

    try:
        with st.spinner("Generator agent proposing molecules…"):
            text = call_llm([{"role": "user", "content": gen_prompt}])

        proposed = extract_smiles(text)

        seen, rows = set(), []
        for smi in proposed:
            mol = Chem.MolFromSmiles(smi)
            if mol is None:
                continue
            canon = Chem.MolToSmiles(mol)
            if canon in seen:
                continue
            seen.add(canon)
            row = {"SMILES": canon, "Forbidden": forbidden_hit(mol, pats)}
            row.update(compute_metrics(mol))
            rows.append(row)

        if not rows:
            st.session_state["results"] = {
                "error": "No valid molecules came back. Raise the Temperature slider and try again."
            }
        else:
            df = pd.DataFrame(rows)
            kept = df[df["Forbidden"] == ""].copy().sort_values("QED", ascending=False)
            st.session_state["results"] = {
                "kept": kept,
                "proposed": len(proposed),
                "unique": len(df),
                "dropped": int((df["Forbidden"] != "").sum()),
            }
    except Exception as e:
        st.session_state["results"] = {"error": explain_error(e)}

# --- Render results from session_state (survives chat reruns) ---
res = st.session_state.get("results")
if res:
    if "error" in res:
        st.error(res["error"])
    else:
        kept = res["kept"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Proposed (valid)", res["proposed"])
        c2.metric("Unique", res["unique"])
        c3.metric("Passed forbid-filter", len(kept))
        c4.metric("Drug-like (Ro5)", int(kept["Ro5"].sum()))

        st.markdown("#### Ranked candidates (by QED)")
        show_cols = ["SMILES", "QED", "SA", "MW", "LogP", "HBD", "HBA", "Ro5"]
        st.dataframe(kept[show_cols], use_container_width=True, hide_index=True)

        if res["dropped"]:
            st.caption(f"{res['dropped']} candidate(s) dropped for containing a forbidden substructure.")

        st.download_button("Download CSV", kept.to_csv(index=False).encode(),
                           file_name="tamg_candidates.csv", mime="text/csv")

        st.markdown("#### ➡️ What to do with these results")
        st.markdown(
            "These numbers **rank** candidates — they don't prove any of them binds. "
            "Use them to pick a shortlist:\n"
            "1. **Keep the all-rounders** — high QED, low SA, and Ro5 = True (not just one good number).\n"
            "2. **Drop the impractical ones** — SA above ~5 (hard to make) or LogP above 5 (not drug-like).\n"
            "3. **Refine & re-run** — add more forbidden groups, or ask the chat below for "
            "*“smaller / simpler / more polar”* candidates, then **Generate** again.\n"
            "4. **Interrogate your picks** in the chat — *“compare candidate 1 and 3”*, "
            "*“how would I lower this one's LogP?”*\n"
            "5. **Download the CSV** of your shortlist.\n\n"
            "**Next stage (not in this app):** dock the shortlist to check real binding."
        )
        st.info("Scores are real RDKit computations. Docking/binding validation is not wired in — "
                "present this as LLM-proposed, RDKit-validated.")

# ---------------------------------------------------------------------------
# Free-form chat
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader("💬 Ask TAMG")

system_instructions = (
    "You are TAMG, an expert computational chemistry assistant for drug discovery. "
    f"Target: {target_protein or 'unspecified'}. "
    f"Forbidden substructures (SMARTS): {forbid_substructures or 'None'}. "
    "Give valid SMILES and property estimates (MW, LogP, HBD, HBA) when relevant, "
    "and never propose anything matching the forbidden substructures."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Ask about a candidate, a property, or request specific molecules…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        ph = st.empty()
        ph.markdown("Thinking…")
        try:
            msgs = [{"role": "system", "content": system_instructions}] + st.session_state.messages
            answer = call_llm(msgs)
            ph.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception as e:
            ph.error(explain_error(e))
