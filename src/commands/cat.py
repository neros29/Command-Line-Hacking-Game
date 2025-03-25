from colorama import Fore
from utils.utils import load_machine
from src.utils.file_utils import resolve_path, read_file
import os

def execute(args, pwd, machine_name):
    """View the contents of a file."""
    if len(args) < 1:
        print(Fore.RED + "Usage: cat [file]")
        return pwd

    machine = load_machine(machine_name)
    
    file = args[0]
    
    # Resolve the path
    path_parts = resolve_path(file, pwd, machine["file_system"])
    
    # Read the file
    success, content = read_file(machine, path_parts)
    
    if not success:
        print(Fore.RED + content)  # Display the error message
        return pwd
    
    # Check if this command's output will be piped
    is_pipe_source = os.environ.get("IS_PIPE_SOURCE", "0") == "1"
    
    if is_pipe_source:
        # Just print the raw text for piping
        print(content, end="")
    else:
        # Pretty print with colors for direct viewing
        for line in content.split("\n"):
            print(Fore.GREEN + line)
    
    return pwd

def help():
    print("Usage: cat [file] Displays the contents of a file.")
