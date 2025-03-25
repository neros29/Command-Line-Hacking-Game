from colorama import Fore
from src.utils.utils import load_machine, check_path

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
        
    target_path = check_path(machine, path_parts)
    
    if target_path is not None:
        if isinstance(target_path, dict):  # Check if the target path is a directory
            return "/" + "/".join(path_parts)
        else:
            print(Fore.RED + f"{new_dir} is not a directory")
            return pwd
    else:
        print(Fore.RED + f"Directory {new_dir} not found")
        return pwd

def help():
    print("Usage: cd [directory] Changes the current directory to the specified directory.")
    
if __name__ == "__main__":    
    current_dir = execute("local", ["Desktop"], pwd="/home", machine_name="local_machine")
    print(f"Current directory: {current_dir}")