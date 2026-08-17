import os
from typing import List
from app.database.models import FileMetadata
from datetime import datetime

class LocalScanner:
    def __init__(self, base_path: str):
        self.base_path = os.path.normpath(base_path)

    def scan(self) -> List[FileMetadata]:
        files_metadata = []
        
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.base_path)
                
                # Normalize slashes for comparison
                rel_path = rel_path.replace("\\", "/")
                
                try:
                    stat = os.stat(full_path)
                    mod_time = datetime.fromtimestamp(stat.st_mtime)
                    
                    files_metadata.append(FileMetadata(
                        path=rel_path,
                        name=file,
                        size=stat.st_size,
                        modified_time=mod_time,
                        is_dir=False
                    ))
                except Exception as e:
                    print(f"Error leyendo archivo {full_path}: {e}")
                    
        return files_metadata
