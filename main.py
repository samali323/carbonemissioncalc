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



#see if we can add flight times into the database and pull from there?
#see why clicking round trip opens the dashboard
#add player salaries
#
