import pandas as pd
from typing import List
from app.database.models import ComparisonResult

class Exporter:
    @staticmethod
    def _results_to_dataframe(results: List[ComparisonResult]) -> pd.DataFrame:
        data = []
        for r in results:
            data.append({
                "Estado": r.status,
                "Ruta": r.path,
                "Nombre": r.name,
                "Tamaño Local (Bytes)": r.size_local,
                "Tamaño NAS (Bytes)": r.size_nas,
                "Fecha Local": r.mod_time_local.strftime("%Y-%m-%d %H:%M:%S") if r.mod_time_local else None,
                "Fecha NAS": r.mod_time_nas.strftime("%Y-%m-%d %H:%M:%S") if r.mod_time_nas else None
            })
        return pd.DataFrame(data)

    @staticmethod
    def export_to_csv(results: List[ComparisonResult], file_path: str):
        df = Exporter._results_to_dataframe(results)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')

    @staticmethod
    def export_to_excel(results: List[ComparisonResult], file_path: str):
        df = Exporter._results_to_dataframe(results)
        df.to_excel(file_path, index=False, engine='openpyxl')
