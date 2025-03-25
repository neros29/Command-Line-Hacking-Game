import getpass
from colorama import Fore
from utils.password_manager import hash_password, verify_password
from utils.utils import load_machine, save_machine

def execute(args, pwd, machine_name):
    """User management command"""
    from src.main import modules  # Import here to avoid circular imports
    
    # Get the current environment
    env = modules.get("__env__", None)
    if not env:
        print(Fore.RED + "Error: Environment not initialized")
        return pwd
    
    if len(args) < 1:
        print_user_help()
        return pwd
    
    subcommand = args[0]
    
    if subcommand == "add":
        return add_user(args[1:], env, machine_name)
    elif subcommand == "del":
        return delete_user(args[1:], env, machine_name)
    elif subcommand == "mod":
        return modify_user(args[1:], env, machine_name)
    elif subcommand == "list":
        return list_users(env)
    elif subcommand == "info":
        return user_info(args[1:], env)
    else:
        print(Fore.RED + f"Unknown subcommand: {subcommand}")
        print_user_help()
    
    return pwd

def print_user_help():
    """Print help for user command"""
    print("User management command")
    print("Usage: user <subcommand> [options]")
    print("")
    print("Subcommands:")
    print("  add <username> [options]  - Add a new user")
    print("    --root                  - Give root privileges")
    print("    --group <group>         - Set primary group")
    print("    --home <dir>            - Set home directory")
    print("  del <username>            - Delete a user")
    print("  mod <username> [options]  - Modify a user")
    print("    --root                  - Toggle root privileges")
    print("    --group <group>         - Change primary group")
    print("    --home <dir>            - Change home directory")
    print("    --add-perm <perm>       - Add a permission")
    print("    --del-perm <perm>       - Remove a permission")
    print("  list                      - List all users")
    print("  info <username>           - Show user information")

def add_user(args, env, machine_name):
    """Add a new user"""
    if not env.is_root:
        print(Fore.RED + "Permission denied: Only root can add users")
        return env.pwd
    
    if len(args) < 1:
        print(Fore.RED + "Error: Username required")
        print("Usage: user add <username> [options]")
        return env.pwd
    
    username = args[0]
    
    # Parse options
    is_root = "--root" in args
    
    # Get group option
    group_index = -1
    if "--group" in args:
        group_index = args.index("--group")
    
    group = "users"  # Default group
    if group_index >= 0 and group_index + 1 < len(args):
        group = args[group_index + 1]
    
    # Get home directory option
    home_index = -1
    if "--home" in args:
        home_index = args.index("--home")
    
    home = f"/home/{username}"  # Default home
    if home_index >= 0 and home_index + 1 < len(args):
        home = args[home_index + 1]
    
    # Get machine data
    machine_data = load_machine(machine_name)
    
    # Initialize users dict if it doesn't exist
    if "users" not in machine_data["meta_data"]:
        machine_data["meta_data"]["users"] = {}
    
    users = machine_data["meta_data"]["users"]
    
    # Check if user already exists
    if username in users:
        print(Fore.RED + f"Error: User '{username}' already exists")
        return env.pwd
    
    # Ask for password
    password = getpass.getpass(prompt="Enter password for new user: ")
    confirm = getpass.getpass(prompt="Confirm password: ")
    
    if password != confirm:
        print(Fore.RED + "Error: Passwords do not match")
        return env.pwd
    
    # Get next available UID (1000+)
    uid = 1000
    for user, data in users.items():
        if data.get("uid", 0) >= uid and data.get("uid", 0) < 65534:
            uid = data.get("uid", 0) + 1
    
    # Create the user
    users[username] = {
        "password": hash_password(password),
        "home": home,
        "shell": "/bin/bash",
        "group": group,
        "is_root": is_root,
        "uid": 0 if is_root else uid,
        "gid": 0 if is_root else uid,
        "permissions": ["all"] if is_root else ["home", "public"]
    }
    
    # Save machine data
    machine_data["meta_data"]["users"] = users
    save_machine(machine_name, machine_data)
    
    print(Fore.GREEN + f"User '{username}' added successfully")
    if is_root:
        print(Fore.YELLOW + f"Note: User '{username}' has root privileges")
    
    return env.pwd

def delete_user(args, env, machine_name):
    """Delete a user"""
    if not env.is_root:
        print(Fore.RED + "Permission denied: Only root can delete users")
        return env.pwd
    
    if len(args) < 1:
        print(Fore.RED + "Error: Username required")
        print("Usage: user del <username>")
        return env.pwd
    
    username = args[0]
    
    # Get machine data
    machine_data = load_machine(machine_name)
    users = machine_data["meta_data"].get("users", {})
    
    # Check if user exists
    if username not in users:
        print(Fore.RED + f"Error: User '{username}' does not exist")
        return env.pwd
    
    # Can't delete yourself
    if username == env.current_user:
        print(Fore.RED + "Error: Cannot delete the current user")
        return env.pwd
    
    # Confirm deletion
    confirm = input(f"Delete user '{username}'? [y/N] ")
    if confirm.lower() != "y":
        print("User deletion cancelled")
        return env.pwd
    
    # Delete the user
    del users[username]
    
    # Save machine data
    machine_data["meta_data"]["users"] = users
    save_machine(machine_name, machine_data)
    
    print(Fore.GREEN + f"User '{username}' deleted successfully")
    return env.pwd

