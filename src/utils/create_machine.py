import json
import os
import random

def create_linux_file_system(ip, commands):
    linux_file_system = {
        "name": "linux_user",
        "ip": ip,
        "ports": [22, 80, 443],
        "home": {
            "user": {
                "Desktop": {},
                "Documents": {},
                "Pictures": {},
                "Downloads": {},
                "Videos": {},
                "Music": {}
            }
        },
        "root": {
            "bin": {},
            "etc": {},
            "lib": {},
            "usr": {},
            "var": {}
        },
        "tmp": {},
        "bin": commands
    }
    return linux_file_system

def create_website_file_system(ip, commands):
    website_file_system = {
        "name": "website",
        "ip": ip,
        "ports": [80, 443],
        "root": {
            "index.html": "file",
            "about.html": "file",
            "contact.html": "file",
            "assets": {
                "css": {},
                "js": {},
                "images": {}
            }
        },
        "tmp": {},
        "bin": commands
    }
    return website_file_system

def create_windows_file_system(ip, commands):
    windows_file_system = {
        "name": "windows_user",
        "ip": ip,
        "ports": [3389],
        "C:": {
            "Users": {
                "Guest": {
                    "Documents": {},
                    "Downloads": {},
                    "Pictures": {},
                    "Desktop": {}
                },
                "Admin": {
                    "Documents": {},
                    "Downloads": {},
                    "Pictures": {},
                    "Desktop": {},
                    "AppData": {
                        "Local": {},
                        "Roaming": {},
                        "Temp": {}
                    },
                }
            },
            "Program Files": {
                "CommandLineTools": commands                
            },
            "Temp": {
                "tempfiles": {
                }
            },
            "ProgramData": {
                "Settings": {
                    "user_settings.cfg": "file"
                }
            }
        },
        "bin": commands
    }
    return windows_file_system

def save_file_system(file_system, foldername, filename):
    os.makedirs(foldername, exist_ok=True)
    filepath = os.path.join(foldername, filename)
    with open(filepath, 'w') as f:
        json.dump(file_system, f, indent=4)

def get_commands():
    available_commands = []
    for file in list(os.listdir("src/commands")):
        if file.startswith("_") or not file.endswith(".py"):
            continue
        available_commands.append(file[:-3])
    selected_commands = {}
    print("Available commands: ", ", ".join(available_commands))
    print("Enter the commands you want to include in the bin directory (type 'done' to finish):")
    while True:
        command = input("Command: ").strip()
        if command == "done":
            break
        if command in available_commands:
            selected_commands[command] = "command"
        else:
            print(f"Command '{command}' is not available.")
    return selected_commands

def generate_random_ip(existing_ips):
    while True:
        ip = f"192.168.{random.randint(0, 255)}.{random.randint(1, 254)}"
        if ip not in existing_ips:
            return ip

if __name__ == "__main__":
    print("Choose the file system to create:")
    print("1. Linux")
    print("2. Website")
    print("3. Windows")
    choice = input("Enter the number of your choice: ").strip()

    commands = get_commands()

    # Get existing IPs from the machines folder
    existing_ips = set()
    machines_folder = "src/machines"
    if os.path.exists(machines_folder):
        for folder in os.listdir(machines_folder):
            if os.path.isdir(os.path.join(machines_folder, folder)):
                existing_ips.add(folder)

    ip = generate_random_ip(existing_ips)

    if choice == "1":
        file_system = create_linux_file_system(ip, commands)
    elif choice == "2":
        file_system = create_website_file_system(ip, commands)
    elif choice == "3":
        file_system = create_windows_file_system(ip, commands)
    else:
        print("Invalid choice.")
        exit(1)

    foldername = os.path.join(machines_folder, ip)
    filename = f"{ip}.json"
    save_file_system(file_system, foldername, filename)
    print(f"File system created and saved as {os.path.join(foldername, filename)}.")