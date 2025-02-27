# Core imports
from __future__ import annotations

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import pandas as pd

# Application-specific imports
from src.config.constants import (
    DEFAULT_PASSENGERS, EMISSION_FACTORS, TRANSPORT_MODES, SOCIAL_CARBON_COSTS,
    CARBON_PRICES_EUR, EU_ETS_PRICE
)
from src.dashboard.dashboard_connector import DashboardConnector
from src.data.team_data import get_team_airport, get_airport_coordinates, TEAM_COUNTRIES
from src.gui.theme import COLORS
from src.gui.widgets.auto_complete import TeamAutoComplete, CompetitionAutoComplete
from src.models.emissions import EmissionsCalculator, EmissionsResult
from src.utils.calculations import (
    calculate_transport_emissions, calculate_equivalencies, calculate_distance, determine_mileage_type, calculate_flight_time, format_time_duration
)



# Section 2: Main Window Class Definition and Core UI Setup
class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Football Team Flight Emissions Calculator")
        self.geometry("1200x800")

        # Get project root and set up database connection
        self.project_root = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            "..",
            ".."
        ))
        self.db_path = os.path.join(self.project_root, "data", "routes.db")

        # Configure color scheme
        self.configure(bg=COLORS['bg_primary'])

        # Configure styles
        style = ttk.Style()

        style.configure(
            'Custom.TEntry',
            fieldbackground=COLORS['entry_bg'],
            background=COLORS['bg_secondary'],
            foreground=COLORS['text_primary']
        )

        style.configure(
            'Custom.TButton',
            background=COLORS['accent'],
            foreground=COLORS['text_primary']
        )

        style = ttk.Style()
        style.configure('TFrame', background=COLORS['bg_primary'])
        style.configure('TLabelframe', background=COLORS['bg_primary'])
        style.configure('TLabel', background=COLORS['bg_primary'], foreground=COLORS['text_primary'])
        style.configure('TButton', background=COLORS['accent'])
        style.configure('Custom.TEntry', fieldbackground=COLORS['entry_bg'])

        # Initialize calculator and data storage
        self.calculator = EmissionsCalculator()
        self.matches_data = None
        self.original_matches_data = None

        # Configure text widget style
        self.option_add('*Text*Background', COLORS['bg_secondary'])
        self.option_add('*Text*foreground', COLORS['text_primary'])

        # Update Treeview style
        style.configure(
            "Treeview",
            background=COLORS['bg_secondary'],
            fieldbackground=COLORS['bg_secondary'],
            foreground=COLORS['text_primary']
        )

        style.configure(
            "Treeview.Heading",
            background=COLORS['accent'],
            foreground=COLORS['text_primary']
        )

        # Initialize calculator and data storage
        self.calculator = EmissionsCalculator()
        self.matches_data = None
        self.original_matches_data = None

        # Create main container
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill='both', expand=True)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Create tab frames
        self.calculator_tab = ttk.Frame(self.notebook, padding=10)
        self.analysis_tab = ttk.Frame(self.notebook, padding=10)
        self.settings_tab = ttk.Frame(self.notebook, padding=10)
        self.dashboard_connector = DashboardConnector()
        self.dashboard_connector.start_dashboard(self)

        # Add tabs to notebook
        self.notebook.add(self.calculator_tab, text='Calculator')
        self.notebook.add(self.analysis_tab, text='Analysis')
        self.notebook.add(self.settings_tab, text='Settings')

        # File path variable
        self.file_path_var = tk.StringVar()

        # Create tab contents
        self.create_calculator_tab()
        self.create_analysis_tab()
        self.create_settings_tab()

        # Settings file
        self.settings_file = "settings.json"
        self._load_initial_data()

        self.last_error = None  # Store the last error message
        self.create_error_handling_widgets()

        self.passengers_var = tk.StringVar(value=str(DEFAULT_PASSENGERS))
        self.passengers_entry.config(textvariable=self.passengers_var)
        self.passengers_var.trace_add('write', self.on_passengers_change)

    def create_error_handling_widgets(self):
        """Create widgets for error handling"""
        error_frame = ttk.Frame(self.calculator_tab)
        error_frame.grid(row=2, column=0, columnspan=2, sticky='ew', padx=10, pady=5)

        self.copy_error_button = ttk.Button(
            error_frame,
            text="Copy Last Error",
            command=self.copy_error_to_clipboard,
            state='disabled'
        )
        self.copy_error_button.pack(side='right', padx=5)

    def copy_error_to_clipboard(self):
        """Copy the last error message to clipboard"""
        if self.last_error:
            self.clipboard_clear()
            self.clipboard_append(self.last_error)
            messagebox.showinfo("Success", "Error message copied to clipboard")

    # Section 3: Calculator Tab and Emissions Calculations
    def create_calculator_tab(self):
        # Left input frame
        left_frame = ttk.Frame(self.calculator_tab, padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        # Match details frame
        team_frame = ttk.LabelFrame(left_frame, text="Match Details", padding="10")
        team_frame.pack(fill='x', pady=(0, 10))

        # Home Team
        ttk.Label(team_frame, text="Home Team:").pack(anchor=tk.W)
        self.home_team_entry = TeamAutoComplete(team_frame, width=50)
        self.home_team_entry.pack(fill='x', pady=(0, 10))

        # Away Team
        ttk.Label(team_frame, text="Away Team:").pack(anchor=tk.W)
        self.away_team_entry = TeamAutoComplete(team_frame, width=50)
        self.away_team_entry.pack(fill='x', pady=(0, 10))

        # Journey settings frame
        settings_frame = ttk.LabelFrame(left_frame, text="Journey Settings", padding="10")
        settings_frame.pack(fill='x', pady=(0, 10))

        # Passengers
        ttk.Label(settings_frame, text="Number of Passengers:").pack(anchor=tk.W)
        self.passengers_entry = ttk.Entry(settings_frame)
        self.passengers_entry.pack(fill='x', pady=(0, 10))
        self.passengers_entry.insert(0, str(DEFAULT_PASSENGERS))
        self.passengers_entry.bind('<KeyRelease>', self.on_passengers_change)

        # Round trip checkbox
        self.round_trip_var = tk.BooleanVar()
        self.round_trip_checkbox = ttk.Checkbutton(
            settings_frame,
            text="Round Trip",
            variable=self.round_trip_var,
            command=self.on_round_trip_toggle
        )
        self.round_trip_checkbox.pack(anchor=tk.W)

        # Buttons frame
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill='x', pady=10)

        # Calculate button
        self.calculate_btn = ttk.Button(
            button_frame,
            text="Calculate Emissions",
            command=self.calculate
        )
        self.calculate_btn.pack(side=tk.LEFT, padx=5)

        # Export button
        self.export_button = ttk.Button(
            button_frame,
            text="Export Results",
            command=self.export_to_csv,
            state='disabled'
        )
        self.export_button.pack(side=tk.LEFT, padx=5)

        # Dashboard button
        self.dashboard_button = ttk.Button(
            button_frame,
            text="Open Dashboard",
            command=self.handle_dashboard_click,
            state='enabled'  # Initially disabled
        )
        self.dashboard_button.pack(side=tk.LEFT, padx=5)

        # Results frame
        right_frame = ttk.Frame(self.calculator_tab, padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Results text
        self.result_text = tk.Text(
            right_frame,
            wrap=tk.WORD,
            height=30,
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            font=('Courier', 10), # Using Courier monospace font
            relief='solid',
            borderwidth=1,
            padx=10,
            pady=10
        )
        self.result_text.pack(fill='both', expand=True)
        # Add bindings for team selection

        self.home_team_entry.bind('<<ComboboxSelected>>', self.on_team_selection)
        self.away_team_entry.bind('<<ComboboxSelected>>', self.on_team_selection)

        # Configure grid weights
        self.calculator_tab.columnconfigure(1, weight=1)
        self.calculator_tab.rowconfigure(0, weight=1)

    def on_team_selection(self, event=None):

        """Handle team selection and automatically calculate emissions"""

        home_team = self.home_team_entry.get()

        away_team = self.away_team_entry.get()

        if home_team and away_team:  # Only proceed if both teams are selected

            try:

                self.calculate()  # Calculate emissions
            except Exception as e:

                messagebox.showerror("Error", str(e))

    def on_round_trip_toggle(self):
        """Recalculate emissions when round trip toggle changes"""
        try:
            if self.home_team_entry.get() and self.away_team_entry.get():
                self.calculate()  # This will trigger a full recalculation
        except Exception as e:
            messagebox.showerror("Error", f"Error updating results: {str(e)}")

    def on_passengers_change(self, *args):
        """Recalculate emissions when passenger count changes"""
        if hasattr(self, 'latest_result'):
            self.calculate()

    def handle_dashboard_click(self):
        """Handle dashboard button click"""
        if hasattr(self, 'latest_result'):
            self.dashboard_connector.open_dashboard_browser()
        else:
            messagebox.showwarning("No Data", "Please calculate emissions first")

    def open_dashboard(self):
        try:
            import webbrowser
            import json
            import tempfile
            import os
            # Prepare data for dashboard
            if hasattr(self, 'latest_result'):
                dashboard_data = {
                    'home_team': self.home_team_entry.get(),
                    'away_team': self.away_team_entry.get(),
                    'total_emissions': self.latest_result.total_emissions,
                    'per_passenger': self.latest_result.per_passenger,
                    'distance': self.latest_result.distance_km,
                    'is_round_trip': self.latest_result.is_round_trip,
                    'flight_type': self.latest_result.flight_type
                }
                # Save data to temp file
                temp_dir = tempfile.gettempdir()
                data_file = os.path.join(temp_dir, 'dashboard_data.json')
                with open(data_file, 'w') as f:
                    json.dump(dashboard_data, f)
                # Open dashboard URL
                webbrowser.open('http://127.0.0.1:8050/')
            else:
                messagebox.showwarning("No Data", "Please calculate emissions first")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open dashboard: {str(e)}")

    def calculate(self):
        """Calculate emissions for selected teams"""
        try:
            # Get inputs
            home_team = self.home_team_entry.get()
            away_team = self.away_team_entry.get()
            passengers = int(self.passengers_entry.get())
            is_round_trip = self.round_trip_var.get()

            # Validate inputs
            if not home_team or not away_team:
                raise ValueError("Please enter both home and away teams")

            # Get airports and coordinates
            home_airport = get_team_airport(home_team)
            away_airport = get_team_airport(away_team)

            if not home_airport or not away_airport:
                raise ValueError("Airport not found for one or both teams")

            home_coords = get_airport_coordinates(home_airport)
            away_coords = get_airport_coordinates(away_airport)

            if not home_coords or not away_coords:
                raise ValueError("Coordinates not found for one or both airports")

            # Calculate distance
            distance = calculate_distance(
                home_coords['lat'],
                home_coords['lon'],
                away_coords['lat'],
                away_coords['lon']
            )

            # Calculate emissions using ICAO calculator
            result_dict = self.calculator.icao_calculator.calculate_emissions(
                distance_km=distance,
                aircraft_type="A320",
                cabin_class="business",
                passengers=passengers,
                cargo_tons=2.0,
                is_international=True
            )

            # Adjust for round trip if needed
            if is_round_trip:
                result_dict["emissions_total_kg"] *= 2
                result_dict["emissions_per_pax_kg"] *= 2
                distance *= 2

            # Create EmissionsResult object
            result = EmissionsResult(
                total_emissions=result_dict['emissions_total_kg'] / 1000,
                per_passenger=result_dict['emissions_per_pax_kg'] / 1000,
                distance_km=distance,
                corrected_distance_km=result_dict['corrected_distance_km'],
                fuel_consumption=result_dict['fuel_consumption_kg'],
                flight_type=determine_mileage_type(distance),
                is_round_trip=is_round_trip,
                additional_data=result_dict['factors_applied']
            )

            # Store and update display

            # Store and update display

            self.latest_result = result

            self.display_results(result, home_team, away_team)

            self.update_transport_comparison(result)

            self.export_button.config(state='normal')

            # Update dashboard data

            self.dashboard_connector.update_dashboard_data(self)


        except Exception as e:

            messagebox.showerror("Error", str(e))

            self.last_error = str(e)

            self.copy_error_button.config(state='normal')

    # Section 3 (continued): Calculator Tab and Emissions Calculations
    @staticmethod
    def format_stored_time(seconds):
        """Format time in seconds to a human readable string."""
        if seconds is None:
            return "N/A"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if hours == 0:
            return f"{minutes} minutes"
        elif minutes == 0:
            return f"{hours} hours"
        else:
            return f"{hours} hours {minutes} minutes"

    def update_transport_comparison(self, result):
        """Update transport mode comparison with comprehensive analysis"""
        away_team = self.away_team_entry.get()
        home_team = self.home_team_entry.get()
        away_country = TEAM_COUNTRIES.get(away_team, 'EU')
        carbon_price = CARBON_PRICES_EUR.get(away_country, EU_ETS_PRICE)
        is_round_trip = self.round_trip_var.get()

        # Get stored route information from database
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT driving_duration, transit_duration, driving_distance, transit_distance
                FROM routes 
                WHERE home_team = ? AND away_team = ?
            """, (home_team, away_team))

            row = cursor.fetchone()
            conn.close()

            if row:
                driving_duration, transit_duration, driving_distance, transit_distance = row

                # Double durations if round trip
                if is_round_trip:
                    driving_duration = driving_duration * 2 if driving_duration else None
                    transit_duration = transit_duration * 2 if transit_duration else None
                    driving_distance = driving_distance * 2 if driving_distance else 0
                    transit_distance = transit_distance * 2 if transit_distance else 0

                # Convert stored distances from meters to kilometers
                driving_km = driving_distance / 1000 if driving_distance else 0
                transit_km = transit_distance / 1000 if transit_distance else 0

                driving_time = MainWindow.format_stored_time(driving_duration)
                transit_time = MainWindow.format_stored_time(transit_duration)
            else:
                driving_time = "N/A"
                transit_time = "N/A"
                driving_km = 0
                transit_km = 0

        except Exception as e:
            print(f"Database error: {str(e)}")
            driving_time = "N/A"
            transit_time = "N/A"
            driving_km = 0
            transit_km = 0

        # Calculate emissions for each mode
        air_emissions = result.total_emissions
        base_distance = result.distance_km

        # Calculate rail and bus emissions using stored distances when available
        rail_emissions = calculate_transport_emissions('rail', transit_km or base_distance,
                                                    int(self.passengers_entry.get()),
                                                    is_round_trip)
        bus_emissions = calculate_transport_emissions('bus', driving_km or base_distance,
                                                   int(self.passengers_entry.get()),
                                                   is_round_trip)

        # Calculate flight time with round trip handling built in
        flight_time_seconds = calculate_flight_time(base_distance, is_round_trip)
        flight_time_str = format_time_duration(flight_time_seconds)

        # Transport Mode Comparison table
        self.result_text.insert(tk.END, "\nTransport Mode Comparison:\n")
        self.result_text.insert(tk.END, "=" * 90 + "\n")

        # Column widths
        mode_width = 15
        time_width = 20
        dist_width = 15
        co2_width = 15
        saved_width = 15

        # Header with vertical lines
        header = (
            f"| {'Mode':^{mode_width}} "
            f"| {'Est. Travel Time':^{time_width}} "
            f"| {'Distance (km)':^{dist_width}} "
            f"| {'CO2 (t)':^{co2_width}} "
            f"| {'CO2 Saved (t)':^{saved_width}} |\n"
        )
        self.result_text.insert(tk.END, header)
        self.result_text.insert(tk.END, "|" + "-" * (mode_width + 2) + "|" + "-" * (time_width + 2) +
                              "|" + "-" * (dist_width + 2) + "|" + "-" * (co2_width + 2) + "|" + "-" * (saved_width + 2) + "|\n")

        # Data rows with vertical lines
        modes_data = [
            ("Air", flight_time_str, base_distance, air_emissions, None),
            ("Rail", transit_time, transit_km or base_distance, rail_emissions, air_emissions - rail_emissions),
            ("Bus", driving_time, driving_km or base_distance, bus_emissions, air_emissions - bus_emissions)
        ]

        for mode, time, dist, co2, saved in modes_data:
            saved_str = f"{saved:^{saved_width}.2f}" if saved is not None else " " * saved_width
            row = (
                f"| {mode:^{mode_width}} "
                f"| {time:^{time_width}} "
                f"| {dist:^{dist_width}.1f} "
                f"| {co2:^{co2_width}.2f} "
                f"| {saved_str} |\n"
            )
            self.result_text.insert(tk.END, row)


        self.result_text.insert(tk.END, "=" * 90 + "\n")

        # Carbon Price Analysis with vertical lines
        self.result_text.insert(tk.END, f"\nCarbon Price Analysis ({away_country}):\n")
        self.result_text.insert(tk.END, "=" * 70 + "\n")
        self.result_text.insert(tk.END, f"Carbon Price: €{carbon_price:.2f}/tCO2\n\n")

        # Carbon costs table with vertical lines
        mode_width = 20
        cost_width = 20

        for mode, emissions in [("Air", air_emissions), ("Rail", rail_emissions), ("Bus", bus_emissions)]:
            cost = emissions * carbon_price
            row = f"| {mode:^{mode_width}} | €{cost:^{cost_width}.2f} |\n"
            self.result_text.insert(tk.END, row)

        # Social Cost Analysis with vertical lines
        self.result_text.insert(tk.END, "\nSocial Cost Analysis:\n")
        self.result_text.insert(tk.END, "=" * 70 + "\n")

        # Column widths for social cost table
        mode_col = 12
        type_col = 12
        cost_col = 10

        # Header with vertical lines
        header = (
            f"| {'Mode':^{mode_col}} "
            f"| {'Cost Type':^{type_col}} "
            f"| {'Low':^{cost_col}} "
            f"| {'Median':^{cost_col}} "
            f"| {'Mean':^{cost_col}} "
            f"| {'High':^{cost_col}} |\n"
        )
        self.result_text.insert(tk.END, header)
        self.result_text.insert(tk.END, "|" + "-" * (mode_col + 2) + "|" + "-" * (type_col + 2) +
                                "|" + "-" * (cost_col + 2) + "|" + "-" * (cost_col + 2) +
                                "|" + "-" * (cost_col + 2) + "|" + "-" * (cost_col + 2) + "|\n")

        # Social costs data with vertical lines
        for mode, emissions in [("Air", air_emissions), ("Rail", rail_emissions), ("Bus", bus_emissions)]:
            synthetic_costs = [
                emissions * SOCIAL_CARBON_COSTS['synthetic_iqr_low'],
                emissions * SOCIAL_CARBON_COSTS['synthetic_median'],
                emissions * SOCIAL_CARBON_COSTS['synthetic_mean'],
                emissions * SOCIAL_CARBON_COSTS['synthetic_iqr_high']
            ]

            # Synthetic row
            synth_row = (
                f"| {mode:^{mode_col}} "
                f"| {'Synthetic':^{type_col}} "
                f"| €{synthetic_costs[0]:^{cost_col - 1}.0f} "
                f"| €{synthetic_costs[1]:^{cost_col - 1}.0f} "
                f"| €{synthetic_costs[2]:^{cost_col - 1}.0f} "
                f"| €{synthetic_costs[3]:^{cost_col - 1}.0f} |\n"
            )
            self.result_text.insert(tk.END, synth_row)

            # EPA and IWG rows
            epa_cost = emissions * SOCIAL_CARBON_COSTS['epa_median']
            iwg_cost = emissions * SOCIAL_CARBON_COSTS['iwg_75th']

            epa_row = (
                f"| {' ':^{mode_col}} "
                f"| {'EPA':^{type_col}} "
                f"| {' ':^{cost_col}} "
                f"| €{epa_cost:^{cost_col - 1}.0f} "
                f"| {' ':^{cost_col}} "
                f"| {' ':^{cost_col}} |\n"
            )
            iwg_row = (
                f"| {' ':^{mode_col}} "
                f"| {'IWG':^{type_col}} "
                f"| {' ':^{cost_col}} "
                f"| €{iwg_cost:^{cost_col - 1}.0f} "
                f"| {' ':^{cost_col}} "
                f"| {' ':^{cost_col}} |\n"
            )

            self.result_text.insert(tk.END, epa_row)
            self.result_text.insert(tk.END, iwg_row)

            if mode != "Bus":  # Don't add separator after last mode
                self.result_text.insert(tk.END, "|" + "-" * (mode_col + 2) + "|" + "-" * (type_col + 2) +
                                        "|" + "-" * (cost_col + 2) + "|" + "-" * (cost_col + 2) +
                                        "|" + "-" * (cost_col + 2) + "|" + "-" * (cost_col + 2) + "|\n")

    def _calculate_air_route_factor(self, distance_km: float) -> float:
        """Calculate route factor for air travel"""
        flight_type = determine_mileage_type(distance_km)

        if flight_type == "Short":
            return EMISSION_FACTORS['ShortBusiness']
        elif flight_type == "Medium":
            return EMISSION_FACTORS['MediumBusiness']
        else:
            return EMISSION_FACTORS['LongBusiness']

    def _calculate_rail_route_factor(self, distance_km: float) -> float:
        """Calculate route factor for rail travel"""
        return TRANSPORT_MODES['rail']['co2_per_km']

    def _calculate_bus_route_factor(self, distance_km: float) -> float:
        """Calculate route factor for bus travel"""
        return TRANSPORT_MODES['bus']['co2_per_km']

    def display_results(self, result, home_team, away_team):
        """Display calculation results in the results text widget"""

        self.result_text.delete(1.0, tk.END)
        # Configure tags for styling
        self.result_text.tag_configure('header',
                                       font=('Segoe UI', 12, 'bold'),
                                       foreground=COLORS['accent'])

        self.result_text.tag_configure('subheader',
                                       font=('Segoe UI', 11, 'bold'),
                                       foreground=COLORS['accent_light'])

        self.result_text.tag_configure('normal',
                                       font=('Segoe UI', 10),
                                       foreground=COLORS['text_primary'])

        # Flight Details Section
        self.result_text.insert(tk.END, "🛫 Flight Details\n")
        self.result_text.insert(tk.END, "-" * 40 + "\n")
        self.result_text.insert(tk.END, f"🏠 Home Team: {home_team} \n    Airport: {get_team_airport(home_team)}\n")
        self.result_text.insert(tk.END, f"🏃 Away Team: {away_team} \n    Airport: {get_team_airport(away_team)}\n")
        self.result_text.insert(tk.END, f"📏 Distance: {result.distance_km:,.1f} km\n")
        self.result_text.insert(tk.END, f"✈️ Flight Type: {result.flight_type}\n")
        self.result_text.insert(tk.END, f"🔄 Round Trip: {'Yes ↔️' if result.is_round_trip else 'No →'}\n\n")

        # Emissions Section
        self.result_text.insert(tk.END, "🌡️ Emissions Results\n")
        self.result_text.insert(tk.END, "-" * 40 + "\n")
        self.result_text.insert(tk.END, f"📊 Total CO2: {result.total_emissions:,.2f} metric tons\n")
        self.result_text.insert(tk.END, f"👤 Per Passenger: {result.per_passenger:,.2f} metric tons\n\n")

        # Environmental Equivalencies Section
        self.result_text.insert(tk.END, "🌍 Environmental Impact Equivalencies\n")
        self.result_text.insert(tk.END, "-" * 40 + "\n")

        # Calculate equivalencies
        equivalencies = calculate_equivalencies(result.total_emissions)

        # Organize equivalencies by category
        categories = {
            "🚗 Transportation Impact": {
                'gasoline_vehicles_year': "Gasoline vehicles driven for one year",
                'electric_vehicles_year': "Electric vehicles driven for one year",
                'gasoline_vehicle_miles': "Miles driven by gasoline vehicle"
            },
            "⚡ Energy Usage": {
                'homes_energy_year': "Homes' energy use for one year",
                'homes_electricity_year': "Homes' electricity use for one year",
                'smartphones_charged': "Smartphones charged"
            },
            "🌳 Environmental Offset": {
                'tree_seedlings_10years': "Tree seedlings grown for 10 years",
                'forest_acres_year': "Acres of U.S. forests in one year",
                'forest_preserved_acres': "Acres of U.S. forests preserved"
            },
            "♻️ Waste & Resources": {
                'waste_tons_recycled': "Tons of waste recycled",
                'garbage_trucks_recycled': "Garbage trucks of waste recycled",
                'trash_bags_recycled': "Trash bags of waste recycled"
            },
            "⛽ Fuel Equivalents": {
                'gasoline_gallons': "Gallons of gasoline",
                'diesel_gallons': "Gallons of diesel",
                'propane_cylinders': "Propane cylinders for BBQ",
                'oil_barrels': "Barrels of oil"
            }
        }

        # Display equivalencies by category
        for category, items in categories.items():
            self.result_text.insert(tk.END, f"\n{category}\n")
            self.result_text.insert(tk.END, "-" * 30 + "\n")
            for key, description in items.items():
                if key in equivalencies:
                    value = equivalencies[key]
                    formatted_value = f"{value:,.2f}"
                    self.result_text.insert(tk.END, f"  • {formatted_value} {description}\n")

        # Footer
        self.result_text.insert(tk.END, "\n" + "=" * 80 + "\n")
        self.result_text.insert(tk.END, "💡 This report helps visualize the environmental impact of the flight\n")
        self.result_text.insert(tk.END, "🌱 Consider sustainable alternatives when possible\n")

        # Enable export button if it exists
        if hasattr(self, 'export_button'):
            self.export_button.config(state='normal')

        # Add dashboard button at the bottom

        self.result_text.insert(tk.END, "\n\n")

        # Configure tag for dashboard link

        self.result_text.tag_configure(

            "dashboard_link",

            foreground=COLORS['accent'],

            font=('Segoe UI', 10, 'underline'),

            justify='center'

        )

        # Bind click event to dashboard link

        self.result_text.tag_bind(

            "dashboard_link",

            '<Button-1>',

            lambda e: self.open_dashboard(result)

        )

        # Change cursor on hover

        self.result_text.tag_bind(

            "dashboard_link",

            '<Enter>',

            lambda e: self.result_text.configure(cursor="hand2")

        )

        self.result_text.tag_bind(

            "dashboard_link",

            '<Leave>',

            lambda e: self.result_text.configure(cursor="")

        )

    def open_dashboard(self, result):
        """Open the Dash dashboard with current calculation results"""
        try:
            # Prepare data for dashboard
            dashboard_data = {
                'total_emissions': result.total_emissions,
                'per_passenger': result.per_passenger,
                'distance_km': result.distance_km,
                'flight_type': result.flight_type,
                'is_round_trip': result.is_round_trip,
                'home_team': self.home_team_entry.get(),
                'away_team': self.away_team_entry.get(),
                'passengers': int(self.passengers_entry.get())
            }

            # Save data to temporary file for dashboard to read
            import json
            import tempfile
            import webbrowser
            import os

            temp_dir = tempfile.gettempdir()
            data_file = os.path.join(temp_dir, 'dashboard_data.json')

            with open(data_file, 'w') as f:
                json.dump(dashboard_data, f)

            # Open dashboard URL
            webbrowser.open('http://127.0.0.1:8050/')

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open dashboard: {str(e)}")

    # Section 4: Analysis Tab and Data Processing

    def create_analysis_tab(self):
        """Create enhanced analysis tab with sorting and filtering"""
        # Configure Treeview styles
        style = ttk.Style()

        # Configure both treeviews with identical heading styles
        for tree_type in ["Summary", "Match"]:
            # Base treeview style
            style.configure(
                f"{tree_type}.Treeview",
                background=COLORS['bg_secondary'],
                foreground=COLORS['text_primary'],
                fieldbackground=COLORS['bg_secondary']
            )

            # Heading style
            style.configure(
                f"{tree_type}.Treeview.Heading",
                background=COLORS['accent'],
                foreground=COLORS['bg_secondary'],
                relief='flat'
            )

            # Add hover effect for headers
            style.map(
                f"{tree_type}.Treeview.Heading",
                background=[('active', COLORS['accent_light'])]
            )

        # Create main container
        analysis_container = ttk.Frame(self.analysis_tab, padding="10")
        analysis_container.pack(fill='both', expand=True)

        # Summary section
        summary_frame = ttk.LabelFrame(analysis_container, text="Summary", padding="10")
        summary_frame.pack(fill='x', pady=(0, 10))

        # Create summary tree
        self.summary_tree = ttk.Treeview(
            summary_frame,
            columns=("Competition", "Matches", "Total Emissions", "Average"),
            show='headings',
            height=5,
            style="Summary.Treeview"
        )

        # Configure summary columns with sorting
        for col in ["Competition", "Matches", "Total Emissions", "Average"]:
            self.summary_tree.heading(
                col,
                text=col,
                anchor='center',
                command=lambda c=col: self.sort_treeview(self.summary_tree, c, False)
            )
            self.summary_tree.column(col, anchor='center')

        # Add summary scrollbar
        summary_scroll = ttk.Scrollbar(summary_frame, orient="vertical", command=self.summary_tree.yview)
        self.summary_tree.configure(yscrollcommand=summary_scroll.set)
        self.summary_tree.pack(side='left', fill='x', expand=True)
        summary_scroll.pack(side='right', fill='y')

        # Match Details section
        matches_frame = ttk.LabelFrame(analysis_container, text="Match Details", padding="10")
        matches_frame.pack(fill='both', expand=True)

        # Filter frame
        filter_frame = ttk.Frame(matches_frame)
        filter_frame.pack(fill='x', pady=(0, 5))

        # Filter fields with autocomplete
        self.filters = {}

        # Home team filter
        ttk.Label(filter_frame, text="Home Team:").grid(row=0, column=0, padx=5, pady=5)
        self.filters['Home Team'] = TeamAutoComplete(
            filter_frame,
            width=20,
            style='Custom.TEntry'
        )
        self.filters['Home Team'].grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        # Away team filter
        ttk.Label(filter_frame, text="Away Team:").grid(row=0, column=2, padx=5, pady=5)
        self.filters['Away Team'] = TeamAutoComplete(
            filter_frame,
            width=20,
            style='Custom.TEntry'
        )
        self.filters['Away Team'].grid(row=0, column=3, padx=5, pady=5, sticky='ew')

        # Competition filter
        ttk.Label(filter_frame, text="Competition:").grid(row=0, column=4, padx=5, pady=5)
        self.filters['Competition'] = CompetitionAutoComplete(
            filter_frame,
            width=20,
            style='Custom.TEntry'
        )
        self.filters['Competition'].grid(row=0, column=5, padx=5, pady=5, sticky='ew')

        # Filter buttons
        button_frame = ttk.Frame(filter_frame)
        button_frame.grid(row=0, column=6, padx=5, pady=5)

        ttk.Button(
            button_frame,
            text="Apply Filters",
            command=self.apply_filters,
            style='Custom.TButton'
        ).pack(side='left', padx=2)

        ttk.Button(
            button_frame,
            text="Clear Filters",
            command=self.clear_filters,
            style='Custom.TButton'
        ).pack(side='left', padx=2)

        # Configure filter frame grid weights
        for i in range(7):
            filter_frame.grid_columnconfigure(i, weight=1)

        # Bind events for filter updates
        for filter_widget in self.filters.values():
            filter_widget.bind('<KeyRelease>', lambda e: self.on_filter_change())

        # Create matches tree
        self.matches_tree = ttk.Treeview(
            matches_frame,
            columns=("Home Team", "Away Team", "Competition"),
            show='headings',
            height=15,
            style="Match.Treeview"
        )

        # Configure alternating row colors
        self.matches_tree.tag_configure('evenrow', background=COLORS['bg_secondary'])
        self.matches_tree.tag_configure('oddrow', background=COLORS['bg_secondary'])

        # Configure match columns with sorting
        for col in ["Home Team", "Away Team", "Competition"]:
            self.matches_tree.heading(
                col,
                text=col,
                anchor='center',
                command=lambda c=col: self.sort_treeview(self.matches_tree, c, False)
            )
            self.matches_tree.column(col, anchor='center')

        # Add matches scrollbars
        y_scroll = ttk.Scrollbar(matches_frame, orient="vertical", command=self.matches_tree.yview)
        x_scroll = ttk.Scrollbar(matches_frame, orient="horizontal", command=self.matches_tree.xview)

        self.matches_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        # Pack matches components
        x_scroll.pack(side='bottom', fill='x')
        y_scroll.pack(side='right', fill='y')
        self.matches_tree.pack(fill='both', expand=True)

        # Add match selection bindings
        self.add_match_selection_bindings()

    def on_filter_change(self):
        """Handle real-time filter updates"""
        if hasattr(self, '_filter_timer'):
            self.after_cancel(self._filter_timer)

        self._filter_timer = self.after(300, self.apply_filters)

    def sort_treeview(self, tree, col, reverse):
        """Sort treeview contents by column"""
        data = []

        # Get column index
        cols = tree["columns"]
        col_idx = cols.index(col)

        # Get data
        for item in tree.get_children(''):
            values = tree.item(item)['values']
            data.append((values, item))

        def convert(value):
            try:
                # Remove commas and convert to float
                return float(str(value).replace(',', ''))
            except (ValueError, TypeError):
                return str(value).lower()

        # Sort data
        data.sort(key=lambda x: convert(x[0][col_idx]), reverse=reverse)

        # Rearrange items
        for idx, (values, item) in enumerate(data):
            tree.move(item, '', idx)

        # Switch sort direction next time
        tree.heading(col, command=lambda: self.sort_treeview(tree, col, not reverse))

    def apply_filters(self):
        """Apply filters to match details"""
        filters = {
            'Home Team': self.filters['Home Team'].get().lower(),
            'Away Team': self.filters['Away Team'].get().lower(),
            'Competition': self.filters['Competition'].get().lower()
        }

        hidden_items = []
        for item in self.matches_tree.get_children():
            values = self.matches_tree.item(item)['values']
            matches_filters = all(
                not f or f in str(values[i]).lower()
                for i, f in enumerate(filters.values())
            )

            if not matches_filters:
                self.matches_tree.detach(item)
                hidden_items.append(item)

        # Store hidden items for restoration
        self.hidden_items = hidden_items

    def clear_filters(self):
        """Clear all filters"""
        for filter_widget in self.filters.values():
            filter_widget.set('')  # Use set() method for autocomplete widgets

        # Restore hidden items
        if hasattr(self, 'hidden_items'):
            for item in self.hidden_items:
                self.matches_tree.move(item, '', 'end')
            self.hidden_items = []

    def add_match_selection_bindings(self):
        """Add bindings for match selection"""
        self.matches_tree.bind("<Double-1>", self.select_match)
        self.matches_tree.bind("<Return>", self.select_match)

    def select_match(self, event):
        """Handle match selection from analysis tab"""
        selection = self.matches_tree.selection()

        if not selection:
            return

        # Get match details
        values = self.matches_tree.item(selection[0])['values']

        # Update calculator entries
        self.home_team_entry.set_text(values[0])  # Use set_text() for TeamAutoComplete
        self.away_team_entry.set_text(values[1])
        self.round_trip_var.set(False)

        try:
            # Get inputs
            home_team = values[0]
            away_team = values[1]
            passengers = int(self.passengers_entry.get())
            is_round_trip = self.round_trip_var.get()

            # Get airports and coordinates
            home_airport = get_team_airport(home_team)
            away_airport = get_team_airport(away_team)

            if not home_airport or not away_airport:
                raise ValueError("Airport not found for one or both teams")

            home_coords = get_airport_coordinates(home_airport)
            away_coords = get_airport_coordinates(away_airport)

            if not home_coords or not away_coords:
                raise ValueError("Coordinates not found for one or both airports")

            # Calculate distance first
            distance = calculate_distance(
                home_coords['lat'],
                home_coords['lon'],
                away_coords['lat'],
                away_coords['lon']
            )

            # Calculate emissions using ICAO calculator
            result_dict = self.calculator.icao_calculator.calculate_emissions(
                distance_km=distance,
                aircraft_type="A320",
                cabin_class="business",
                passengers=passengers,
                cargo_tons=2.0,
                is_international=True
            )

            # Create EmissionsResult object
            result = EmissionsResult(
                total_emissions=result_dict['emissions_total_kg'] / 1000,  # Convert to metric tons
                per_passenger=result_dict['emissions_per_pax_kg'] / 1000,
                distance_km=distance,
                corrected_distance_km=result_dict['corrected_distance_km'],
                fuel_consumption=result_dict['fuel_consumption_kg'],
                flight_type=determine_mileage_type(distance),
                is_round_trip=is_round_trip,
                additional_data=result_dict['factors_applied']
            )

            # Display results
            self.display_results(result, home_team, away_team)
            self.update_transport_comparison(result)
            self.export_button.config(state='normal')

            # Switch to calculator tab
            self.notebook.select(self.calculator_tab)

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def update_analysis_display(self):
        if self.matches_data is None:
            return

        self.summary_tree.delete(*self.summary_tree.get_children())
        self.matches_tree.delete(*self.matches_tree.get_children())

        try:
            total_matches = total_emissions = total_distance = 0
            matches_data = []
            competitions = self.matches_data.groupby('Competition')

            # Configure styles for summary tree - use COLORS dictionary
            style = ttk.Style()
            style.configure(
                "Summary.Treeview.Heading",
                background=COLORS['bg_primary'],  # Use accent color from COLORS
                foreground=COLORS['text_primary'],  # Use text color from COLORS
            )

            for comp_name, group in competitions:
                comp_emissions = comp_distance = 0
                match_count = len(group)

                for _, row in group.iterrows():
                    home_team = row['Home Team']
                    away_team = row['Away Team']
                    home_airport = get_team_airport(home_team)
                    away_airport = get_team_airport(away_team)

                    if home_airport and away_airport:
                        home_coords = get_airport_coordinates(home_airport)
                        away_coords = get_airport_coordinates(away_airport)

                        if home_coords and away_coords:
                            distance = calculate_distance(
                                home_coords['lat'], home_coords['lon'],
                                away_coords['lat'], away_coords['lon']
                            )

                            if distance == 0.0:
                                match_count -= 1
                                continue

                            result = self.calculator.calculate_flight_emissions(
                                home_coords['lat'], home_coords['lon'],
                                away_coords['lat'], away_coords['lon'],
                                passengers=30,
                                is_round_trip=True
                            )

                            comp_emissions += result.total_emissions
                            comp_distance += result.distance_km
                            total_emissions += result.total_emissions
                            total_distance += result.distance_km
                            total_matches += 1

                            matches_data.append({
                                'home_team': home_team,
                                'away_team': away_team,
                                'competition': comp_name,
                            })

                if match_count > 0:
                    avg_emissions = comp_emissions / match_count
                    self.summary_tree.insert('', 'end', values=(
                        comp_name,
                        self.format_number(match_count),
                        self.format_number(comp_emissions),
                        self.format_number(avg_emissions)
                    ))

            if total_matches > 0:
                self.summary_tree.insert('', 'end', values=(
                    "TOTAL",
                    self.format_number(total_matches),
                    self.format_number(total_emissions),
                    self.format_number(total_emissions / total_matches)
                ), tags=('total',))

                # Use COLORS for total row styling
                self.summary_tree.tag_configure('total',
                                                background=COLORS['bg_primary'],  # Use accent color
                                                foreground=COLORS['bg_secondary'],  # Light text for contrast
                                                font=('Segoe UI', 9, 'bold'))

            # Configure alternating row colors using COLORS
            self.matches_tree.tag_configure('evenrow',
                                            background=COLORS['bg_primary'])  # Light accent color
            self.matches_tree.tag_configure('oddrow',
                                            background=COLORS['bg_secondary'])  # Background color

            # Update matches tree with alternating colors
            for idx, match in enumerate(matches_data):
                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                self.matches_tree.insert('', 'end', values=(
                    match['home_team'],
                    match['away_team'],
                    match['competition'],
                ), tags=(tag,))

        except Exception as e:
            messagebox.showerror("Analysis Error", f"Error updating analysis: {str(e)}")
            raise

    # Section 5: Settings and Utilities
    def create_settings_tab(self):
        """Create settings tab contents"""
        # Load data frame
        load_frame = ttk.LabelFrame(self.settings_tab, text="Load Data", padding="10")
        load_frame.pack(pady=20, padx=20, fill=tk.X)

        # File selection
        file_frame = ttk.Frame(load_frame)
        file_frame.pack(fill=tk.X, pady=5)

        ttk.Label(file_frame, text="CSV File:").pack(side=tk.LEFT, padx=5)
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Buttons
        button_frame = ttk.Frame(load_frame)
        button_frame.pack(fill=tk.X, pady=10)

        browse_button = ttk.Button(button_frame, text="Browse", command=self.browse_file)
        browse_button.pack(side=tk.LEFT, padx=5)

        load_button = ttk.Button(button_frame, text="Load", command=self.load_matches_data)
        load_button.pack(side=tk.LEFT, padx=5)

        save_button = ttk.Button(button_frame, text="Save Settings", command=self.save_settings)
        save_button.pack(side=tk.RIGHT, padx=5)

        # Status label
        self.matches_status = ttk.Label(load_frame, text="")
        self.matches_status.pack(pady=5)

    def _load_initial_data(self):
        """Load initial data from settings or default file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    last_csv = settings.get('last_csv')
                    if last_csv and os.path.exists(last_csv):
                        self.file_path_var.set(last_csv)
                        self.load_matches_data()
                        return

            if os.path.exists('cleaned_matches.csv'):
                self.file_path_var.set('cleaned_matches.csv')
                self.load_matches_data()
        except Exception as e:
            print(f"Error loading initial data: {e}")

    def load_matches_data(self):
        """Load match data from CSV"""
        try:
            file_path = self.file_path_var.get()
            if not file_path:
                raise ValueError("Please select a CSV file")

            data = pd.read_csv(file_path)

            required_cols = ['Home Team', 'Away Team', 'Competition']
            if not all(col in data.columns for col in required_cols):
                raise ValueError("Missing required columns")

            self.original_matches_data = data.copy()
            self.matches_data = data.copy()

            self.update_analysis_display()

            self.matches_status.config(
                text=f"Loaded {len(data)} matches",
                foreground='green'
            )

        except Exception as e:
            self.matches_status.config(
                text=f"Error: {str(e)}",
                foreground='red'
            )
            messagebox.showerror("Error", f"Failed to load matches: {str(e)}")

    def browse_file(self):
        """Open file dialog to select CSV file"""
        filename = filedialog.askopenfilename(
            title="Select Matches File",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.file_path_var.set(filename)
            self.load_matches_data()

    def save_settings(self):
        """Save current settings to file"""
        try:
            settings = {
                'last_csv': self.file_path_var.get()
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)

            self.matches_status.config(
                text="Settings saved successfully",
                foreground='green'
            )
        except Exception as e:
            self.matches_status.config(
                text=f"Error saving settings: {str(e)}",
                foreground='red'
            )

    def format_number(self, value):
        """Format numbers with commas"""
        try:
            if isinstance(value, str):
                value = float(value)
            if isinstance(value, (int, float)):
                if value.is_integer():
                    return f"{int(value):,}"
                return f"{value:,.2f}"
            return value
        except (ValueError, AttributeError):
            return value

    def export_to_csv(self):
        """Export analysis results to CSV"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if file_path:
            try:
                # Get data from treeviews
                summary_data = []
                match_data = []

                for item in self.summary_tree.get_children():
                    values = self.summary_tree.item(item)['values']
                    summary_data.append({
                        'Competition': values[0],
                        'Matches': values[1],
                        'Total Emissions': values[2],
                        'Average': values[3]
                    })

                for item in self.matches_tree.get_children():
                    values = self.matches_tree.item(item)['values']
                    match_data.append({
                        'Home Team': values[0],
                        'Away Team': values[1],
                        'Competition': values[2],
                        'Distance': values[3],
                        'Emissions': values[4]
                    })

                # Write to CSV
                pd.DataFrame(match_data).to_csv(
                    file_path,
                    index=False
                )

                messagebox.showinfo("Success", "Data exported successfully")

            except Exception as e:
                messagebox.showerror("Export Error", f"Error exporting data: {str(e)}")

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
