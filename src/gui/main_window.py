from __future__ import annotations

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


import pandas as pd
import self

from src.config.constants import DEFAULT_PASSENGERS, EMISSION_FACTORS, TRANSPORT_MODES, CARBON_PRICE, \
    ALTERNATIVE_TRANSPORT_PREMIUM, SOCIAL_CARBON_COST, TEAM_COUNTRIES, SOCIAL_CARBON_COSTS, CARBON_PRICES_EUR, \
    EU_ETS_PRICE
from src.data.team_data import get_team_airport, get_airport_coordinates
from src.gui.widgets.auto_complete import TeamAutoComplete, CompetitionAutoComplete
from src.models.emissions import EmissionsCalculator
from src.utils.calculations import calculate_transport_emissions, calculate_equivalencies, get_carbon_price
from src.models.emissions import EmissionsResult
from src.utils.calculations import calculate_distance, determine_mileage_type
from src.models.icao_calculator import ICAOEmissionsCalculator

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Football Team Flight Emissions Calculator")
        self.geometry("1200x800")

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

        # Results frame
        right_frame = ttk.Frame(self.calculator_tab, padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Results text
        self.result_text = tk.Text(right_frame, wrap=tk.WORD, height=30)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.pack(fill='both', expand=True)

        # Configure grid weights
        self.calculator_tab.columnconfigure(1, weight=1)
        self.calculator_tab.rowconfigure(0, weight=1)

    def update_transport_comparison(self, result):
        """Update transport mode comparison with comprehensive SCC analysis"""
        # Get away team's country and corresponding carbon price
        away_team = self.away_team_entry.get()
        away_country = TEAM_COUNTRIES.get(away_team, 'EU')  # Default to EU if country not found
        carbon_price = CARBON_PRICES_EUR.get(away_country, EU_ETS_PRICE)  # Use EU ETS price as default

        self.result_text.insert(tk.END, "\nTransport Mode Comparison:\n")
        self.result_text.insert(tk.END, "=" * 80 + "\n")

        # Display mode comparison header
        self.result_text.insert(tk.END,
                                f"{'Mode':20}  {'Distance (km)':15} {'CO2 (metric tons)':15} {'CO2 Saved':15}\n")
        self.result_text.insert(tk.END, "-" * 80 + "\n")

        # Calculate emissions for each mode
        air_emissions = result.total_emissions
        base_distance = result.distance_km

        rail_distance = (base_distance / (2 if self.round_trip_var.get() else 1)) * TRANSPORT_MODES['rail'][
            'distance_multiplier']
        bus_distance = (base_distance / (2 if self.round_trip_var.get() else 1)) * TRANSPORT_MODES['bus'][
            'distance_multiplier']

        rail_emissions = calculate_transport_emissions('rail', rail_distance * (2 if self.round_trip_var.get() else 1),
                                                       int(self.passengers_entry.get()), self.round_trip_var.get())
        bus_emissions = calculate_transport_emissions('bus', bus_distance * (2 if self.round_trip_var.get() else 1),
                                                      int(self.passengers_entry.get()), self.round_trip_var.get())

        # Display basic comparison
        self.result_text.insert(tk.END,
                                f"{'Air':20}  {base_distance:15.1f} {air_emissions:15.2f} {'':15}\n")
        self.result_text.insert(tk.END,
                                f"{'Rail':20}  {rail_distance * (2 if self.round_trip_var.get() else 1):15.1f} {rail_emissions:15.2f} {air_emissions - rail_emissions:15.2f}\n")
        self.result_text.insert(tk.END,
                                f"{'Bus':20}  {bus_distance * (2 if self.round_trip_var.get() else 1):15.1f} {bus_emissions:15.2f} {air_emissions - bus_emissions:15.2f}\n")

        # Add Carbon Price Analysis section
        self.result_text.insert(tk.END, f"\nCarbon Price Analysis ({away_country}):\n")
        self.result_text.insert(tk.END, "=" * 80 + "\n")
        self.result_text.insert(tk.END, f"Carbon Price: €{carbon_price:.2f}/tCO2\n\n")

        # Calculate and display carbon costs for each mode
        modes = {
            'Air': air_emissions,
            'Rail': rail_emissions,
            'Bus': bus_emissions
        }

        for mode, emissions in modes.items():
            cost = emissions * carbon_price
            self.result_text.insert(tk.END, f"{mode}: €{cost:.2f}\n")

        # Add Social Cost Analysis section
        self.result_text.insert(tk.END, "\nSocial Cost Analysis:\n")
        self.result_text.insert(tk.END, "=" * 80 + "\n")

        # Header for the detailed social cost table
        self.result_text.insert(tk.END,
                                f"{'Transport Mode':<15} | {'Cost Type':<15} | {'Low (€)':<12} | {'Median (€)':<12} | {'Mean (€)':<12} | {'High (€)':<12}\n")
        self.result_text.insert(tk.END, "-" * 85 + "\n")

        # Calculate and display social costs for each mode
        for mode, emissions in modes.items():
            # Calculate costs using different SCC estimates
            synthetic_low = emissions * SOCIAL_CARBON_COSTS['synthetic_iqr_low']
            synthetic_median = emissions * SOCIAL_CARBON_COSTS['synthetic_median']
            synthetic_mean = emissions * SOCIAL_CARBON_COSTS['synthetic_mean']
            synthetic_high = emissions * SOCIAL_CARBON_COSTS['synthetic_iqr_high']
            epa = emissions * SOCIAL_CARBON_COSTS['epa_median']
            iwg = emissions * SOCIAL_CARBON_COSTS['iwg_75th']

            # Display synthetic costs
            self.result_text.insert(tk.END,
                                    f"{mode:<15} | {'Synthetic':<15} | €{synthetic_low:<11.2f} | €{synthetic_median:<11.2f} | €{synthetic_mean:<11.2f} | €{synthetic_high:<11.2f}\n")

            # Display government estimates
            self.result_text.insert(tk.END,
                                    f"{'':<15} | {'EPA':<15} | {'':<12} | €{epa:<11.2f} | {'':<12} | {'':<12}\n")
            self.result_text.insert(tk.END,
                                    f"{'':<15} | {'IWG':<15} | {'':<12} | €{iwg:<11.2f} | {'':<12} | {'':<12}\n")

            if mode != list(modes.keys())[-1]:  # Add separator between modes
                self.result_text.insert(tk.END, "-" * 85 + "\n")

        # Add explanatory notes
        self.result_text.insert(tk.END, "\nNotes:\n")
        self.result_text.insert(tk.END,
                                f"- Carbon costs are based on {away_country}'s carbon price of €{carbon_price:.2f}/tCO2\n")
        self.result_text.insert(tk.END, "- Social costs use the synthetic distribution as recommended\n")
        self.result_text.insert(tk.END, "- All costs are in EUR\n")

    def _calculate_air_route_factor(self, distance_km: float) -> float:

        """Calculate route factor for air travel"""

        flight_type = determine_mileage_type(distance_km)

        # Use emission factors from constants

        if flight_type == "Short":

            return EMISSION_FACTORS['ShortBusiness']

        elif flight_type == "Medium":

            return EMISSION_FACTORS['MediumBusiness']

        else:

            return EMISSION_FACTORS['LongBusiness']

    def _calculate_rail_route_factor(self, distance_km: float) -> float:
        """
        Calculate route factor for rail travel.

        Args:
            distance_km: Distance in kilometers

        Returns:
            float: CO2 emissions factor in kg CO2 per passenger-km
        """
        # Get rail emission factor from TRANSPORT_MODES constant
        # Modern electric train: 0.041 kg CO2 per passenger-km
        return TRANSPORT_MODES['rail']['co2_per_km']

    def _calculate_bus_route_factor(self, distance_km: float) -> float:
        """
        Calculate route factor for bus travel.

        Args:
            distance_km: Distance in kilometers

        Returns:
            float: CO2 emissions factor in kg CO2 per passenger-km
        """
        # Get bus emission factor from TRANSPORT_MODES constant
        # Modern coach bus: 0.027 kg CO2 per passenger-km
        return TRANSPORT_MODES['bus']['co2_per_km']

        return TRANSPORT_MODES['bus']['co2_per_km']
    def create_analysis_tab(self):
        """Create enhanced analysis tab with sorting and filtering"""
        analysis_container = ttk.Frame(self.analysis_tab, padding="10")
        analysis_container.pack(fill='both', expand=True)

        # Summary section
        summary_frame = ttk.LabelFrame(analysis_container, text="Summary", padding="10")
        summary_frame.pack(fill='x', pady=(0, 10))

        self.summary_tree = ttk.Treeview(
            summary_frame,
            columns=("Competition", "Matches", "Total Emissions", "Average"),
            show='headings',
            height=5
        )

        # Configure columns with sorting
        for col in ["Competition", "Matches", "Total Emissions", "Average"]:
            self.summary_tree.heading(col,
                                      text=col,
                                      anchor='center',
                                      command=lambda c=col: self.sort_treeview(self.summary_tree, c, False)
                                      )
            self.summary_tree.column(col, anchor='center')

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
        self.filters['Home Team'] = TeamAutoComplete(filter_frame, width=20)
        self.filters['Home Team'].grid(row=0, column=1, padx=5, pady=5)

        # Away team filter
        ttk.Label(filter_frame, text="Away Team:").grid(row=0, column=2, padx=5, pady=5)
        self.filters['Away Team'] = TeamAutoComplete(filter_frame, width=20)
        self.filters['Away Team'].grid(row=0, column=3, padx=5, pady=5)

        # Competition filter
        ttk.Label(filter_frame, text="Competition:").grid(row=0, column=4, padx=5, pady=5)
        self.filters['Competition'] = CompetitionAutoComplete(filter_frame, width=20)
        self.filters['Competition'].grid(row=0, column=5, padx=5, pady=5)

        # Filter buttons
        button_frame = ttk.Frame(filter_frame)
        button_frame.grid(row=0, column=6, padx=5, pady=5)

        ttk.Button(button_frame, text="Apply Filters", command=self.apply_filters).pack(side='left', padx=2)
        ttk.Button(button_frame, text="Clear Filters", command=self.clear_filters).pack(side='left', padx=2)

        # Configure filter frame grid
        for i in range(7):
            filter_frame.grid_columnconfigure(i, weight=1)

        # Matches treeview
        self.matches_tree = ttk.Treeview(

            matches_frame,

            columns=("Home Team", "Away Team", "Competition"),  # Removed Distance and Emissions

            show='headings',

            height=15

        )

        # Configure columns with sorting

        for col in ["Home Team", "Away Team", "Competition"]:  # Removed Distance and Emissions

            self.matches_tree.heading(col,

                                      text=col,

                                      anchor='center',

                                      command=lambda c=col: self.sort_treeview(self.matches_tree, c, False)

                                      )

            self.matches_tree.column(col, anchor='center')
        # Scrollbars
        y_scroll = ttk.Scrollbar(matches_frame, orient="vertical", command=self.matches_tree.yview)
        x_scroll = ttk.Scrollbar(matches_frame, orient="horizontal", command=self.matches_tree.xview)

        self.matches_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        x_scroll.pack(side='bottom', fill='x')
        y_scroll.pack(side='right', fill='y')
        self.matches_tree.pack(fill='both', expand=True)

        # Add bindings for match selection
        self.add_match_selection_bindings()

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

            # Update transport comparison table

            self.update_transport_comparison(result)

            self.export_button.config(state='normal')

            # Switch to calculator tab

            self.notebook.select(self.calculator_tab)


        except Exception as e:

            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def create_settings_tab(self):
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

    def update_analysis_display(self):

        if self.matches_data is None:
            return

        self.summary_tree.delete(*self.summary_tree.get_children())

        self.matches_tree.delete(*self.matches_tree.get_children())

        try:

            total_matches = total_emissions = total_distance = 0

            matches_data = []

            competitions = self.matches_data.groupby('Competition')

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

                            # Calculate distance first

                            distance = calculate_distance(

                                home_coords['lat'], home_coords['lon'],

                                away_coords['lat'], away_coords['lon']

                            )

                            # Skip matches with 0.0 km distance

                            if distance == 0.0:
                                match_count -= 1  # Reduce match count for zero distance matches

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

                # Only add competition summary if there are valid matches

                if match_count > 0:
                    avg_emissions = comp_emissions / match_count

                    self.summary_tree.insert('', 'end', values=(

                        comp_name,

                        self.format_number(match_count),

                        self.format_number(comp_emissions),

                        self.format_number(avg_emissions)

                    ))

            # Add total row only if there are valid matches

            if total_matches > 0:
                self.summary_tree.insert('', 'end', values=(

                    "TOTAL",

                    self.format_number(total_matches),

                    self.format_number(total_emissions),

                    self.format_number(total_emissions / total_matches)

                ), tags=('total',))

                self.summary_tree.tag_configure('total',

                                                background='#E8E8E8',

                                                font=('Segoe UI', 9, 'bold')

                                                )

            # Update matches tree with only non-zero distance matches

            for i, match in enumerate(matches_data):
                row_tags = ('even',) if i % 2 == 0 else ('odd',)

                self.matches_tree.insert('', 'end', values=(

                    match['home_team'],

                    match['away_team'],

                    match['competition'],

                ), tags=row_tags)

            self.matches_tree.tag_configure('even', background='#f0f0f0')

            self.matches_tree.tag_configure('odd', background='#ffffff')


        except Exception as e:

            messagebox.showerror("Analysis Error", f"Error updating analysis: {str(e)}")

            raise

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

            # Get airports

            home_airport = get_team_airport(home_team)

            away_airport = get_team_airport(away_team)

            if not home_airport or not away_airport:
                raise ValueError("Airport not found for one or both teams")

            # Get coordinates

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

            # Store as latest result and update display

            self.latest_result = result

            self.display_results(result, home_team, away_team)

            self.update_transport_comparison(result)

            self.export_button.config(state='normal')


        except Exception as e:

            messagebox.showerror("Error", str(e))

            self.last_error = str(e)

            self.copy_error_button.config(state='normal')

    def display_results(self, result, home_team, away_team):
        # Clear previous results
        self.result_text.delete(1.0, tk.END)

        # Header
        self.result_text.insert(tk.END, "✈️ Flight Emissions Report ✈️\n")
        self.result_text.insert(tk.END, "=" * 80 + "\n\n")

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

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()