import os
from colorama import Fore
from src.utils.utils import load_machine
import os

def resolve_path(target_path, pwd, machine):
    """Resolve the target path to its components."""
    if target_path.startswith('/'):
        # Absolute path
        path_parts = [part for part in target_path.split('/') if part]
    else:
        # Relative path
        pwd_parts = [part for part in pwd.split('/') if part]
        path_parts = pwd_parts.copy()
        for part in target_path.split('/'):
            if part == "..":
                if path_parts:
                    path_parts.pop()
            elif part and part != ".":
                path_parts.append(part)
    return path_parts

def navigate_to_path(machine, path_parts):
    """Navigate to the target directory."""
    current = machine
    for directory in path_parts:
        if isinstance(current, dict) and directory in current:
            current = current[directory]
        else:
            return False, None
    return True, current

def execute(args, pwd, machine_name):
    """List directory contents with support for recursive listing."""
    machine = load_machine(machine_name)
    machine = machine["file_system"]
    
    # Process options
    recursive = False
    show_hidden = False  # New flag for -a option
    target_path = pwd
    
    # Parse arguments
    for i, arg in enumerate(args):
        if arg == "-r" or arg == "--recursive":
            recursive = True
        elif arg == "-a" or arg == "--all":
            show_hidden = True  # Set flag when -a is detected
        elif not arg.startswith("-"):
            target_path = arg
    
    # Replace path resolution logic with:
    path_parts = resolve_path(target_path, pwd, machine)
    
    # Replace directory navigation with:
    success, current = navigate_to_path(machine, path_parts)
    if not success:
        print(Fore.RED + f"Directory '{target_path}' not found")
        return pwd
    
    # Check if piping to another command
    is_pipe_source = os.environ.get("IS_PIPE_SOURCE", "0") == "1"
    
    # Helper function to filter hidden files
    def should_display(name):
        if show_hidden:
            return True
        return not name.startswith(".")
    
    # Handle recursive listing
    if recursive:
        files_list = []
        
        def list_recursive(dir_content, current_path):
            """Recursively list directory contents."""
            if not isinstance(dir_content, dict):
                return
                
            for name, content in sorted(dir_content.items()):
                if not should_display(name):
                    continue
                    
                full_path = f"{current_path}/{name}" if current_path else name
                
                if isinstance(content, dict):
                    # It's a directory - recurse into it
                    list_recursive(content, full_path)
                else:
                    # It's a file - add to results
                    files_list.append(full_path)
        
        # Start recursive listing
        list_recursive(current, "/" + "/".join(path_parts) if path_parts else "")
        
        # Display results
        if files_list:
            for file_path in sorted(files_list):
                if is_pipe_source:
                    # For piping, just output the file names without colors or formatting
                    file_name = file_path.split('/')[-1]
                    print(file_name)
                else:
                    print(Fore.YELLOW + file_path)
        else:
            if not is_pipe_source:
                print(Fore.YELLOW + "No files found")
    else:
        # Standard non-recursive listing
        if isinstance(current, dict):
            directories = [key for key in current.keys() if isinstance(current[key], dict) and should_display(key)]
            files = [key for key in current.keys() if isinstance(current[key], str) and should_display(key)]
            all_items = sorted(directories + files)
            
            if all_items:
                for item in all_items:
                    if is_pipe_source:
                        # For piping, just output the names without colors
                        print(item)
                    else:
                        print(Fore.YELLOW + item)
            else:
                if not is_pipe_source:
                    print(Fore.YELLOW + "Directory is empty")
        else:
            print(Fore.RED + f"'{target_path}' is not a directory")
    
    return pwd

def help():
    print("Usage: ls [options] [directory] - Lists the contents of the specified directory.")
    print("Options:")
    print("  -r, --recursive    List subdirectories recursively")
    print("  -a, --all          Show hidden files (files starting with .)")