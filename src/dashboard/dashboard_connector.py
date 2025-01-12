from src.dashboard.app import DashboardApp
from tkinter import ttk
import webbrowser
import json
import tempfile
import os
import threading
import time
import requests

from src.utils.calculations import calculate_transport_emissions, calculate_equivalencies

import threading
import webbrowser
import json
import tempfile
import os
import time
import requests
from tkinter import ttk
from src.dashboard.app import DashboardApp


class DashboardConnector:
    def __init__(self):
        """Initialize the DashboardConnector"""
        self.dashboard = None
        self.server_running = False
        self.temp_dir = tempfile.gettempdir()
        self.data_file = os.path.join(self.temp_dir, 'dashboard_data.json')
        self.status_label = None
        self.browser_opened = False

    def start_dashboard(self, main_window):
        """Start the dashboard server"""
        try:
            def run_server():
                try:
                    self.dashboard = DashboardApp()
                    self.dashboard.run_server(debug=False, port=8050)
                    self.server_running = True
                except Exception as e:
                    print(f"Dashboard server error: {str(e)}")
                    self.server_running = False

            # Start dashboard server in a separate thread
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()

            # Wait briefly for server to start
            time.sleep(2)

            # Create status bar
            status_frame = ttk.Frame(main_window)
            status_frame.pack(side="bottom", fill="x", padx=10, pady=5)

            # Add dashboard status label
            self.status_label = ttk.Label(
                status_frame,
                text="Dashboard Status: Starting...",
                foreground="orange"
            )
            self.status_label.pack(side="left", padx=5)

            # Update status after brief delay
            main_window.after(2000, self.update_status)

        except Exception as e:
            print(f"Dashboard error: {str(e)}")

    def open_dashboard_browser(self):
        """Open the dashboard in the default web browser"""
        try:
            # Check if server is running
            response = requests.get('http://127.0.0.1:8050', timeout=1)
            if response.status_code == 200:
                webbrowser.open('http://127.0.0.1:8050')
                self.browser_opened = True
            else:
                print("Dashboard server not responding")
        except Exception as e:
            print(f"Error opening dashboard: {str(e)}")
            # Try to start server if it's not running
            if not self.server_running:
                print("Attempting to restart dashboard server...")
                self.start_dashboard(None)
                time.sleep(2)  # Wait for server to start
                webbrowser.open('http://127.0.0.1:8050')

    def update_dashboard_data(self, main_window):
        """Update dashboard data from main window"""
        try:
            if hasattr(main_window, 'latest_result'):
                from src.utils.calculations import calculate_transport_emissions, calculate_equivalencies

                dashboard_data = {
                    'total_emissions': main_window.latest_result.total_emissions,
                    'per_passenger': main_window.latest_result.per_passenger,
                    'distance_km': main_window.latest_result.distance_km,
                    'flight_type': main_window.latest_result.flight_type,
                    'is_round_trip': main_window.latest_result.is_round_trip,
                    'home_team': main_window.home_team_entry.get(),
                    'away_team': main_window.away_team_entry.get(),
                    'transport_comparison': {
                        'air': main_window.latest_result.total_emissions,
                        'rail': calculate_transport_emissions('rail',
                                                              main_window.latest_result.distance_km,
                                                              int(main_window.passengers_entry.get()),
                                                              main_window.latest_result.is_round_trip),
                        'bus': calculate_transport_emissions('bus',
                                                             main_window.latest_result.distance_km,
                                                             int(main_window.passengers_entry.get()),
                                                             main_window.latest_result.is_round_trip)
                    },
                    'environmental_impact': calculate_equivalencies(main_window.latest_result.total_emissions)
                }

                # Save to temp file
                with open(self.data_file, 'w') as f:
                    json.dump(dashboard_data, f)


        except Exception as e:
            print(f"Error updating dashboard data: {str(e)}")

    def update_status(self):
        """Update dashboard status label"""
        try:
            response = requests.get('http://127.0.0.1:8050', timeout=1)
            if response.status_code == 200:
                if self.status_label:
                    self.status_label.config(
                        text="Dashboard Status: Running ✓",
                        foreground="green"
                    )
                self.server_running = True
        except:
            if self.status_label:
                self.status_label.config(
                    text="Dashboard Status: Not Connected ✗",
                    foreground="red"
                )
            self.server_running = False
