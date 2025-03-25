from colorama import Fore

def execute(args, pwd, machine_name):
    """Display groups for a user"""
    from src.main import modules
    
    env = modules.get("__env__", None)
    if not env:
        print(Fore.RED + "Error: Environment not initialized")
        return pwd
    
    # Get target username
    username = args[0] if args else env.current_user
    
    # Get users from machine data
    users = env.meta_data.get("users", {})
    
    if username not in users:
        print(Fore.RED + f"Error: User '{username}' does not exist")
        return pwd
    
    # Non-root users can only see their own groups
    if username != env.current_user and not env.is_root:
        print(Fore.RED + "Permission denied: You can only view your own groups")
        return pwd
    
    # Get group info
    group = users[username].get("group", "users")
    
    print(f"{username} : {group}")
    return pwd

def help():
    print("Display group membership for a user")
    print("Usage: groups [username]")
    print("If no username is provided, displays groups for the current user")