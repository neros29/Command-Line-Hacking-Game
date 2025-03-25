import unittest
import sys
import os
import io
from unittest.mock import patch

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.utils import load_machine
import src.commands.ls as ls
import src.commands.cd as cd
import src.commands.mkdir as mkdir
from test_utils import FileSystemTestFixture

class TestCommands(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test."""
        self.machine_name = "local"
        self.pwd = "/home"
        self.fs_fixture = FileSystemTestFixture(self.machine_name)
        self.fs_fixture.setup()
    
    def tearDown(self):
        """Clean up after each test."""
        self.fs_fixture.teardown()
    
    def test_ls_command(self):
        """Test that ls command returns the same pwd"""
        result = ls.execute([], self.pwd, self.machine_name)
        self.assertEqual(result, self.pwd)
    
    def test_cd_command(self):
        """Test cd command changes directory"""
        # Test changing to root directory
        result = cd.execute(["/"], self.pwd, self.machine_name)
        self.assertEqual(result, "/")
        
        # Test changing back to home
        result = cd.execute(["/home"], "/", self.machine_name)
        self.assertEqual(result, "/home")
    
    def test_mkdir_command(self):
        """Test mkdir creates a directory"""
        test_dir = "test_directory"
        # Create a directory
        result = mkdir.execute([test_dir], self.pwd, self.machine_name)
        self.assertEqual(result, self.pwd)
        
        # Check if directory exists with ls
        machine = load_machine(self.machine_name)
        path_parts = [p for p in self.pwd.split('/') if p]
        
        # Navigate to current directory in filesystem
        current = machine["file_system"]
        for part in path_parts:
            current = current[part]
        
        # Check if test_directory exists
        self.assertIn(test_dir, current)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_echo_command(self, mock_stdout):
        """Test that echo command outputs text correctly"""
        from src.commands import echo
        
        # Test echo with simple text
        echo.execute(["Hello world"], self.pwd, self.machine_name)
        output = mock_stdout.getvalue()
        self.assertIn("Hello world", output)
        
        # Clear output buffer
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        
        # Test echo with quoted text
        echo.execute(["\"Hello, with quotes\""], self.pwd, self.machine_name)
        output = mock_stdout.getvalue()
        self.assertIn("Hello, with quotes", output)
    
    def test_mv_command(self):
        """Test that mv command moves files correctly"""
        # Create a test file
        test_file = "test_file.txt"
        test_dir = "test_dir"
        
        # First create a file and directory to test with
        mkdir.execute([test_dir], self.pwd, self.machine_name)
        
        from src.commands import touch
        touch.execute([test_file], self.pwd, self.machine_name)
        
        # Load machine to check file exists
        machine = load_machine(self.machine_name)
        current = machine["file_system"]
        for part in self.pwd.split('/'):
            if part:
                current = current[part]
        
        # Verify the file exists at the source
        self.assertIn(test_file, current)
        
        # Now move the file
        from src.commands import mv
        mv.execute([test_file, test_dir], self.pwd, self.machine_name)
        
        # Reload machine data after move
        machine = load_machine(self.machine_name)
        
        # Check source location - file should be gone
        current = machine["file_system"]
        for part in self.pwd.split('/'):
            if part:
                current = current[part]
        self.assertNotIn(test_file, current)
        
        # Check destination location - file should be there
        dest_path = current[test_dir]
        self.assertIn(test_file, dest_path)
        
    def test_mv_rename(self):
        """Test that mv command can rename files"""
        # Create a test file
        test_file = "original.txt"
        new_name = "renamed.txt"
        
        # Create the test file
        from src.commands import touch
        touch.execute([test_file], self.pwd, self.machine_name)
        
        # Rename the file
        from src.commands import mv
        mv.execute([test_file, new_name], self.pwd, self.machine_name)
        
        # Check if rename worked properly
        machine = load_machine(self.machine_name)
        current = machine["file_system"]
        for part in self.pwd.split('/'):
            if part:
                current = current[part]
        
        # Original name should be gone
        self.assertNotIn(test_file, current)
        # New name should exist
        self.assertIn(new_name, current)

if __name__ == '__main__':
    unittest.main()