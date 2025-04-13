#!/usr/bin/env python3
"""
SharePoint client for uploading files and creating folders
"""
import os
import logging
from office365.runtime.auth.user_credential import UserCredential
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SharePointClient:
    """
    Client for interacting with SharePoint
    """
    def __init__(self, site_url, username, password):
        """
        Initialize the SharePoint client
        
        Args:
            site_url (str): SharePoint site URL
            username (str): SharePoint username
            password (str): SharePoint password
        """
        self.site_url = site_url
        self.username = username
        self.password = password
        self.ctx = None
        self.connect()
        
    def connect(self):
        """
        Connect to SharePoint
        """
        try:
            user_credentials = UserCredential(self.username, self.password)
            self.ctx = ClientContext(self.site_url).with_credentials(user_credentials)
            logger.info(f"Connected to SharePoint site: {self.site_url}")
        except Exception as e:
            logger.error(f"Failed to connect to SharePoint: {e}")
            raise
            
    def create_folder(self, folder_path):
        """
        Create a folder in SharePoint
        
        Args:
            folder_path (str): Relative path of the folder to create
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Split the path into parts to create each level
            parts = folder_path.strip('/').split('/')
            current_path = ""
            
            for part in parts:
                if not part:
                    continue
                    
                current_path = f"{current_path}/{part}" if current_path else part
                
                # Check if folder exists
                folder_url = current_path
                try:
                    folder = self.ctx.web.get_folder_by_server_relative_url(folder_url)
                    self.ctx.load(folder)
                    self.ctx.execute_query()
                    logger.debug(f"Folder already exists: {folder_url}")
                except Exception:
                    # Folder doesn't exist, create it
                    folder = self.ctx.web.folders.add(folder_url)
                    self.ctx.execute_query()
                    logger.info(f"Created folder: {folder_url}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to create folder {folder_path}: {e}")
            return False
            
    def upload_file(self, local_file_path, sharepoint_folder_path):
        """
        Upload a file to SharePoint
        
        Args:
            local_file_path (str): Path to the local file
            sharepoint_folder_path (str): Relative path of the SharePoint folder
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure the folder exists
            self.create_folder(sharepoint_folder_path)
            
            # Get the filename from the local path
            file_name = os.path.basename(local_file_path)
            
            # Construct the target file path in SharePoint
            target_folder_url = sharepoint_folder_path
            if not target_folder_url.startswith('/'):
                target_folder_url = f"/{target_folder_url}"
                
            # Read the file content
            with open(local_file_path, 'rb') as file_content:
                content = file_content.read()
                
            # Upload the file
            target_file_url = f"{target_folder_url}/{file_name}"
            File.save_binary(self.ctx, target_file_url, content)
            logger.info(f"Uploaded file {file_name} to {target_folder_url}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to upload file {local_file_path}: {e}")
            return False
            
    def upload_folder_contents(self, local_folder_path, sharepoint_folder_path):
        """
        Upload all files in a local folder to SharePoint
        
        Args:
            local_folder_path (str): Path to the local folder
            sharepoint_folder_path (str): Relative path of the SharePoint folder
            
        Returns:
            dict: Dictionary with counts of successful and failed uploads
        """
        results = {
            'success': 0,
            'failed': 0,
            'files': []
        }
        
        # Ensure the folder exists
        self.create_folder(sharepoint_folder_path)
        
        # Walk through the local folder
        for root, dirs, files in os.walk(local_folder_path):
            for file in files:
                local_file_path = os.path.join(root, file)
                
                # Calculate the relative path from the base folder
                rel_path = os.path.relpath(root, local_folder_path)
                if rel_path == '.':
                    target_folder = sharepoint_folder_path
                else:
                    target_folder = f"{sharepoint_folder_path}/{rel_path}"
                
                # Upload the file
                success = self.upload_file(local_file_path, target_folder)
                
                if success:
                    results['success'] += 1
                    results['files'].append({
                        'path': local_file_path,
                        'status': 'success'
                    })
                else:
                    results['failed'] += 1
                    results['files'].append({
                        'path': local_file_path,
                        'status': 'failed'
                    })
        
        logger.info(f"Uploaded {results['success']} files to {sharepoint_folder_path}, {results['failed']} failed")
        return results

# Example usage
if __name__ == "__main__":
    # Replace with your actual SharePoint details
    client = SharePointClient(
        "https://yourcompany.sharepoint.com/sites/yoursite",
        "your.email@yourcompany.com",
        "your-password"
    )
    
    # Create a folder
    client.create_folder("FreshdeskTickets/Test")
    
    # Upload a file
    client.upload_file("test.txt", "FreshdeskTickets/Test")
    
    # Upload a folder
    client.upload_folder_contents("./test_folder", "FreshdeskTickets/Test")
