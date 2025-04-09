import os
import platform

def clear_console():
    """Clear the console screen based on the operating system"""
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')  # For Linux and macOS 