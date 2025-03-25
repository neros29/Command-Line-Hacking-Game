from colorama import Fore, Back, Style
import os
import re
import json
from utils.utils import load_machine, check_path
from utils.file_utils import check_file_access,  resolve_path, check_file_exists, navigate_to_path, read_file

def execute(args, pwd, machine_name):
    """Search for patterns in files or piped input."""
    # Check if input is coming from a pipe
    is_piped = os.environ.get("IS_PIPED", "0") == "1"
    is_pipe_source = os.environ.get("IS_PIPE_SOURCE", "0") == "1"
    
    # Parse options first
    recursive = False
    case_sensitive = True
    line_numbers = False
    
    i = 0
    while i < len(args) and args[i].startswith('-'):
        if args[i] in ['-r', '--recursive']:
            recursive = True
        elif args[i] in ['-i', '--ignore-case']:
            case_sensitive = False
        elif args[i] in ['-n', '--line-number']:
            line_numbers = True
        elif args[i] == '-':
            # Not an option
            break
        i += 1
        
    if i >= len(args):
        print(Fore.RED + "No pattern specified.")
        return pwd
    
    pattern = args[i]
    i += 1
    
    # Create regex pattern
    try:
        if case_sensitive:
            regex = re.compile(pattern)
        else:
            regex = re.compile(pattern, re.IGNORECASE)
    except re.error:
        print(Fore.RED + f"Invalid regular expression: {pattern}")
        return pwd
    
    # Create a list to collect all matching lines for piping
    all_matching_lines = []
    
    # Handle piped input if present
    if is_piped:
        piped_input = os.environ.get("PIPED_INPUT", "")
        lines = piped_input.split('\n')
        
        # Process each line from piped input
        for line_num, line in enumerate(lines, 1):
            if line and regex.search(line):  # Only process non-empty lines
                output_line = ""
                
                # Add line numbers if requested
                if line_numbers:
                    if is_pipe_source:
                        output_line += f"{line_num}: "
                    else:
                        output_line += f"{Fore.YELLOW}{line_num}{Fore.RESET}: "
                
                # Format output based on whether we're piping to another command
                if is_pipe_source:
                    # Plain output for piping
                    output_line += line
                    all_matching_lines.append(output_line)
                else:
                    # Highlighted output for display
                    last_end = 0
                    highlighted_line = ""
                    
                    for match in regex.finditer(line):
                        start, end = match.span()
                        highlighted_line += line[last_end:start]
                        highlighted_line += f"{Fore.GREEN}{Back.BLACK}{Style.BRIGHT}{line[start:end]}{Style.RESET_ALL}"
                        last_end = end
                    
                    highlighted_line += line[last_end:]
                    print(output_line + highlighted_line)
        
        # If we're piping output to another command, update PIPED_INPUT
        if is_pipe_source:
            os.environ["PIPED_INPUT"] = "\n".join(all_matching_lines)
        
        return pwd
    
    # If not piped input, we need files to search
    if i >= len(args):
        print(Fore.RED + "No files specified.")
        return pwd
    
    file_patterns = args[i:]
    
    # Load machine data
    machine_data = load_machine(machine_name)
    file_system = machine_data["file_system"]
    
    # Process files
    matched_files = 0
    total_matches = 0
    
    def search_file(file_path, virtual_file_path):
        nonlocal matched_files, total_matches
        
        try:
            success, content = read_file(machine_data, file_path.split('/'))
            if not success:
                return
            
            lines = content.split('\n')
            file_matches = 0
            
            for line_num, line in enumerate(lines, 1):
                if regex.search(line):
                    file_matches += 1
                    total_matches += 1
                    
                    output_line = ""
                    
                    # If multiple files, show the filename
                    if len(file_patterns) > 1 or recursive:
                        if line_numbers:
                            if is_pipe_source:
                                output_line += f"{virtual_file_path}:{line_num}: "
                            else:
                                output_line += f"{Fore.CYAN}{virtual_file_path}{Fore.RESET}:{Fore.YELLOW}{line_num}{Fore.RESET}: "
                        else:
                            if is_pipe_source:
                                output_line += f"{virtual_file_path}: "
                            else:
                                output_line += f"{Fore.CYAN}{virtual_file_path}{Fore.RESET}: "
                    elif line_numbers:
                        if is_pipe_source:
                            output_line += f"{line_num}: "
                        else:
                            output_line += f"{Fore.YELLOW}{line_num}{Fore.RESET}: "
                    
                    # Format the line based on whether we're piping
                    if is_pipe_source:
                        # Plain output for piping
                        output_line += line
                        print(output_line)
                    else:
                        # Highlighted output for display
                        last_end = 0
                        highlighted_line = ""
                        
                        for match in regex.finditer(line):
                            start, end = match.span()
                            highlighted_line += line[last_end:start]
                            highlighted_line += f"{Fore.GREEN}{Back.BLACK}{Style.BRIGHT}{line[start:end]}{Style.RESET_ALL}"
                            last_end = end
                        
                        highlighted_line += line[last_end:]
                        print(output_line + highlighted_line)
            
            if file_matches > 0:
                matched_files += 1
                
        except Exception as e:
            print(Fore.RED + f"Error processing file {virtual_file_path}: {str(e)}")
    
    def process_path(base_path, virtual_path):
        path_parts = resolve_path(virtual_path, base_path, file_system)
        exists, is_directory, node = check_file_exists(file_system, path_parts)
        
        if not exists:
            print(Fore.RED + f"No such file or directory: {virtual_path}")
            return
        
        if is_directory:
            if recursive:
                # Use navigate_to_path for directory contents
                success, dir_contents = navigate_to_path(file_system, path_parts)
                if success:
                    for name, content in dir_contents.items():
                        new_virtual_path = os.path.join(virtual_path, name).replace('\\', '/')
                        process_path(base_path, new_virtual_path)
            else:
                print(Fore.RED + f"{virtual_path} is a directory")
        else:
            # Use read_file for file content
            success, content = read_file(machine_data, path_parts)
            if success:
                lines = content.split('\n')
                file_matches = 0
                
                for line_num, line in enumerate(lines, 1):
                    if regex.search(line):
                        file_matches += 1
                        total_matches += 1
                        
                        output_line = ""
                        
                        # If multiple files, show the filename
                        if len(file_patterns) > 1 or recursive:
                            if line_numbers:
                                if is_pipe_source:
                                    output_line += f"{virtual_path}:{line_num}: "
                                else:
                                    output_line += f"{Fore.CYAN}{virtual_path}{Fore.RESET}:{Fore.YELLOW}{line_num}{Fore.RESET}: "
                            else:
                                if is_pipe_source:
                                    output_line += f"{virtual_path}: "
                                else:
                                    output_line += f"{Fore.CYAN}{virtual_path}{Fore.RESET}: "
                        elif line_numbers:
                            if is_pipe_source:
                                output_line += f"{line_num}: "
                            else:
                                output_line += f"{Fore.YELLOW}{line_num}{Fore.RESET}: "
                        
                        # Format the line based on whether we're piping
                        if is_pipe_source:
                            # Plain output for piping - but collect instead of print
                            output_line += line
                            all_matching_lines.append(output_line)
                        else:
                            # Highlighted output for display
                            last_end = 0
                            highlighted_line = ""
                            
                            for match in regex.finditer(line):
                                start, end = match.span()
                                highlighted_line += line[last_end:start]
                                highlighted_line += f"{Fore.GREEN}{Back.BLACK}{Style.BRIGHT}{line[start:end]}{Style.RESET_ALL}"
                                last_end = end
                            
                            highlighted_line += line[last_end:]
                            print(output_line + highlighted_line)
                
                if file_matches > 0:
                    matched_files += 1
    
    # Process each file/directory pattern
    for file_pattern in file_patterns:
        # Handle absolute vs relative paths
        if file_pattern.startswith('/'):
            # Absolute path
            virtual_path = file_pattern
        else:
            # Relative path
            if pwd == '/':
                virtual_path = '/' + file_pattern
            else:
                virtual_path = pwd + '/' + file_pattern
        
        process_path(pwd, virtual_path)
    
    # Update PIPED_INPUT if this command is a pipe source
    if is_pipe_source:
        os.environ["PIPED_INPUT"] = "\n".join(all_matching_lines)
    
    # Print summary if multiple files were searched (only if not piping output)
    if (len(file_patterns) > 1 or recursive) and not is_pipe_source:
        print(f"\n{Fore.CYAN}Found {total_matches} matches in {matched_files} files{Fore.RESET}")
    
    return pwd

def help():
    print("Usage: grep [OPTIONS] PATTERN FILE... - Search for PATTERN in each FILE")
    print("       grep [OPTIONS] PATTERN         - Search for PATTERN in piped input")
    print("Options:")
    print("  -r, --recursive    Search directories recursively")
    print("  -i, --ignore-case  Ignore case distinctions in PATTERN")
    print("  -n, --line-number  Print line number with output lines")