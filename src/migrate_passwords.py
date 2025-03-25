#!/usr/bin/env python3
from utils.password_manager import migrate_passwords
import sys

def main():
    """
    Script to migrate all plaintext passwords to hashed passwords.
    Can be run with a machine name as argument to migrate just that machine.
    """
    if len(sys.argv) > 1:
        machine_name = sys.argv[1]
        print(f"Migrating passwords for machine: {machine_name}")
        migrate_passwords(machine_name)
    else:
        print("Migrating passwords for all machines...")
        migrate_passwords()
    
    print("Password migration complete!")

if __name__ == "__main__":
    main()