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

#two calculate flight time calculations??
#salaries by competition and highest in each competition
#write code to figure out how to get total costs for each method.
