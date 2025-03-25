import os
from utils.utils import load_machine, check_path
import json
from colorama import init, Fore
from utils.logger import Logger

def execute(args, pwd, machine_name):
    # Load the machine's file system
    machine_data = load_machine(machine_name)
    machine = machine_data["file_system"]
    current_user = machine_data["meta_data"].get("current_user", "system")

    """Create a new directory."""
    # Remove any empty arguments
    args = [part for part in args if part != " "]
    if len(args) == 0:
        print("Usage: mkdir [directory]")
        return pwd

    new_dir = args[0]
    new_dir = "".join(new_dir)
    new_dir_parts = [part for part in new_dir.split("/") if part != ""]

    if new_dir.startswith("/"):
        # Absolute path
        path_parts = new_dir_parts
    else:
        # Relative path
        path_parts = pwd.split('/')
        path_parts = [part for part in path_parts if part != ""]
        for part in new_dir_parts:
            if part == "..":
                if len(path_parts) > 0:
                    path_parts.pop()
            else:
                path_parts.append(part)

    # Check if the target path already exists
    target_path = check_path(machine, path_parts)
    
    if target_path is not None:
        print("Directory already exists")
        return pwd
    else:
        current = machine
        # Navigate to the target directory's parent
        for directory in path_parts[:-1]:
            if directory == "":
                continue
            if isinstance(current, dict) and directory in current:
                current = current[directory]  # Move into the next directory
            else:
                print("Directory not found")
                return pwd
        
        # Create the new directory
        current[path_parts[-1]] = {}

        # Add logger after successfully creating a directory
        logger = Logger(machine_name)
        path_str = f"/{'/'.join(path_parts)}"
        logger.log_file_activity(current_user, path_str, "CREATE_DIRECTORY")

        # Save the updated machine structure back to the JSON file
        machine_file_path = f"src/machines/{machine_name}/{machine_name}.json"
        with open(machine_file_path, "w") as machine_file:
            machine_data["file_system"] = machine
            json.dump(machine_data, machine_file, indent=4)

        return pwd

def help():
    print("Usage: mkdir [directory] Creates a new directory with the specified name.")
