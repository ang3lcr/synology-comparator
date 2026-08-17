import hashlib
import os

class Hashing:
    @staticmethod
    def compute_local_md5(file_path: str, chunk_size: int = 8192) -> str:
        md5_hash = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            print(f"Error calculating MD5 for {file_path}: {e}")
            return ""
