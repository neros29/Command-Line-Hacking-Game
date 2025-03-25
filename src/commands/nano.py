import os
import curses
from colorama import Fore, Style
from utils.utils import load_machine, check_path
import json
from utils.logger import Logger

def execute(args, pwd, machine_name):
    """Implements a simple nano-like text editor"""
    if len(args) < 1:
        print(Fore.RED + "Usage: nano [file]")
        return pwd

    file_name = args[0]
    machine_data = load_machine(machine_name)
    file_system = machine_data["file_system"]
    
    # Determine if file path is absolute or relative
    if file_name.startswith('/'):
        # Absolute path
        path_parts = [part for part in file_name.split('/') if part != ""]
        working_path = '/' + '/'.join(path_parts[:-1]) if len(path_parts) > 1 else '/'
        file_name = path_parts[-1] if path_parts else ""
    else:
        # Relative path
        path_parts = [part for part in pwd.split('/') if part != ""]
        working_path = pwd
    
    # Get current directory in file system
    current = file_system
    for directory in path_parts:
        if directory == "":
            continue
        if isinstance(current, dict) and directory in current:
            current = current[directory]
        else:
            print(Fore.RED + f"Directory {directory} not found")
            return pwd
    
    file_content = ""
    is_new_file = False
    
    # Check if file exists
    if file_name in current:
        if isinstance(current[file_name], str):
            # It's a file path
            try:
                file_path = current[file_name]
                with open(file_path, 'r') as f:
                    file_content = f.read()
            except FileNotFoundError:
                print(Fore.YELLOW + f"New file: {file_name}")
                is_new_file = True
        else:
            print(Fore.RED + f"{file_name} is a directory")
            return pwd
    else:
        print(Fore.YELLOW + f"New file: {file_name}")
        is_new_file = True
    
    # Initialize curses for text editing
    edited_content = run_editor(file_content)
    
    if edited_content is None:  # User canceled editing
        return pwd
    
    # Save file
    try:
        # Create physical file with better path handling
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        os_path = os.path.join(project_root, "src", "machines", machine_name, "files")
        os.makedirs(os_path, exist_ok=True)
        
        def path_to_safe_filename(virtual_path, filename):
            """Convert a virtual path to a safe physical filename"""
            # Replace slashes with double underscores to create a unique filename
            path_encoded = virtual_path.replace('/', '__DIR__').replace('\\', '__DIR__')
            # Remove the leading __DIR__ if it exists
            if path_encoded.startswith('__DIR__'):
                path_encoded = path_encoded[7:]
            # Handle empty path
            if not path_encoded:
                return filename
            return f"{path_encoded}__DIR__{filename}"
        
        # Create the physical file path with the directory-encoded filename
        safe_filename = path_to_safe_filename(working_path, file_name)
        real_file_path = os.path.join(os_path, safe_filename)
        
        with open(real_file_path, 'w') as f:
            f.write(edited_content)
        
        # Use a relative path in the virtual file system for better portability
        current[file_name] = f"src/machines/{machine_name}/files/{safe_filename}"
        
        # Save machine data
        machine_file_path = os.path.join(project_root, "src", "machines", machine_name, f"{machine_name}.json")
        with open(machine_file_path, 'w') as f:
            json.dump(machine_data, f, indent=4)
        
        print(Fore.GREEN + f"File {file_name} saved")
        logger = Logger(machine_name)
        logger.log_file_activity(machine_data["meta_data"]["username"], f"{working_path}/{file_name}", "EDIT")
    except Exception as e:
        print(Fore.RED + f"Error saving file: {str(e)}")
    
    return pwd

