# Terminal Hacking Game

A text-based terminal simulator that mimics a Unix/Linux environment where players can practice hacking and cybersecurity skills in a safe, virtual environment.

## Features

- Realistic command-line interface with common Unix/Linux commands
- Virtual file system navigation
- Network scanning and exploitation
- Multiple virtual machines with different configurations
- User management with password authentication
- Logging system that tracks player activities
- Customizable environments

## Command Line Options

- `--machine`: Specify the machine name to start with (default: local)
- `--skip-setup`: Skip the user setup screen and launch directly

## Available Commands

The game includes many common Unix/Linux commands including:

- `ls`: List directory contents
- `cd`: Change directory
- `mkdir`: Create directories
- `touch`: Create empty files
- `cat`: Display file contents
- `rm`: Remove files or directories
- `mv`: Move or rename files
- `nmap`: Network scanning tool
- `ssh`: Connect to remote machines
- `passwd`: Change user passwords
- And many more...

## How The Game Works

### Getting Started

1. Run `launch_game.py` to start the game
2. You'll be prompted to set up a root password for the selected machine
3. The game will boot up with a simulated Linux startup sequence
4. Run the game:
5. You'll be presented with a command prompt where you can enter commands

> **Note:** The default password for all users is `toor` if you haven't changed it during setup.

### Command System

- Type `help` to see all available commands
- Type `help [command]` to get specific help for a command
- The game supports command piping (e.g. `cat file.txt | grep password`)
- Most Linux commands work as expected with appropriate permissions

### Network Features

- The local machine is your starting point
- The only machine that can be accessed on the network is `10.10.10.10`
- Use `nmap 10.10.10.10` to scan for open ports
  - Target has services running on ports 50, 80, 443, and 162
- Use `ssh 10.10.10.10` or `ssh admin@10.10.10.10` to attempt connection
  - Authentication requires the correct password

### Security Features

- Commands are logged via a security monitoring system
- Network activities between machines are tracked
- File permissions are enforced based on user rights
- Some commands require root privileges
- Password hashing uses bcrypt for secure storage

## Game Structure

The game simulates a network of machines, each with its own file system, users, and security configurations. Players start on the local machine and can attempt to discover and exploit vulnerabilities to gain access to other machines on the network.

## Installation

### Prerequisites

- Python 3.8 or above
- Git (for cloning the repository)

### Steps

1. Clone this repository:
    - git clone https://github.com/neros29/terminal-hacking-game.git cd terminal-hacking-game
2. Create and activate a virtual environment (recommended)
    - python -m venv .myenv

        - On Windows
            - .myenv\Scripts\activate

        - On macOS/Linux
            - source .myenv/bin/activate
3. Install dependencies
    - pip install -r requirements.txt
4. Run the game
    - python launch_game.py

## Project Status

⚠️ **IMPORTANT**: This project is currently just a showcase of core functionality. It is not a complete game and does not contain any actual missions or objectives. This version demonstrates the terminal environment and command system but lacks gameplay content.

### Current Limitations

- No structured missions or objectives are implemented
- Some commands might not work as expected
- Certain machines or scenarios may be incomplete
- Limited error handling in some parts of the game
- User progress is not saved between sessions

### Future Plans

I am planning significant enhancements in future revisions including:

- Custom scripting language for creating missions and scenarios
- Additional Unix/Linux commands and tools
- Fully attackable machines with realistic vulnerabilities
- Structured hacking challenges with progression system
- Multiple difficulty levels 
- More sophisticated network topology
- Enhanced security mechanisms

## Contributions

Contributions are welcome! Please feel free to submit a Pull Request.

## Contact

If you have any questions or feedback, please open an issue on this repository.

