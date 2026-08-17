import sys
from app.synology.client import SynologyClient
client = SynologyClient()
try:
    # Need credentials to test... wait, I can't authenticate without the user's NAS credentials.
    import inspect
    from synology_api.filestation import FileStation
    sig = inspect.signature(FileStation.get_file_list)
    print("Signature:", sig)
except Exception as e:
    print(e)