def run_editor(initial_content):
    """Run the nano-like editor using curses"""
    def editor(stdscr):
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
        
        # Initialize content as list of lines
        content = initial_content.split('\n')
        if not content:
            content = [""]
        
        # Initial cursor position
        y, x = 0, 0
        
        # Window height and width
        height, width = stdscr.getmaxyx()
        
        # Offset for scrolling
        offset = 0
        
        # Status messages
        status = "CTRL+X: Exit | CTRL+O: Save"
        saved_msg = ""
        
        while True:
            stdscr.clear()
            
            # Display content with line numbers
            for i in range(min(height - 2, len(content) - offset)):
                line = content[i + offset]
                if i + offset == y:
                    # Highlight current line
                    stdscr.addstr(i, 0, f"{i+offset+1:<3} ", curses.color_pair(1))
                    stdscr.addstr(i, 4, line[:width-5], curses.color_pair(1))
                else:
                    stdscr.addstr(i, 0, f"{i+offset+1:<3} ", curses.A_DIM)
                    stdscr.addstr(i, 4, line[:width-5])
            
            # Display status bar
            stdscr.addstr(height-2, 0, status, curses.color_pair(2) | curses.A_BOLD)
            if saved_msg:
                stdscr.addstr(height-1, 0, saved_msg)
            
            # Position cursor
            try:
                stdscr.move(y - offset, min(x + 4, width - 1))
            except curses.error:
                pass
            
            # Get input
            key = stdscr.getch()
            
            if key == curses.KEY_UP:
                if y > 0:
                    y -= 1
                    x = min(x, len(content[y]))
                    if y < offset:
                        offset = y
            elif key == curses.KEY_DOWN:
                if y < len(content) - 1:
                    y += 1
                    x = min(x, len(content[y]))
                    if y >= offset + height - 2:
                        offset = y - height + 3
            elif key == curses.KEY_LEFT:
                if x > 0:
                    x -= 1
                elif y > 0:
                    y -= 1
                    x = len(content[y])
            elif key == curses.KEY_RIGHT:
                if x < len(content[y]):
                    x += 1
                elif y < len(content) - 1:
                    y += 1
                    x = 0
            elif key == 10:  # Enter
                content.insert(y + 1, content[y][x:])
                content[y] = content[y][:x]
                y += 1
                x = 0
                if y >= offset + height - 2:
                    offset += 1
            elif key == 8 or key == 127 or key == curses.KEY_BACKSPACE:  # Backspace
                if x > 0:
                    content[y] = content[y][:x-1] + content[y][x:]
                    x -= 1
                elif y > 0:
                    x = len(content[y-1])
                    content[y-1] += content[y]
                    content.pop(y)
                    y -= 1
            elif key == curses.KEY_DC:  # Delete key
                if x < len(content[y]):
                    content[y] = content[y][:x] + content[y][x+1:]
                elif y < len(content) - 1:
                    # Delete at end of line - join with next line
                    content[y] += content[y+1]
                    content.pop(y+1)
            elif key == 24:  # Ctrl+X - Exit
                if saved_msg == "":  # No save has occurred
                    # Check if content has changed
                    if '\n'.join(content) != initial_content:
                        # Display save prompt
                        stdscr.addstr(height-1, 0, "Save modified buffer? (y/n) ", curses.A_BOLD)
                        stdscr.refresh()
                        while True:
                            save_response = stdscr.getch()
                            if save_response in [121, 89]:  # 'y' or 'Y'
                                saved_msg = "File saved"
                                return '\n'.join(content)
                            elif save_response in [110, 78]:  # 'n' or 'N'
                                return initial_content
                            # Ignore other keys, keep waiting for y/n
                    else:
                        # No changes, just exit
                        return initial_content
                else:
                    # Already saved during this session
                    return '\n'.join(content)
            elif key == 15:  # Ctrl+O - Save
                saved_msg = "File saved"
                return '\n'.join(content)
            elif key == 27:  # Escape key
                saved_msg = "Canceled"
                return None
            elif 32 <= key <= 126:  # Printable characters
                content[y] = content[y][:x] + chr(key) + content[y][x:]
                x += 1
    
    try:
        return curses.wrapper(editor)
    except Exception as e:
        print(f"Editor error: {str(e)}")
        return initial_content

def help():
    print("Usage: nano [file] - Opens the specified file in the nano text editor.")