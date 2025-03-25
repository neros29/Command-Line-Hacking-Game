from colorama import Fore, Style
import time
import random
import importlib
import getpass
from utils.utils import load_machine
from utils.logger import Logger
from utils.network_monitor import log_remote_event
from utils.password_manager import verify_password

def execute(args, pwd, machine_name):
    """Simulate an SSH connection to a target machine with password authentication and up to 5 attempts."""
    if len(args) < 1:
        print(Fore.RED + "Usage: ssh [IP] or ssh username@IP")
        return pwd

    # Support optional username in 'user@IP' format.
    target_input = args[0]
    if "@" in target_input:
        target_username, target_ip = target_input.split("@", 1)
    else:
        target_username = None
        target_ip = target_input

    try:
        # Attempt to load the target machine's configuration
        target_machine = load_machine(target_ip)
        if "meta_data" not in target_machine or target_machine["meta_data"].get("name") == "unknown":
            raise KeyError

        # Check if port 22 is open on the target machine
        if 22 not in target_machine["meta_data"].get("ports", []):
            print(Fore.RED + "SSH service is not available on target machine (port 22 closed).")
            return pwd

        # Simulate SSH connection steps
        print(Fore.CYAN + f"Connecting to {target_ip} ...")
        time.sleep(random.uniform(0.5, 1.5))
        
        # Allow up to 5 password attempts
        expected_password_hash = target_machine["meta_data"].get("password", "defaultpass")
        authenticated = False
        for attempt in range(5):
            if target_username:
                print(Fore.YELLOW + f"Authenticating as {target_username} (attempt {attempt+1}/5)...")
                password = getpass.getpass(prompt=f"Password for {target_username}: ")
            else:
                print(Fore.YELLOW + f"Authenticating (attempt {attempt+1}/5)...")
                password = getpass.getpass(prompt="Password: ")
            
            time.sleep(random.uniform(0.5, 1.5))
            
            # Use the new password verification function
            if verify_password(password, expected_password_hash):
                authenticated = True
                break
            else:
                print(Fore.RED + "Incorrect password.")
        if not authenticated:
            print(Fore.RED + "Authentication failed after 5 attempts. Connection terminated.")
            return pwd

        print(Fore.GREEN + f"Connection established to {target_ip}!")
        
        # Log the connection event on the current machine using its source IP
        source_ip = load_machine(machine_name)["meta_data"]["ip"]
        logger = Logger(machine_name)
        connection_details = f"SSH connection initiated to {target_ip}"
        if target_username:
            connection_details += f" as {target_username}"
        logger.log_network(source_ip, target_ip, "CONNECT", connection_details)
        
        # Log the event on the remote machine - FIX: using positional args instead of keyword
        log_remote_event(source_ip, target_ip, "CONNECT", connection_details)
        
        # Set the working directory to '/home' upon successful login
        pwd = "/home"
        
        # Start a simulated remote session
        remote_name = target_machine["meta_data"]["name"]
        print(Fore.YELLOW + f"Remote session on {remote_name} ({target_ip}) started. Type 'exit' to return to your local machine.")
        
        # Get the available commands in the remote machine's bin folder
        bin_commands = target_machine.get("file_system", {}).get("bin", {})

        while True:
            remote_command = input(Fore.BLUE + f"{remote_name}@{target_ip}:{pwd}$ ")
            if remote_command.strip() == "":
                continue
            if remote_command.strip() == "exit":
                print(Fore.RED + "Exiting remote session, returning to local machine...")
                pwd = "/home"  # Reset pwd when exiting remote session
                break
            else:
                tokens = remote_command.split()
                command_name = tokens[0]
                if command_name in bin_commands:
                    try:
                        # Dynamically import the command from the commands folder and execute it
                        module = importlib.import_module(f"src.commands.{command_name}")
                        pwd = module.execute(tokens[1:], pwd, target_ip)
                    except Exception as e:
                        print(Fore.RED + f"Error executing remote command '{command_name}': {str(e)}")
                else:
                    print(Fore.RED + f"Remote command '{remote_command}' not recognized in remote bin folder.")
        
    except (FileNotFoundError, KeyError):
        print(Fore.RED + f"Machine with IP {target_ip} not found or has invalid data.")
    
    return pwd

def help():
    print("Usage: ssh [IP] or ssh username@IP")
    print("  Simulates establishing an SSH connection to the specified target machine with password authentication.")
    print("  The user is allowed up to 5 password attempts.")
    print("  Once connected, the terminal prompt shows the remote machine's name and IP with the working directory set to '/home'.")
    print("  Commands available in the remote machine's 'bin' folder are executed if present.")
    print("  Type 'exit' to return to your local machine and reset the working directory to '/home'.")