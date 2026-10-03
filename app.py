import os
import streamlit as st
from litellm import completion, AuthenticationError, NotFoundError

# Page Configuration
st.set_page_config(
    page_title="Target-Aware Molecule Generator (TAMG)",
    page_icon="🧬",
    layout="wide"
)

st.title("🧬 Target-Aware Molecule Generator (TAMG)")
st.markdown("Generate and optimize target-specific molecular candidates with substructure constraints.")

# --- SECRETS & ENVIRONMENT CONFIGURATION ---
try:
    if "OPENAI_API_KEY" in st.secrets:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.header("🧬 Target & Structure Settings")
    
    # 1. Target Protein Selection
    target_protein = st.text_input(
        "Target Protein",
        value="SARS-CoV-2 Mpro (6LU7)",
        help="Specify the target protein name, accession code, or PDB ID."
    )
    
    # 2. Forbid Substructures (SMARTS format)
    forbid_substructures = st.text_input(
        "Forbid Substructures (SMARTS)",
        value="",
        placeholder="e.g., [N;R0]=O or leave blank",
        help="Provide SMARTS notation for undesirable chemical fragments or toxicophores to exclude."
    )
    
    st.markdown("---")
    st.header("⚙️ Model Configuration")
    
    # Model selector
    provider_option = st.selectbox(
        "Select Model",
        (
            "groq/llama-3.1-8b-instant",
            "openai/gpt-4o-mini",
            "groq/llama-3.3-70b-versatile"
        ),
        index=0,
        key="unique_tamg_model_selector"
    )
    
    temperature = st.slider("Temperature (Creativity)", 0.0, 1.0, 0.4)
    
    st.markdown("---")
    st.markdown("### API Key Status")
    st.text(f"OpenAI Key Set: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
    st.text(f"Groq Key Set: {'Yes' if os.getenv('GROQ_API_KEY') else 'No'}")

# --- SYSTEM PROMPT CONSTRUCTION ---
system_instructions = f"""You are TAMG (Target-Aware Molecule Generator), an expert computational chemistry assistant.
Your goal is to propose, analyze, and optimize molecular candidates for drug discovery.

Current Execution Parameters:
- Target Protein: {target_protein if target_protein else 'Unspecified Target'}
- Forbidden Substructures (SMARTS): {forbid_substructures if forbid_substructures else 'None'}

When generating candidates or answering molecular design queries:
1. Ensure proposed molecules strictly target {target_protein if target_protein else 'the specified target'}.
2. Verify that no proposed candidate contains any forbidden substructures matching: {forbid_substructures if forbid_substructures else 'None'}.
3. Provide valid SMILES strings along with basic property estimates (e.g., MW, LogP, HBD, HBA) when appropriate.
"""

# --- CHAT & GENERATION INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display conversation history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User prompt input
if prompt := st.chat_input("Enter generation constraints, SMILES query, or request molecular candidates..."):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate model response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Generating molecular candidates...")
        
        try:
            # Build payload with active system instructions
            formatted_messages = [
                {"role": "system", "content": system_instructions}
            ] + [
                {"role": m["role"], "content": m["content"]} 
                for m in st.session_state.messages
            ]
            
            # Execute LiteLLM API call
            response = completion(
                model=provider_option,
                messages=formatted_messages,
                temperature=temperature
            )
            
            assistant_response = response.choices[0].message.content
            message_placeholder.markdown(assistant_response)
            
            # Save response to chat history
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            
        except AuthenticationError:
            error_msg = "Authentication Error: Please check your API key settings in Streamlit Secrets."
            message_placeholder.error(error_msg)
        except NotFoundError:
            error_msg = f"Model Error: The model `{provider_option}` was not found or is unavailable for your API tier."
            message_placeholder.error(error_msg)
        except Exception as e:
            message_placeholder.error(f"An unexpected error occurred: {str(e)}")
