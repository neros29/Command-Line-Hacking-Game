import unittest
import sys
import os
import io
import re
from unittest.mock import patch
from src.utils.utils import *

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import HackingEnvironment
from test_utils import FileSystemTestFixture

def strip_ansi_codes(text):
    """Remove ANSI color codes from text for easier testing"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

class TestIntegration(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test."""
        self.fs_fixture = FileSystemTestFixture("local")
        self.fs_fixture.setup()
        self.env = HackingEnvironment()
    
    def tearDown(self):
        """Clean up after each test."""
        self.fs_fixture.teardown()
    
    def test_directory_navigation_workflow(self):
        """Test directory creation and navigation workflow"""
        # Initial pwd should be /home
        self.assertEqual(self.env.pwd, "/home")
        
        # Create a new directory
        self.env.execute_command("mkdir test_dir")
        
        # Navigate to that directory
        self.env.execute_command("cd test_dir")
        self.assertEqual(self.env.pwd, "/home/test_dir")
        
        # Go back up
        self.env.execute_command("cd ..")
        self.assertEqual(self.env.pwd, "/home")
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_file_operations_workflow(self, mock_stdout):
        """Test file operations workflow"""
        # Check the contents of home
        self.env.execute_command("ls")
        output1 = mock_stdout.getvalue()
        
        # Create a directory
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        self.env.execute_command("mkdir my_files")
        
        # List again to see the directory
        self.env.execute_command("ls")
        output2 = mock_stdout.getvalue()
        
        # The second output should be longer (contain more entries)
        self.assertGreater(len(output2), len(output1))
        self.assertIn("my_files", output2)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_pipe_integration(self, mock_stdout):
        """Test that piping works correctly between commands"""
        # Create a test file with specific content
        self.env.execute_command("touch /home/pipe_test.txt")
        
        # Get the file's physical path and write content to it
        machine_data = load_machine("local")
        file_path = machine_data["file_system"]["home"]["pipe_test.txt"]
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..'))
        with open(os.path.join(project_root, file_path), 'w') as f:
            f.write("Line with apple\nLine with banana\nLine with apple and orange\n")
        
        # Test piping: cat the file and grep for 'apple'
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        self.env.execute_command("cat /home/pipe_test.txt | grep apple")
        output = strip_ansi_codes(mock_stdout.getvalue())
        
        # Check pipe output - should only show lines with 'apple'
        self.assertIn("Line with apple", output)
        self.assertIn("Line with apple and orange", output)
        self.assertNotIn("Line with banana", output)
        
        # Test that environment is properly cleaned up after piping
        self.assertNotIn("PIPED_INPUT", os.environ)
        self.assertNotIn("IS_PIPED", os.environ)
        self.assertNotIn("IS_PIPE_SOURCE", os.environ)

if __name__ == '__main__':
    unittest.main()