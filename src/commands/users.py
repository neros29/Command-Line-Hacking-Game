from colorama import Fore
from utils.utils import load_machine

def execute(args, pwd, machine_name):
    """List all users on the system"""
    # Instead of getting users from environment, load directly from the machine file
    machine_data = load_machine(machine_name)
    
    # Get users from freshly loaded machine data
    users = machine_data.get("meta_data", {}).get("users", {})
    
    if not users:
        print(Fore.YELLOW + "No users found in the system.")
        return pwd
    
    usernames = list(users.keys())
    
    # Enhance the output with formatting and user details (optional)
    print(Fore.GREEN + "System Users:")
    print("-------------")
    for username in sorted(usernames):
        user_info = users[username]
        # Add indicators for root/admin users
        if user_info.get("is_root", False):
            print(f"{username} (root)")
        else:
            print(username)
    
    return pwd

def help():
    print("List all users on the system")
    print("Usage: users")
    print("Displays all users registered on the current machine")