import unittest
import sys
import os
import io
import re
import getpass
import shutil
import tempfile
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.utils import load_machine, save_machine
from src.main import HackingEnvironment
from test_utils import FileSystemTestFixture, strip_ansi_codes

class TestCommandsComprehensive(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test."""
        self.machine_name = "local"
        self.pwd = "/home"
        self.fs_fixture = FileSystemTestFixture(self.machine_name)
        self.fs_fixture.setup()
        
        # Create a test environment
        self.env = HackingEnvironment(machine_name=self.machine_name)
        self.env.current_user = "root"  # Set as root for permissions
        self.env.is_root = True
        
        # Import commands
        import src.commands.ls as ls
        import src.commands.cd as cd
        import src.commands.mkdir as mkdir
        import src.commands.touch as touch
        import src.commands.cat as cat
        import src.commands.rm as rm
        import src.commands.mv as mv
        import src.commands.echo as echo
        import src.commands.grep as grep
        
        self.commands = {
            'ls': ls,
            'cd': cd,
            'mkdir': mkdir,
            'touch': touch,
            'cat': cat,
            'rm': rm,
            'mv': mv,
            'echo': echo,
            'grep': grep
        }
    
    def tearDown(self):
        """Clean up after each test."""
        self.fs_fixture.teardown()
    
    #
    # LS COMMAND TESTS
    #
    def test_ls_basic(self):
        """Test basic ls command with no arguments"""
        result = self.commands['ls'].execute([], self.pwd, self.machine_name)
        self.assertEqual(result, self.pwd)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_ls_specific_directory(self, mock_stdout):
        """Test ls on a specific directory"""
        self.commands['ls'].execute(["/bin"], self.pwd, self.machine_name)
        output = mock_stdout.getvalue()
        self.assertIn("ls", output)  # Should list ls command
        self.assertIn("cd", output)  # Should list cd command
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_ls_nonexistent_directory(self, mock_stdout):
        """Test ls on a nonexistent directory"""
        self.commands['ls'].execute(["/nonexistent"], self.pwd, self.machine_name)
        output = mock_stdout.getvalue()
        self.assertIn("not found", output.lower())
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_ls_hidden_flag(self, mock_stdout):
        """Test ls with -a flag to show hidden files"""
        # Create a hidden file first
        self.commands['touch'].execute([".hidden_file"], self.pwd, self.machine_name)
        
        # List without -a flag
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        self.commands['ls'].execute([], self.pwd, self.machine_name)
        output1 = mock_stdout.getvalue()
        
        # List with -a flag
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        self.commands['ls'].execute(["-a"], self.pwd, self.machine_name)
        output2 = mock_stdout.getvalue()
        
        # Hidden file should not be in regular output but should be in -a output
        self.assertNotIn(".hidden_file", output1)
        self.assertIn(".hidden_file", output2)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_ls_recursive(self, mock_stdout):
        """Test ls with -r flag for recursive listing"""
        # Create a nested directory structure
        self.commands['mkdir'].execute(["test_dir"], self.pwd, self.machine_name)
        self.commands['touch'].execute(["test_dir/file1.txt"], self.pwd, self.machine_name)
        self.commands['mkdir'].execute(["test_dir/subdir"], self.pwd, self.machine_name)
        self.commands['touch'].execute(["test_dir/subdir/file2.txt"], self.pwd, self.machine_name)
        
        # Recursive ls
        self.commands['ls'].execute(["-r", "test_dir"], self.pwd, self.machine_name)
        output = mock_stdout.getvalue()
        
        # Should show both files in the directory structure
        self.assertIn("file1.txt", output)
        self.assertIn("subdir", output)
        self.assertIn("file2.txt", output)
    
    #
    # CD COMMAND TESTS
    #
    def test_cd_basic(self):
        """Test basic cd command"""
        # Change to root directory
        result = self.commands['cd'].execute(["/"], self.pwd, self.machine_name)
        self.assertEqual(result, "/")
        
        # Change to home directory
        result = self.commands['cd'].execute(["/home"], "/", self.machine_name)
        self.assertEqual(result, "/home")
    
    def test_cd_relative_paths(self):
        """Test cd with relative paths"""
        # Create a directory
        self.commands['mkdir'].execute(["test_dir"], self.pwd, self.machine_name)
        
        # Change to that directory with relative path
        result = self.commands['cd'].execute(["test_dir"], self.pwd, self.machine_name)
        self.assertEqual(result, f"{self.pwd}/test_dir")
        
        # Go up one directory with ..
        result = self.commands['cd'].execute([".."], f"{self.pwd}/test_dir", self.machine_name)
        self.assertEqual(result, self.pwd)
    
    def test_cd_nonexistent_directory(self):
        """Test cd to a nonexistent directory"""
        result = self.commands['cd'].execute(["/nonexistent"], self.pwd, self.machine_name)
        # Should stay in the same directory
        self.assertEqual(result, self.pwd)
    
    def test_cd_to_file(self):
        """Test cd to a file (should fail)"""
        # Create a file
        self.commands['touch'].execute(["test_file.txt"], self.pwd, self.machine_name)
        
        # Try to cd to it
        result = self.commands['cd'].execute(["test_file.txt"], self.pwd, self.machine_name)
        # Should stay in the same directory
        self.assertEqual(result, self.pwd)
    
    #
    # MKDIR COMMAND TESTS
    #
    def test_mkdir_basic(self):
        """Test basic mkdir command"""
        result = self.commands['mkdir'].execute(["new_dir"], self.pwd, self.machine_name)
        self.assertEqual(result, self.pwd)
        
        # Verify directory was created
        machine = load_machine(self.machine_name)
        self.assertIn("new_dir", machine["file_system"]["home"])
        self.assertTrue(isinstance(machine["file_system"]["home"]["new_dir"], dict))
    
    def test_mkdir_nested_directory(self):
        """Test creating nested directories"""
        # Create parent directory
        self.commands['mkdir'].execute(["parent_dir"], self.pwd, self.machine_name)
        
        # Create child directory
        result = self.commands['mkdir'].execute(["parent_dir/child_dir"], self.pwd, self.machine_name)
        self.assertEqual(result, self.pwd)
        
        # Verify nested directory was created
        machine = load_machine(self.machine_name)
        self.assertIn("child_dir", machine["file_system"]["home"]["parent_dir"])
    
    def test_mkdir_existing_directory(self):
        """Test creating a directory that already exists"""
        # Create directory
        self.commands['mkdir'].execute(["existing_dir"], self.pwd, self.machine_name)
        
        # Try to create it again
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            result = self.commands['mkdir'].execute(["existing_dir"], self.pwd, self.machine_name)
            output = mock_stdout.getvalue()
            self.assertIn("already exists", output)
    
    #
    # TOUCH COMMAND TESTS
    #
    def test_touch_basic(self):
        """Test basic touch command"""
        result = self.commands['touch'].execute(["new_file.txt"], self.pwd, self.machine_name)
        self.assertEqual(result, self.pwd)
        
        # Verify file was created
        machine = load_machine(self.machine_name)
        self.assertIn("new_file.txt", machine["file_system"]["home"])
    
    def test_touch_nested_file(self):
        """Test creating a file in a nested directory"""
        # Create directory
        self.commands['mkdir'].execute(["test_dir"], self.pwd, self.machine_name)
        
        # Create file in that directory
        result = self.commands['touch'].execute(["test_dir/nested_file.txt"], self.pwd, self.machine_name)
        self.assertEqual(result, self.pwd)
        
        # Verify file was created
        machine = load_machine(self.machine_name)
        self.assertIn("nested_file.txt", machine["file_system"]["home"]["test_dir"])
    
    def test_touch_nonexistent_directory(self):
        """Test creating a file in a nonexistent directory"""
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            result = self.commands['touch'].execute(["nonexistent_dir/file.txt"], self.pwd, self.machine_name)
            output = mock_stdout.getvalue()
            self.assertIn("not found", output.lower())
    
    #
    # CAT COMMAND TESTS
    #
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cat_basic(self, mock_stdout):
        """Test basic cat command on an existing file"""
        # Create a physical test file
        machine = load_machine(self.machine_name)
        
        # Create a test file with content
        test_content = "This is test content for cat command.\nLine 2 of the test file."
        self.commands['touch'].execute(["test_cat.txt"], self.pwd, self.machine_name)
        
        # Get the physical path
        machine = load_machine(self.machine_name)
        file_path = machine["file_system"]["home"]["test_cat.txt"]
        
        # Write content to the physical file
        with open(file_path, 'w') as f:
            f.write(test_content)
        
        # Cat the file
        result = self.commands['cat'].execute(["test_cat.txt"], self.pwd, self.machine_name)
        self.assertEqual(result, self.pwd)
        
        # Verify output contains file content
        output = strip_ansi_codes(mock_stdout.getvalue())
        for line in test_content.split('\n'):
            self.assertIn(line, output)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cat_nonexistent_file(self, mock_stdout):
        """Test cat on a nonexistent file"""
        result = self.commands['cat'].execute(["nonexistent.txt"], self.pwd, self.machine_name)
        self.assertEqual(result, self.pwd)
        
        # Should show an error
        output = mock_stdout.getvalue()
        self.assertIn("not found", output.lower())
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cat_directory(self, mock_stdout):
        """Test cat on a directory (should fail)"""
        # Create a directory
        self.commands['mkdir'].execute(["test_dir"], self.pwd, self.machine_name)
        
        # Try to cat it
        result = self.commands['cat'].execute(["test_dir"], self.pwd, self.machine_name)
        self.assertEqual(result, self.pwd)
        
        # Should show an error
        output = mock_stdout.getvalue()
        self.assertIn("directory", output.lower())
    
    #
    # RM COMMAND TESTS
    #
    def test_rm_basic(self):
        """Test basic rm command"""
        # Create a file
        self.commands['touch'].execute(["file_to_remove.txt"], self.pwd, self.machine_name)
        
        # Verify it exists
        machine = load_machine(self.machine_name)
        self.assertIn("file_to_remove.txt", machine["file_system"]["home"])
        
        # Remove it
        result = self.commands['rm'].execute(["file_to_remove.txt"], self.pwd, self.machine_name)
        self.assertEqual(result, self.pwd)
        
        # Verify it's gone
        machine = load_machine(self.machine_name)
        self.assertNotIn("file_to_remove.txt", machine["file_system"]["home"])
    
    def test_rm_recursive(self):
        """Test rm with -r flag (recursive)"""
        # Create a directory with files
        self.commands['mkdir'].execute(["dir_to_remove"], self.pwd, self.machine_name)
        self.commands['touch'].execute(["dir_to_remove/file1.txt"], self.pwd, self.machine_name)
        self.commands['touch'].execute(["dir_to_remove/file2.txt"], self.pwd, self.machine_name)
        
        # Verify it exists
        machine = load_machine(self.machine_name)
        self.assertIn("dir_to_remove", machine["file_system"]["home"])
        
        # Try to remove without -r (should fail)
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            result = self.commands['rm'].execute(["dir_to_remove"], self.pwd, self.machine_name)
            output = mock_stdout.getvalue()
            self.assertIn("directory", output.lower())
        
        # Remove with -r
        result = self.commands['rm'].execute(["-r", "dir_to_remove"], self.pwd, self.machine_name)
        self.assertEqual(result, self.pwd)
        
        # Verify it's gone
        machine = load_machine(self.machine_name)
        self.assertNotIn("dir_to_remove", machine["file_system"]["home"])
    
    def test_rm_nonexistent(self):
        """Test removing a nonexistent file"""
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            result = self.commands['rm'].execute(["nonexistent.txt"], self.pwd, self.machine_name)
            output = mock_stdout.getvalue()
            self.assertIn("not found", output.lower())
    
    #
    # MV COMMAND TESTS
    #
    def test_mv_file(self):
        """Test moving a file to a different directory"""
        # Create a file and directory
        self.commands['touch'].execute(["file_to_move.txt"], self.pwd, self.machine_name)
        self.commands['mkdir'].execute(["target_dir"], self.pwd, self.machine_name)
        
        # Move the file
        result = self.commands['mv'].execute(["file_to_move.txt", "target_dir"], self.pwd, self.machine_name)
        self.assertEqual(result, self.pwd)
        
        # Verify the file moved
        machine = load_machine(self.machine_name)
        self.assertNotIn("file_to_move.txt", machine["file_system"]["home"])
        self.assertIn("file_to_move.txt", machine["file_system"]["home"]["target_dir"])
    
    def test_mv_rename(self):
        """Test renaming a file"""
        # Create a file
        self.commands['touch'].execute(["original.txt"], self.pwd, self.machine_name)
        
        # Rename it
        result = self.commands['mv'].execute(["original.txt", "renamed.txt"], self.pwd, self.machine_name)
        self.assertEqual(result, self.pwd)
        
        # Verify the rename
        machine = load_machine(self.machine_name)
        self.assertNotIn("original.txt", machine["file_system"]["home"])
        self.assertIn("renamed.txt", machine["file_system"]["home"])
    
    def test_mv_directory(self):
        """Test moving a directory"""
        # Create directories
        self.commands['mkdir'].execute(["dir_to_move"], self.pwd, self.machine_name)
        self.commands['mkdir'].execute(["target_parent"], self.pwd, self.machine_name)
        
        # Move the directory
        result = self.commands['mv'].execute(["dir_to_move", "target_parent"], self.pwd, self.machine_name)
        self.assertEqual(result, self.pwd)
        
        # Verify the move
        machine = load_machine(self.machine_name)
        self.assertNotIn("dir_to_move", machine["file_system"]["home"])
        self.assertIn("dir_to_move", machine["file_system"]["home"]["target_parent"])
    
    def test_mv_nonexistent(self):
        """Test moving a nonexistent file"""
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            result = self.commands['mv'].execute(["nonexistent.txt", "somewhere"], self.pwd, self.machine_name)
            output = mock_stdout.getvalue()
            self.assertIn("not found", output.lower())
    
    #
    # ECHO COMMAND TESTS
    #
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_echo_basic(self, mock_stdout):
        """Test basic echo command"""
        test_text = "Hello, world!"
        result = self.commands['echo'].execute([test_text], self.pwd, self.machine_name)
        self.assertEqual(result, self.pwd)
        
        # Verify output
        output = strip_ansi_codes(mock_stdout.getvalue())
        self.assertIn(test_text, output)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_echo_multiple_args(self, mock_stdout):
        """Test echo with multiple arguments"""
        args = ["Hello,", "world!"]
        result = self.commands['echo'].execute(args, self.pwd, self.machine_name)
        self.assertEqual(result, self.pwd)
        
        # Verify output
        output = strip_ansi_codes(mock_stdout.getvalue())
        self.assertIn("Hello, world!", output)
    
    def test_echo_redirect(self):
        """Test echo with output redirection"""
        # Check if the command supports redirection
        # Note: This might need to be implemented in the echo command
        test_text = "Redirected text"
        output_file = "redirect_output.txt"
        
        result = self.commands['echo'].execute([test_text, ">", output_file], self.pwd, self.machine_name)
        self.assertEqual(result, self.pwd)
        
        # Verify file was created with content
        machine = load_machine(self.machine_name)
        self.assertIn(output_file, machine["file_system"]["home"])
    
    #
    # GREP COMMAND TESTS
    #
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_grep_basic(self, mock_stdout):
        """Test basic grep command with piped input"""
        # Set up piped input
        os.environ["PIPED_INPUT"] = "Line 1: apple\nLine 2: banana\nLine 3: apple and orange"
        os.environ["IS_PIPED"] = "1"
        
        # Run grep
        result = self.commands['grep'].execute(["apple"], self.pwd, self.machine_name)
        self.assertEqual(result, self.pwd)
        
        # Verify output contains only matching lines
        output = strip_ansi_codes(mock_stdout.getvalue())
        self.assertIn("Line 1: apple", output)
        self.assertIn("Line 3: apple and orange", output)
        self.assertNotIn("Line 2: banana", output)
        
        # Clean up environment
        del os.environ["PIPED_INPUT"]
        del os.environ["IS_PIPED"]
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_grep_case_insensitive(self, mock_stdout):
        """Test grep with -i flag (case insensitive)"""
        # Set up piped input
        os.environ["PIPED_INPUT"] = "Line 1: APPLE\nLine 2: banana\nLine 3: Apple and orange"
        os.environ["IS_PIPED"] = "1"
        
        # Run grep with -i
        result = self.commands['grep'].execute(["-i", "apple"], self.pwd, self.machine_name)
        self.assertEqual(result, self.pwd)
        
        # Verify output contains all case-insensitive matches
        output = strip_ansi_codes(mock_stdout.getvalue())
        self.assertIn("Line 1: APPLE", output)
        self.assertIn("Line 3: Apple and orange", output)
        self.assertNotIn("Line 2: banana", output)
        
        # Clean up environment
        del os.environ["PIPED_INPUT"]
        del os.environ["IS_PIPED"]
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_grep_no_matches(self, mock_stdout):
        """Test grep with no matching lines"""
        # Set up piped input
        os.environ["PIPED_INPUT"] = "Line 1: apple\nLine 2: banana\nLine 3: orange"
        os.environ["IS_PIPED"] = "1"
        
        # Run grep
        result = self.commands['grep'].execute(["nonexistent"], self.pwd, self.machine_name)
        self.assertEqual(result, self.pwd)
        
        # Verify output is empty
        output = strip_ansi_codes(mock_stdout.getvalue())
        self.assertEqual("", output.strip())
        
        # Clean up environment
        del os.environ["PIPED_INPUT"]
        del os.environ["IS_PIPED"]