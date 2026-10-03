import os
import streamlit as st
from litellm import completion, AuthenticationError, NotFoundError

# Page Configuration
st.set_page_config(
    page_title="AI Assistant",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 Streamlit AI Assistant")
st.markdown("Powered by LiteLLM")

# --- SECRETS & ENVIRONMENT CONFIGURATION ---
# Safely load API keys from Streamlit secrets into environment variables
try:
    if "OPENAI_API_KEY" in st.secrets:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except Exception:
    # Allows local testing if secrets.toml isn't set up yet
    pass

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.header("Configuration")
    
    # Model selection (using active, reliable model slugs)
    provider_option = st.selectbox(
        "Select Model",
        [
            "groq/llama-3.1-8b-instant",
            "openai/gpt-4o-mini",
            "groq/llama-3.3-70b-versatile"
        ]
    )
    
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7)
    
    st.markdown("---")
    st.markdown("### API Key Status")
    st.text(f"OpenAI Key Set: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
    st.text(f"Groq Key Set: {'Yes' if os.getenv('GROQ_API_KEY') else 'No'}")

# --- CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("How can I help you today?"):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        try:
            # Format messages for LiteLLM
            formatted_messages = [
                {"role": m["role"], "content": m["content"]} 
                for m in st.session_state.messages
            ]
            
            # Execute LiteLLM completion call
            response = completion(
                model=provider_option,
                messages=formatted_messages,
                temperature=temperature
            )
            
            assistant_response = response.choices[0].message.content
            message_placeholder.markdown(assistant_response)
            
            # Save to history
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            
        except AuthenticationError as e:
            error_msg = "Authentication Error: Please check your API key in Streamlit Secrets (`Settings > Secrets`)."
            message_placeholder.error(error_msg)
        except NotFoundError as e:
            error_msg = f"Model Error: The model `{provider_option}` was not found or is unavailable for your account tier."
            message_placeholder.error(error_msg)
        except Exception as e:
            message_placeholder.error(f"An unexpected error occurred: {str(e)}")
