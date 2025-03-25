import os
from utils.utils import load_machine, check_path
import json
from colorama import Fore
from utils.logger import Logger

def execute(args, pwd, machine_name):
    """Remove a file or directory"""
    # Load the machine's file system
    machine_data = load_machine(machine_name)
    machine = machine_data["file_system"]

    # Remove any empty arguments
    args = [part for part in args if part != " "]
    if len(args) == 0:
        print("Usage: rm [file/directory]")
        return pwd

    target = args[0]
    target_parts = [part for part in target.split("/") if part != ""]

    if target.startswith("/"):
        # Absolute path
        path_parts = target_parts
    else:
        # Relative path
        path_parts = pwd.split('/')
        path_parts = [part for part in path_parts if part != ""]
        for part in target_parts:
            if part == "..":
                if len(path_parts) > 0:
                    path_parts.pop()
            else:
                path_parts.append(part)

    # Check if the target path exists
    target_path = check_path(machine, path_parts)
    
    if target_path is None:
        print("File or directory not found")
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
        
        # Remove the file or directory
        if isinstance(current[path_parts[-1]], dict):
            # It's a directory
            if current[path_parts[-1]]:
                print("Directory is not empty")
                return pwd
            else:
                del current[path_parts[-1]]
                logger = Logger(machine_name)
                path_str = f"/{'/'.join(path_parts)}"
                logger.log_file_activity(machine_data["meta_data"]["username"], path_str, "DELETE")
        else:
            # It's a file
            file_path = current[path_parts[-1]]
            del current[path_parts[-1]]
            # Delete the actual file from the filesystem
            try:
                os.remove(file_path)
                logger = Logger(machine_name)
                path_str = f"/{'/'.join(path_parts)}"
                logger.log_file_activity(machine_data["meta_data"]["username"], path_str, "DELETE")
            except FileNotFoundError:
                print("File not found")
                return pwd
            except Exception as e:
                print(f"An error occurred: {e}")
                return pwd

        # Save the updated machine structure back to the JSON file
        machine_file_path = f"src/machines/{machine_name}/{machine_name}.json"
        with open(machine_file_path, "w") as machine_file:
            machine_data["file_system"] = machine
            json.dump(machine_data, machine_file, indent=4)

        return pwd

def help():
    print("Usage: rm [file/directory] Removes the specified file or directory.")