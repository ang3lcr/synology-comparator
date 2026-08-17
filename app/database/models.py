from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class FileMetadata:
    path: str
    name: str
    size: int
    modified_time: Optional[datetime] = None
    is_dir: bool = False

@dataclass
class ComparisonResult:
    path: str
    name: str
    status: str # OK, FALTANTE, DIFERENTE, SOLO_NAS
    size_local: Optional[int] = None
    size_nas: Optional[int] = None
    mod_time_local: Optional[datetime] = None
    mod_time_nas: Optional[datetime] = None
