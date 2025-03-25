from colorama import Fore, Style
import json
import time
import random
from utils.utils import load_machine
from utils.logger import Logger
from utils.network_monitor import log_remote_event
import os
import re

def sanitize_path(path):
    """Sanitize a path to prevent directory traversal attacks"""
    # Replace problematic characters and sequences
    path = re.sub(r'\.\.', '', path)  # Remove ..
    path = re.sub(r'[^a-zA-Z0-9_\-!/]', '_', path)  # Allow only alphanumeric and safe chars
    return path

def execute(args, pwd, machine_name):
    if len(args) < 1:
        print(Fore.RED + "Usage: nmap [IP] [--file|-f]")
        return pwd

    ip = args[0]
    save_to_file = False
    if len(args) > 1:
        if args[0] in ["--file", "-f"]:
            save_to_file = True
            ip = args[1]
        else:
            print(Fore.RED + "Invalid argument. Usage: nmap [IP] [--file|-f]")
            return pwd

    machine_file_path = f"src/machines/{machine_name}/{machine_name}.json"
    machine_data = load_machine(machine_name)
    port_info_path = "src/commands/port_info.json"
    victim_machine = load_machine(ip)

    try:
        ports = victim_machine["meta_data"]["ports"]

        with open(port_info_path, "r") as file:
            port_info = json.load(file)["ports"]

        port_dict = {p["port"]: p for p in port_info}

        # Simulate nmap scan with cool graphics
        output = []
        output.append(Fore.CYAN + Style.BRIGHT + f"Starting Nmap 7.80 ( https://nmap.org ) at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        output.append(Fore.GREEN + f"Nmap scan report for {ip}")        
        output.append(Fore.GREEN + f"Host is up (0.000s latency).")
        output.append(Fore.YELLOW + Style.BRIGHT + "PORT      STATE    SERVICE")
        output.append(Fore.YELLOW + "-"*40)
        

        # Print initial output to console
        for line in output:
            time.sleep(random.uniform(0.1, 0.3))  # Simulate scanning delay
            print(line)

        # Save initial output to file if requested
        if save_to_file:
            sanitized_pwd = sanitize_path(pwd)
            sanitized_ip = sanitize_path(ip)
            scan_file_path = os.path.join("src", "machines", machine_name, 
                                          f"{sanitized_pwd.replace('/', '!')}!nmap_scan_{sanitized_ip}.txt")
            with open(scan_file_path, "w") as file:
                for line in output:
                    file.write(line + "\n")
        
        # Log the scan event on the target machine with detailed scan information
        source_ip = machine_data["meta_data"]["ip"]
        scan_type = random.choice(["SYN Stealth Scan", "TCP Connect Scan", "ACK Scan", "FIN Scan", "XMAS Scan"])
        scan_details = f"Port scan ({scan_type}) from {source_ip} detected, scanning {len(ports)} ports"
        log_remote_event(source_ip, ip, "SCAN", scan_details)
        
        time.sleep(random.uniform(1, 2.5))  # Simulate scanning delay
        for port in ports:
            service = "unknown service"
            if port in port_dict:
                service = port_dict[port]["use_case"]

            # Simulate scan progress
             # Simulate scanning delay
            status = "open"
            service_message = f"{service}".ljust(15)
            line = Fore.GREEN + f"{port}/tcp   {status.ljust(8)} {service_message}"
            print(line)
            output.append(line)
          
        output.append(Fore.GREEN + "\nNmap done: 1 IP address (1 host up) scanned in 5.02 seconds.")
        output.append(Fore.GREEN + "Scan complete.")

        # Print remaining output to console
        for line in output[-2:]:
            print(line)

        # Save remaining output to file if requested
        if save_to_file:
            with open(scan_file_path, "a") as file:
                for line in output[len(output)-2:]:
                    file.write(line + "\n")

            # Update the virtual file system
            current = machine_data["file_system"]
            for directory in pwd.split('/'):
                if directory == "":
                    continue
                current = current[directory]

            virtual_path = scan_file_path
            current[f"nmap_scan_{ip}.txt"] = virtual_path
            with open(machine_file_path, "w") as file:
                json.dump(machine_data, file, indent=4)

        # Log the scan on the scanning machine
        logger = Logger(machine_name)
        scan_info = f"Port scan found {len(ports)} open ports using {scan_type} technique"
        logger.log_network(machine_data["meta_data"]["ip"], ip, "SCAN", scan_info)

    except FileNotFoundError:
        print(Fore.RED + f"Machine with IP {ip} not found.")
    except KeyError:
        print(Fore.RED + f"Invalid machine data for IP {ip}.")

    return pwd

def help():
    print("Usage: nmap [--file|-f] [IP]  - Scans the specified IP address for open ports and optionally saves the output to a file.")

