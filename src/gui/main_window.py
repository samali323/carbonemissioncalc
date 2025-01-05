# src/gui/main_window.py
"""Main GUI window implementation."""
import json
import os
import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox, filedialog

import self

from src.config.constants import DEFAULT_PASSENGERS
from src.data.team_data import get_team_airport, get_airport_coordinates
from src.gui.widgets.auto_complete import TeamAutoComplete, CompetitionAutoComplete
from src.models.emissions import EmissionsCalculator


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Football Team Flight Emissions Calculator")
        self.geometry("1200x800")

        # Initialize calculator and data storage
        self.calculator = EmissionsCalculator()
        self.matches_data = None
        self.filtered_matches_data = None
        self.original_matches_data = None

        # Create main container
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill='both', expand=True)

        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Create tabs
        self.calculator_tab = ttk.Frame(self.notebook, padding=10)
        self.matches_tab = ttk.Frame(self.notebook, padding=10)
        self.analysis_tab = ttk.Frame(self.notebook, padding=10)
        self.settings_tab = ttk.Frame(self.notebook, padding=10)

        # Add tabs to notebook
        self.notebook.add(self.calculator_tab, text='Calculator')
        self.notebook.add(self.matches_tab, text='Matches')
        self.notebook.add(self.analysis_tab, text='Analysis')
        self.notebook.add(self.settings_tab, text='Settings')

        # Initialize file path variable
        self.file_path_var = tk.StringVar()

        # Create all tab contents
        self.create_calculator_tab()
        self.create_matches_tab()
        self.create_analysis_tab()
        self.create_settings_tab()

        # Settings file for persistence
        self.settings_file = "settings.json"

        # Load last settings after UI is created
        self.load_settings()

    def create_analysis_tab(self):
        """Create analysis tab content."""
        # Create frames for different sections
        analysis_container = ttk.Frame(self.analysis_tab, padding="10")
        analysis_container.pack(fill='both', expand=True)

        # Summary frame
        summary_frame = ttk.LabelFrame(analysis_container, text="Summary", padding="10")
        summary_frame.pack(fill='x', pady=(0, 10))

        # Create Treeview for summary data
        self.summary_tree = ttk.Treeview(
            summary_frame,
            columns=("Competition", "Matches", "Total Emissions", "Average"),
            show='headings',
            height=5
        )

        # Configure columns
        self.summary_tree.heading("Competition", text="Competition")
        self.summary_tree.heading("Matches", text="# of Matches")
        self.summary_tree.heading("Total Emissions", text="Total Emissions (tCO₂)")
        self.summary_tree.heading("Average", text="Avg Emissions/Match")

        # Set column widths
        self.summary_tree.column("Competition", width=200)
        self.summary_tree.column("Matches", width=100)
        self.summary_tree.column("Total Emissions", width=150)
        self.summary_tree.column("Average", width=150)

        # Add scrollbar
        summary_scroll = ttk.Scrollbar(summary_frame, orient="vertical", command=self.summary_tree.yview)
        self.summary_tree.configure(yscrollcommand=summary_scroll.set)

        # Pack summary tree and scrollbar
        self.summary_tree.pack(side='left', fill='x', expand=True)
        summary_scroll.pack(side='right', fill='y')

        # Detailed matches frame
        matches_frame = ttk.LabelFrame(analysis_container, text="Match Details", padding="10")
        matches_frame.pack(fill='both', expand=True)

        # Create Treeview for matches data
        self.matches_tree = ttk.Treeview(
            matches_frame,
            columns=("Date", "Teams", "Competition", "Distance", "Emissions"),
            show='headings',
            height=15
        )

        # Configure columns
        self.matches_tree.heading("Date", text="Date")
        self.matches_tree.heading("Teams", text="Teams")
        self.matches_tree.heading("Competition", text="Competition")
        self.matches_tree.heading("Distance", text="Distance (km)")
        self.matches_tree.heading("Emissions", text="Emissions (tCO₂)")

        # Set column widths
        self.matches_tree.column("Date", width=100)
        self.matches_tree.column("Teams", width=250)
        self.matches_tree.column("Competition", width=150)
        self.matches_tree.column("Distance", width=100)
        self.matches_tree.column("Emissions", width=100)

        # Add scrollbars
        matches_y_scroll = ttk.Scrollbar(matches_frame, orient="vertical", command=self.matches_tree.yview)
        matches_x_scroll = ttk.Scrollbar(matches_frame, orient="horizontal", command=self.matches_tree.xview)
        self.matches_tree.configure(yscrollcommand=matches_y_scroll.set, xscrollcommand=matches_x_scroll.set)

        # Pack matches tree and scrollbars
        matches_x_scroll.pack(side='bottom', fill='x')
        matches_y_scroll.pack(side='right', fill='y')
        self.matches_tree.pack(side='left', fill='both', expand=True)

    def update_analysis_display(self):
        """Update analysis tab displays with current data."""
        if self.matches_data is None:
            return

        # Clear existing items
        self.summary_tree.delete(*self.summary_tree.get_children())
        self.matches_tree.delete(*self.matches_tree.get_children())

        try:
            total_matches = 0
            total_emissions = 0
            total_distance = 0
            matches_data = []

            # Group data by competition
            competitions = self.matches_data.groupby('Competition')
            competition_stats = {}

            for comp_name, group in competitions:
                comp_emissions = 0
                comp_distance = 0
                match_count = len(group)
                match_emissions = []

                # Process each match in the competition
                for _, row in group.iterrows():
                    home_team = row['Home Team']
                    away_team = row['Away Team']
                    match_date = row['Date']

                    # Get airports
                    home_airport = get_team_airport(home_team)
                    away_airport = get_team_airport(away_team)

                    if home_airport and away_airport:
                        home_coords = get_airport_coordinates(home_airport)
                        away_coords = get_airport_coordinates(away_airport)

                        if home_coords and away_coords:
                            # Calculate emissions
                            result = self.calculator.calculate_flight_emissions(
                                home_coords['lat'], home_coords['lon'],
                                away_coords['lat'], away_coords['lon'],
                                passengers=30,  # Default passengers
                                is_round_trip=True  # Assume round trip
                            )

                            # Update totals
                            comp_emissions += result.total_emissions
                            comp_distance += result.distance_km
                            total_emissions += result.total_emissions
                            total_distance += result.distance_km
                            total_matches += 1

                            # Store match data for display
                            matches_data.append({
                                'date': match_date,
                                'competition': comp_name,
                                'teams': f"{home_team} vs {away_team}",
                                'distance': result.distance_km,
                                'emissions': result.total_emissions
                            })

                # Store competition statistics
                competition_stats[comp_name] = {
                    'matches': match_count,
                    'emissions': comp_emissions,
                    'distance': comp_distance,
                    'avg_emissions': comp_emissions / match_count if match_count > 0 else 0,
                    'avg_distance': comp_distance / match_count if match_count > 0 else 0
                }

                # Add to summary tree
                self.summary_tree.insert('', 'end', values=(
                    comp_name,
                    match_count,
                    f"{comp_emissions:.2f}",
                    f"{comp_emissions / match_count:.2f}" if match_count > 0 else "0.00"
                ))

            # Add grand total row
            self.summary_tree.insert('', 'end', values=(
                "TOTAL (All Matches)",
                total_matches,
                f"{total_emissions:.2f}",
                f"{total_emissions / total_matches:.2f}" if total_matches > 0 else "0.00"
            ), tags=('total',))

            # Configure total row style
            self.summary_tree.tag_configure('total', background='#E8E8E8', font=('Segoe UI', 9, 'bold'))

            # Sort matches by date
            matches_data.sort(key=lambda x: x['date'])

            # Add matches to matches tree with alternating colors
            for i, match in enumerate(matches_data):
                row_tags = ('even',) if i % 2 == 0 else ('odd',)
                self.matches_tree.insert('', 'end', values=(
                    match['date'].strftime('%Y-%m-%d'),
                    match['teams'],
                    match['competition'],
                    f"{match['distance']:.1f}",
                    f"{match['emissions']:.2f}"
                ), tags=row_tags)

            # Configure row colors
            self.matches_tree.tag_configure('even', background='#f0f0f0')
            self.matches_tree.tag_configure('odd', background='#ffffff')

            # Print overall statistics
            print(f"Analysis Complete:"
                  f"\nTotal Matches: {total_matches}"
                  f"\nTotal Distance: {total_distance:.2f} km"
                  f"\nTotal Emissions: {total_emissions:.2f} metric tons CO2"
                  f"\nAverage Emissions per Match: {total_emissions / total_matches:.2f} metric tons CO2")

        except Exception as e:
            messagebox.showerror("Analysis Error", f"Error updating analysis: {str(e)}")
            raise

    def create_calculator_tab(self):
        """Create calculator tab content."""
        # Left Frame for inputs
        left_frame = ttk.Frame(self.calculator_tab, padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        # Teams section
        team_frame = ttk.LabelFrame(left_frame, text="Match Details", padding="10")
        team_frame.pack(fill='x', pady=(0, 10))

        # Competition
        ttk.Label(team_frame, text="Competition:").pack(anchor=tk.W)
        self.competition_entry = CompetitionAutoComplete(team_frame, width=50)
        self.competition_entry.pack(fill='x', pady=(0, 10))

        # Home Team
        ttk.Label(team_frame, text="Home Team:").pack(anchor=tk.W)
        self.home_team_entry = TeamAutoComplete(team_frame, width=50)
        self.home_team_entry.pack(fill='x', pady=(0, 10))

        # Away Team
        ttk.Label(team_frame, text="Away Team:").pack(anchor=tk.W)
        self.away_team_entry = TeamAutoComplete(team_frame, width=50)
        self.away_team_entry.pack(fill='x', pady=(0, 10))

        # Settings section
        settings_frame = ttk.LabelFrame(left_frame, text="Journey Settings", padding="10")
        settings_frame.pack(fill='x', pady=(0, 10))

        # Passengers entry
        ttk.Label(settings_frame, text="Number of Passengers:").pack(anchor=tk.W)
        self.passengers_entry = ttk.Entry(settings_frame)
        self.passengers_entry.pack(fill='x', pady=(0, 10))
        self.passengers_entry.insert(0, str(DEFAULT_PASSENGERS))

        # Round trip checkbox
        self.round_trip_var = tk.BooleanVar()
        self.round_trip_checkbox = ttk.Checkbutton(
            settings_frame,
            text="Round Trip",
            variable=self.round_trip_var,
            command=self.on_round_trip_toggle
        )
        self.round_trip_checkbox.pack(anchor=tk.W)

        # Buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill='x', pady=10)

        self.calculate_btn = ttk.Button(
            button_frame,
            text="Calculate Emissions",
            command=self.calculate
        )
        self.calculate_btn.pack(side=tk.LEFT, padx=5)

        self.export_button = ttk.Button(
            button_frame,
            text="Export Results",
            command=self.export_to_csv,
            state='disabled'
        )
        self.export_button.pack(side=tk.LEFT, padx=5)

        self.dashboard_button = ttk.Button(
            button_frame,
            text="Open Dashboard",
            command=lambda: webbrowser.open('http://127.0.0.1:8050')
        )
        self.dashboard_button.pack(side=tk.LEFT, padx=5)

        # Right Frame for results
        right_frame = ttk.Frame(self.calculator_tab, padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Results text widget with scrollbar
        self.result_text = tk.Text(right_frame, wrap=tk.WORD, height=30)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.pack(fill='both', expand=True)

        # Configure grid weights
        self.calculator_tab.columnconfigure(1, weight=1)
        self.calculator_tab.rowconfigure(0, weight=1)

    def create_matches_tab(self):
        """Create matches tab content."""
        # Filter Frame
        filter_frame = ttk.LabelFrame(self.matches_tab, text="Filter Matches", padding="10")
        filter_frame.pack(pady=10, padx=20, fill=tk.X)

        # Team Filter
        team_filter_frame = ttk.Frame(filter_frame, padding="5")
        team_filter_frame.pack(fill=tk.X, expand=True)
        ttk.Label(team_filter_frame, text="Team:").pack(side=tk.LEFT, padx=5)
        self.team_filter_entry = TeamAutoComplete(team_filter_frame)
        self.team_filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Competition Filter
        comp_filter_frame = ttk.Frame(filter_frame, padding="5")
        comp_filter_frame.pack(fill=tk.X, expand=True)
        ttk.Label(comp_filter_frame, text="Competition:").pack(side=tk.LEFT, padx=5)
        self.competition_filter_entry = CompetitionAutoComplete(comp_filter_frame)
        self.competition_filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def create_settings_tab(self):
        """Create settings tab content."""
        load_matches_frame = ttk.LabelFrame(self.settings_tab, text="Load Matches Data", padding="10")
        load_matches_frame.pack(pady=20, padx=20, fill=tk.X)

        self.file_path_var = tk.StringVar()

        # File selection row
        file_frame = ttk.Frame(load_matches_frame)
        file_frame.pack(fill=tk.X, pady=5)

        ttk.Label(file_frame, text="CSV File:").pack(side=tk.LEFT, padx=5)
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        browse_button = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_button.pack(side=tk.LEFT, padx=5)

        # Add Load button
        load_button = ttk.Button(load_matches_frame, text="Load", command=self.load_matches_data)
        load_button.pack(pady=10)

        # Add status label
        self.matches_status = ttk.Label(load_matches_frame, text="")
        self.matches_status.pack(pady=5)

    def load_settings(self):
        """Load saved settings including last used CSV path."""

    try:
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
                last_csv = settings.get('last_csv')
                if last_csv and os.path.exists(last_csv):
                    self.file_path_var.set(last_csv)
                    self.load_matches_data()
    except Exception as e:
        print(f"Error loading settings: {e}")

    def save_settings(self):
        """Save current settings."""
        try:
            settings = {
                'last_csv': self.file_path_var.get()
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_matches_data(self):
        """Load matches data from the selected CSV file."""
        try:
            import pandas as pd
            file_path = self.file_path_var.get()

            if not file_path:
                raise ValueError("Please select a CSV file first")

            # Read the CSV file
            data = pd.read_csv(file_path)

            # Convert date format if present
            if 'Date' in data.columns:
                data['Date'] = pd.to_datetime(data['Date'], format='%d/%m/%Y')

            # Store both original and working copies
            self.original_matches_data = data.copy()
            self.matches_data = data.copy()
            self.filtered_matches_data = data.copy()

            # Update matches display if it exists
            if hasattr(self, 'update_matches_display'):
                self.update_matches_display(data)

            # Update status with success message
            self.matches_status.config(
                text=f"Successfully loaded {len(data)} matches",
                foreground='green'
            )

        except ValueError as e:
            messagebox.showerror("Error", str(e))
            self.matches_status.config(
                text=str(e),
                foreground='red'
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load matches: {str(e)}")
            self.matches_status.config(
                text=f"Error loading matches: {str(e)}",
                foreground='red'
            )

    def calculate(self):
        """Calculate emissions based on input."""
        try:
            # Get inputs
            home_team = self.home_team_entry.get()
            away_team = self.away_team_entry.get()
            passengers = int(self.passengers_entry.get())
            is_round_trip = self.round_trip_var.get()

            # Get airports
            home_airport = get_team_airport(home_team)
            away_airport = get_team_airport(away_team)

            if not home_airport or not away_airport:
                raise ValueError("Unable to find airport for one or both teams")

            # Get coordinates
            home_coords = get_airport_coordinates(home_airport)
            away_coords = get_airport_coordinates(away_airport)

            if not home_coords or not away_coords:
                raise ValueError("Unable to find coordinates for one or both airports")

            # Calculate emissions
            result = self.calculator.calculate_flight_emissions(
                home_coords['lat'], home_coords['lon'],
                away_coords['lat'], away_coords['lon'],
                passengers=passengers,
                is_round_trip=is_round_trip
            )

            # Update display
            self.display_results(result, home_team, away_team)

            # Enable export button
            self.export_button.config(state='normal')

        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def display_results(self, result, home_team, away_team):
        """Display calculation results."""
        self.result_text.delete('1.0', tk.END)

        # Format and display results
        summary = (f"Match: {home_team} vs {away_team}\n"
                   f"Distance: {result.distance_km:.2f} km\n"
                   f"Total Emissions: {result.total_emissions:.2f} metric tons CO2\n"
                   f"Per Passenger: {result.per_passenger:.2f} metric tons CO2\n")

        self.result_text.insert('1.0', summary)

    def on_round_trip_toggle(self):
        """Handle round trip toggle."""
        if self.home_team_entry.get() and self.away_team_entry.get():
            self.calculate()

    def export_to_csv(self):
        """Export results to CSV."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if file_path:
            # Implement CSV export logic here
            pass

    def browse_file(self):
        """Open file dialog to select CSV file."""
        filename = filedialog.askopenfilename(
            title="Select Matches File",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.file_path_var.set(filename)
            self.load_matches_data()  # Auto-load the file after selection


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