def modify_user(args, env, machine_name):
    """Modify a user"""
    if len(args) < 1:
        print(Fore.RED + "Error: Username required")
        print("Usage: user mod <username> [options]")
        return env.pwd
    
    username = args[0]
    
    # Get machine data
    machine_data = load_machine(machine_name)
    users = machine_data["meta_data"].get("users", {})
    
    # Check if user exists
    if username not in users:
        print(Fore.RED + f"Error: User '{username}' does not exist")
        return env.pwd
    
    # Only root can modify other users
    if username != env.current_user and not env.is_root:
        print(Fore.RED + "Permission denied: Only root can modify other users")
        return env.pwd
    
    # Get user data
    user_data = users[username]
    
    # Parse options
    modified = False
    
    # Toggle root privileges (root only)
    if "--root" in args and env.is_root:
        user_data["is_root"] = not user_data.get("is_root", False)
        print(f"Root privileges {'enabled' if user_data['is_root'] else 'disabled'} for {username}")
        modified = True
    
    # Change group (root only)
    group_index = -1
    if "--group" in args and env.is_root:
        group_index = args.index("--group")
        if group_index + 1 < len(args):
            user_data["group"] = args[group_index + 1]
            print(f"Group changed to '{user_data['group']}' for {username}")
            modified = True
    
    # Change home directory (root only)
    home_index = -1
    if "--home" in args and env.is_root:
        home_index = args.index("--home")
        if home_index + 1 < len(args):
            user_data["home"] = args[home_index + 1]
            print(f"Home directory changed to '{user_data['home']}' for {username}")
            modified = True
    
    # Add permission (root only)
    add_perm_index = -1
    if "--add-perm" in args and env.is_root:
        add_perm_index = args.index("--add-perm")
        if add_perm_index + 1 < len(args):
            perm = args[add_perm_index + 1]
            if "permissions" not in user_data:
                user_data["permissions"] = []
            if perm not in user_data["permissions"]:
                user_data["permissions"].append(perm)
                print(f"Added permission '{perm}' for {username}")
                modified = True
    
    # Remove permission (root only)
    del_perm_index = -1
    if "--del-perm" in args and env.is_root:
        del_perm_index = args.index("--del-perm")
        if del_perm_index + 1 < len(args):
            perm = args[del_perm_index + 1]
            if "permissions" in user_data and perm in user_data["permissions"]:
                user_data["permissions"].remove(perm)
                print(f"Removed permission '{perm}' for {username}")
                modified = True
    
    if modified:
        # Update user data
        users[username] = user_data
        
        # Save machine data
        machine_data["meta_data"]["users"] = users
        save_machine(machine_name, machine_data)
        
        print(Fore.GREEN + f"User '{username}' modified successfully")
    else:
        print("No changes made")
    
    return env.pwd

def list_users(env):
    """List all users"""
    # Get users from machine data
    users = env.meta_data.get("users", {})
    
    if not users:
        print(Fore.YELLOW + "No users defined")
        return env.pwd
    
    print(Fore.GREEN + "Users on this system:")
    print("-" * 55)
    print(f"{'USERNAME':<15} {'GROUP':<10} {'HOME':<15} {'ROOT':<5} {'CURRENT'}")
    print("-" * 55)
    
    for username, data in sorted(users.items()):
        is_root = data.get("is_root", False)
        group = data.get("group", "users")
        home = data.get("home", f"/home/{username}")
        is_current = "→" if username == env.current_user else ""
        
        print(f"{username:<15} {group:<10} {home:<15} {'yes' if is_root else 'no':<5} {is_current}")
    
    return env.pwd

def user_info(args, env):
    """Show user information"""
    if len(args) < 1:
        # Default to current user
        username = env.current_user
    else:
        username = args[0]
    
    # Get users from machine data
    users = env.meta_data.get("users", {})
    
    if username not in users:
        print(Fore.RED + f"Error: User '{username}' does not exist")
        return env.pwd
    
    # Non-root users can only see their own info
    if username != env.current_user and not env.is_root:
        print(Fore.RED + "Permission denied: You can only view your own user info")
        return env.pwd
    
    user_data = users[username]
    
    print(Fore.GREEN + f"User information for '{username}':")
    print("-" * 30)
    
    # Print all user properties except password
    for key, value in user_data.items():
        if key != "password":
            print(f"{key}: {value}")
    
    return env.pwd

def help():
    print_user_help()