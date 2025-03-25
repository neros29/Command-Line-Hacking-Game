from colorama import Fore

def execute(args, pwd, machine_name):
    """Display current username"""
    from src.main import modules
    
    env = modules.get("__env__", None)
    if not env:
        print(Fore.RED + "Error: Environment not initialized")
        return pwd
    
    print(env.current_user)
    return pwd

def help():
    print("Display current username")
    print("Usage: whoami")