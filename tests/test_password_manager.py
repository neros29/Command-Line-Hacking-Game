import unittest
import sys
import os
import bcrypt
import tempfile
import json
import shutil

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.password_manager import hash_password, verify_password, migrate_passwords
from src.utils.utils import load_machine, save_machine

class TestPasswordManager(unittest.TestCase):
    
    def setUp(self):
        """Create a test machine with plaintext password for migration testing"""
        self.test_dir = tempfile.mkdtemp()
        self.machine_name = "test_machine"
        self.machine_dir = os.path.join(self.test_dir, self.machine_name)
        os.makedirs(self.machine_dir)
        
        # Create a machine file with plaintext password
        self.machine_data = {
            "meta_data": {
                "name": "Test Machine",
                "username": "testuser",
                "password": "plaintext_password",
                "ip": "192.168.1.100",
                "users": {
                    "root": {
                        "password": "root_password",
                        "home": "/root",
                        "is_root": True
                    },
                    "user1": {
                        "password": "user1_password",
                        "home": "/home/user1",
                        "is_root": False
                    }
                }
            },
            "file_system": {
                "home": {},
                "root": {}
            }
        }
        
        self.machine_file = os.path.join(self.machine_dir, f"{self.machine_name}.json")
        with open(self.machine_file, 'w') as f:
            json.dump(self.machine_data, f)
            
        # Back up the original machines directory path for patching
        self.original_machines_dir = os.path.abspath(os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "src", "machines"
        ))
    
    def tearDown(self):
        """Clean up test directory"""
        shutil.rmtree(self.test_dir)
    
    def test_password_hashing(self):
        """Test that password hashing works correctly"""
        password = "test_password"
        hashed = hash_password(password)
        
        # Verify the hash is in bcrypt format
        self.assertTrue(hashed.startswith('$2'))
        self.assertNotEqual(password, hashed)
        
        # Test hashing with different types
        byte_password = b"byte_password"
        hashed_bytes = hash_password(byte_password)
        self.assertTrue(hashed_bytes.startswith('$2'))
        
        # Test with None password (should raise ValueError)
        with self.assertRaises(ValueError):
            hash_password(None)
    
    def test_password_verification(self):
        """Test that password verification works correctly"""
        password = "verification_test"
        hashed = hash_password(password)
        
        # Correct password
        self.assertTrue(verify_password(password, hashed))
        
        # Wrong password
        self.assertFalse(verify_password("wrong_password", hashed))
        
        # Test with byte password
        byte_password = b"byte_verification"
        byte_hashed = hash_password(byte_password)
        self.assertTrue(verify_password(byte_password, byte_hashed))
        
        # Test verification with plaintext fallback
        self.assertTrue(verify_password("plain", "plain"))
        
        # Test with empty password
        self.assertFalse(verify_password("", hashed))
        self.assertFalse(verify_password(None, hashed))
        
        # Test with invalid hash
        self.assertFalse(verify_password(password, "invalid_hash"))
        self.assertFalse(verify_password(password, None))
    
    def test_password_migration(self):
        """Test migration from plaintext to hashed passwords"""
        # Mock the machines directory to point to our test directory
        import src.utils.password_manager as pm
        original_dir = pm.os.path.abspath
        
        try:
            # Patch the path function to return our test dir
            def mock_abspath(path):
                if "machines" in path:
                    return self.test_dir
                return original_dir(path)
            
            pm.os.path.abspath = mock_abspath
            
            # Run migration
            migrate_passwords(self.machine_name)
            
            # Load the machine and check if passwords were hashed
            with open(self.machine_file, 'r') as f:
                migrated_data = json.load(f)
            
            # Main password should be hashed
            self.assertTrue(migrated_data["meta_data"]["password"].startswith('$2'))
            
            # User passwords should be hashed
            root_pass = migrated_data["meta_data"]["users"]["root"]["password"]
            user1_pass = migrated_data["meta_data"]["users"]["user1"]["password"]
            
            self.assertTrue(root_pass.startswith('$2'))
            self.assertTrue(user1_pass.startswith('$2'))
            
            # Verify the hashed passwords work with the original plaintext
            self.assertTrue(verify_password("root_password", root_pass))
            self.assertTrue(verify_password("user1_password", user1_pass))
        
        finally:
            # Restore original function
            pm.os.path.abspath = original_dir