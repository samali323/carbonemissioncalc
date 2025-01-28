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

#work on break even analysis, all SAF and Conventional prices shoud be interlinked.
#operational costs tab is sloppy
#carbon costs tab is not need as we have the table
#visualization should be cleaned up as well
