from colorama import Fore
from src.utils.utils import load_machine, check_path
from src.utils.file_utils import resolve_path, check_file_exists

def execute(args, pwd, machine_name):
    machine = load_machine(machine_name)
    machine = machine["file_system"]

    args = [part for part in args if part != " "]
    if len(args) == 0:
        print(Fore.YELLOW + pwd)
        return pwd
    new_dir = args[0]
    
    new_dir = "".join(new_dir)
    new_dir_parts = [part for part in new_dir.split("/") if part != ""]
    
    if new_dir.startswith("/"):
        # Absolute path
        path_parts = new_dir_parts
    else:
        # Relative path - more robust handling of ".." sequences
        path_parts = [part for part in pwd.split('/') if part != ""]
        
        for part in new_dir_parts:
            if part == "..":
                if path_parts:  # Only pop if there's something to pop
                    path_parts.pop()
                # If we're at root, .. has no effect
            elif part == ".":
                continue  # Current directory, do nothing
            else:
                path_parts.append(part)
    
    # Ensure we always have a path (even if empty for root)
    if not path_parts:
        return "/"
        
    path_parts = resolve_path(new_dir, pwd, machine)
    exists, is_directory, item = check_file_exists(machine, path_parts)

    if not exists:
        print(Fore.RED + f"Directory {new_dir} not found")
        return pwd
        
    if not is_directory:
        print(Fore.RED + f"{new_dir} is not a directory")
        return pwd

    return "/" + "/".join(path_parts) if path_parts else "/"

def help():
    print("Usage: cd [directory] Changes the current directory to the specified directory.")
    
if __name__ == "__main__":    
    current_dir = execute("local", ["Desktop"], pwd="/home", machine_name="local_machine")
    print(f"Current directory: {current_dir}")