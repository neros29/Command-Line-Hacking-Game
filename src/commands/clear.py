from colorama import Fore, Style

def execute(args, pwd, machine_name):
    print(Style.RESET_ALL + Fore.RESET + "\033[H\033[J", end="")
    return pwd

def help():
    print("Usage: clear Clears the terminal screen.")
    
