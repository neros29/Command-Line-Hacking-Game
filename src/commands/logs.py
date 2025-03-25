from colorama import Fore
from utils.utils import load_machine, check_path
from utils.file_utils import resolve_path, read_file
def execute(args, pwd, machine_name):
    """View system logs with options for recent entries only"""
    machine_data = load_machine(machine_name)
    
    # Process command options
    view_lines = 10  # Default number of lines to show
    log_name = None
    
    # Parse arguments
    for i, arg in enumerate(args):
        if arg.startswith("-n") and i + 1 < len(args) and args[i + 1].isdigit():
            view_lines = int(args[i + 1])
        elif not arg.startswith("-") and not arg.isdigit():
            log_name = arg
    
    # List available logs by default
    if not log_name:
        print(Fore.CYAN + "Available logs:")
        if "var" in machine_data["file_system"] and "log" in machine_data["file_system"]["var"]:
            logs = machine_data["file_system"]["var"]["log"]
            if logs:
                for log_name in logs:
                    print(Fore.GREEN + f" - {log_name}")
            else:
                print(Fore.YELLOW + "No logs found.")
        else:
            print(Fore.YELLOW + "No logs directory found.")
        print(Fore.CYAN + "\nUsage: logs [logfile] [-n lines]")
        print(Fore.CYAN + "  -n  Number of recent lines to show (default: 10)")
        return pwd
        
    # View a specific log
    if "var" in machine_data["file_system"] and "log" in machine_data["file_system"]["var"]:
        logs = machine_data["file_system"]["var"]["log"]
        if log_name in logs:
            log_path_parts = resolve_path(f"/var/log/{log_name}.log", pwd, machine_data["file_system"])
            success, log_content = read_file(machine_data, log_path_parts)

            if not success:
                print(Fore.RED + f"Error reading log file: {log_content}")
                return pwd
            
            print(Fore.CYAN + f"=== Log: {log_name} (showing last {view_lines} entries) ===")
            
            # Show only the last N lines
            for line in log_content[-view_lines:]:
                print(Fore.GREEN + line.strip())
                
            if len(log_content) > view_lines:
                print(Fore.YELLOW + f"\n[...{len(log_content) - view_lines} more entries not shown...]")
                print(Fore.YELLOW + f"Use 'logs {log_name} -n {len(log_content)}' to see all entries")
                    
        else:
            print(Fore.RED + f"Log file not found: {log_name}")
    else:
        print(Fore.RED + "Log directory not found")
        
    return pwd

def help():
    print("Usage: logs [logfile] [-n lines] - Views available logs or content of specific log file.")