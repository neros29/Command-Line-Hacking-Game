from colorama import Fore
import getpass
from utils.password_manager import verify_password
from utils.utils import get_environment

def execute(args, pwd, machine_name):
    """
    Executes a command with superuser privileges.
    Usage: sudo [command] [arguments...]
    If the current user is not root, prompts for the password (up to 3 attempts)
    and verifies it against the encrypted stored password.
    """
    if not args:
        print(Fore.RED + "Usage: sudo [command] [arguments...]")
        return pwd

    env = get_environment()
    if not env:
        print(Fore.RED + "Error: Environment not available")
        return pwd

    if env.is_root:
        return env.execute_command(" ".join(args)) or pwd

    attempts = 0
    while attempts < 3:
        password = getpass.getpass(prompt="Password: ")
        users = env.meta_data.get("users", {})
        user_data = users.get(env.current_user, {})
        # verify_password handles bcrypt-encrypted passwords.
        if verify_password(password, user_data.get("password", "")):
            return env.execute_command(" ".join(args)) or pwd
        else:
            print(Fore.RED + "Incorrect password. Sudo access denied.")
            attempts += 1

    return pwd

def help():
    print("Usage: sudo [command] [arguments...]")
    print("Executes a command with superuser privileges after verifying your encrypted password.")