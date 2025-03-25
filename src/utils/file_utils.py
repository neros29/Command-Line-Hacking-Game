import os
import json
from colorama import Fore

def resolve_path(path, pwd, file_system):
    """
    Resolves a path (absolute or relative) to a location in the file system.
    
    Args:
        path (str): The path to resolve
        pwd (str): Current working directory
        file_system (dict): The file system structure
        
    Returns:
        list: A list of directory/file names representing the resolved path
    """
    # Handle absolute vs relative paths
    if path.startswith('/'):
        # Absolute path
        path_parts = [part for part in path.split('/') if part]
    else:
        # Relative path
        pwd_parts = [part for part in pwd.split('/') if part]
        path_parts = pwd_parts.copy()
        
        # Process path components
        for part in path.split('/'):
            if part == "..":
                if path_parts:
                    path_parts.pop()
            elif part and part != ".":
                path_parts.append(part)
    
    return path_parts

def path_to_safe_filename(virtual_path, filename):
    """
    Convert a virtual path to a safe physical filename.
    
    Args:
        virtual_path (str): The virtual path in the file system
        filename (str): The filename
        
    Returns:
        str: A safe filename that includes the encoded path
    """
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
    """
    Convert a safe filename back to a virtual path.
    
    Args:
        safe_filename (str): The safe filename with encoded path
        
    Returns:
        tuple: (path, filename) where path is the virtual path and filename is the original filename
    """
    # Handle both old-style and new-style filenames
    if '__DIR__' in safe_filename:
        parts = safe_filename.split('__DIR__')
        filename = parts[-1]
        path = '/'.join(parts[:-1])
        return path, filename
    return None, safe_filename

def write_to_file(machine, path_parts, content):
    """
    Writes content to a file at the specified path.
    Creates the file if it doesn't exist, following the same approach as touch.
    
    Args:
        machine (dict): The machine data structure
        path_parts (list): List of path components (from resolve_path)
        content (str): Content to write to the file
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not path_parts:
        return False
    
    # Navigate to the parent directory
    current = machine["file_system"]
    parent_path = path_parts[:-1]
    filename = path_parts[-1]
    
    # Navigate to the parent directory
    for directory in parent_path:
        if directory in current and isinstance(current[directory], dict):
            current = current[directory]
        else:
            # Parent directory doesn't exist
            return False
    
    try:
        # Get machine name
        machine_name = machine.get("name", "local")
        
        # Setup paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        os_path = os.path.join(project_root, "src", "machines", machine_name, "files")
        os.makedirs(os_path, exist_ok=True)
        
        # Create a unique filename that includes the path
        working_path = '/' + '/'.join(parent_path) if parent_path else '/'
        safe_filename = path_to_safe_filename(working_path, filename)
        real_file_path = os.path.join(os_path, safe_filename)
        
        # Create the file with content
        with open(real_file_path, 'w') as f:
            f.write(content)
        
        # Update the virtual file system
        current[filename] = f"src/machines/{machine_name}/files/{safe_filename}"
        
        # Save machine data
        machine_file_path = os.path.join(project_root, "src", "machines", machine_name, f"{machine_name}.json")
        with open(machine_file_path, 'w') as f:
            json.dump(machine, f, indent=4)
        
        return True
    except Exception as e:
        print(f"Error writing to file: {str(e)}")
        return False

def read_file(machine, path_parts):
    """
    Reads content from a file at the specified path.
    
    Args:
        machine (dict): The machine data structure
        path_parts (list): List of path components (from resolve_path)
        
    Returns:
        tuple: (success, content) where success is bool and content is the file content or error message
    """
    if not path_parts:
        return False, "Invalid path"
    
    # Navigate to the file in the virtual file system
    current = machine["file_system"]
    file_path = path_parts
    
    # Navigate to the directory containing the file
    for part in file_path[:-1]:
        if part in current and isinstance(current[part], dict):
            current = current[part]
        else:
            return False, f"Directory {part} not found"
    
    # Check if the file exists
    filename = file_path[-1]
    if filename not in current:
        return False, f"File {filename} not found"
    
    file_content = current[filename]
    
    # Check if it's a directory or command
    if isinstance(file_content, dict):
        return False, f"{filename} is a directory, not a file"
    if file_content == "command":
        return False, f"You are not authorized to view the contents of {filename}"
    
    # Read the actual file content
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        real_file_path = os.path.join(project_root, file_content)
        
        with open(real_file_path, "r") as f:
            content = f.read()
            return True, content
    except FileNotFoundError:
        return False, f"Physical file {file_content} not found"
    except Exception as e:
        return False, f"Error reading file: {str(e)}"

def navigate_to_path(file_system, path_parts):
    """
    Navigates to a specific path in the file system.
    
    Args:
        file_system (dict): The file system structure
        path_parts (list): List of path components (from resolve_path)
        
    Returns:
        tuple: (success, result) where success is bool and result is either 
               the directory object or an error message
    """
    if not path_parts:
        return True, file_system
    
    current = file_system
    
    # Navigate to each component of the path
    for part in path_parts:
        if part in current and isinstance(current[part], dict):
            current = current[part]
        else:
            return False, f"Path component '{part}' not found or is not a directory"
    
    return True, current

def check_file_exists(file_system, path_parts):
    """
    Checks if a file or directory exists at the specified path.
    
    Args:
        file_system (dict): The file system structure
        path_parts (list): List of path components (from resolve_path)
        
    Returns:
        tuple: (exists, is_directory, item) where exists is bool, 
               is_directory is bool or None if doesn't exist,
               item is the file/directory object or None if doesn't exist
    """
    if not path_parts:
        return True, True, file_system  # Root directory
    
    # Navigate to the parent directory
    parent_path = path_parts[:-1]
    filename = path_parts[-1]
    
    success, result = navigate_to_path(file_system, parent_path)
    if not success:
        return False, None, None
    
    parent_dir = result
    
    # Check if the file/directory exists
    if filename in parent_dir:
        item = parent_dir[filename]
        is_directory = isinstance(item, dict)
        return True, is_directory, item
    
    return False, None, None

def check_file_access(file_system, path_parts, current_user="root", mode="read"):
    """
    Check if the current user has access to a file or directory.
    
    Args:
        file_system (dict): The file system structure
        path_parts (list): List of path components
        current_user (str): Current username
        mode (str): "read" or "write"
        
    Returns:
        tuple: (has_access, message) where has_access is a boolean and 
               message is an error message or None
    """
    if not path_parts:
        # Root directory
        return True, None
    
    # Check if the file/directory exists first
    exists, is_directory, item = check_file_exists(file_system, path_parts)
    
    if not exists:
        return False, f"No such file or directory: /{'/'.join(path_parts)}"
    
    # Root user has access to everything
    if current_user == "root":
        return True, None
    
    # For directories or command files, implement your permission logic
    # For example:
    if is_directory:
        # Directory permission logic
        return True, None
    else:
        # File permission logic - this is a simple example
        # You might have a more complex permission system
        if mode == "write" and path_parts[0] == "etc":
            return False, "Permission denied: Cannot modify system files"
        
        if mode == "write" and path_parts[0] == "bin":
            return False, "Permission denied: Cannot modify system binaries"
        
        # Additional permission checks can be added here
        
        return True, None