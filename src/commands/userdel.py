from colorama import Fore
from utils.utils import load_machine, save_machine

def execute(args, pwd, machine_name):
    """Delete a user from the system"""
    from src.main import modules
    
    env = modules.get("__env__", None)
    if not env:
        print(Fore.RED + "Error: Environment not initialized")
        return pwd
    
    # Only root can delete users
    if not env.is_root:
        print(Fore.RED + "Permission denied: Only root can delete users")
        return pwd
    
    if len(args) < 1:
        print(Fore.RED + "Error: Username required")
        print("Usage: userdel username")
        return pwd
    
    username = args[0]
    
    # Cannot delete yourself
    if username == env.current_user:
        print(Fore.RED + "Error: Cannot delete the current user")
        return pwd
    
    # Get machine data
    machine_data = load_machine(machine_name)
    users = machine_data["meta_data"].get("users", {})
    
    # Check if user exists
    if username not in users:
        print(Fore.RED + f"Error: User '{username}' does not exist")
        return pwd
    
    # Confirm deletion
    confirm = input(f"Delete user '{username}'? [y/N] ")
    if confirm.lower() != "y":
        print("User deletion cancelled")
        return pwd
    
    # Delete the user
    del users[username]
    
    # Save machine data
    machine_data["meta_data"]["users"] = users
    save_machine(machine_name, machine_data)
    
    print(Fore.GREEN + f"User '{username}' deleted successfully")
    return pwd

def help():
    print("Delete a user from the system")
    print("Usage: userdel username")
    print("Note: Only root can delete users")