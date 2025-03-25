import bcrypt
import os
import json
import logging
from utils.utils import load_machine, save_machine

def hash_password(password):
    """Hash a password using bcrypt."""
    try:
        # Reject None passwords
        if password is None:
            raise ValueError("Password cannot be None")
            
        # Ensure password is string
        if isinstance(password, bytes):
            password_bytes = password
        else:
            password_bytes = str(password).encode('utf-8')
            
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    except Exception as e:
        logging.error(f"Error hashing password: {str(e)}")
        raise ValueError(f"Failed to hash password: {str(e)}")

def verify_password(plain_password, hashed_password):
    """Verify a password against its hash."""
    try:
        # If empty password or hash, fail securely
        if not plain_password or not hashed_password:
            return False
            
        # Handle case where password might be stored in plaintext (legacy)
        if not isinstance(hashed_password, str) or not hashed_password.startswith('$2'):
            return plain_password == hashed_password
        
        # Convert inputs to bytes for bcrypt
        if isinstance(plain_password, bytes):
            pwd_bytes = plain_password
        else:
            pwd_bytes = str(plain_password).encode('utf-8')
            
        hash_bytes = hashed_password.encode('utf-8')
        
        # Verify with bcrypt
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception as e:
        logging.error(f"Password verification error: {str(e)}")
        return False

def migrate_passwords(machine_name=None):
    """
    Migrate plaintext passwords to hashed passwords.
    If machine_name is specified, only migrate that machine.
    Otherwise, migrate all machines.
    """
    # Set up absolute path to machines directory
    machines_dir = os.path.abspath(os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        "machines"
    ))
    
    if machine_name:
        machines = [machine_name]
    else:
        # Get all machine directories
        machines = []
        try:
            if not os.path.exists(machines_dir):
                print(f"Error: Machines directory not found at {machines_dir}")
                return
                
            for d in os.listdir(machines_dir):
                # Skip special directories
                if d.startswith('__') or d.startswith('.'):
                    continue
                
                # Only include directories with matching JSON file
                machine_path = os.path.join(machines_dir, d)
                json_path = os.path.join(machine_path, f"{d}.json")
                
                if os.path.isdir(machine_path) and os.path.exists(json_path):
                    machines.append(d)
        except Exception as e:
            print(f"Error listing machines: {str(e)}")
    
    migrated_count = 0
    
    for machine in machines:
        try:
            machine_data = load_machine(machine)
            
            if not isinstance(machine_data, dict):
                print(f"Warning: Invalid data format for machine {machine}")
                continue
            
            modified = False
                
            # 1. Migrate machine-level password
            if "meta_data" in machine_data and "password" in machine_data["meta_data"]:
                password = machine_data["meta_data"]["password"]
                
                # Skip if password is None or empty
                if password is None or password == "":
                    print(f"Warning: Empty password for machine {machine}")
                # Only hash if not already hashed (not starting with $2)
                elif not str(password).startswith('$2'):
                    try:
                        # Hash the plaintext password
                        machine_data["meta_data"]["password"] = hash_password(password)
                        modified = True
                        print(f"✓ Migrated main password for machine: {machine}")
                        migrated_count += 1
                    except Exception as e:
                        print(f"Error hashing main password for {machine}: {str(e)}")
            
            # 2. Migrate user passwords
            if "meta_data" in machine_data and "users" in machine_data["meta_data"]:
                users = machine_data["meta_data"]["users"]
                
                for username, user_data in users.items():
                    if "password" in user_data:
                        user_password = user_data["password"]
                        
                        # Skip if password is None or empty
                        if user_password is None or user_password == "":
                            continue
                            
                        # Check if already hashed
                        if not str(user_password).startswith('$2'):
                            try:
                                users[username]["password"] = hash_password(user_password)
                                modified = True
                                print(f"✓ Migrated password for user: {username} on machine: {machine}")
                                migrated_count += 1
                            except Exception as e:
                                print(f"Error hashing password for user {username} on {machine}: {str(e)}")
            
            # Save changes if any were made
            if modified:
                save_machine(machine, machine_data)
                    
        except FileNotFoundError:
            print(f"Error: Machine '{machine}' not found")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in machine file for {machine}")
        except Exception as e:
            print(f"Error migrating password for {machine}: {str(e)}")
    
    print(f"\nPassword migration complete! Migrated {migrated_count} passwords.")