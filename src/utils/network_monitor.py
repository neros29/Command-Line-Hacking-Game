import os
import json
import datetime
from utils.utils import load_machine
from utils.logger import Logger
import threading

# Global flag to ensure only one security daemon thread is running
SECURITY_DAEMON_RUNNING = False

def log_remote_event(source_ip, target_machine, action, details=None):
    """
    Log an event on a remote machine when it's being accessed
    
    Args:
        source_ip: IP address of the source machine
        target_machine: Name (IP) of the target machine
        action: Type of action being performed (SCAN, SSH, etc.)
        details: Additional details about the action
    """
    global SECURITY_DAEMON_RUNNING
    try:
        # Make sure the target machine has a log directory
        ensure_machine_logs(target_machine)
        
        # Create a timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Prepare the log entry
        if action == "SCAN":
            log_entry = f"[{timestamp}] SRC[{source_ip}] ACTION[{action}] DETAILS[Port scan detected]"
        else:
            detail_str = f" DETAILS[{details}]" if details else ""
            log_entry = f"[{timestamp}] SRC[{source_ip}] ACTION[{action}]{detail_str}"
        
        # Get the path to the target machine's log file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        target_logs_dir = os.path.join(project_root, "src", "machines", target_machine, "logs")
        os.makedirs(target_logs_dir, exist_ok=True)
        
        # Write to the target's network log
        log_file = os.path.join(target_logs_dir, f"network_{log_date}.log")
        with open(log_file, 'a') as f:
            f.write(log_entry + "\n")
        
        # Update the target's virtual file system to reference the log file
        update_target_log_reference(target_machine, "network")
        
        # Trigger the security daemon if the target IP matches and not already running
        if target_machine == "10.10.10.10":
            if not SECURITY_DAEMON_RUNNING:
                # Use __import__ to import from a folder starting with a digit
                daemon_module = __import__("src.machines.10.10.10.security_daemon", fromlist=["SecurityDaemon"])
                SecurityDaemon = getattr(daemon_module, "SecurityDaemon")
                daemon = SecurityDaemon()
                t = threading.Thread(target=daemon.run, daemon=True)
                t.start()
                SECURITY_DAEMON_RUNNING = True
        
        return True
    except Exception as e:
        print(f"Error logging to remote machine: {str(e)}")
        return False

def ensure_machine_logs(machine_name):
    """Ensure the target machine has a log directory structure"""
    machine_data = load_machine(machine_name)
    file_system = machine_data["file_system"]
    
    # Check if /var exists
    if "var" not in file_system:
        file_system["var"] = {}
        
    # Check if /var/log exists
    if "log" not in file_system["var"]:
        file_system["var"]["log"] = {}
    
    # Save the updated machine data
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
    machine_file_path = os.path.join(project_root, "src", "machines", machine_name, f"{machine_name}.json")
    with open(machine_file_path, 'w') as f:
        json.dump(machine_data, f, indent=4)

def update_target_log_reference(machine_name, log_type):
    """Update the target machine's virtual file system to reference the log file"""
    machine_data = load_machine(machine_name)
    file_system = machine_data["file_system"]
    log_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Update the log reference in the virtual file system
    physical_path = f"src/machines/{machine_name}/logs/{log_type}_{log_date}.log"
    file_system["var"]["log"][f"{log_type}.log"] = physical_path
    
    # Save the updated machine data
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
    machine_file_path = os.path.join(project_root, "src", "machines", machine_name, f"{machine_name}.json")
    with open(machine_file_path, 'w') as f:
        json.dump(machine_data, f, indent=4)