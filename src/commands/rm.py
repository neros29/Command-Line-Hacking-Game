import os
from colorama import Fore
from utils.utils import load_machine, save_machine
from src.utils.file_utils import resolve_path, check_file_exists, navigate_to_path

def execute(args, pwd, machine_name):
    """Remove a file or directory"""
    # Load the machine's file system
    machine_data = load_machine(machine_name)
    machine = machine_data["file_system"]
    current_user = machine_data["meta_data"].get("current_user", "system")

    # Remove any empty arguments
    args = [part for part in args if part != " "]
    if len(args) == 0:
        print(Fore.RED + "Usage: rm [file/directory]")
        return pwd

    # Check for recursive flag
    recursive = False
    if "-r" in args:
        recursive = True
        args.remove("-r")
        if len(args) == 0:
            print(Fore.RED + "Usage: rm -r [directory]")
            return pwd

    target = args[0]
    
    # Resolve the path
    path_parts = resolve_path(target, pwd, machine)
    exists, is_directory, item = check_file_exists(machine, path_parts)

    if not exists:
        print(Fore.RED + "File or directory not found")
        return pwd
    
    # If it's a directory, check for recursion
    if is_directory:
        if not recursive and len(item) > 0:
            print(Fore.RED + "Cannot remove directory: Directory not empty (use -r for recursive removal)")
            return pwd
    
    # Navigate to the parent directory
    parent_path_parts = path_parts[:-1]
    success, parent_dir = navigate_to_path(machine, parent_path_parts)
    
    if not success:
        print(Fore.RED + "Parent directory not found")
        return pwd
    
    # Remove the item
    filename = path_parts[-1]
    if filename in parent_dir:
        # If it's a file, delete the physical file if it exists
        if not is_directory:
            file_path = parent_dir[filename]
            if isinstance(file_path, str) and file_path != "command":
                try:
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
                    full_path = os.path.join(project_root, file_path)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                except Exception as e:
                    print(Fore.YELLOW + f"Warning: Could not delete physical file: {str(e)}")
        
        # Remove from the file system
        del parent_dir[filename]
        
        # Save the updated file system
        save_machine(machine_name, machine_data)
    
    return pwd

def help():
    print("Usage: rm [file] - Removes a file")
    print("       rm -r [directory] - Removes a directory and its contents")