import os
from crewai import Agent, Task, Crew
from langchain_groq import ChatGroq
import config

def generate_smiles(target_context, forbid_smarts=""):
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY missing in Secrets.")
        
    llm = ChatGroq(model=config.LLM_MODEL, groq_api_key=api_key)
    
    chemist = Agent(
        role="Medicinal Chemist",
        goal="Propose novel drug-like SMILES molecules.",
        backstory="Expert computational chemist.",
        llm=llm,
        allow_delegation=False
    )
    
    prompt = f"Propose 30 valid SMILES strings for {target_context}."
    if forbid_smarts:
        prompt += f" Do NOT include any molecule with this substructure SMARTS: {forbid_smarts}."
    prompt += " Only output the SMILES strings, one per line. No markdown."
    
    task = Task(description=prompt, agent=chemist, expected_output="Raw text list of SMILES.")
    crew = Crew(agents=[chemist], tasks=[task])
    result = crew.kickoff()
    
    return [s.strip() for s in str(result).split('\n') if len(s.strip()) > 3]
