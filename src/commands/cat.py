from colorama import Fore
from utils.utils import load_machine
import os

# Add this function near the top of the file
def safe_filename_to_path(safe_filename):
    """Convert a safe filename back to a virtual path"""
    # Handle both old-style and new-style filenames
    if '__DIR__' in safe_filename:
        parts = safe_filename.split('__DIR__')
        filename = parts[-1]
        path = '/'.join(parts[:-1])
        return path, filename
    return None, safe_filename

def execute(args, pwd, machine_name):
    """View the contents of a file."""
    if len(args) < 1:
        print(Fore.RED + "Usage: cat [file]")
        return pwd

    machine = load_machine(machine_name)
    file_system = machine["file_system"]
    
    file = args[0]
    
    # Handle both absolute and relative paths
    if file.startswith('/'):
        path_parts = [part for part in file.split('/') if part]
    else:
        pwd_parts = [part for part in pwd.split('/') if part]
        path_parts = pwd_parts + [part for part in file.split('/') if part]

    try:
        # Navigate to the file in the virtual file system
        current = file_system
        for part in path_parts[:-1]:  # Navigate to parent directory
            if part in current:
                current = current[part]
            else:
                print(Fore.RED + f"Directory {part} not found")
                return pwd
            
        if path_parts[-1] not in current:
            print(Fore.RED + f"File {file} not found")
            return pwd
            
        file_content = current[path_parts[-1]]
        
        if isinstance(file_content, dict):
            print(Fore.RED + f"{file} is a directory, not a file")
            return pwd
            
        if file_content == "command":
            print(Fore.RED + f"You are not authorized to view the contents of {file}")
            return pwd
            
        # Read and display the actual file content
        try:
            with open(file_content, "r") as r:
                text = r.read()
                # Check if this command's output will be piped
                is_pipe_source = os.environ.get("IS_PIPE_SOURCE", "0") == "1"
                
                if is_pipe_source:
                    # Just print the raw text for piping
                    print(text, end="")
                else:
                    # Pretty print with colors for direct viewing
                    for line in text.split("\n"):
                        print(Fore.GREEN + line)
        except FileNotFoundError:
            print(Fore.RED + f"Physical file {file_content} not found")
            
    except KeyError:
        print(Fore.RED + f"File {file} not found in the specified path")
    except Exception as e:
        print(Fore.RED + f"Error reading file: {str(e)}")
        
    return pwd

def help():
    print("Usage: cat [file] Displays the contents of a file.")
