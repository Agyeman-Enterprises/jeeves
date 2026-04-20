"""
Dropbox service for cloud storage.
"""

import logging
import os
from typing import Dict, List, Optional

LOGGER = logging.getLogger(__name__)

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")

# Try to import Dropbox SDK
try:
    import dropbox
    DROPBOX_AVAILABLE = True
except ImportError:
    DROPBOX_AVAILABLE = False
    LOGGER.warning("dropbox not installed. Install with: pip install dropbox")


class DropboxService:
    """Service for interacting with Dropbox."""
    
    def __init__(self):
        self.client = None
        self.is_configured = False
        
        if not DROPBOX_AVAILABLE:
            LOGGER.warning("Dropbox library not available")
            return
        
        if not DROPBOX_ACCESS_TOKEN:
            LOGGER.warning("Dropbox access token not configured. Set DROPBOX_ACCESS_TOKEN")
            return
        
        try:
            self.client = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
            self.is_configured = True
            LOGGER.info("Dropbox service configured")
        except Exception as e:
            LOGGER.error(f"Failed to initialize Dropbox client: {e}")
    
    def upload_file(self, local_path: str, remote_path: str, overwrite: bool = False) -> Dict[str, any]:
        """
        Upload a file to Dropbox.
        
        Args:
            local_path: Local file path
            remote_path: Dropbox path (e.g., "/Documents/file.txt")
            overwrite: Whether to overwrite existing file
        
        Returns:
            Dict with success status and file metadata
        """
        if not self.is_configured:
            return {
                "success": False,
                "error": "Dropbox not configured"
            }
        
        try:
            mode = dropbox.files.WriteMode.overwrite if overwrite else dropbox.files.WriteMode.add
            
            with open(local_path, 'rb') as f:
                file_metadata = self.client.files_upload(
                    f.read(),
                    remote_path,
                    mode=mode
                )
            
            LOGGER.info(f"File uploaded to Dropbox: {remote_path}")
            return {
                "success": True,
                "path": file_metadata.path_display,
                "id": file_metadata.id
            }
        except Exception as e:
            LOGGER.error(f"Failed to upload file to Dropbox: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def download_file(self, remote_path: str, local_path: str) -> Dict[str, any]:
        """
        Download a file from Dropbox.
        
        Args:
            remote_path: Dropbox path
            local_path: Local destination path
        
        Returns:
            Dict with success status
        """
        if not self.is_configured:
            return {
                "success": False,
                "error": "Dropbox not configured"
            }
        
        try:
            metadata, response = self.client.files_download(remote_path)
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            LOGGER.info(f"File downloaded from Dropbox: {remote_path}")
            return {
                "success": True,
                "path": local_path
            }
        except Exception as e:
            LOGGER.error(f"Failed to download file from Dropbox: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_files(self, path: str = "") -> Dict[str, any]:
        """
        List files in a Dropbox folder.
        
        Args:
            path: Dropbox folder path (empty for root)
        
        Returns:
            Dict with list of files
        """
        if not self.is_configured:
            return {
                "success": False,
                "error": "Dropbox not configured"
            }
        
        try:
            result = self.client.files_list_folder(path)
            files = []
            
            for entry in result.entries:
                files.append({
                    "name": entry.name,
                    "path": entry.path_display,
                    "is_folder": isinstance(entry, dropbox.files.FolderMetadata)
                })
            
            return {
                "success": True,
                "files": files
            }
        except Exception as e:
            LOGGER.error(f"Failed to list Dropbox files: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
dropbox_service = DropboxService()

