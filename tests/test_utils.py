import os
import json
import shutil
import tempfile

class FileSystemTestFixture:
    """Test fixture that preserves and restores file system state between tests."""

    def __init__(self, machine_name="local"):
        self.machine_name = machine_name
        self.backup_dir = tempfile.mkdtemp(prefix="fs_test_backup_")
        
        # Use absolute paths to ensure proper file handling
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.machine_dir = os.path.join(project_root, "src", "machines", machine_name)
        self.machine_file = os.path.join(self.machine_dir, f"{machine_name}.json")
        self.files_dir = os.path.join(self.machine_dir, "files")
        
    def setup(self):
        """Create backups of the machine JSON and files directory."""
        # Backup machine JSON file
        if os.path.exists(self.machine_file):
            shutil.copy2(self.machine_file, os.path.join(self.backup_dir, f"{self.machine_name}.json"))
            
        # Backup files directory
        if os.path.exists(self.files_dir):
            backup_files_dir = os.path.join(self.backup_dir, "files")
            # Ensure clean backup if it exists already
            if os.path.exists(backup_files_dir):
                shutil.rmtree(backup_files_dir)
            shutil.copytree(self.files_dir, backup_files_dir)
        elif not os.path.exists(os.path.join(self.backup_dir, "files")):
            # Create an empty files directory in backup if it doesn't exist
            os.makedirs(os.path.join(self.backup_dir, "files"), exist_ok=True)
            
    def teardown(self):
        """Restore from backups and clean up."""
        try:
            # Restore machine JSON file
            backup_json = os.path.join(self.backup_dir, f"{self.machine_name}.json")
            if os.path.exists(backup_json):
                shutil.copy2(backup_json, self.machine_file)
                
            # Restore files directory
            backup_files = os.path.join(self.backup_dir, "files")
            if os.path.exists(self.files_dir):
                shutil.rmtree(self.files_dir)
            if os.path.exists(backup_files):
                shutil.copytree(backup_files, self.files_dir)
                
            # Clean up backup directory
            shutil.rmtree(self.backup_dir)
        except Exception as e:
            print(f"Warning: Error during test cleanup: {e}")
            # Attempt to clean up the backup directory even if restoration failed
            if os.path.exists(self.backup_dir):
                try:
                    shutil.rmtree(self.backup_dir)
                except:
                    pass