import os
import json
import time
import datetime
from colorama import Fore
from utils.utils import path_to_safe_filename, load_machine
import random

class Logger:
    """Logging system for terminal hacking game that logs to both virtual and physical files"""
    
    # Modify these constants at the top of your class
    MAX_LOG_SIZE_KB = 1024  # Increased maximum log file size in KB
    MAX_ENTRIES_PER_LOG = 2000  # Increased maximum number of entries per log file
    LOG_RETENTION_DAYS = 9999  # Effectively disable automatic log deletion
    
    def __init__(self, machine_name="local"):
        self.machine_name = machine_name
        self.current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Set up log directories in physical file system
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        self.logs_dir = os.path.join(self.project_root, "src", "machines", machine_name, "logs")
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Ensure the virtual log directory exists
        self._ensure_log_directory()
        
        # Clean up old logs when starting
        self._clean_old_logs()
    
    def _ensure_log_directory(self):
        """Ensure the /var/log directory exists in the virtual file system"""
        machine_data = load_machine(self.machine_name)
        file_system = machine_data["file_system"]
        
        # Check if /var exists
        if "var" not in file_system:
            file_system["var"] = {}
            
        # Check if /var/log exists
        if "log" not in file_system["var"]:
            file_system["var"]["log"] = {}
        
        # Save the updated machine data
        machine_file_path = os.path.join(self.project_root, "src", "machines", self.machine_name, f"{self.machine_name}.json")
        with open(machine_file_path, 'w') as f:
            json.dump(machine_data, f, indent=4)
            
    def _get_log_file_path(self, log_type):
        """Get the physical path to the log file"""
        filename = f"{log_type}_{self.current_date}.log"
        return os.path.join(self.logs_dir, filename)
        
    def _get_virtual_log_path(self, log_type):
        """Get the virtual path to the log file in the machine's file system"""
        filename = f"{log_type}.log"
        virtual_path = f"/var/log/{filename}"
        return virtual_path
        
    def _update_virtual_log_reference(self, log_type):
        """Update the virtual file system to reference the physical log file"""
        machine_data = load_machine(self.machine_name)
        file_system = machine_data["file_system"]
        
        # Get the safe filename for the physical file
        safe_filename = path_to_safe_filename("/var/log", f"{log_type}.log")
        physical_path = f"src/machines/{self.machine_name}/logs/{log_type}_{self.current_date}.log"
        
        # Update the virtual file system
        file_system["var"]["log"][f"{log_type}.log"] = physical_path
        
        # Save the updated machine data
        machine_file_path = os.path.join(self.project_root, "src", "machines", self.machine_name, f"{self.machine_name}.json")
        with open(machine_file_path, 'w') as f:
            json.dump(machine_data, f, indent=4)
    
    def _clean_old_logs(self):
        """Only manage log size, don't auto-delete based on age"""
        try:
            for filename in os.listdir(self.logs_dir):
                file_path = os.path.join(self.logs_dir, filename)
                if os.path.isfile(file_path):
                    # Check if file size exceeds limit and rotate if needed
                    if os.path.getsize(file_path) > self.MAX_LOG_SIZE_KB * 1024:
                        # Rotate the log - keep only the most recent entries
                        with open(file_path, 'r') as f:
                            lines = f.readlines()
                        
                        # Keep only the last MAX_ENTRIES_PER_LOG entries
                        if len(lines) > self.MAX_ENTRIES_PER_LOG:
                            with open(file_path, 'w') as f:
                                f.writelines(lines[-self.MAX_ENTRIES_PER_LOG:])
        except Exception as e:
            print(f"Error managing logs: {str(e)}")
    
    def _remove_log_from_virtual_fs(self, filename):
        """Remove a log file reference from the virtual file system"""
        try:
            # Extract the log type from filename (e.g., "system" from "system_2023-01-01.log")
            if '_' in filename and '.' in filename:
                log_type = filename.split('_')[0]
                
                # Load machine data
                machine_data = load_machine(self.machine_name)
                
                # Remove the log reference if it exists
                if "var" in machine_data["file_system"] and "log" in machine_data["file_system"]["var"]:
                    log_name = f"{log_type}.log"
                    if log_name in machine_data["file_system"]["var"]["log"]:
                        del machine_data["file_system"]["var"]["log"][log_name]
                        
                        # Save the updated machine data
                        machine_file_path = os.path.join(self.project_root, "src", "machines", 
                                                        self.machine_name, f"{self.machine_name}.json")
                        with open(machine_file_path, 'w') as f:
                            json.dump(machine_data, f, indent=4)
        except Exception:
            # Silently fail on errors - this is cleanup code
            pass
    
    def _check_and_rotate_log(self, log_file):
        """Check if log file size exceeds limit and rotate if needed"""
        try:
            if os.path.exists(log_file) and os.path.getsize(log_file) > self.MAX_LOG_SIZE_KB * 1024:
                # Rotate the log - keep only the most recent entries
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                
                # Keep only the last MAX_ENTRIES_PER_LOG entries
                if len(lines) > self.MAX_ENTRIES_PER_LOG:
                    with open(log_file, 'w') as f:
                        f.writelines(lines[-self.MAX_ENTRIES_PER_LOG:])
                        return True
            return False
        except Exception as e:
            print(f"Error rotating log file: {str(e)}")
            return False
    
    def log(self, message, log_type="system"):
        """Log a message to both virtual and physical files with size management"""
        # Create timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Get physical log file path
        log_file = self._get_log_file_path(log_type)
        
        # Check and rotate log if needed
        self._check_and_rotate_log(log_file)
        
        # Write to physical log file
        with open(log_file, 'a') as f:
            f.write(log_entry)
            
        # Update virtual log reference
        self._update_virtual_log_reference(log_type)
        
    def log_command(self, user, command, pwd, success=True):
        """Log a command execution"""
        status = "SUCCESS" if success else "FAILED"
        message = f"USER[{user}] PWD[{pwd}] CMD[{command}] STATUS[{status}]"
        self.log(message, "commands")
        
    def log_login(self, user, success=True, source_ip=None):
        """Log a login attempt with realistic auth log format"""
        self.log_auth(user, "LOGIN", source_ip if source_ip else "127.0.0.1", success)
        
        # Also maintain original log format for compatibility
        status = "SUCCESS" if success else "FAILED"
        source = f" from {source_ip}" if source_ip else ""
        message = f"LOGIN USER[{user}] STATUS[{status}]{source}"
        self.log(message, "auth")
        
    def log_network(self, source_ip, destination_ip, action, details=None):
        """Log network activity with realistic system log formatting and size management"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hostname = self.machine_name
        
        if action == "SCAN":
            # Create authentic-looking scan detection logs
            ports = details.split("found ")[1].split(" ")[0] if "found" in str(details) else "multiple"
            log_entry = f"[{timestamp}] kernel: [ 1453.276442] [UFW BLOCK] IN=eth0 OUT= MAC=00:16:3e:5e:6c:00:ff:16:3e:3a:d4:70:08:00 " \
                       f"SRC={source_ip} DST={destination_ip} LEN=40 TOS=0x00 PREC=0x00 TTL=249 ID=8475 " \
                       f"PROTO=TCP SPT={random.randint(32000, 65000)} DPT=80 WINDOW=1024 RES=0x00 SYN URGP=0\n"
                       
            # Add multiple firewall entries to simulate multiple connection attempts
            for _ in range(min(int(ports) if ports.isdigit() else 3, 5)):
                port = random.choice([22, 80, 443, 8080, 3306, 21, 23, 25, 110])
                src_port = random.randint(32000, 65000)
                log_entry += f"[{timestamp}] kernel: [ 1453.{random.randint(100000, 999999)}] [UFW BLOCK] IN=eth0 OUT= " \
                             f"MAC=00:16:3e:5e:6c:00:ff:16:3e:3a:d4:70:08:00 SRC={source_ip} " \
                             f"DST={destination_ip} LEN=40 TOS=0x00 PREC=0x00 TTL=249 ID={random.randint(1000, 9999)} " \
                             f"PROTO=TCP SPT={src_port} DPT={port} WINDOW=1024 RES=0x00 SYN URGP=0\n"
            
            # Add IDS detection entry
            log_entry += f"[{timestamp}] snort[12752]: [1:1000002:2] SCAN-NMAP TCP detected {{TCP}} " \
                         f"{source_ip}:{random.randint(32000, 65000)} -> {destination_ip}:* [Classification: Attempted Information Leak] " \
                         f"[Priority: 2] [instance 1]\n"
            
            # Add auth.log style entry
            log_entry += f"[{timestamp}] sshd[1234]: Failed password for invalid user admin from {source_ip} port {random.randint(32000, 65000)} ssh2\n"
        
        elif action == "CONNECT":
            # SSH connection attempt logs
            log_entry = f"[{timestamp}] sshd[1234]: Connection from {source_ip} port {random.randint(32000, 65000)}\n" \
                        f"[{timestamp}] sshd[1234]: Failed password for {details if details else 'invalid user'} " \
                        f"from {source_ip} port {random.randint(32000, 65000)} ssh2\n"
        
        elif action == "BRUTEFORCE":
            # Bruteforce attempt logs
            log_entry = f"[{timestamp}] sshd[1234]: Invalid user {details if details else 'admin'} from {source_ip} port {random.randint(32000, 65000)}\n"
            for _ in range(3):
                log_entry += f"[{timestamp}] sshd[1234]: Failed password for invalid user {random.choice(['admin', 'root', 'user'])} " \
                             f"from {source_ip} port {random.randint(32000, 65000)} ssh2\n"
            log_entry += f"[{timestamp}] sshd[1234]: PAM: 5 more authentication failures; logname= uid=0 euid=0 tty=ssh ruser= rhost={source_ip}\n"
        
        else:
            # Generic network activity log
            detail_str = f" {details}" if details else ""
            log_entry = f"[{timestamp}] IN=eth0 OUT= MAC=00:16:3e:5e:6c:00:ff:16:3e:3a:d4:70:08:00 " \
                        f"SRC={source_ip} DST={destination_ip} LEN=48 TOS=0x00 PREC=0x00 TTL=115 " \
                        f"ID={random.randint(1000, 9999)} PROTO=TCP SPT={random.randint(32000, 65000)} " \
                        f"DPT=80 WINDOW=65535 RES=0x00 SYN URGP=0 ACTION=[{action}]{detail_str}\n"
        
        # Get the log file path
        log_file = self._get_log_file_path("network")
        
        # Check and rotate log if needed
        self._check_and_rotate_log(log_file)
        
        # Write to physical log file
        with open(log_file, 'a') as f:
            f.write(log_entry)
            
        # Update virtual log reference
        self._update_virtual_log_reference("network")
        
    def log_system(self, event, details=None):
        """Log system events like startup and shutdown"""
        detail_str = f" DETAILS[{details}]" if details else ""
        message = f"EVENT[{event}]{detail_str}"
        self.log(message, "system")
        
    def log_file_activity(self, user, file_path, action):
        """Log file system activities like create, modify, delete"""
        message = f"USER[{user}] FILE[{file_path}] ACTION[{action}]"
        self.log(message, "files")
        
    def clear_logs(self):
        """Clear all logs (mainly for testing purposes)"""
        log_types = ["system", "commands", "auth", "network", "files"]
        for log_type in log_types:
            log_file = self._get_log_file_path(log_type)
            if os.path.exists(log_file):
                os.remove(log_file)

    def log_auth(self, user, action, ip=None, success=True, details=None):
        """Create realistic auth.log entries with size management"""
        timestamp = datetime.datetime.now().strftime("%b %d %H:%M:%S")
        hostname = self.machine_name
        pid = random.randint(1000, 9999)
        
        if action == "LOGIN":
            if success:
                log_entry = f"{timestamp} {hostname} sshd[{pid}]: Accepted password for {user} from {ip} port {random.randint(30000, 65000)} ssh2\n" \
                            f"{timestamp} {hostname} sshd[{pid}]: pam_unix(sshd:session): session opened for user {user} by (uid=0)\n"
            else:
                log_entry = f"{timestamp} {hostname} sshd[{pid}]: Failed password for {user} from {ip} port {random.randint(30000, 65000)} ssh2\n"
                # Add additional fail entries for realism
                if random.random() < 0.3:  # 30% chance of multiple failures
                    for _ in range(random.randint(1, 3)):
                        log_entry += f"{timestamp} {hostname} sshd[{pid}]: Failed password for {user} from {ip} port {random.randint(30000, 65000)} ssh2\n"
        
        elif action == "LOGOUT":
            log_entry = f"{timestamp} {hostname} sshd[{pid}]: pam_unix(sshd:session): session closed for user {user}\n"
        
        elif action == "SU":
            if success:
                log_entry = f"{timestamp} {hostname} su: pam_unix(su:session): session opened for user {user} by root(uid=0)\n"
            else:
                log_entry = f"{timestamp} {hostname} su: pam_unix(su:auth): authentication failure; logname=root uid=0 euid=0 tty=/dev/pts/0 ruser=root rhost= user={user}\n" \
                            f"{timestamp} {hostname} su: FAILED su for {user} by root\n"
        
        else:
            detail_str = f" {details}" if details else ""
            log_entry = f"{timestamp} {hostname} auth: ACTION[{action}] USER[{user}]{detail_str}\n"
        
        # Get log file path
        log_file = self._get_log_file_path("auth")
        
        # Check and rotate log if needed
        self._check_and_rotate_log(log_file)
        
        # Write to physical log file
        with open(log_file, 'a') as f:
            f.write(log_entry)
            
        # Update virtual log reference
        self._update_virtual_log_reference("auth")