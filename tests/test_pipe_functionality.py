import unittest
import sys
import os
import io
import re
from unittest.mock import patch

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import HackingEnvironment
from test_utils import FileSystemTestFixture
from src.utils.utils import load_machine

def strip_ansi_codes(text):
    """Remove ANSI color codes from text for easier testing"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

class TestPipeFunctionality(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test."""
        self.fs_fixture = FileSystemTestFixture("local")
        self.fs_fixture.setup()
        self.env = HackingEnvironment()
        
        # Create a test file for testing cat | grep
        self.test_file_path = "/home/test_file.txt"
        self.env.execute_command(f"touch {self.test_file_path}")
        
        # Now reload the machine to get updated filesystem
        machine_data = load_machine("local")
        
        # Find the physical path to the file we just created
        file_path = machine_data["file_system"]["home"]["test_file.txt"]
        
        # Write content to the test file
        file_content = "Line 1: test\nLine 2: example\nLine 3: test pattern\nLine 4: another example"
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..'))
        
        with open(os.path.join(project_root, file_path), 'w') as f:
            f.write(file_content)
    
    def tearDown(self):
        """Clean up after each test."""
        self.fs_fixture.teardown()
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cat_grep_pipe(self, mock_stdout):
        """Test piping cat output to grep"""
        self.env.execute_command("cat /home/test_file.txt | grep test")
        output = strip_ansi_codes(mock_stdout.getvalue())
        
        # Check that grep filtered the output correctly
        self.assertIn("Line 1: test", output)
        self.assertIn("Line 3: test pattern", output)
        self.assertNotIn("Line 2: example", output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_ls_grep_pipe(self, mock_stdout):
        """Test piping ls output to grep"""
        # Create a few files with specific patterns
        self.env.execute_command("touch /home/file1.txt")
        self.env.execute_command("touch /home/file2.log")
        self.env.execute_command("touch /home/document.txt")
        
        # Clear the output buffer before the actual test command
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        
        # Pipe ls to grep to filter only .txt files
        # Note: Using \.txt to properly escape the period
        self.env.execute_command("ls /home | grep \\.txt")
        output = strip_ansi_codes(mock_stdout.getvalue())
        
        # Verify grep filtered correctly
        self.assertIn("file1.txt", output)
        self.assertIn("document.txt", output)
        self.assertIn("test_file.txt", output)
        self.assertNotIn("file2.log", output)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_complex_pipe_chain(self, mock_stdout):
        """Test a more complex pipe chain with three commands"""
        # Create a complex file structure
        self.env.execute_command("mkdir /home/dir1")
        self.env.execute_command("mkdir /home/dir2")
        self.env.execute_command("touch /home/dir1/test1.txt")
        self.env.execute_command("touch /home/dir1/test2.txt")
        self.env.execute_command("touch /home/dir2/file.log")
        
        # Clear the output buffer before the actual test command
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        
        # Simplify the test to debug what's happening
        # First, verify ls works
        self.env.execute_command("ls /home/dir1")
        ls_output = strip_ansi_codes(mock_stdout.getvalue())
        
        # Reset output buffer
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        
        # Now try a simpler pipe with ls and one grep
        self.env.execute_command("ls /home/dir1 | grep txt")
        
        output = strip_ansi_codes(mock_stdout.getvalue())
        
        # Verify the output
        self.assertIn("test1.txt", output)
        self.assertIn("test2.txt", output)

        # Reset output buffer again
        mock_stdout.truncate(0)
        mock_stdout.seek(0)

        # Now try the full complex pipe
        self.env.execute_command("ls /home/dir1 | grep txt | grep test")

        complex_output = strip_ansi_codes(mock_stdout.getvalue())

        # Verify the final output has only test*.txt files
        self.assertIn("test1.txt", complex_output)
        self.assertIn("test2.txt", complex_output)

if __name__ == '__main__':
    unittest.main()