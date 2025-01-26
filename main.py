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

#carbon pricing schemes could be neater
#make a table out of the fuel analysis output, explain the cost benefit analysis. what does SAF premium mean?
#total cost trend should go to ten years and is it based off fuel? also years should not be in commas or decimals
#Cost components should be neater, should fix carbon cost c it is 0 atm, SAF requirement should be 2% and raise to 6% gradually to 2030
#Make the table easier to read
