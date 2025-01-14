# src/utils/route_calculator.py
import pandas as pd
import sqlite3
import time
import os
from googlemaps import Client
from typing import Dict, Tuple, Optional
from src.data.team_data import get_team_airport, get_airport_coordinates


class RouteCalculator:
    def __init__(self):
        """
        Initialize the RouteCalculator with Google Maps API key and database connection.
        Database will be stored in the project root's data directory.
        """
        self.api_key = " "
        self.gmaps = Client(key=self.api_key)

        # Get project root directory (2 levels up from this file)
        self.project_root = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            "..",
            ".."
        ))

        # Set database path to project root's data directory
        self.db_path = os.path.join(self.project_root, "data", "routes.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.setup_database()

    def setup_database(self):
        """Create the routes table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS routes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    home_team TEXT,
                    away_team TEXT,
                    driving_duration INTEGER,
                    driving_distance INTEGER,
                    transit_duration INTEGER,
                    transit_distance INTEGER,
                    last_updated TIMESTAMP,
                    UNIQUE(home_team, away_team)
                )
            """)
            conn.commit()

    def get_cached_route(self, home_team: str, away_team: str) -> Optional[Dict]:
        """Get route information from the database cache."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT driving_duration, driving_distance,
                       transit_duration, transit_distance, last_updated
                FROM routes
                WHERE home_team = ? AND away_team = ?
                AND last_updated > datetime('now', '-30 days')
            """, (home_team, away_team))

            result = cursor.fetchone()
            if result:
                return {
                    'driving_duration': result[0],
                    'driving_distance': result[1],
                    'transit_duration': result[2],
                    'transit_distance': result[3],
                    'last_updated': result[4]
                }
            return None

    def fetch_route_info(self, origin_coords: Dict, dest_coords: Dict) -> Dict:
        """Fetch route information from Google Maps API."""
        try:
            origin = f"{origin_coords['lat']},{origin_coords['lon']}"
            destination = f"{dest_coords['lat']},{dest_coords['lon']}"

            # Get driving directions
            driving_result = self.gmaps.directions(
                origin,
                destination,
                mode="driving",
                departure_time="now"
            )

            # Get transit directions
            transit_result = self.gmaps.directions(
                origin,
                destination,
                mode="transit",
                departure_time="now"
            )

            # Extract relevant information
            driving_info = driving_result[0]['legs'][0] if driving_result else None
            transit_info = transit_result[0]['legs'][0] if transit_result else None

            return {
                'driving_duration': driving_info['duration']['value'] if driving_info else None,
                'driving_distance': driving_info['distance']['value'] if driving_info else None,
                'transit_duration': transit_info['duration']['value'] if transit_info else None,
                'transit_distance': transit_info['distance']['value'] if transit_info else None
            }

        except Exception as e:
            print(f"Error fetching route info: {str(e)}")
            return None

    def save_route_info(self, home_team: str, away_team: str, route_info: Dict):
        """Save route information to database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO routes 
                (home_team, away_team, driving_duration, driving_distance,
                 transit_duration, transit_distance, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                home_team, away_team,
                route_info['driving_duration'], route_info['driving_distance'],
                route_info['transit_duration'], route_info['transit_distance']
            ))
            conn.commit()

    @staticmethod
    def format_duration(hours: float) -> str:
        """Convert decimal hours to a hours:minutes format."""
        total_minutes = int(hours * 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60

        if hours == 0:
            return f"{minutes} minutes"
        elif hours == 1:
            if minutes == 0:
                return "1 hour"
            return f"1 hour {minutes} minutes"
        else:
            if minutes == 0:
                return f"{hours} hours"
            return f"{hours} hours {minutes} minutes"

    def get_route_details(self, home_team: str, away_team: str) -> Dict:
        """Get detailed route information for a specific match."""
        cached_route = self.get_cached_route(home_team, away_team)
        if cached_route:
            driving_hours = cached_route['driving_duration'] / 3600
            transit_hours = cached_route['transit_duration'] / 3600

            return {
                'driving_hours': driving_hours,
                'driving_time': self.format_duration(driving_hours),
                'driving_km': cached_route['driving_distance'] / 1000,
                'transit_hours': transit_hours,
                'transit_time': self.format_duration(transit_hours),
                'transit_km': cached_route['transit_distance'] / 1000,
                'last_updated': cached_route['last_updated']
            }
        return None

    def process_matches(self, matches_df: pd.DataFrame,
                        delay: int = 1,
                        batch_size: int = 40):
        """Process matches from DataFrame and store route information."""
        processed = 0
        for _, row in matches_df.iterrows():
            home_team = row['Home Team']
            away_team = row['Away Team']

            # Check cache first
            cached_route = self.get_cached_route(home_team, away_team)
            if cached_route:
                continue

            # Get airport codes
            home_airport = get_team_airport(home_team)
            away_airport = get_team_airport(away_team)

            if not home_airport or not away_airport:
                print(f"Missing airport data for {home_team} vs {away_team}")
                continue

            # Get coordinates
            home_coords = get_airport_coordinates(home_airport)
            away_coords = get_airport_coordinates(away_airport)

            if not home_coords or not away_coords:
                print(f"Missing coordinate data for {home_airport} or {away_airport}")
                continue

            # Fetch new route info
            route_info = self.fetch_route_info(home_coords, away_coords)
            if route_info:
                self.save_route_info(home_team, away_team, route_info)
                processed += 1
                print(f"Processed {home_team} vs {away_team}")

                # Add delay between API calls
                time.sleep(delay)

                # Take a break after batch_size matches
                if processed % batch_size == 0:
                    print(f"Processed {processed} matches. Taking a break...")
                    time.sleep(delay * 5)

    def get_route_statistics(self) -> pd.DataFrame:
        """Get statistics about stored routes."""
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query("""
                SELECT 
                    COUNT(*) as total_routes,
                    AVG(driving_duration)/3600.0 as avg_driving_duration_hours,
                    AVG(transit_duration)/3600.0 as avg_transit_duration_hours,
                    MIN(last_updated) as oldest_record,
                    MAX(last_updated) as newest_record
                FROM routes
            """, conn)

    @classmethod
    def run_population(cls):
        """Run the route population process from the command line."""
        try:
            print("Starting route population process...")

            # Create calculator instance
            calculator = cls()

            # Check for existing routes
            stats = calculator.get_route_statistics()
            existing_routes = stats['total_routes'].iloc[0] if not stats.empty else 0

            if existing_routes > 0:
                print(f"\nFound {existing_routes} existing routes in database.")
                choice = input("Do you want to update existing routes? (y/n): ").lower()
                if choice != 'y':
                    print("Exiting without updates.")
                    return

            # Load matches
            csv_path = os.path.join(calculator.project_root, "cleaned_matches.csv")
            if not os.path.exists(csv_path):
                print(f"Error: File '{csv_path}' not found.")
                return

            print(f"Loading matches from: {csv_path}")
            matches_df = pd.read_csv(csv_path)
            total_matches = len(matches_df)
            print(f"\nLoaded {total_matches} matches from CSV.")

            # Get processing parameters
            try:
                delay = int(input("\nEnter delay between API calls in seconds (2 recommended): ") or "2")
                batch_size = int(input("Enter batch size (40 recommended): ") or "40")
            except ValueError:
                print("Invalid input. Using default values: delay=2, batch_size=40")
                delay = 2
                batch_size = 40

            print("\nStarting to process matches...")
            print("This will take some time due to API rate limits.")
            print("Progress will be shown for each match processed.")

            # Process matches
            calculator.process_matches(matches_df, delay=delay, batch_size=batch_size)

            # Show final statistics
            final_stats = calculator.get_route_statistics()
            print("\nFinal Statistics:")
            print(f"Total routes stored: {final_stats['total_routes'].iloc[0]}")
            print(f"Average driving time: {final_stats['avg_driving_duration_hours'].iloc[0]:.1f} hours")
            print(f"Average transit time: {final_stats['avg_transit_duration_hours'].iloc[0]:.1f} hours")

        except KeyboardInterrupt:
            print("\nProcess interrupted by user. Data up to this point has been saved.")
        except Exception as e:
            print(f"\nError during population: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    RouteCalculator.run_population()
