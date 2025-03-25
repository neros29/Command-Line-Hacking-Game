import unittest
import sys
import os
import io
from unittest.mock import patch

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import HackingEnvironment
from test_utils import FileSystemTestFixture

class TestEnvironment(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test."""
        self.fs_fixture = FileSystemTestFixture("local")
        self.fs_fixture.setup()
        self.env = HackingEnvironment()
    
    def tearDown(self):
        """Clean up after each test."""
        self.fs_fixture.teardown()
    
    def test_environment_init(self):
        """Test environment initialization"""
        self.assertEqual(self.env.pwd, "/home")
        self.assertEqual(self.env.current_machine_name, "local")
        self.assertIsNotNone(self.env.commands_list)
        
    def test_commands_loaded(self):
        """Test commands are properly loaded"""
        # Some essential commands that should be loaded
        essential_commands = ["ls", "cd", "mkdir", "cat"]
        
        for cmd in essential_commands:
            self.assertIn(cmd, self.env.commands_list)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_execute_command(self, mock_stdout):
        """Test command execution"""
        # Execute help command (should print to stdout)
        self.env.execute_command("help")
        output = mock_stdout.getvalue()
        
        # Verify output contains command help info
        self.assertIn("For more information", output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_help_command(self, mock_stdout):
        """Test help command directly"""
        self.env.help_command()
        output = mock_stdout.getvalue()
        
        # Verify output contains command help info
        self.assertIn("For more information", output)

if __name__ == '__main__':
    unittest.main()