import os
from colorama import Fore
from utils.utils import load_machine, check_path, path_to_safe_filename
import json

def execute(args, pwd, machine_name):
    """Create an empty file at the specified location."""
    # Load the machine's file system
    machine_data = load_machine(machine_name)
    machine = machine_data["file_system"]

    # Check for valid arguments
    args = [part for part in args if part != " "]
    if len(args) == 0:
        print(Fore.RED + "Usage: touch [file]")
        return pwd

    file_name = args[0]
    
    # Determine if file path is absolute or relative
    if file_name.startswith('/'):
        # Absolute path
        path_parts = [part for part in file_name.split('/') if part != ""]
        working_path = '/' + '/'.join(path_parts[:-1]) if len(path_parts) > 1 else '/'
        file_name = path_parts[-1] if path_parts else ""
    else:
        # Relative path
        path_parts = [part for part in pwd.split('/') if part != ""]
        working_path = pwd
        
        # Handle paths with directories
        if '/' in file_name:
            file_parts = [part for part in file_name.split('/') if part != ""]
            file_name = file_parts[-1]
            for part in file_parts[:-1]:
                if part == "..":
                    if path_parts:
                        path_parts.pop()
                else:
                    path_parts.append(part)
            working_path = '/' + '/'.join(path_parts) if path_parts else '/'
    
    # Navigate to the target directory
    current = machine
    for directory in [p for p in working_path.split('/') if p]:
        if isinstance(current, dict) and directory in current:
            current = current[directory]
        else:
            print(Fore.RED + f"Directory {directory} not found")
            return pwd
    
    # Check if file already exists (not an error for touch, just updates timestamp)
    if file_name in current and isinstance(current[file_name], dict):
        print(Fore.RED + f"{file_name} is a directory")
        return pwd
    
    # Create the empty file
    try:
        # Setup paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        os_path = os.path.join(project_root, "src", "machines", machine_name, "files")
        os.makedirs(os_path, exist_ok=True)
        
        # Create a unique filename that includes the path
        safe_filename = path_to_safe_filename(working_path, file_name)
        real_file_path = os.path.join(os_path, safe_filename)
        
        # Create the empty file
        with open(real_file_path, 'w') as f:
            pass  # Just create an empty file
        
        # Update the virtual file system
        current[file_name] = f"src/machines/{machine_name}/files/{safe_filename}"
        
        # Save machine data
        machine_file_path = os.path.join(project_root, "src", "machines", machine_name, f"{machine_name}.json")
        with open(machine_file_path, 'w') as f:
            json.dump(machine_data, f, indent=4)
        
    except Exception as e:
        print(Fore.RED + f"Error creating file: {str(e)}")
    
    return pwd

def help():
    print("Usage: touch [file] - Creates an empty file at the specified path.")