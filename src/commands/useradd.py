import getpass
from colorama import Fore
from utils.password_manager import hash_password
from utils.utils import load_machine, save_machine

def execute(args, pwd, machine_name):
    """Add a new user to the system"""
    from src.main import modules
    
    env = modules.get("__env__", None)
    if not env:
        print(Fore.RED + "Error: Environment not initialized")
        return pwd
    
    # Only root can add users
    if not env.is_root:
        print(Fore.RED + "Permission denied: Only root can add users")
        return pwd
    
    if len(args) < 1:
        print(Fore.RED + "Error: Username required")
        print("Usage: useradd username [--root]")
        return pwd
    
    username = args[0]
    is_root = "--root" in args
    
    # Get machine data
    machine_data = load_machine(machine_name)
    
    # Initialize users dict if it doesn't exist
    if "users" not in machine_data["meta_data"]:
        machine_data["meta_data"]["users"] = {}
    
    users = machine_data["meta_data"]["users"]
    
    # Check if user already exists
    if username in users:
        print(Fore.RED + f"Error: User '{username}' already exists")
        return pwd
    
    # Ask for password
    password = getpass.getpass(prompt="Enter password for new user: ")
    confirm = getpass.getpass(prompt="Confirm password: ")
    
    if password != confirm:
        print(Fore.RED + "Error: Passwords do not match")
        return pwd
    
    # Create the user
    users[username] = {
        "password": hash_password(password),
        "home": f"/home/{username}",
        "shell": "/bin/bash",
        "group": "users",
        "is_root": is_root,
        "uid": 0 if is_root else 1000 + len(users),
        "gid": 0 if is_root else 1000 + len(users),
        "permissions": ["all"] if is_root else ["home", "public"]
    }
    
    # Save machine data
    machine_data["meta_data"]["users"] = users
    save_machine(machine_name, machine_data)
    
    print(Fore.GREEN + f"User '{username}' added successfully")
    
    return pwd

def help():
    print("Add a new user to the system")
    print("Usage: useradd username [--root]")
    print("  --root: Grant root privileges to the new user")
    print("Note: Only root can add users")