from typing import List, Callable
from app.database.models import FileMetadata
from app.synology.client import SynologyClient
from datetime import datetime

class RemoteScanner:
    def __init__(self, client: SynologyClient, base_path: str):
        self.client = client
        self.base_path = base_path

    def scan(self, progress_callback: Callable[[int, int], None] = None) -> List[FileMetadata]:
        """
        Scan a remote directory recursively.
        synology-api might return a flat structure or nested depending on the call,
        but get_file_list doesn't natively do recursive. We have to walk it or use 'list_share' equivalent.
        Actually, we can use search API, or walk it manually.
        For Phase 1 MVP, we will list one directory. A recursive approach is needed for full comparison.
        """
        return self._walk_recursive(self.base_path, progress_callback)
        
    def _walk_recursive(self, current_path: str, progress_callback, _scanned_count=0) -> List[FileMetadata]:
        all_files = []
        offset = 0
        limit = 1000
        
        while True:
            response = self.client.list_folder(current_path, offset=offset, limit=limit)
            if not response or 'data' not in response or 'files' not in response['data']:
                break
                
            files = response['data']['files']
            total = response['data'].get('total', 0)
            
            for item in files:
                name = item['name']
                is_dir = item['isdir']
                
                if is_dir:
                    # Recursive call
                    sub_files = self._walk_recursive(item['path'], progress_callback, _scanned_count + len(all_files))
                    all_files.extend(sub_files)
                else:
                    # File
                    additional = item.get('additional', {})
                    size_raw = additional.get('size', 0)
                    try:
                        size = int(size_raw)
                    except (ValueError, TypeError):
                        size = 0
                        
                    mod_time_unix = additional.get('time', {}).get('mtime', 0)
                    mod_time = datetime.fromtimestamp(mod_time_unix) if mod_time_unix else None
                    
                    # Compute relative path to base_path
                    rel_path = item['path'].replace(self.base_path, "", 1).lstrip('/')
                    
                    all_files.append(FileMetadata(
                        path=rel_path,
                        name=name,
                        size=size,
                        modified_time=mod_time,
                        is_dir=False
                    ))
                    
                    if progress_callback:
                        progress_callback(len(all_files), 0) # Total is hard to know in recursive
            
            offset += limit
            if offset >= total:
                break
                
        return all_files
