from typing import List, Dict
from app.database.models import FileMetadata, ComparisonResult

from app.scanner.hashing import Hashing
from app.synology.client import SynologyClient
import os

class FileComparator:
    @staticmethod
    def compare(local_files: List[FileMetadata], remote_files: List[FileMetadata], 
                deep_verify: bool = False, client: SynologyClient = None, 
                base_local_path: str = "", base_remote_path: str = "", progress_callback = None) -> List[ComparisonResult]:
        results = []
        
        # Build dictionaries for fast lookup by path
        # Assuming path includes relative directory and filename
        local_dict = {f.path: f for f in local_files if not f.is_dir}
        remote_dict = {f.path: f for f in remote_files if not f.is_dir}
        
        all_paths = set(local_dict.keys()).union(set(remote_dict.keys()))
        
        for path in all_paths:
            local = local_dict.get(path)
            remote = remote_dict.get(path)
            
            if local and remote:
                status = "OK"
                
                if local.size != remote.size:
                    status = "DIFERENTE"
                else:
                    if deep_verify and client:
                        if progress_callback:
                            progress_callback(f"Verificando MD5 para {local.name}...")
                        local_md5 = Hashing.compute_local_md5(os.path.join(base_local_path, local.path))
                        # Determine remote path
                        rel_dir = os.path.dirname(local.path).replace("\\", "/")
                        rem_p = f"{base_remote_path}/{rel_dir}/{local.name}" if rel_dir else f"{base_remote_path}/{local.name}"
                        remote_md5 = client.get_file_md5(rem_p)
                        
                        if local_md5 and remote_md5 and local_md5 != remote_md5:
                            status = "DIFERENTE"
                
                results.append(ComparisonResult(
                    path=path,
                    name=local.name,
                    status=status,
                    size_local=local.size,
                    size_nas=remote.size,
                    mod_time_local=local.modified_time,
                    mod_time_nas=remote.modified_time
                ))
            elif local and not remote:
                results.append(ComparisonResult(
                    path=path,
                    name=local.name,
                    status="FALTANTE",
                    size_local=local.size,
                    size_nas=None,
                    mod_time_local=local.modified_time,
                    mod_time_nas=None
                ))
            elif remote and not local:
                results.append(ComparisonResult(
                    path=path,
                    name=remote.name,
                    status="SOLO_NAS",
                    size_local=None,
                    size_nas=remote.size,
                    mod_time_local=None,
                    mod_time_nas=remote.modified_time
                ))
                
        # Sort results by path
        results.sort(key=lambda x: x.path)
        return results
