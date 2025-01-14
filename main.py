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



#added play salaries, now we can do time and money saved
#first thing to do is fix logo manager, have it saved locally as well
#how to share this project or atleast the streamlit with others easily.
