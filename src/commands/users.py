from colorama import Fore

def execute(args, pwd, machine_name):
    """List all users on the system"""
    from src.main import modules
    
    env = modules.get("__env__", None)
    if not env:
        print(Fore.RED + "Error: Environment not initialized")
        return pwd
    
    # Get users from machine data
    users = env.meta_data.get("users", {})
    
    usernames = list(users.keys())
    print(" ".join(usernames))
    
    return pwd

def help():
    print("List all users on the system")
    print("Usage: users")