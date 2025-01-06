# main.py
"""Main entry point for the application."""
from src.gui.main_window import MainWindow


def main():
    """Run the main application."""
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()


#matches tabs not loading data
#make competition optional
#add other transport options
#add economic equivalencies and other factors from before
#choosing from matches tab should fill out the calculator
#keep all changes in GitHub
