import os
import importlib
import json
import sys
import time
import random
from colorama import init, Fore

# Get the absolute path to the project root, not utils directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def load_command(command_name):
    """Dynamically load and return a command from the 'commands' directory."""
    try:
        module = importlib.import_module(f'commands.{command_name}')
        return module.__dict__.get(command_name)
    except ImportError:
        raise FileNotFoundError(f"Command {command_name} not found.")

def load_machine(machine_name):
    """Load machine configuration with better error handling."""
    try:
        # Use relative paths from the project structure
        file_path = os.path.join("src", "machines", machine_name, f"{machine_name}.json")
        if not os.path.exists(file_path):
            # Fallback to absolute path if needed
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
            file_path = os.path.join(project_root, "src", "machines", machine_name, f"{machine_name}.json")
        
        with open(file_path, "r") as f:
            machine_data = json.load(f)
            return machine_data
    except FileNotFoundError:
        print(Fore.RED + f"Error: Machine '{machine_name}' not found.")
        return {"file_system": {"bin": {}}, "meta_data": {"name": "unknown", "ip": "0.0.0.0"}}
    except json.JSONDecodeError:
        print(Fore.RED + f"Error: Invalid JSON in machine file for '{machine_name}'.")
        return {"file_system": {"bin": {}}, "meta_data": {"name": "unknown", "ip": "0.0.0.0"}}

def save_machine(machine_name, machine_data):
    """
    Save machine data to the corresponding JSON file.
    
    Args:
        machine_name (str): Name of the machine
        machine_data (dict): Machine data to save
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        machine_file_path = f"src/machines/{machine_name}/{machine_name}.json"
        
        # Ensure the directory exists
        machine_dir = os.path.dirname(machine_file_path)
        if not os.path.exists(machine_dir):
            os.makedirs(machine_dir)
        
        # Save machine data to file
        with open(machine_file_path, "w") as file:
            json.dump(machine_data, file, indent=4)
        
        return True
    except Exception as e:
        print(f"Error saving machine data: {str(e)}")
        return False

def check_path(machine_data, path_list):
    """
    Checks if a given virtual path exists in the machine JSON structure.
    
    :param machine_data: Dictionary representing the machine's virtual file system.
    :param path_list: List of directory names forming the path.
    :return: The contents of the path if it exists, otherwise None.
    """
    current = machine_data  # Start at the root level of the JSON

    for directory in path_list:
        if isinstance(current, dict) and directory in current:
            current = current[directory]  # Move into the next directory
        else:
            return None  # Path does not exist
    
    return current  # Return the final value found

def animated_text(text, delay=0.05):
    """Prints text with a typing animation."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def loading_bar(task, length=30, speed_range=(1, 5)):
    """Creates a smoother loading bar with randomized speed."""
    print(Fore.CYAN + task)
    for i in range(length):
        percent = (i + 1) / length * 100
        bar = '#' * (i + 1) + '-' * (length - (i + 1))
        sys.stdout.write(Fore.CYAN + f"\r[{bar}] {percent:.2f}%")
        sys.stdout.flush()
        time.sleep(random.uniform(speed_range[0] / 100, speed_range[1] / 100))
    print()

def path_to_safe_filename(virtual_path, filename):
    """Convert a virtual path to a safe physical filename"""
    # Replace slashes with double underscores to create a unique filename
    path_encoded = virtual_path.replace('/', '__DIR__').replace('\\', '__DIR__')
    # Remove the leading __DIR__ if it exists
    if path_encoded.startswith('__DIR__'):
        path_encoded = path_encoded[7:]
    # Handle empty path
    if not path_encoded:
        return filename
    return f"{path_encoded}__DIR__{filename}"

def safe_filename_to_path(safe_filename):
    """Convert a safe filename back to a virtual path"""
    # Handle both old-style and new-style filenames
    if '__DIR__' in safe_filename:
        parts = safe_filename.split('__DIR__')
        filename = parts[-1]
        path = '/'.join(parts[:-1])
        return path, filename
    return None, safe_filename

def check_file_access(path, username, user_data, env):
    """
    Check if the user has access to the specified path.
    
    Args:
        path (str): The file path to check
        username (str): The current username
        user_data (dict): The user's data from meta_data.users
        env: The environment object
        
    Returns:
        bool: True if the user has access, False otherwise
    """
    # Root can access everything
    if user_data.get("is_root", False):
        return True
    
    # Get user permissions
    permissions = user_data.get("permissions", [])
    
    # "all" permission grants access to everything
    if "all" in permissions:
        return True
    
    # Regular users can't access /root directory
    if path.startswith("/root"):
        return False
    
    # Check for bin permission
    if path.startswith("/bin"):
        return "bin" in permissions
    
    # Check for var permission
    if path.startswith("/var"):
        return "var" in permissions
    
    # Check home directory access
    if path.startswith("/home/"):
        # Users can access their own home directory
        if path.startswith(user_data.get("home", f"/home/{username}")):
            return True
        
        # Check for public directories
        public_dirs = ["/home/public", "/home/shared"]
        if any(path.startswith(pub_dir) for pub_dir in public_dirs):
            return "public" in permissions
        
        # Check home permission for access to other users' homes
        return "home" in permissions
    
    # All other paths are accessible by default
    return True
