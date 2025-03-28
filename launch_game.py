#!/usr/bin/env python3
"""
Cross-platform launcher for Terminal Hacking Game
"""
import os
import sys
import platform
import getpass
import json
import argparse

def setup_users():
    """Set up root password before launching the game"""
    from src.utils.password_manager import hash_password
    from src.utils.utils import load_machine, save_machine
    
    machine_name = "local"  # Always use local machine
    
    try:
        # Check if setup has already been completed
        setup_flag_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".setup_complete")
        
        # If the setup flag exists, skip the setup
        if os.path.exists(setup_flag_file):
            return
            
        print("\n=== Root Password Setup ===")
        print("This will allow you to set the root password for the machine.")
        print("The default password for all users is 'toor' if you skip this step.")
        print("You'll only see this prompt once when first running the game.")
        
        # Check if user wants to skip setup
        choice = input("Set custom root password? (y/n): ").lower()
        if choice != 'y':
            print("Using default password 'toor' for all users.")
            # Create the setup flag file to skip next time
            with open(setup_flag_file, "w") as f:
                f.write("Setup completed on first run")
            return
            
        # Load the machine data
        machine_data = load_machine(machine_name)
        if not machine_data:
            print("Error: Default machine not found. Please run the game first to initialize it.")
            print("Using default password 'toor' for all users.")
            # Create the setup flag file to skip next time
            with open(setup_flag_file, "w") as f:
                f.write("Setup completed on first run")
            return
                
        # Access or create the users dictionary
        if "meta_data" not in machine_data:
            machine_data["meta_data"] = {}
        if "users" not in machine_data["meta_data"]:
            machine_data["meta_data"]["users"] = {}
            
        users = machine_data["meta_data"]["users"]
        
        # Setup root user
        while True:
            # Ask for password
            password = getpass.getpass("Enter root password: ")
            confirm = getpass.getpass("Confirm password: ")
            
            if password != confirm:
                print("Passwords do not match. Please try again.")
                continue
            
            # Create or update root user
            if "root" not in users:
                users["root"] = {
                    "password": hash_password(password),
                    "home": "/root",
                    "shell": "/bin/bash",
                    "group": "root",
                    "is_root": True,
                    "uid": 0,
                    "gid": 0,
                    "permissions": ["all"]
                }
                print("Root user created successfully.")
            else:
                # Update existing root user
                users["root"]["password"] = hash_password(password)
                print("Root password updated successfully.")
            
            # Save and exit
            machine_data["meta_data"]["users"] = users
            save_machine(machine_name, machine_data)
            print("Root password set successfully.")
            
            # Create the setup flag file to skip next time
            with open(setup_flag_file, "w") as f:
                f.write("Setup completed on first run")
                
            break
                
    except Exception as e:
        print(f"Error during root password setup: {str(e)}")
        print("Using default password 'toor' for all users.")
        
        # Create the setup flag file to skip next time even on error
        setup_flag_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".setup_complete")
        with open(setup_flag_file, "w") as f:
            f.write("Setup completed on first run (with errors)")

def main():
    """Cross-platform launcher for Terminal Hacking Game"""
    # Ensure that the src directory is in the Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Terminal Hacking Game Launcher")
    parser.add_argument("--machine", type=str, default="local", help="Specify the machine name to start with")
    parser.add_argument("--skip-setup", action="store_true", help="Skip the user setup screen and launch directly")
    parser.add_argument("--reset-setup", action="store_true", help="Force the setup prompt to appear again")
    args = parser.parse_args()
    
    # Handle setup reset if requested
    if args.reset_setup:
        setup_flag_file = os.path.join(current_dir, ".setup_complete")
        if os.path.exists(setup_flag_file):
            os.remove(setup_flag_file)
            print("Setup has been reset. You will be prompted for password setup.")
    
    # Activate virtual environment if needed
    if platform.system() == "Windows":
        activate_path = os.path.join(current_dir, ".myenv", "Scripts", "activate_this.py")
    else:
        activate_path = os.path.join(current_dir, ".myenv", "bin", "activate_this.py")
    
    if os.path.exists(activate_path):
        with open(activate_path) as f:
            exec(f.read(), {'__file__': activate_path})
    
    # Import and run the setup module if not skipped
    if not args.skip_setup:
        # We need to initialize the Python path before importing our modules
        sys.path.insert(0, os.path.join(current_dir, "src"))
        try:
            setup_users()
        except ImportError as e:
            print(f"Warning: Couldn't run user setup: {str(e)}")
            print("The game will start with default users (password: toor).")
    
    # Import and run the main module with the specified machine name
    from src.main import main
    os.environ["GAME_MACHINE"] = args.machine
    main()

if __name__ == "__main__":
    main()