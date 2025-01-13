import sqlite3
import pandas as pd
from datetime import datetime
from typing import Union
from src.models.emissions import EmissionsCalculator
from src.data.team_data import get_team_airport, get_airport_coordinates, TEAM_COUNTRIES
from src.utils.calculations import (
    calculate_distance, calculate_transport_emissions,
    calculate_equivalencies, get_carbon_price
)

class EmissionsProcessor:
    def __init__(self, db_path='data/routes.db'):
        self.db_path = db_path
        self.calculator = EmissionsCalculator()
        self.setup_database()

    def setup_database(self):
        """Create new tables for storing emissions data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create emissions results table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_emissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            home_team TEXT,
            away_team TEXT,
            distance_km REAL,
            flight_type TEXT,
            total_emissions REAL,
            per_passenger_emissions REAL,
            rail_emissions REAL,
            bus_emissions REAL,
            rail_saved REAL,
            bus_saved REAL,
            carbon_price REAL,
            carbon_cost_air REAL,
            carbon_cost_rail REAL,
            carbon_cost_bus REAL,
            flight_duration INTEGER,
            driving_duration INTEGER,
            transit_duration INTEGER,
            driving_distance REAL,
            transit_distance REAL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(home_team, away_team) REFERENCES routes(home_team, away_team),
            UNIQUE(home_team, away_team)
        )""")

        # Create environmental impact table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS environmental_impact (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER,
            impact_type TEXT,
            value REAL,
            unit TEXT,
            FOREIGN KEY(match_id) REFERENCES match_emissions(id)
        )""")

        # Create social costs table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS social_costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER,
            transport_mode TEXT,
            cost_type TEXT,
            low_cost REAL,
            median_cost REAL,
            mean_cost REAL,
            high_cost REAL,
            FOREIGN KEY(match_id) REFERENCES match_emissions(id)
        )""")

        conn.commit()
        conn.close()

    def calculate_flight_time(self, distance_km: float, is_minutes: bool = True) -> Union[str, int]:
        """Calculate flight time"""
        # Parameters
        CRUISE_SPEED = 800  # km/h
        CLIMB_SPEED = 550   # km/h
        TAXI_TIME = 0.5     # hours
        BOARDING_TIME = 0.5 # hours
        CLIMB_DISTANCE = 150 # km
        MIN_TIME = 0.5      # hours

        # Calculate cruise and climb times
        cruise_distance = max(0, distance_km - (CLIMB_DISTANCE * 2))
        cruise_time = cruise_distance / CRUISE_SPEED
        climb_time = (min(distance_km, CLIMB_DISTANCE * 2)) / CLIMB_SPEED

        # Adjust taxi and boarding times for short flights
        if distance_km < 500:
            boarding_factor = 0.75
            taxi_factor = 0.75
        else:
            boarding_factor = 1.0
            taxi_factor = 1.0

        # Calculate total time
        total_time = (cruise_time + climb_time +
                      TAXI_TIME * taxi_factor +
                      BOARDING_TIME * boarding_factor)

        total_time = max(total_time, MIN_TIME)

        if is_minutes:
            return int(total_time * 60)

        hours = int(total_time)
        minutes = int((total_time % 1) * 60)
        return f"{hours}h {minutes}m"

    def calculate_match_emissions(self, route_data, passengers=30):
        """Calculate emissions using existing route data"""
        try:
            home_team = route_data['home_team']
            away_team = route_data['away_team']

            # Get airports and coordinates
            home_airport = get_team_airport(home_team)
            away_airport = get_team_airport(away_team)

            if not home_airport or not away_airport:
                raise ValueError(f"Airport not found for {home_team} or {away_team}")

            home_coords = get_airport_coordinates(home_airport)
            away_coords = get_airport_coordinates(away_airport)

            if not home_coords or not away_coords:
                raise ValueError(f"Coordinates not found for {home_airport} or {away_airport}")

            # Calculate air emissions
            result = self.calculator.calculate_flight_emissions(
                origin_lat=home_coords['lat'],
                origin_lon=home_coords['lon'],
                dest_lat=away_coords['lat'],
                dest_lon=away_coords['lon'],
                passengers=passengers,
                is_round_trip=False
            )

            # Calculate flight time
            flight_duration = self.calculate_flight_time(result.distance_km)

            # Use existing route data for rail/bus calculations
            driving_distance = route_data['driving_distance'] / 1000  # Convert to km
            transit_distance = route_data['transit_distance'] / 1000  # Convert to km

            # Calculate emissions using actual distances
            rail_emissions = calculate_transport_emissions('rail', transit_distance, passengers, False)
            bus_emissions = calculate_transport_emissions('bus', driving_distance, passengers, False)

            # Calculate carbon prices
            carbon_price = get_carbon_price(away_team, home_team)
            carbon_cost_air = result.total_emissions * carbon_price
            carbon_cost_rail = rail_emissions * carbon_price
            carbon_cost_bus = bus_emissions * carbon_price

            return {
                'basic_data': {
                    'home_team': home_team,
                    'away_team': away_team,
                    'distance_km': result.distance_km,
                    'flight_type': result.flight_type,
                    'total_emissions': result.total_emissions,
                    'per_passenger_emissions': result.per_passenger,
                    'rail_emissions': rail_emissions,
                    'bus_emissions': bus_emissions,
                    'rail_saved': result.total_emissions - rail_emissions,
                    'bus_saved': result.total_emissions - bus_emissions,
                    'carbon_price': carbon_price,
                    'carbon_cost_air': carbon_cost_air,
                    'carbon_cost_rail': carbon_cost_rail,
                    'carbon_cost_bus': carbon_cost_bus,
                    'flight_duration': flight_duration,
                    'driving_duration': route_data['driving_duration'],
                    'transit_duration': route_data['transit_duration'],
                    'driving_distance': driving_distance,
                    'transit_distance': transit_distance
                },
                'environmental_impact': calculate_equivalencies(result.total_emissions)
            }

        except Exception as e:
            print(f"Error calculating emissions for {home_team} vs {away_team}: {str(e)}")
            return None

    def process_all_matches(self):
        """Process all matches in the database"""
        conn = sqlite3.connect(self.db_path)

        try:
            # Get all routes with their existing data
            routes_df = pd.read_sql_query("""
                SELECT 
                    home_team, away_team, 
                    driving_duration, transit_duration,
                    driving_distance, transit_distance
                FROM routes
            """, conn)

            total = len(routes_df)
            print(f"Processing {total} matches...")

            for i, row in routes_df.iterrows():
                print(f"Processing match {i+1}/{total}: {row['home_team']} vs {row['away_team']}")

                # Calculate emissions using existing route data
                results = self.calculate_match_emissions(row)
                if results:
                    self._save_results(results, conn)

                # Commit every 100 matches
                if (i + 1) % 100 == 0:
                    conn.commit()
                    print(f"Committed {i+1} matches")

            conn.commit()
            print("All matches processed successfully")

        except Exception as e:
            print(f"Error processing matches: {str(e)}")
            conn.rollback()
        finally:
            conn.close()

    def _save_results(self, results, conn):
        """Save calculation results to database"""
        cursor = conn.cursor()

        # Insert basic emissions data
        cursor.execute("""
        INSERT OR REPLACE INTO match_emissions (
            home_team, away_team, distance_km, flight_type,
            total_emissions, per_passenger_emissions,
            rail_emissions, bus_emissions, rail_saved, bus_saved,
            carbon_price, carbon_cost_air, carbon_cost_rail, carbon_cost_bus,
            flight_duration, driving_duration, transit_duration,
            driving_distance, transit_distance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            results['basic_data']['home_team'],
            results['basic_data']['away_team'],
            results['basic_data']['distance_km'],
            results['basic_data']['flight_type'],
            results['basic_data']['total_emissions'],
            results['basic_data']['per_passenger_emissions'],
            results['basic_data']['rail_emissions'],
            results['basic_data']['bus_emissions'],
            results['basic_data']['rail_saved'],
            results['basic_data']['bus_saved'],
            results['basic_data']['carbon_price'],
            results['basic_data']['carbon_cost_air'],
            results['basic_data']['carbon_cost_rail'],
            results['basic_data']['carbon_cost_bus'],
            results['basic_data']['flight_duration'],
            results['basic_data']['driving_duration'],
            results['basic_data']['transit_duration'],
            results['basic_data']['driving_distance'],
            results['basic_data']['transit_distance']
        ))

        match_id = cursor.lastrowid

        # Save environmental impact data
        for impact_type, value in results['environmental_impact'].items():
            cursor.execute("""
            INSERT INTO environmental_impact (match_id, impact_type, value, unit)
            VALUES (?, ?, ?, ?)
            """, (match_id, impact_type, value, "metric"))

if __name__ == "__main__":
    processor = EmissionsProcessor()
    processor.process_all_matches()
