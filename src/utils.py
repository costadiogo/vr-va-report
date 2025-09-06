import pandas as pd
import sqlite3
import unicodedata

from typing import Any, List

DB_PATH = "database.db"

def strip_accents(s: str) -> str:
    if not isinstance(s, str):
        return ""
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def get_table_structure(self) -> str:
    """Obtém estrutura atual da tabela report."""
    try:
        with sqlite3.connect(self.db_path) as conn:
            # Obter schema da tabela
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(report)")
            columns = cursor.fetchall()
            
            # Obter amostra de dados
            df_sample = pd.read_sql("SELECT * FROM report LIMIT 3", conn)
            
            structure = "COLUNAS DA TABELA REPORT:\n"
            for col in columns:
                structure += f"- {col[1]} ({col[2]})\n"
            
            structure += f"\nTOTAL DE REGISTROS: {len(pd.read_sql('SELECT COUNT(*) FROM report', conn))}\n"
            structure += f"\nAMOSTRA DOS DADOS:\n{df_sample.to_string()}\n"
            
            return structure
    except Exception as e:
        return f"Erro ao obter estrutura: {e}"
    
def find_and_load_file(files: List[Any], file_type: str) -> pd.DataFrame:
    """Encontra e  carrega arquivo específico baseado no tipo."""
    file_patterns = {
        'ativos': ['ativo', 'active'],
        'admissao': ['admiss', 'admission'],
        'desligados': ['deslig', 'fired', 'demit']
    }
    
    patterns = file_patterns.get(file_type, [file_type])
    
    for file in files:
        file_name = file.name.lower()
        if any(pattern in file_name for pattern in patterns):
            return pd.read_excel(file)
    
    return pd.DataFrame()