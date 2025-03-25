import getpass
from colorama import Fore
from utils.password_manager import hash_password, verify_password
from utils.utils import load_machine, save_machine, get_environment

def execute(args, pwd, machine_name):
    """Change a user's password"""
    env = get_environment()
    if not env:
        print(Fore.RED + "Error: Environment not initialized")
        return pwd
    
    # Get the target username
    target_user = args[0] if args else env.current_user
    
    # Get users from machine data
    machine_data = load_machine(machine_name)
    users = machine_data.get("meta_data", {}).get("users", {})
    
    # If users is empty, create it with the default root user
    if not users:
        users = {"root": {"password": machine_data["meta_data"]["password"], "is_root": True}}
        machine_data["meta_data"]["users"] = users
    
    # Check permissions
    if target_user != env.current_user and not env.is_root:
        print(Fore.RED + "Permission denied: Only root can change other users' passwords")
        return pwd
    
    # Check if user exists
    if target_user not in users and not env.is_root:
        print(Fore.RED + f"User '{target_user}' does not exist")
        return pwd
    
    # Ask for current password if changing own password
    if target_user == env.current_user:
        current_password = getpass.getpass(prompt="Current password: ")
        if not verify_password(current_password, users[target_user].get("password")):
            print(Fore.RED + "Current password is incorrect")
            return pwd
    
    # Ask for new password
    new_password = getpass.getpass(prompt="New password: ")
    confirm_password = getpass.getpass(prompt="Confirm new password: ")
    
    if new_password != confirm_password:
        print(Fore.RED + "Passwords do not match")
        return pwd
    
    # Create user if it doesn't exist (only root can do this)
    if target_user not in users:
        users[target_user] = {"is_root": False}
    
    # Hash and store the new password
    users[target_user]["password"] = hash_password(new_password)
    
    # Update machine data
    machine_data["meta_data"]["users"] = users
    save_machine(machine_name, machine_data)
    
    print(Fore.GREEN + f"Password for '{target_user}' changed successfully")
    return pwd

def help():
    print("Change user password. Usage: passwd [username]")
    print("If no username is provided, changes the current user's password.")
    print("Only root can change other users' passwords.")