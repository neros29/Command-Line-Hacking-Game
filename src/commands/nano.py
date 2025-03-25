import os
import curses
from colorama import Fore, Style
from utils.utils import load_machine
import json
from utils.logger import Logger
from src.utils.file_utils import resolve_path, write_to_file, check_file_exists, read_file

def execute(args, pwd, machine_name):
    """Implements a simple nano-like text editor"""
    if len(args) < 1:
        print(Fore.RED + "Usage: nano [file]")
        return pwd

    file_path = args[0]
    machine_data = load_machine(machine_name)
    file_system = machine_data["file_system"]
    current_user = machine_data["meta_data"].get("current_user", "system")
    
    # Resolve the file path
    path_parts = resolve_path(file_path, pwd, file_system)
    if not path_parts:
        print(Fore.RED + "Invalid file path")
        return pwd
    
    filename = path_parts[-1]
    parent_path = path_parts[:-1]
    
    # Navigate to the parent directory
    current = file_system
    for directory in parent_path:
        if isinstance(current, dict) and directory in current:
            current = current[directory]
        else:
            print(Fore.RED + f"Directory {'/'.join(parent_path)} not found")
            return pwd
    
    path_parts = resolve_path(file_path, pwd, machine_data["file_system"])
    exists, is_directory, item = check_file_exists(machine_data["file_system"], path_parts)

    if exists and is_directory:
        print(Fore.RED + f"{file_path} is a directory")
        return pwd
        
    initial_content = ""
    if exists:
        success, content = read_file(machine_data, path_parts)
        if success:
            initial_content = content
    
    # Initialize curses for text editing
    edited_content = run_editor(initial_content)
    
    if edited_content is None:  # User canceled editing
        return pwd
    
    # Write the file using the shared utility
    working_path = '/' + '/'.join(parent_path) if parent_path else '/'
    if write_to_file(machine_data, path_parts, edited_content):
        print(Fore.GREEN + f"Saved {file_path}")
        # Log the file activity
        logger = Logger(machine_name)
        logger.log_file_activity(current_user, f"{working_path}/{filename}", "EDIT")
    else:
        print(Fore.RED + f"Failed to save {file_path}")
    
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