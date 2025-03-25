#!/usr/bin/env python3
"""
Security daemon for the 10.10.10.10 machine.
This is a simulated daemon that would run on a real server to monitor
and log suspicious network activity.
"""

import os
import time
import datetime
import json

class SecurityDaemon:
    def __init__(self, machine_name="10.10.10.10"):
        self.machine_name = machine_name
        self.network_activity = []
        self.log_dir = os.path.join("src", "machines", machine_name, "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        
    def check_logs(self):
        """Analyze log files for suspicious activity"""
        try:
            log_date = datetime.datetime.now().strftime("%Y-%m-%d")
            network_log = os.path.join(self.log_dir, f"network_{log_date}.log")
            
            if os.path.exists(network_log):
                with open(network_log, "r") as f:
                    logs = f.readlines()
                
                # Process each log entry
                for log in logs:
                    if "SCAN" in log and log not in self.network_activity:
                        self.network_activity.append(log)
                        self.log_security_event("Detected port scan", log)
            
            # Add other types of detection here
            return len(self.network_activity)
        except Exception as e:
            self.log_security_event("Error checking logs", str(e))
            return 0
            
    def log_security_event(self, event_type, details):
        """Log a security event to the security log"""
        try:
            log_date = datetime.datetime.now().strftime("%Y-%m-%d")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            security_log = os.path.join(self.log_dir, f"security_{log_date}.log")
            
            with open(security_log, "a") as f:
                f.write(f"[{timestamp}] EVENT[{event_type}] DETAILS[{details}]\n")
                
            # Update the virtual file system to reference this log
            self.update_log_reference("security")
        except Exception as e:
            print(f"Error logging security event: {str(e)}")
    
    def update_log_reference(self, log_type):
        """Update the machine's virtual file system to include the security log"""
        try:
            # Load machine data
            machine_file_path = os.path.join("src", "machines", self.machine_name, f"{self.machine_name}.json")
            with open(machine_file_path, "r") as f:
                machine_data = json.load(f)
            
            # Add the log reference
            log_date = datetime.datetime.now().strftime("%Y-%m-%d")
            physical_path = f"src/machines/{self.machine_name}/logs/{log_type}_{log_date}.log"
            machine_data["file_system"]["var"]["log"][f"{log_type}.log"] = physical_path
            
            # Save the updated machine data
            with open(machine_file_path, "w") as f:
                json.dump(machine_data, f, indent=4)
        except Exception as e:
            print(f"Error updating log reference: {str(e)}")
    
    def run(self):
        """Continuously monitor for suspicious activity"""
        print(f"[*] Security daemon started on {self.machine_name}")
        try:
            while True:
                events = self.check_logs()
                if events > 0:
                    print(f"[!] Detected {events} security events")
                time.sleep(5)  # Check every 5 seconds
        except KeyboardInterrupt:
            print("\n[*] Security daemon stopped")

if __name__ == "__main__":
    daemon = SecurityDaemon()
    daemon.run()