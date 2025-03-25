import unittest
import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Ensure src is in the path for proper imports
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# Import test modules
import test_commands
import test_filesystem
import test_environment
import test_integration
import test_pipe_functionality
import test_commands_comprehensive
import test_password_manager
import test_user_management

def run_all_tests():
    # Create a test suite combining all test cases
    test_suite = unittest.TestSuite()
    
    # Add original test cases
    test_suite.addTest(unittest.makeSuite(test_commands.TestCommands))
    test_suite.addTest(unittest.makeSuite(test_filesystem.TestFileSystem))
    test_suite.addTest(unittest.makeSuite(test_environment.TestEnvironment))
    test_suite.addTest(unittest.makeSuite(test_integration.TestIntegration))
    test_suite.addTest(unittest.makeSuite(test_pipe_functionality.TestPipeFunctionality))
    
    # Add new comprehensive tests
    test_suite.addTest(unittest.makeSuite(test_commands_comprehensive.TestCommandsComprehensive))
    test_suite.addTest(unittest.makeSuite(test_password_manager.TestPasswordManager))
    test_suite.addTest(unittest.makeSuite(test_user_management.TestUserManagement))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)

if __name__ == '__main__':
    print("Running all terminal hacking game tests...")
    run_all_tests()