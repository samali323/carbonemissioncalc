# main.py
import threading

import webbrowser

import requests

from tkinter import ttk, messagebox
from src.gui.main_window import MainWindow


def main():
    """Run the main application."""
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()



#need breakdown of how each option is calculated
#NPV is wrong
