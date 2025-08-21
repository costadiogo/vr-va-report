from src.process import process_vr
import os

base_path = "data"

if __name__ == "__main__":
    
    RESULT = process_vr(
        active_xlsx=os.path.join(base_path, "ATIVOS.xlsx"),
        admitted_month_xlsx=os.path.join(base_path, "ADMISSÃO_ABRIL.xlsx"),
        fired_xlsx=os.path.join(base_path, "DESLIGADOS.xlsx"),
        vacation_xlsx=os.path.join(base_path, "FÉRIAS.xlsx"),
        absence_xlsx=os.path.join(base_path, "AFASTAMENTOS.xlsx"),
        interns_xlsx=os.path.join(base_path, "ESTÁGIO.xlsx"),
        apprentice_xlsx=os.path.join(base_path, "APRENDIZ.xlsx"),
        exterior_xlsx=os.path.join(base_path, "EXTERIOR.xlsx"),
        working_days_basis_xlsx=os.path.join(base_path, "Base_dias_uteis.xlsx"),
        union_base_values_xlsx=os.path.join(base_path, "Base_sindicato_x_valor.xlsx")
    )
    
    RESULT.to_excel("VR MENSAL 05-2025.xlsx", index=False)