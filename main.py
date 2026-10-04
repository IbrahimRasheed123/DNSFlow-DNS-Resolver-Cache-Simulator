"""
Main Entry Point for DNS Resolver & DNS Cache Simulator.
Launch desktop application with:
    python main.py
"""

import sys
import os
import customtkinter as ctk

from config import APP_NAME, APP_VERSION
from gui import DNSAppGUI


def main():
    """Initialize and run the desktop application."""
    # Ensure minimum Python version
    if sys.version_info < (3, 10):
        print(f"Error: {APP_NAME} requires Python 3.10 or higher.")
        print(f"Current version is {sys.version}")
        sys.exit(1)

    # Initialize CustomTkinter Root Window
    root = ctk.CTk()

    # Create and initialize the GUI application
    app = DNSAppGUI(root)

    # Handle graceful exit
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # Start Tkinter main event loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication terminated by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
