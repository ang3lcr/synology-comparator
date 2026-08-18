import os
import logging
from typing import List, Optional
from synology_api import filestation
import urllib.parse
import time

class SynologyClient:
    def __init__(self):
        self.fs = None
        
    def connect(self, address: str, username: str, password: str, port: str = "5000", secure: bool = False) -> bool:
        """
        Connect to Synology NAS using synology-api.
        Address can be QuickConnect ID or direct IP/URL.
        """
        # Parse URL if the user included http:// or https://
        if address.startswith("http://"):
            address = address.replace("http://", "").rstrip("/")
            secure = False
            port = "80" if port == "5000" else port
        elif address.startswith("https://"):
            address = address.replace("https://", "").rstrip("/")
            secure = True
            port = "443" if port == "5000" else port
            
        # If the address still contains a port (e.g., 192.168.1.100:5001)
        if ":" in address:
            parts = address.split(":")
            address = parts[0]
            port = parts[1]
            
        # Determine if it's a QuickConnect ID or an IP/Domain
        quickconnect_id = None
        ip_address = address
        
        if "quickconnect.to" in address:
            quickconnect_id = address.split(".")[0]
            ip_address = None
        elif "." not in address:
            # If no dots, it's likely a QuickConnect ID (e.g. MiNAS)
            quickconnect_id = address
            ip_address = None

        try:
            # We assume DSM 7 by default
            self.fs = filestation.FileStation(
                ip_address=ip_address,
                port=port, 
                username=username, 
                password=password, 
                secure=secure, 
                cert_verify=False, 
                dsm_version=7,
                debug=False,
                quickconnect_id=quickconnect_id
            )
            return True
        except Exception as e:
            logging.error(f"Error conectando a Synology: {e}")
            raise

    def list_folder(self, path: str, offset: int = 0, limit: int = 1000) -> dict:
        """
        List contents of a remote folder using FileStation API.
        Returns the raw dictionary from synology-api.
        """
        if not self.fs:
            raise Exception("No conectado al NAS")
            
        # The filestation.get_file_list method allows offset and limit
        # Additional fields: time, size
        return self.fs.get_file_list(
            folder_path=path,
            offset=offset,
            limit=limit,
            sort_by="name",
            sort_direction="asc",
            additional=["time", "size"]
        )
        
    def upload_file(self, local_path: str, remote_dest_path: str, overwrite: bool = False):
        if not self.fs:
            raise Exception("No conectado al NAS")
            
        return self.fs.upload_file(
            dest_path=remote_dest_path,
            file_path=local_path,
            create_parents=True,
            overwrite=overwrite
        )
        
    def get_file_md5(self, remote_file_path: str) -> str:
        """
        Calculates remote MD5. Since synology-api might not have get_md5 directly exposed in v0.9.1,
        we use the raw API call if necessary, but actually the FileStation has start_md5_calc and get_md5_status.
        This can be asynchronous on the NAS, so we start it and poll.
        """
        if not self.fs:
            return ""
            
        try:
            # First start the calculation
            taskid_response = self.fs.start_md5_calc(file_path=remote_file_path)
            if 'data' not in taskid_response or 'taskid' not in taskid_response['data']:
                return ""
            
            taskid = taskid_response['data']['taskid']
            
            # Poll status
            while True:
                status_response = self.fs.get_md5_status(taskid=taskid)
                if 'data' not in status_response:
                    return ""
                
                status_data = status_response['data']
                if status_data.get('finished', False):
                    return status_data.get('md5', "")
                
                time.sleep(1)
        except Exception as e:
            logging.error(f"Error obteniendo MD5 remoto para {remote_file_path}: {e}")
            return ""
