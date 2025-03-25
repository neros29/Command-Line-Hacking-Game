from colorama import Fore
import os
from src.utils.utils import load_machine
from src.utils.file_utils import resolve_path, write_to_file


def execute(args, pwd, machine_name):
    """
    Echo command implementation with redirection support
    """
    # Check for redirection
    if ">" in args:
        redirect_index = args.index(">")
        if redirect_index < len(args) - 1:
            # Get text before redirection and filename after
            text = " ".join(args[:redirect_index])
            output_file = args[redirect_index + 1]
            
            # Process special characters in the text
            text = text.replace("\\n", "\n").replace("\\t", "\t")
            
            # If quoted, remove the quotes
            if text and text[0] == text[-1] and text[0] in ['"', "'"]:
                text = text[1:-1]
            
            # Write to file using file system functions
            machine = load_machine(machine_name)
            resolved_path = resolve_path(output_file, pwd, machine["file_system"])
            
            # Create the file with the text content - write_to_file now saves the machine data
            if write_to_file(machine, resolved_path, text):
                pass  # File written successfully
            else:
                print(Fore.RED + f"Error: Could not write to {output_file}")
        else:
            print(Fore.RED + "Error: No output file specified for redirection")
    else:
        # Regular echo without redirection
        # Check if this command's output will be piped
        is_pipe_source = os.environ.get("IS_PIPE_SOURCE", "0") == "1"
        
        # Join all arguments as a string to echo
        message = " ".join(args)
        
        # Process special characters in the message
        message = message.replace("\\n", "\n").replace("\\t", "\t")
        
        # If quoted, remove the quotes
        if message and message[0] == message[-1] and message[0] in ['"', "'"]:
            message = message[1:-1]
        
        # Print without colors if piping, with colors otherwise
        if is_pipe_source:
            print(message, end="")
        else:
            print(Fore.GREEN + message)
    
    return pwd

def help():
    print("Usage: echo [text] - Displays text in the terminal. Can be used with pipes.")
    print("       echo [text] > [file] - Redirects output to a file.")