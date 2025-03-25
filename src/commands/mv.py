from colorama import Fore
import os
import json
from utils.utils import load_machine, check_path, path_to_safe_filename
from utils.logger import Logger

def execute(args, pwd, machine_name):
    """Move a file or directory from source to destination."""
    # Load the machine's file system
    machine_data = load_machine(machine_name)
    machine = machine_data["file_system"]

    # Check for valid arguments
    args = [part for part in args if part != " "]
    if len(args) < 2:
        print(Fore.RED + "Usage: mv [source] [destination]")
        return pwd

    source = args[0]
    destination = args[1]
    
    # Parse source path
    if source.startswith('/'):
        # Absolute path
        source_parts = [part for part in source.split('/') if part != ""]
    else:
        # Relative path
        pwd_parts = [part for part in pwd.split('/') if part != ""]
        source_parts = pwd_parts.copy()
        for part in source.split('/'):
            if part == "..":
                if source_parts:
                    source_parts.pop()
            elif part and part != ".":
                source_parts.append(part)
    
    # Parse destination path
    if destination.startswith('/'):
        # Absolute path
        dest_parts = [part for part in destination.split('/') if part != ""]
    else:
        # Relative path
        pwd_parts = [part for part in pwd.split('/') if part != ""]
        dest_parts = pwd_parts.copy()
        for part in destination.split('/'):
            if part == "..":
                if dest_parts:
                    dest_parts.pop()
            elif part and part != ".":
                dest_parts.append(part)
    
    # Check if source exists
    source_parent_parts = source_parts[:-1]
    source_name = source_parts[-1] if source_parts else ""
    
    source_parent = machine
    for part in source_parent_parts:
        if part in source_parent and isinstance(source_parent[part], dict):
            source_parent = source_parent[part]
        else:
            print(Fore.RED + f"Source path '{source}' not found")
            return pwd
    
    if source_name not in source_parent:
        print(Fore.RED + f"Source '{source_name}' not found")
        return pwd
    
    # Determine if destination is a directory or a file
    is_rename = False
    dest_parent_parts = dest_parts.copy()
    dest_name = None
    
    # Check if destination exists and is a directory
    dest_target = check_path(machine, dest_parts)
    if dest_target is not None and isinstance(dest_target, dict):
        # Destination exists and is a directory - we'll move into it
        dest_name = source_name
    else:
        # Destination might be a path with a new filename
        dest_name = dest_parts[-1] if dest_parts else ""
        dest_parent_parts = dest_parts[:-1]
        is_rename = True
    
    # Check if destination parent path exists
    dest_parent = machine
    for part in dest_parent_parts:
        if part in dest_parent and isinstance(dest_parent[part], dict):
            dest_parent = dest_parent[part]
        else:
            print(Fore.RED + f"Destination path '{destination}' not valid")
            return pwd
    
    # Check if file already exists at destination
    if dest_name in dest_parent and not is_rename:
        print(Fore.RED + f"'{dest_name}' already exists at destination")
        return pwd
    
    # Get the source content
    source_content = source_parent[source_name]
    
    # Handle directories
    if isinstance(source_content, dict):
        # Move the directory structure
        dest_parent[dest_name] = source_content
        # Remove from source
        del source_parent[source_name]
        
        # Log the move
        source_path = "/" + "/".join(source_parts)
        dest_path = "/" + "/".join(dest_parent_parts) + "/" + dest_name
        logger = Logger(machine_name)
        logger.log_file_activity(machine_data["meta_data"]["username"], 
                                source_path + " -> " + dest_path, "MOVE")
    else:
        # Handle files - need to rename physical file if needed
        try:
            # Physical paths
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
            
            # Get current physical path
            source_physical_path = source_content
            
            # Check if we need to create a new physical file (for renaming)
            if is_rename or dest_parent is not source_parent:
                # Calculate paths
                dest_virtual_path = "/" + "/".join(dest_parent_parts)
                safe_filename = path_to_safe_filename(dest_virtual_path, dest_name)
                dest_physical_path = f"src/machines/{machine_name}/files/{safe_filename}"
                
                # Copy the file content
                try:
                    with open(source_physical_path, 'r') as src_file:
                        content = src_file.read()
                    
                    # Ensure the destination directory exists
                    os.makedirs(os.path.join(project_root, "src", "machines", 
                              machine_name, "files"), exist_ok=True)
                    
                    with open(os.path.join(project_root, dest_physical_path), 'w') as dest_file:
                        dest_file.write(content)
                    
                    # Add to the destination
                    dest_parent[dest_name] = dest_physical_path
                    
                    # Delete the original physical file if it exists and is different from destination
                    if os.path.exists(os.path.join(project_root, source_physical_path)) and source_physical_path != dest_physical_path:
                        try:
                            os.remove(os.path.join(project_root, source_physical_path))
                        except Exception as e:
                            print(Fore.YELLOW + f"Warning: Could not delete original file: {str(e)}")
                    
                except Exception as e:
                    print(Fore.RED + f"Error moving file: {str(e)}")
                    return pwd
            else:
                # Same location, just update the reference
                dest_parent[dest_name] = source_content
            
            # Remove from source
            del source_parent[source_name]
            
            # Log the move
            source_path = "/" + "/".join(source_parts)
            dest_path = "/" + "/".join(dest_parent_parts) + "/" + dest_name
            logger = Logger(machine_name)
            logger.log_file_activity(machine_data["meta_data"]["username"], 
                                   source_path + " -> " + dest_path, "MOVE")
            
        except Exception as e:
            print(Fore.RED + f"Error moving file: {str(e)}")
            return pwd
    
    # Save the updated file system
    machine_file_path = os.path.join(project_root, "src", "machines", 
                                    machine_name, f"{machine_name}.json")
    with open(machine_file_path, 'w') as f:
        json.dump(machine_data, f, indent=4)
    
    return pwd

def help():
    print("Usage: mv [source] [destination] - Moves a file or directory to a new location or renames it.")