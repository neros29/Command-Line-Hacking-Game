from colorama import Fore
import os

def execute(args, pwd, machine_name):
    """Echo text to the terminal, useful for piping."""
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