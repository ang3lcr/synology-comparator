from PySide6.QtCore import QThread, Signal
from app.synology.client import SynologyClient
from app.scanner.local_scanner import LocalScanner
from app.scanner.remote_scanner import RemoteScanner
from app.scanner.comparator import FileComparator
from typing import List
from app.database.models import ComparisonResult
from app.database.cache import FileCache

class CompareWorker(QThread):
    progress = Signal(str, int)  # message, percentage
    finished = Signal(list)      # List[ComparisonResult]
    error = Signal(str)

    def __init__(self, client: SynologyClient, local_path: str, remote_path: str, 
                 use_cache: bool = True, deep_verify: bool = False, cache: FileCache = None):
        super().__init__()
        self.client = client
        self.local_path = local_path
        self.remote_path = remote_path
        self.use_cache = use_cache
        self.deep_verify = deep_verify
        self.cache = cache
        self.is_cancelled = False

    def run(self):
        try:
            self.progress.emit("Escaneando carpeta local...", -1)
            
            def local_progress(count):
                if self.is_cancelled:
                    raise Exception("Cancelado por el usuario")
                self.progress.emit(f"Escaneando carpeta local... ({count} archivos)", -1)
                
            local_scanner = LocalScanner(self.local_path)
            local_files = local_scanner.scan(local_progress)
            
            if self.is_cancelled: return

            self.progress.emit(f"Encontrados {len(local_files)} archivos locales. Consultando NAS...", -1)
            
            def remote_progress(count, total):
                if self.is_cancelled:
                    raise Exception("Cancelado por el usuario")
                self.progress.emit(f"Consultando NAS... ({count} archivos encontrados)", -1)
            
            remote_scanner = RemoteScanner(self.client, self.remote_path)
            remote_files = remote_scanner.scan(remote_progress)
            
            if self.is_cancelled: return

            self.progress.emit("Comparando archivos...", 80)
            
            def comp_progress(msg, progress_percent=None):
                if self.is_cancelled:
                    raise Exception("Cancelado por el usuario")
                
                if progress_percent is not None:
                    # El progreso de la comparación tomará del 80% al 100% de la barra total
                    overall_prog = 80 + int(progress_percent * 0.20)
                else:
                    overall_prog = 90
                
                self.progress.emit(msg, overall_prog)
                
            results = FileComparator.compare(
                local_files, 
                remote_files, 
                self.deep_verify, 
                self.client, 
                self.local_path, 
                self.remote_path, 
                comp_progress
            )
            
            self.progress.emit("Comparación completada. Guardando caché...", -1)
            
            if self.cache:
                def cache_progress(count, total):
                    if self.is_cancelled:
                        raise Exception("Cancelado por el usuario")
                    # Progress is very fast, so indeterminate is fine, or we can just emit count
                    self.progress.emit(f"Guardando caché... ({count}/{total})", -1)
                    
                self.cache.save_cache_bulk(results, cache_progress)
            
            self.progress.emit("Proceso finalizado.", 100)
            self.finished.emit(results)
            
        except Exception as e:
            error_str = str(e)
            if "Operation not permitted" in error_str or "407" in error_str or "408" in error_str or "No such file or directory" in error_str:
                msg = (f"Carpeta inexistente o permiso denegado en el NAS (Ruta: {self.remote_path}). "
                       "Asegúrate de incluir el nombre de la carpeta compartida al inicio "
                       "(ej. /CarpetaCompartida/Documentos) y que esté escrita exactamente igual (respetando mayúsculas y minúsculas).")
                self.error.emit(msg)
            elif "401" in error_str or "400" in error_str:
                self.error.emit("Las credenciales no son válidas o la sesión ha expirado.")
            else:
                self.error.emit(error_str)
