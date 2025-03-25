import unittest
import sys
import os
import json

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.utils import load_machine

class TestFileSystem(unittest.TestCase):
    
    def test_load_machine(self):
        """Test loading machine configuration"""
        machine = load_machine("local")
        self.assertIsNotNone(machine)
        self.assertIn("file_system", machine)
        self.assertIn("meta_data", machine)
    
    def test_filesystem_structure(self):
        """Test filesystem has required directories"""
        machine = load_machine("local")
        fs = machine["file_system"]
        
        # Check required directories
        self.assertIn("home", fs)
        self.assertIn("bin", fs)
        
        # Check bin has commands
        self.assertIn("ls", fs["bin"])
        self.assertIn("cd", fs["bin"])
    
    def test_machine_metadata(self):
        """Test machine metadata contains required fields"""
        machine = load_machine("local")
        meta = machine["meta_data"]
        
        # Check required metadata
        self.assertIn("name", meta)
        self.assertIn("username", meta)
        self.assertIn("password", meta)
        self.assertIn("ip", meta)

if __name__ == '__main__':
    unittest.main()