from PySide6.QtCore import QThread, Signal
from app.synology.client import SynologyClient
import os
import logging

class UploaderWorker(QThread):
    progress = Signal(str, int)
    file_progress = Signal(str, int)
    finished = Signal(int, int) # success_count, fail_count
    error = Signal(str)

    def __init__(self, client: SynologyClient, files_to_upload: list, base_local_path: str, base_remote_path: str, overwrite: str = "NO"):
        super().__init__()
        self.client = client
        self.files_to_upload = files_to_upload # List of ComparisonResult (status == FALTANTE or DIFERENTE)
        self.base_local_path = base_local_path
        self.base_remote_path = base_remote_path
        self.overwrite = overwrite
        self.is_cancelled = False

    def run(self):
        try:
            total_files = len(self.files_to_upload)
            success = 0
            failed = 0

            for i, res in enumerate(self.files_to_upload):
                if self.is_cancelled:
                    break

                self.progress.emit(f"Subiendo {i+1}/{total_files}: {res.name}", int((i/total_files)*100))
                
                local_full_path = os.path.join(self.base_local_path, res.path).replace("\\", "/")
                remote_full_path = self.base_remote_path
                relative_dir = os.path.dirname(res.path).replace("\\", "/")
                if relative_dir:
                    remote_full_path = f"{self.base_remote_path}/{relative_dir}"
                
                if not os.path.exists(local_full_path):
                    logging.warning(f"Archivo local no existe: {local_full_path}")
                    failed += 1
                    continue
                    
                overwrite_flag = True if self.overwrite == "SI" else False
                
                try:
                    res_upload = self.client.upload_file(local_full_path, remote_full_path, overwrite_flag)
                    if isinstance(res_upload, tuple):
                        status_code, err_data = res_upload
                        logging.error(f"Error subiendo {res.name} (HTTP {status_code}): {err_data}")
                        failed += 1
                    elif isinstance(res_upload, dict) and not res_upload.get('success', False):
                        logging.error(f"Error subiendo {res.name}: {res_upload}")
                        failed += 1
                    else:
                        logging.info(f"Subido con éxito: {res.name} -> {remote_full_path}")
                        success += 1
                except Exception as e:
                    logging.error(f"Error subiendo {res.name}: {e}", exc_info=True)
                    failed += 1

            self.progress.emit("Subida finalizada.", 100)
            self.finished.emit(success, failed)
            
        except Exception as e:
            logging.error(f"Error general en UploaderWorker: {e}", exc_info=True)
            self.error.emit(str(e))
