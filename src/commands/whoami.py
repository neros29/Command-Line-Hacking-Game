from colorama import Fore
from utils.utils import get_environment

def execute(args, pwd, machine_name):
    """Display current username"""
    env = get_environment()
    if not env:
        print(Fore.RED + "Error: Environment not initialized")
        return pwd
    
    print(env.current_user)
    return pwd

def help():
    print("Display current username")
    print("Usage: whoami")