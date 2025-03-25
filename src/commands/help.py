from colorama import Fore
import os
import sys
import importlib

def execute(args, pwd, machine_name):
    """Display help information about commands with support for piping."""
    is_pipe_source = os.environ.get("IS_PIPE_SOURCE", "0") == "1"
    
    # Import modules dynamically
    from src.main import modules
    
    # Get the list of available commands
    commands_list = []
    for command in modules:
        commands_list.append(command)
    
    # Determine if we're showing help for a specific command
    specific_command = None
    if len(args) >= 1:
        specific_command = args[0]
    
    # Format output with or without colors based on whether we're piping
    if specific_command:
        if specific_command in commands_list:
            if not is_pipe_source:
                print(Fore.RESET + f"Help for {specific_command}:")
            
            module = modules[specific_command]
            if hasattr(module, 'help'):
                # Capture the output to handle pipe formatting
                original_stdout = sys.stdout
                output = []
                
                try:
                    # We'll use our own output capture instead of directly calling help()
                    # to better control the format for piping
                    if is_pipe_source:
                        # When piping, we need to capture and print without colors
                        from io import StringIO
                        temp_stdout = StringIO()
                        sys.stdout = temp_stdout
                        module.help()
                        help_output = temp_stdout.getvalue()
                        # Remove color codes for piped output
                        help_output = help_output.replace(Fore.RED, "").replace(Fore.GREEN, "")
                        help_output = help_output.replace(Fore.YELLOW, "").replace(Fore.BLUE, "")
                        help_output = help_output.replace(Fore.CYAN, "").replace(Fore.MAGENTA, "")
                        help_output = help_output.replace(Fore.RESET, "")
                        print(help_output, end="")
                    else:
                        # Normal display with colors
                        module.help()
                finally:
                    sys.stdout = original_stdout
            else:
                if is_pipe_source:
                    print(f"No help available for {specific_command}")
                else:
                    print(Fore.RED + f"No help available for {specific_command}")
        else:
            if is_pipe_source:
                print(f"Command '{specific_command}' not found")
            else:
                print(Fore.RED + f"Command '{specific_command}' not found")
    else:
        # Display help for all commands
        if not is_pipe_source:
            print(Fore.RESET + "For more information on a specific command, type HELP command-name")
        
        for command in sorted(commands_list):
            if is_pipe_source:
                # Basic format for piping
                output_line = command.ljust(15)
                module = modules[command]
                if hasattr(module, 'help'):
                    # Get the first line of help text
                    from io import StringIO
                    temp_stdout = StringIO()
                    old_stdout = sys.stdout
                    sys.stdout = temp_stdout
                    module.help()
                    help_text = temp_stdout.getvalue().strip().split('\n')[0]
                    sys.stdout = old_stdout
                    
                    # Remove color codes and command usage info
                    help_text = help_text.replace(Fore.RED, "").replace(Fore.GREEN, "")
                    help_text = help_text.replace(Fore.YELLOW, "").replace(Fore.BLUE, "")
                    help_text = help_text.replace(Fore.CYAN, "").replace(Fore.MAGENTA, "")
                    help_text = help_text.replace(Fore.RESET, "")
                    
                    # Remove "Usage: command" prefix if present
                    if "Usage:" in help_text:
                        help_text = help_text.split("-", 1)[-1].strip()
                    
                    output_line += help_text
                else:
                    output_line += "No help available"
                print(output_line)
            else:
                # Pretty format with colors for display
                spaces = 15 - len(command)
                print(f"{command}{' ' * spaces}", end="")
                module = modules[command]
                if hasattr(module, 'help'):
                    module.help()
                else:
                    print(Fore.RED + "No help available")
        
        if not is_pipe_source:
            print("\nFor more information on tools see the command-line reference in the online help.")
    
    return pwd

def help():
    print("Usage: help [command] - Displays help information for commands")