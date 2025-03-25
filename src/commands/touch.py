import os
from colorama import Fore
from utils.utils import load_machine
from src.utils.file_utils import resolve_path, write_to_file, navigate_to_path

def execute(args, pwd, machine_name):
    """Create an empty file at the specified location."""
    # Load the machine's file system
    machine_data = load_machine(machine_name)
    
    # Check for valid arguments
    args = [part for part in args if part != " "]
    if len(args) == 0:
        print(Fore.RED + "Usage: touch [file]")
        return pwd

    file_path = args[0]
    
    # Resolve the path
    path_parts = resolve_path(file_path, pwd, machine_data["file_system"])
    parent_parts = path_parts[:-1]
    filename = path_parts[-1]

    # Check if parent directory exists
    success, parent_dir = navigate_to_path(machine_data["file_system"], parent_parts)
    if not success:
        print(Fore.RED + f"Directory not found: /{'/'.join(parent_parts)}")
        return pwd
    
    # Create the file
    if write_to_file(machine_data, path_parts, ""):
        print(Fore.GREEN + f"Created file: {file_path}")
    else:
        print(Fore.RED + f"Failed to create file: {file_path}")
    
    return pwd

def help():
    print("Usage: touch [file] - Creates an empty file at the specified path.")