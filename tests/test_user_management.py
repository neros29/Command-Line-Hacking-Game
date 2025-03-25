import unittest
import sys
import os
import io
import getpass
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.utils import load_machine, save_machine
from src.main import HackingEnvironment
from test_utils import FileSystemTestFixture

class TestUserManagement(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test."""
        self.machine_name = "local"
        self.fs_fixture = FileSystemTestFixture(self.machine_name)
        self.fs_fixture.setup()
        
        # Create a test environment
        self.env = HackingEnvironment(machine_name=self.machine_name)
        self.env.current_user = "root"  # Set as root for permissions
        self.env.is_root = True
        
        # Register environment in modules dictionary
        from src.main import modules
        modules["__env__"] = self.env
        
        # Add the missing pwd attribute initialization
        self.pwd = "/root"
        
        # Import user management commands
        import src.commands.user as user_cmd
        import src.commands.useradd as useradd_cmd
        import src.commands.userdel as userdel_cmd
        import src.commands.passwd as passwd_cmd
        
        self.commands = {
            'user': user_cmd,
            'useradd': useradd_cmd,
            'userdel': userdel_cmd,
            'passwd': passwd_cmd
        }
    
    def tearDown(self):
        """Clean up after each test."""
        self.fs_fixture.teardown()
        
        # Clean up modules reference
        from src.main import modules
        if "__env__" in modules:
            del modules["__env__"]
    
    @patch('getpass.getpass')
    def test_useradd_basic(self, mock_getpass):
        """Test adding a basic user"""
        # Mock password inputs
        mock_getpass.side_effect = ["testpassword", "testpassword"]
        
        # Add a user
        self.commands['useradd'].execute(["testuser"], self.pwd, self.machine_name)
        
        # Verify user was added
        machine = load_machine(self.machine_name)
        users = machine["meta_data"].get("users", {})
        
        self.assertIn("testuser", users)
        self.assertEqual(users["testuser"]["home"], "/home/testuser")
        self.assertFalse(users["testuser"]["is_root"])
    
    @patch('getpass.getpass')
    def test_useradd_root(self, mock_getpass):
        """Test adding a user with root privileges"""
        # Mock password inputs
        mock_getpass.side_effect = ["rootpass", "rootpass"]
        
        # Add a root user
        self.commands['useradd'].execute(["adminuser", "--root"], self.pwd, self.machine_name)
        
        # Verify user was added with root privileges
        machine = load_machine(self.machine_name)
        users = machine["meta_data"].get("users", {})
        
        self.assertIn("adminuser", users)
        self.assertTrue(users["adminuser"]["is_root"])
        self.assertIn("all", users["adminuser"]["permissions"])
    
    @patch('getpass.getpass')
    def test_useradd_mismatch_passwords(self, mock_getpass):
        """Test adding a user with mismatched passwords"""
        # Mock password inputs that don't match
        mock_getpass.side_effect = ["password1", "password2"]
        
        # Add a user with mismatched passwords
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.commands['useradd'].execute(["failuser"], self.pwd, self.machine_name)
            output = mock_stdout.getvalue()
            
            # Should fail
            self.assertIn("not match", output.lower())
        
        # Verify user was not added
        machine = load_machine(self.machine_name)
        users = machine["meta_data"].get("users", {})
        self.assertNotIn("failuser", users)
    
    @patch('getpass.getpass')
    def test_userdel_basic(self, mock_getpass):
        """Test deleting a user"""
        # First add a user
        mock_getpass.side_effect = ["testpass", "testpass"]
        self.commands['useradd'].execute(["user_to_delete"], self.pwd, self.machine_name)
        
        # Verify user was added
        machine = load_machine(self.machine_name)
        self.assertIn("user_to_delete", machine["meta_data"].get("users", {}))
        
        # Now delete the user
        self.commands['userdel'].execute(["user_to_delete"], self.pwd, self.machine_name)
        
        # Verify user was deleted
        machine = load_machine(self.machine_name)
        self.assertNotIn("user_to_delete", machine["meta_data"].get("users", {}))
    
    def test_userdel_nonexistent(self):
        """Test deleting a nonexistent user"""
        # Get a reference to the main modules dictionary
        from src.main import modules
        
        # Save the original modules state
        original_env = modules.get("__env__", None)
        
        try:
            # Set the environment in the modules dictionary
            modules["__env__"] = self.env
            
            # Ensure root permissions
            self.env.is_root = True
            
            with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
                self.commands['userdel'].execute(["nonexistentuser"], self.pwd, self.machine_name)
                output = mock_stdout.getvalue()
                self.assertIn("not exist", output.lower())
        finally:
            # Restore the original environment in modules
            if original_env:
                modules["__env__"] = original_env
            else:
                # If there was no environment before, remove it
                if "__env__" in modules:
                    del modules["__env__"]
    
    @patch('getpass.getpass')
    def test_passwd_change_password(self, mock_getpass):
        """Test changing a user's password"""
        # First add a user
        mock_getpass.side_effect = ["oldpass", "oldpass", "oldpass", "newpass", "newpass"]
        self.commands['useradd'].execute(["passuser"], self.pwd, self.machine_name)
        
        # Change the password
        self.commands['passwd'].execute(["passuser"], self.pwd, self.machine_name)
        
        # Verify password was changed
        machine = load_machine(self.machine_name)
        users = machine["meta_data"].get("users", {})
        
        # Can't check the actual hash, but can verify it's not the same as old password
        original_machine = load_machine(self.machine_name)
        self.assertNotEqual(users["passuser"]["password"], "oldpass")
    
    @patch('getpass.getpass')
    def test_user_modify_permissions(self, mock_getpass):
        """Test modifying user permissions"""
        # First add a user
        mock_getpass.side_effect = ["userpass", "userpass"]
        self.commands['useradd'].execute(["permuser"], self.pwd, self.machine_name)
        
        # Modify permissions
        self.commands['user'].execute(["mod", "permuser", "--add-perm", "bin"], self.pwd, self.machine_name)
        
        # Verify permission was added
        machine = load_machine(self.machine_name)
        users = machine["meta_data"].get("users", {})
        
        self.assertIn("bin", users["permuser"]["permissions"])
        
        # Remove the permission
        self.commands['user'].execute(["mod", "permuser", "--del-perm", "bin"], self.pwd, self.machine_name)
        
        # Verify permission was removed
        machine = load_machine(self.machine_name)
        users = machine["meta_data"].get("users", {})
        
        self.assertNotIn("bin", users["permuser"]["permissions"])
    
    @patch('getpass.getpass')
    def test_user_toggle_root(self, mock_getpass):
        """Test toggling root privileges"""
        # First add a user
        mock_getpass.side_effect = ["userpass", "userpass"]
        self.commands['useradd'].execute(["rootuser"], self.pwd, self.machine_name)
        
        # Verify user is not root
        machine = load_machine(self.machine_name)
        self.assertFalse(machine["meta_data"]["users"]["rootuser"]["is_root"])
        
        # Toggle root privileges
        self.commands['user'].execute(["mod", "rootuser", "--root"], self.pwd, self.machine_name)
        
        # Verify user is now root
        machine = load_machine(self.machine_name)
        self.assertTrue(machine["meta_data"]["users"]["rootuser"]["is_root"])
        
        # Toggle back
        self.commands['user'].execute(["mod", "rootuser", "--root"], self.pwd, self.machine_name)
        
        # Verify user is no longer root
        machine = load_machine(self.machine_name)
        self.assertFalse(machine["meta_data"]["users"]["rootuser"]["is_root"])
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_user_list(self, mock_stdout):
        """Test listing users"""
        # Add some users first
        with patch('getpass.getpass') as mock_getpass:
            mock_getpass.side_effect = ["pass1", "pass1", "pass2", "pass2"]
            self.commands['useradd'].execute(["user1"], self.pwd, self.machine_name)
            self.commands['useradd'].execute(["user2"], self.pwd, self.machine_name)
        
        # List users
        self.commands['user'].execute(["list"], self.pwd, self.machine_name)
        output = mock_stdout.getvalue()
        
        # Verify all users are listed
        self.assertIn("root", output)
        self.assertIn("user1", output)
        self.assertIn("user2", output)

