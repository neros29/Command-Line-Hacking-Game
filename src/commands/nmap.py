from colorama import Fore, Style
import json
import time
import random
from utils.utils import load_machine
from utils.logger import Logger
from utils.network_monitor import log_remote_event
from src.utils.file_utils import resolve_path, write_to_file
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

    save_to_file = False
    ip = args[0]
    
    if len(args) > 1:
        if args[0] in ["--file", "-f"]:
            save_to_file = True
            ip = args[1]
        elif args[1] in ["--file", "-f"]:
            save_to_file = True
            ip = args[0]
        else:
            print(Fore.RED + "Invalid argument. Usage: nmap [IP] [--file|-f]")
            return pwd

    machine_data = load_machine(machine_name)
    port_info_path = "src/commands/port_info.json"
    
    try:
        victim_machine = load_machine(ip)
        ports = victim_machine["meta_data"]["ports"]

        with open(port_info_path, "r") as file:
            port_info = json.load(file)["ports"]

        port_dict = {p["port"]: p for p in port_info}

        # Simulate nmap scan with cool graphics
        output = []
        output.append(f"Starting Nmap 7.80 ( https://nmap.org ) at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        output.append(f"Nmap scan report for {ip}")        
        output.append(f"Host is up (0.000s latency).")
        output.append("PORT      STATE    SERVICE")
        output.append("-"*40)
        
        # Print initial output to console with colors
        for line in output:
            time.sleep(random.uniform(0.1, 0.3))  # Simulate scanning delay
            print(Fore.CYAN + line)

        # Log the scan event on the target machine with detailed scan information
        source_ip = machine_data["meta_data"]["ip"]
        scan_type = random.choice(["SYN Stealth Scan", "TCP Connect Scan", "ACK Scan", "FIN Scan", "XMAS Scan"])
        scan_details = f"Port scan ({scan_type}) from {source_ip} detected, scanning {len(ports)} ports"
        log_remote_event(source_ip, ip, "SCAN", scan_details)
        
        # Scan port information
        port_output = []
        time.sleep(random.uniform(1, 2.5))  # Simulate scanning delay
        for port in ports:
            service = "unknown service"
            if port in port_dict:
                service = port_dict[port]["use_case"]

            # Simulate scan progress
            status = "open"
            service_message = f"{service}".ljust(15)
            line = f"{port}/tcp   {status.ljust(8)} {service_message}"
            print(Fore.GREEN + line)
            port_output.append(line)
        
        # Finish output
        final_output = [
            "\nNmap done: 1 IP address (1 host up) scanned in 5.02 seconds.",
            "Scan complete."
        ]
        
        # Print remaining output to console
        for line in final_output:
            print(Fore.GREEN + line)
            
        # Save to file if requested
        if save_to_file:
            # Create a file name
            file_name = f"nmap_scan_{ip}.txt"
            # Combine all output sections
            all_output = output + port_output + final_output
            file_content = "\n".join(all_output)
            
            # Use the write_to_file function to save the scan results
            path_parts = resolve_path(file_name, pwd, machine_data["file_system"])
            
            if write_to_file(machine_data, path_parts, file_content):
                print(Fore.CYAN + f"Scan saved to file: {file_name}")
            else:
                print(Fore.RED + f"Error: Could not save scan to file: {file_name}")

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
    print("Usage: nmap [IP] [--file|-f]  - Scans the specified IP address for open ports.")
    print("       --file, -f: Save the scan results to a file in the current directory.")

