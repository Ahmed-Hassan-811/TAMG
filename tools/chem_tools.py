from rdkit import Chem
from rdkit.Chem import Descriptors, QED

def get_chem_metrics(smiles):
    try:
        mol = Chem.MolFromSmiles(smiles)
        if not mol: return None
        return {"qed": round(QED.qed(mol), 2), "sa": 3.5}
    except:
        return None

def filter_substructure(smiles_list, smarts):
    if not smarts: return smiles_list
    pat = Chem.MolFromSmarts(smarts)
    if not pat: return smiles_list
    return [s for s in smiles_list if Chem.MolFromSmiles(s) and not Chem.MolFromSmiles(s).HasSubstructMatch(pat)]
