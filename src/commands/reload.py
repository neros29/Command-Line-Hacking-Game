from colorama import Fore
import os
import importlib
import sys
from src.utils.utils import get_environment

def execute(args, pwd, machine_name):
    """Reload all command modules to test changes without restarting."""
    try:
        # Get reference to the main HackingEnvironment instance
        import src.main as main
        
        # Use the utility function instead of direct access
        env = get_environment()
        if not env:
            print(Fore.RED + "Error: Could not access the environment instance")
            return pwd
        
        # Get the commands directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        commands_dir = current_dir
        
        # Store old command count for comparison
        old_command_count = len(env.commands_list)
        old_commands = set(env.commands_list)
        
        # Reload all modules
        reloaded_count = 0
        new_commands = []
        
        print(Fore.CYAN + "Reloading command modules...")
        
        for filename in os.listdir(commands_dir):
            # Only process Python files, skip directories and __init__.py
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]  # Remove .py extension
                module_path = f'src.commands.{module_name}'
                
                try:
                    # Reload the module if it's already loaded
                    if module_path in sys.modules:
                        main.modules[module_name] = importlib.reload(sys.modules[module_path])
                        reloaded_count += 1
                        print(Fore.GREEN + f"Reloaded: {module_name}")
                    # Import if it's a new module
                    else:
                        main.modules[module_name] = importlib.import_module(module_path)
                        new_commands.append(module_name)
                        print(Fore.MAGENTA + f"New module: {module_name}")
                except Exception as e:
                    print(Fore.RED + f"Error loading {module_name}: {str(e)}")
        
        # Update the commands list - make sure this matches how main.py initializes it
        env.commands_list = []
        
        # Force reload of all modules
        main.modules.clear()
        env.get_commands()
        
        # Explicitly reprocess the commands directory
        for filename in os.listdir(commands_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]
                if module_name not in main.modules:
                    try:
                        main.modules[module_name] = importlib.import_module(f'src.commands.{module_name}')
                    except Exception as e:
                        print(Fore.RED + f"Failed to import {module_name}: {str(e)}")
        
        # Ensure command list is rebuilt
        env.commands_list = list(main.modules.keys())
        
        # Print stats
        current_commands = set(env.commands_list)
        added_commands = current_commands - old_commands
        
        print(Fore.GREEN + f"Reloaded {reloaded_count} modules.")
        if added_commands:
            print(Fore.MAGENTA + f"Added {len(added_commands)} new commands: {', '.join(added_commands)}")
        
        print(Fore.CYAN + "Command reload complete!")
        print(Fore.YELLOW + f"Available commands: {', '.join(sorted(env.commands_list))}")
        
    except Exception as e:
        print(Fore.RED + f"Error reloading modules: {str(e)}")
    
    return pwd

def help():
    print("Usage: reload - Reloads all command modules for testing without restarting the game.")