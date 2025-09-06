from typing import Optional
from . import utils

# -----------------------
# Mapeamento sindicato -> UF/State (para achar o valor VR)
# -----------------------
def infer_state_from_union(s: str) -> Optional[str]:
    if not isinstance(s, str):
        return None
    s0 = s.upper()
    
    # Mapeamento mais específico baseado nos dados reais
    if "SINDPD SP" in s0 or "SAO PAULO" in utils.strip_accents(s0):
        return "São Paulo"
    elif "SINDPD RJ" in s0 or "RIO DE JANEIRO" in s0:
        return "Rio de Janeiro"
    elif "SINDPPD RS" in s0 or "RIO GRANDE DO SUL" in s0:
        return "Rio Grande do Sul"
    elif "SITEPD PR" in s0 or "PARANA" in utils.strip_accents(s0) or "CURITIBA" in s0:
        return "Paraná"
    
    # Fallback para método geral
    UF_TO_STATE = {
        "SP": "São Paulo",
        "RJ": "Rio de Janeiro", 
        "RS": "Rio Grande do Sul",
        "PR": "Paraná",
    }
    
    for uf, state in UF_TO_STATE.items():
        if f" {uf} " in s0 or s0.endswith(f" {uf}.") or s0.endswith(f" {uf}") or s0.startswith(f"{uf} "):
            return state
    return None