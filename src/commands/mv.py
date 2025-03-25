from colorama import Fore
import os
import json
from utils.utils import load_machine, check_path, path_to_safe_filename, save_machine
from utils.file_utils import resolve_path, check_file_exists, navigate_to_path
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
    src_parts = resolve_path(source, pwd, machine)
    exists_src, is_dir_src, src_item = check_file_exists(machine, src_parts)

    if not exists_src:
        print(Fore.RED + f"Source '{source}' not found")
        return pwd
    
    # Get source parent directory and filename
    src_parent_parts = src_parts[:-1]
    src_filename = src_parts[-1]
    
    # Navigate to source parent directory
    success_src, src_parent = navigate_to_path(machine, src_parent_parts)
    if not success_src:
        print(Fore.RED + f"Source parent directory not found")
        return pwd
    
    # Parse destination path
    dest_parts = resolve_path(destination, pwd, machine)
    exists_dest, is_dir_dest, dest_item = check_file_exists(machine, dest_parts)
    
    # Determine if destination is a directory or a file
    is_rename = False
    dest_name = None
    
    if exists_dest and is_dir_dest:
        # Destination exists and is a directory - we'll move into it
        dest_name = src_parts[-1]
    else:
        # Destination might be a path with a new filename
        dest_name = dest_parts[-1] if dest_parts else ""
        is_rename = True
    
    # Check if destination parent path exists
    dest_parent_parts = dest_parts[:-1] if is_rename else dest_parts
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
    source_content = src_item
    
    # Handle directories
    if is_dir_src:
        # Move the directory structure
        dest_parent[dest_name] = source_content
        # Remove from source parent
        del src_parent[src_filename]
        
        # Log the move
        source_path = "/" + "/".join(src_parts)
        dest_path = "/" + "/".join(dest_parent_parts) + "/" + dest_name
        logger = Logger(machine_name)
        
        # Get current user - use current_user from meta_data if it exists, otherwise use a default
        current_user = machine_data["meta_data"].get("current_user", "system")
        logger.log_file_activity(current_user, source_path + " -> " + dest_path, "MOVE")
    else:
        # Handle files - need to rename physical file if needed
        try:
            # Physical paths
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
            
            # Get current physical path
            source_physical_path = source_content
            
            # Check if we need to create a new physical file (for renaming)
            if is_rename or dest_parent is not src_parent:
                # Calculate paths
                dest_virtual_path = "/" + "/".join(dest_parent_parts)
                safe_filename = path_to_safe_filename(dest_virtual_path, dest_name)
                dest_physical_path = f"src/machines/{machine_name}/files/{safe_filename}"
                
                # Copy the file content
                with open(os.path.join(project_root, source_physical_path), 'r') as src_file:
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
                
                # Remove from source parent
                del src_parent[src_filename]
            else:
                # Same location, just update the reference
                # Calculate destination path for same directory rename
                dest_virtual_path = "/" + "/".join(dest_parent_parts)
                safe_filename = path_to_safe_filename(dest_virtual_path, dest_name)
                dest_physical_path = f"src/machines/{machine_name}/files/{safe_filename}"
                
                # Copy the file content
                with open(os.path.join(project_root, source_physical_path), 'r') as src_file:
                    content = src_file.read()
                
                # Ensure the destination directory exists
                os.makedirs(os.path.join(project_root, "src", "machines", 
                          machine_name, "files"), exist_ok=True)
                
                with open(os.path.join(project_root, dest_physical_path), 'w') as dest_file:
                    dest_file.write(content)
                
                # Add to the destination
                dest_parent[dest_name] = dest_physical_path
                
                # Delete the original physical file if it exists and is different
                if os.path.exists(os.path.join(project_root, source_physical_path)) and source_physical_path != dest_physical_path:
                    try:
                        os.remove(os.path.join(project_root, source_physical_path))
                    except Exception as e:
                        print(Fore.YELLOW + f"Warning: Could not delete original file: {str(e)}")
                
                # Remove from source parent
                del src_parent[src_filename]
            
            # Log the move
            source_path = "/" + "/".join(src_parts)
            dest_path = "/" + "/".join(dest_parent_parts) + "/" + dest_name
            logger = Logger(machine_name)
            
            # Get current user - use current_user from meta_data if it exists, otherwise use a default
            current_user = machine_data["meta_data"].get("current_user", "system")
            logger.log_file_activity(current_user, source_path + " -> " + dest_path, "MOVE")
            
        except Exception as e:
            print(Fore.RED + f"Error moving file: {str(e)}")
            return pwd
    
    # Save the updated file system using the utility function
    save_machine(machine_name, machine_data)
    
    return pwd

def help():
    print("Usage: mv [source] [destination] - Moves a file or directory to a new location or renames it.")