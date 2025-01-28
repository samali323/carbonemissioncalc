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


#fix the potential cost savings table and the rail and bus operational costs. maybe readd the operational costs tab or have it broken down at the bottom?
#empty leg doesnt make sense to average user
#split charter needs explanation
#need breakdown of how each option is calculated
#see if we can implement nested columns in streamlit https://discuss.streamlit.io/t/columns-nesting-workaround/57376
