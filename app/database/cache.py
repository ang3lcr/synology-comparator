import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict

class FileCache:
    def __init__(self, db_path: str = "cache.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS file_cache (
                    local_path TEXT,
                    remote_path TEXT,
                    rel_path TEXT PRIMARY KEY,
                    size INTEGER,
                    mod_time TEXT,
                    file_hash TEXT,
                    status TEXT,
                    last_checked TEXT
                )
            ''')
            conn.commit()

    def save_cache(self, rel_path: str, local_path: str, remote_path: str, size: int, mod_time: Optional[datetime], status: str, file_hash: Optional[str] = None):
        mod_time_str = mod_time.isoformat() if mod_time else None
        last_checked = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO file_cache 
                (local_path, remote_path, rel_path, size, mod_time, file_hash, status, last_checked)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (local_path, remote_path, rel_path, size, mod_time_str, file_hash, status, last_checked))
            conn.commit()

    def save_cache_bulk(self, results, progress_callback=None):
        last_checked = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            total = len(results)
            chunk_size = 1000
            for i in range(0, total, chunk_size):
                chunk = results[i:i+chunk_size]
                data = []
                for res in chunk:
                    mod_time_str = res.mod_time_local.isoformat() if res.mod_time_local else None
                    size = res.size_local or res.size_nas or 0
                    data.append(("", "", res.path, size, mod_time_str, None, res.status, last_checked))
                
                conn.executemany('''
                    INSERT OR REPLACE INTO file_cache 
                    (local_path, remote_path, rel_path, size, mod_time, file_hash, status, last_checked)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', data)
                
                if progress_callback:
                    progress_callback(min(i + chunk_size, total), total)
            conn.commit()

    def get_cache(self, rel_path: str) -> Optional[dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM file_cache WHERE rel_path = ?', (rel_path,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'local_path': row[0],
                    'remote_path': row[1],
                    'rel_path': row[2],
                    'size': row[3],
                    'mod_time': datetime.fromisoformat(row[4]) if row[4] else None,
                    'file_hash': row[5],
                    'status': row[6],
                    'last_checked': datetime.fromisoformat(row[7]) if row[7] else None
                }
            return None

    def clear_cache(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM file_cache')
            conn.commit()
