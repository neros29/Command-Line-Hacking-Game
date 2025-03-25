import os
import json
import time
import sys
import inspect
from colorama import init, Fore, Style
import random
from utils.utils import * # Import utility functions
from utils.logger import Logger
import importlib
import platform
import getpass
import subprocess
import shlex
import io
from contextlib import redirect_stdout
from utils.password_manager import verify_password, hash_password
import argparse

# Ensure that the src directory is in the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, project_root)

modules = {}
commands_dir = os.path.join(current_dir, 'commands')
for filename in os.listdir(commands_dir):
    if filename.endswith('.py') and not filename.startswith('__'):
        module_name = filename[:-3]  # remove .py extension
        modules[module_name] = importlib.import_module(f'src.commands.{module_name}')

init(autoreset=True)

def parse_arguments():
    """Parse command line arguments for the Terminal Hacking Game."""
    parser = argparse.ArgumentParser(description="Terminal Hacking Game")
    parser.add_argument("--machine", type=str, default="local", help="Specify the machine name to start with")
    return parser.parse_args()

class HackingEnvironment:
    def __init__(self, machine_name="local"):
        # Initialize variables
        self.clear_screen()
        self.pwd = "/home"  # Set the current directory to the Desktop
        self.current_machine_name = machine_name  # Use the parameter
        
        self.current_machine = load_machine(self.current_machine_name)
        self.file_system = self.current_machine["file_system"]
        self.meta_data = self.current_machine["meta_data"]
        
        # Remove these two lines that are causing the error
        
        # Initialize user settings
        self.current_user = None
        self.is_root = False
        self.user_home = None
        self.user_permissions = []
        
        self.hacked_machines = {}  # Store hacked machines
        
        # Initialize the logger
        self.logger = Logger(self.current_machine_name)
        self.logger.log_system("SYSTEM_STARTUP", "Terminal hacking environment initialized")

        # Initialize the hacking environment
        # self.start_up()
        # self.login()
        self.commands_list = []
        self.get_commands()

    def clear_screen(self):
        """Clear the terminal screen in a cross-platform way."""
        try:
            if platform.system() == "Windows":
                os.system('cls')
            else:
                os.system('clear')
        except Exception:
            # Fallback to ANSI escape codes if system commands fail
            print("\033[H\033[J", end="")

    def login(self):
        """Authenticate the user before allowing access to the system."""
        max_attempts = 5
        attempts = 0
        
        # Get users from machine data
        users = self.meta_data.get("users", {})
        
        # If no users defined, create a default root user
        if not users:
            default_password = "password"  # Default password for new installations
            users = {
                "root": {
                    "password": hash_password(default_password),
                    "home": "/root",
                    "shell": "/bin/bash",
                    "group": "root",
                    "is_root": True,
                    "uid": 0,
                    "gid": 0,
                    "permissions": ["all"]
                }
            }
            self.meta_data["users"] = users
            self.current_machine["meta_data"]["users"] = users
            save_machine(self.current_machine_name, self.current_machine)
            
            print(Fore.YELLOW + f"Created default root user with password: {default_password}")
            print(Fore.YELLOW + "Please change this password immediately using 'passwd'")
        
        print(Fore.YELLOW + f"\nLogin to {self.meta_data['name']}...")
        
        while attempts < max_attempts:
            attempts += 1
            
            # First ask for username
            username = input(f"Username ({attempts}/{max_attempts}): ")
            
            # Then ask for password
            password = getpass.getpass(prompt="Password: ")
            
            # Check if user exists
            if username in users:
                user_data = users[username]
                user_password = user_data.get("password")
                
                # Verify password
                if verify_password(password, user_password):
                    print(Fore.GREEN + "Login successful.")
                    
                    # Set current user and permissions
                    self.current_user = username
                    self.is_root = user_data.get("is_root", False)
                    self.user_home = user_data.get("home", f"/home/{username}")
                    self.user_permissions = user_data.get("permissions", [])
                    
                    # If logging in for the first time, start in user's home directory
                    if self.pwd == "/home" and self.user_home:
                        self.pwd = self.user_home
                    
                    # Log the successful login
                    self.logger.log_login(username, success=True)
                    return True
            
            print(Fore.RED + "Authentication failed.")
            # Log the failed login attempt
            self.logger.log_login(username, success=False)
        
        print(Fore.RED + f"Maximum login attempts exceeded. System access denied.")
        return False
    
    def get_commands(self):
        """Create a list of all the commands"""
        for command in self.file_system["bin"]:
            self.commands_list.append(command)
    
    def execute_command(self, command_string):
        """Execute command with support for pipes."""
        # Store original environment state to restore after command execution
        original_env = {}
        pipe_env_vars = ["PIPED_INPUT", "IS_PIPED", "IS_PIPE_SOURCE"]
        for var in pipe_env_vars:
            original_env[var] = os.environ.get(var)
        
        try:
            if command_string.strip() == "":
                return

            # Check if the command contains pipes
            if "|" in command_string:
                # Split the command by pipes, but respect quoted pipes
                in_quotes = False
                quote_char = None
                segments = []
                current_segment = ""
                
                for char in command_string:
                    if char in ['"', "'"]:
                        if not in_quotes:
                            in_quotes = True
                            quote_char = char
                        elif char == quote_char:
                            in_quotes = False
                            quote_char = None
                    
                    if char == '|' and not in_quotes:
                        segments.append(current_segment.strip())
                        current_segment = ""
                    else:
                        current_segment += char
                
                # Add the last segment
                if current_segment:
                    segments.append(current_segment.strip())
                
                piped_commands = segments
                
                # Set up for handling piped input/output
                piped_input = ""
                
                # Log the full piped command - FIXED: use self.current_user instead of meta_data["username"]
                self.logger.log_command(self.current_user, command_string, self.pwd)
                
                # Execute each command in the pipe, passing output as input to the next command
                for i, cmd in enumerate(piped_commands):
                    # Capture the output of this command
                    buffer = io.StringIO()
                    
                    # Save the original stdout
                    original_stdout = sys.stdout
                    
                    try:
                        # Redirect stdout to our buffer
                        sys.stdout = buffer
                        
                        # Parse the command
                        try:
                            args = shlex.split(cmd)
                            command = args[0] if args else ""
                        except ValueError:
                            args = cmd.split()
                            command = args[0] if args else ""
                        
                        if not command:
                            continue
                        
                        # Make modules accessible to commands
                        modules["__env__"] = self

                        # Check file permissions for commands that access files
                        file_access_commands = ["cat", "ls", "cd", "nano", "rm", "mkdir", "touch", "mv", "cp"]
                        if command in file_access_commands:
                            # Extract the target path from arguments if available
                            target_path = None
                            if len(args) > 1:
                                if command in ["cd", "mkdir", "touch"]:
                                    target_path = args[1]
                                elif command in ["rm", "cat", "nano"]:
                                    target_path = args[-1]  # Last arg is typically the file
                                elif command in ["mv", "cp"]:
                                    target_path = args[-1]  # Destination is the last arg
                            
                            # Normalize path if provided
                            if target_path:
                                if not target_path.startswith("/"):
                                    target_path = os.path.normpath(os.path.join(self.pwd, target_path))
                            
                            # Check permissions if we have a target path
                            if target_path and not check_file_access(target_path, self.current_user, self.is_root):
                                print(Fore.RED + f"Permission denied: '{self.current_user}' cannot access '{target_path}'")
                                self.logger.log_command(self.current_user, command, self.pwd, False)
                                return

                        # Execute the command
                        if command in self.commands_list:
                            # Set environment variables for piped input
                            os.environ["PIPED_INPUT"] = piped_input
                            os.environ["IS_PIPED"] = "1" if i > 0 else "0"
                            os.environ["IS_PIPE_SOURCE"] = "1" if i < len(piped_commands) - 1 else "0"
                            
                            # Reload the file system if needed
                            file_modifying_commands = ["nano", "rm", "mkdir", "touch", "mv"]
                            if command in file_modifying_commands:
                                self.file_system = load_machine(self.current_machine_name)
                            
                            module = modules[command]
                            if hasattr(module, 'execute'):
                                # Execute but don't log individual piped commands separately
                                old_pwd = self.pwd
                                self.pwd = module.execute(args[1:], self.pwd, self.current_machine_name)
                            else:
                                print(Fore.RED + f"Command {command} not found")
                                self.logger.log_command(self.current_user, command_string, self.pwd, False)
                        else:
                            print(Fore.RED + f"\"{command}\" is not recognized")
                            self.logger.log_command(self.current_user, command_string, self.pwd, False)
                        
                        # Get the output from this command
                        output = buffer.getvalue()
                        piped_input = output  # Set as input for next command
                        
                    finally:
                        # Restore stdout
                        sys.stdout = original_stdout
                
                # Print the final output if it's not empty
                if piped_input.strip():
                    print(piped_input, end="")
                
                # Clean up environment variables
                if "PIPED_INPUT" in os.environ:
                    del os.environ["PIPED_INPUT"]
                if "IS_PIPED" in os.environ:
                    del os.environ["IS_PIPED"]
                if "IS_PIPE_SOURCE" in os.environ:
                    del os.environ["IS_PIPE_SOURCE"]
                
                return
                
            else:
                # Non-piped command - use the original execution logic
                # Parse command respecting quoted strings
                try:
                    args = shlex.split(command_string)
                except ValueError as e:
                    print(Fore.RED + f"Parse error: {str(e)}")
                    self.logger.log_command(self.current_user, command_string, self.pwd, False)
                    return
                        
                command = args[0] if args else ""
                
                # Clear environment variables from previous piped commands
                if "PIPED_INPUT" in os.environ:
                    del os.environ["PIPED_INPUT"]
                if "IS_PIPED" in os.environ:
                    del os.environ["IS_PIPED"]
                if "IS_PIPE_SOURCE" in os.environ:
                    del os.environ["IS_PIPE_SOURCE"]
                
                # Make modules accessible to commands
                modules["__env__"] = self

                # Check file permissions for commands that access files
                file_access_commands = ["cat", "ls", "cd", "nano", "rm", "mkdir", "touch", "mv", "cp"]
                if command in file_access_commands and args:
                    # Extract the target path from arguments
                    target_path = None
                    if command in ["cd", "mkdir", "touch"]:
                        target_path = args[-1]
                    elif command in ["rm", "cat", "nano"]:
                        target_path = args[-1]
                    elif command in ["mv", "cp"]:
                        target_path = args[-1]  # Destination
                    
                    # Normalize path if provided
                    if target_path and not target_path.startswith("/"):
                        target_path = os.path.normpath(os.path.join(self.pwd, target_path))
                    
                    # Get current user data
                    users = self.meta_data.get("users", {})
                    user_data = users.get(self.current_user, {})
                    
                    # Check permissions if we have a target path
                    if target_path and not check_file_access(target_path, self.current_user, user_data, self):
                        print(Fore.RED + f"Permission denied: '{self.current_user}' cannot access '{target_path}'")
                        self.logger.log_command(self.current_user, command_string, self.pwd, False)
                        return

                # File-modifying commands need to reload the filesystem
                file_modifying_commands = ["nano", "rm", "mkdir", "touch", "mv"]
                if command in file_modifying_commands:
                    self.file_system = load_machine(self.current_machine_name)
                
                # Process the command
                if command in self.commands_list:
                    module = modules[command]
                    if hasattr(module, 'execute'):
                        try:
                            # Log the command before execution
                            self.logger.log_command(self.current_user, command_string, self.pwd)
                            
                            # Execute the command
                            old_pwd = self.pwd
                            self.pwd = module.execute(args[1:], self.pwd, self.current_machine_name)
                            
                            # Log directory changes if they occurred
                            if old_pwd != self.pwd:
                                self.logger.log_system("DIRECTORY_CHANGE", f"Changed from {old_pwd} to {self.pwd}")
                        except Exception as e:
                            print(Fore.RED + f"Error executing {command}: {str(e)}")
                            self.logger.log_command(self.current_user, command_string, self.pwd, False)
                    else:
                        print(Fore.RED + f"Command {command} not found")
                        self.logger.log_command(self.current_user, command_string, self.pwd, False)
                elif command == "":
                    return
                else:
                    print(Fore.RED + f"\"{command}\" is not recognized as an internal or external command,\noperable program or batch file.")
                    self.logger.log_command(self.current_user, command_string, self.pwd, False)
        
        finally:
            # Clean up - restore original environment state
            for var in pipe_env_vars:
                if original_env[var] is None:
                    if var in os.environ:
                        del os.environ[var]
                else:
                    os.environ[var] = original_env[var]
    
    def help_command(self, command=None):
        """Print Help info about all commands or individual commands"""
        if command:
            if command in self.commands_list:
                print(Fore.RESET + f"Help for {command}:")
                module = modules[command.strip()]
                if hasattr(module, 'help'):
                    module.help()
                else:
                    print(Fore.RED + f"No help available for {command}")
            else:
                print(Fore.RED + f"No help available for {command}")
        else:
            print(Fore.RESET + "For more information on a specific command, type HELP command-name")
            for command in self.commands_list:
                spaces = 15 - len(command)
                print(f"{command}{' ' * spaces}", end="")
                module = modules[command.strip()]
                if hasattr(module, 'help'):
                    module.help()
                else:
                    print(Fore.RED + "No help available")
            print("\nFor more information on tools see the command-line reference in the online help.")

    def start_up(self):
        """Simulates a cinematic hacking machine boot process"""
        # Log the startup event
        self.logger.log_system("BOOT_SEQUENCE", "System boot sequence initiated")

        def typing_effect(text, delay=0.05):
            """Simulates a typing effect for text output"""
            for char in text:
                sys.stdout.write(char)
                sys.stdout.flush()
                time.sleep(delay)
            print()

        def fast_scrolling_logs():
            """Simulates fast boot logs appearing on the screen with hidden Easter eggs"""
            start_time = time.time()
            cpu_info = platform.processor()
            cpu_cores = os.cpu_count()
            messages = [
                "[{:.6f}] Booting Linux Kernel...".format(time.time() - start_time),
                "[{:.6f}] Linux version 5.15.0-86-generic (buildd@lcy02-amd64-051) (gcc version 11.2.0, GNU ld (GNU Binutils for Ubuntu) 2.38) #96-Ubuntu SMP Fri Oct 20 12:30:00 UTC 2023".format(time.time() - start_time),
                "[{:.6f}] Command line: BOOT_IMAGE=/boot/vmlinuz-5.15.0-86-generic root=UUID=abcd1234-5678-90ef-1234-567890abcdef ro quiet splash vt.handoff=7".format(time.time() - start_time),
                "[{:.6f}] Secure boot disabled".format(time.time() - start_time),
                "[{:.6f}] BIOS-provided physical RAM map:".format(time.time() - start_time),
                "[{:.6f}] BIOS-e820: [mem 0x0000000000000000-0x000000000009ffff] usable".format(time.time() - start_time),
                "[{:.6f}] BIOS-e820: [mem 0x00000000000a0000-0x00000000000fffff] reserved".format(time.time() - start_time),
                "[{:.6f}] BIOS-e820: [mem 0x0000000000100000-0x00000000bfffffff] usable".format(time.time() - start_time),
                "[{:.6f}] Kernel Randomization: enabled".format(time.time() - start_time),
                "[{:.6f}] Initializing cgroup subsys cpu".format(time.time() - start_time),
                "[{:.6f}] Initializing cgroup subsys cpuacct".format(time.time() - start_time),
                "[{:.6f}] Initializing cgroup subsys memory".format(time.time() - start_time),
                "[{:.6f}] Initializing cgroup subsys devices".format(time.time() - start_time),
                "[{:.6f}] Initializing cgroup subsys freezer".format(time.time() - start_time),
                "[{:.6f}] Initializing cgroup subsys net_cls".format(time.time() - start_time),
                "[{:.6f}] Initializing cgroup subsys blkio".format(time.time() - start_time),
                f"[{time.time() - start_time:.6f}] CPU: {cpu_info} ({cpu_cores} cores)",
                "[{:.6f}] ACPI: Early table checksum verification disabled".format(time.time() - start_time),
                "[{:.6f}] ACPI: RSDP 0x00000000C0800000 000024 (v02 ASUS  )".format(time.time() - start_time),
                "[{:.6f}] ACPI: XSDT 0x00000000C0800100 0000A4 (v01 ASUS   ASUS0001 00000001      01000013)".format(time.time() - start_time),
                "[{:.6f}] ACPI: FACP 0x00000000C0800200 000114 (v06 ASUS   ASUS0001 00000001      01000013)".format(time.time() - start_time),
                "[{:.6f}] ACPI: DSDT 0x00000000C0800400 014824 (v02 ASUS   ASUS0001 00000001      01000013)".format(time.time() - start_time),
                "[{:.6f}] ACPI: APIC 0x00000000C0807200 0000B0 (v04 ASUS   ASUS0001 00000001      01000013)".format(time.time() - start_time),
                "[{:.6f}] ACPI: MCFG 0x00000000C0807300 00003C (v01 ASUS   ASUS0001 00000001      01000013)".format(time.time() - start_time),
                "[{:.6f}] ACPI: AAFT 0x00000000C0807400 0000DC (v01 ASUS   ASUS0001 00000001      01000013)".format(time.time() - start_time),
                "[{:.6f}] Detected {} CPU cores, enabling SMP".format(cpu_cores, time.time() - start_time),
                "[{:.6f}] Kernel modules successfully loaded".format(time.time() - start_time),
                "[{:.6f}] PCI: Using configuration type 1 for base access".format(time.time() - start_time),
                "[{:.6f}] PCI: bus 00 - 0x20".format(time.time() - start_time),
                "[{:.6f}] PCI: bus 01 - 0x40".format(time.time() - start_time),
                "[{:.6f}] PCI: bus 02 - 0x60".format(time.time() - start_time),
                "[{:.6f}] ACPI: Enabled 16 GPEs in block 00 to 7F".format(time.time() - start_time),
                "[{:.6f}] ACPI: Power Button [PWRB]".format(time.time() - start_time),
                "[{:.6f}] ACPI: Lid Switch [LID0]".format(time.time() - start_time),
                "[{:.6f}] ACPI: Sleep Button [SLPB]".format(time.time() - start_time),
                "[{:.6f}] Freeing unused kernel memory: 1024K".format(time.time() - start_time),
                "[{:.6f}] Starting systemd version 250".format(time.time() - start_time),
                "[{:.6f}] systemd[1]: Detected architecture x86-64.".format(time.time() - start_time),
                "[{:.6f}] systemd[1]: Running in early boot mode.".format(time.time() - start_time),
                "[{:.6f}] Mounting /proc...".format(time.time() - start_time),
                "[{:.6f}] Mounting /sys...".format(time.time() - start_time),
                "[{:.6f}] Mounting /dev...".format(time.time() - start_time),
                "[{:.6f}] Creating static device nodes...".format(time.time() - start_time),
                "[{:.6f}] Starting udev kernel device manager...".format(time.time() - start_time),
                "[{:.6f}] systemd-udevd[222]: Starting udev daemon".format(time.time() - start_time),
                "[{:.6f}] systemd-udevd[222]: Successfully initialized hardware".format(time.time() - start_time),
                "[{:.6f}] Random: crng init done".format(time.time() - start_time),
                "[{:.6f}] Network interfaces initializing...".format(time.time() - start_time),
                "[{:.6f}] eth0: Detected network interface".format(time.time() - start_time),
                "[{:.6f}] eth0: Link is UP - 1000Mbps Full Duplex".format(time.time() - start_time),
                "[{:.6f}] Starting system logging service...".format(time.time() - start_time),
                "[{:.6f}] Mounting local filesystems...".format(time.time() - start_time),
                "[{:.6f}] systemd-fsck[333]: Checking file system integrity...".format(time.time() - start_time),
                "[{:.6f}] systemd-fsck[333]: /dev/sda1: clean, 102234/512000 files, 800321/2097152 blocks".format(time.time() - start_time),
                "[{:.6f}] Starting cron service...".format(time.time() - start_time),
                "[{:.6f}] Starting SSH daemon...".format(time.time() - start_time),
                "[{:.6f}] SSH daemon started. Listening on port 22.".format(time.time() - start_time),
                "[{:.6f}] Starting graphical user interface...".format(time.time() - start_time),
                "[{:.6f}] System boot complete. Welcome to Linux.".format(time.time() - start_time)
            ]
            
            for _ in messages:
                print(Fore.YELLOW + _)
                time.sleep(0.05)

        def loading_bar(stage, color=Fore.BLUE, length=40, speed_range=(1, 9)):
            """Displays a loading bar with a smooth animation"""
            print(color + stage)
            for i in range(length):
                percent = (i + 1) / length * 100
                bar = '#' * (i + 1) + '-' * (length - (i + 1))
                sys.stdout.write(color + f"\r[{bar}] {percent:.2f}%")
                sys.stdout.flush()
                time.sleep(float(f"0.0{random.randint(*speed_range)}"))
            print()

        # Boot sequence start
        print(Fore.CYAN + "Initializing Virtual Hacking Machine...\n")
        time.sleep(0.5)
        
        print(Fore.MAGENTA + "[SYSTEM BOOT] Press F2 for BIOS Setup | F12 for Boot Options")
        time.sleep(0.7)
        
        fast_scrolling_logs()  # Simulating fast boot messages with Easter eggs

        loading_bar("Loading Kernel...", Fore.BLUE)
        loading_bar("Initializing Bootloader...", Fore.CYAN, length=30, speed_range=(3, 8))
        loading_bar("Configuring Network Services...", Fore.GREEN, length=20, speed_range=(5, 9))

        print(Fore.GREEN + "\nSystem Boot Successful. Welcome, Hacker!\n")
        time.sleep(0.3)

        # Hacker-style ASCII Banner
        banner = [
            "  __ _  ____  ____   __   ____          _  _  __  __    ____ ",
            " (  ( \\(  __)(  _ \\ /  \\ / ___)        ( \\/ )(  )(  )  (  __)",
            " /    / ) _)  )   /(  O )\\___ \\        / \\/ \\ )( / (_/\\ ) _) ",
            " \\_)__)(____)(__\\_) \\__/ (____/        \\_)(_/(__)\\____/(____)"
        ]

        for line in banner:
            typing_effect(Fore.RED + line, delay=0.02)

        print(Fore.YELLOW + "\n> Accessing mainframe...")
        time.sleep(1)
        typing_effect(Fore.GREEN + "> Connection Established.")
        typing_effect(Fore.GREEN + "> Welcome to the system, Operative.")

        # Log completion of startup
        self.logger.log_system("BOOT_SEQUENCE_COMPLETE", "System boot completed successfully")

    def run(self):
        """Improved command loop with better handling for commands with arguments."""
        # Log the start of the game session - FIXED to use current_user instead of meta_data['username']
        self.logger.log_system("SESSION_START", f"User {self.current_user} started a new terminal session")
        
        while True:
            try:
                # Update prompt to use current_user instead of meta_data['username']
                command = input(Fore.BLUE + f"{self.current_user}@{self.meta_data['ip']}:{self.pwd}$ ")
                
                if command.strip() == "":
                    continue
                    
                # Parse the command properly
                try:
                    args = shlex.split(command)
                    cmd = args[0] if args else ""
                except ValueError:
                    # Fall back to simple split if shlex fails
                    args = command.split()
                    cmd = args[0] if args else ""
                    
                # Handle built-in commands
                if cmd == "exit":
                    # Updated to use current_user
                    self.logger.log_command(self.current_user, command, self.pwd)
                    self.logger.log_system("SESSION_END", f"User {self.current_user} ended the terminal session")
                    print(Fore.RED + "Exiting virtual environment...")
                    break
                elif cmd in self.commands_list:
                    self.execute_command(command)
                else:
                    print(Fore.RED + f"\"{cmd}\" is not recognized as an internal or external command,\noperable program or batch file.")
                    self.logger.log_command(self.current_user, command_string, self.pwd, False)
                    
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit the terminal")
                self.logger.log_system("KEYBOARD_INTERRUPT", "User interrupted the command input with Ctrl+C")
            except Exception as e:
                print(Fore.RED + f"Error: {str(e)}")
                self.logger.log_system("ERROR", f"Unhandled exception: {str(e)}")

# Start the game
def main():
    arguments = parse_arguments()
    
    env = HackingEnvironment(machine_name=arguments.machine)
    
    # Authenticate the user
    if not env.login():
        print(Fore.RED + "Exiting due to authentication failure.")
        return
    
    env.run()

if __name__ == "__main__":
    main()
