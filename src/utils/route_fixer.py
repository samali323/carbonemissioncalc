import sqlite3
import os
from datetime import datetime
from src.data.team_data import get_team_airport, get_airport_coordinates
from src.utils.calculations import calculate_distance, calculate_driving_time, calculate_transit_time


class RouteFixer:
    def __init__(self):
        # Get project root directory
        self.project_root = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            "..",
            ".."
        ))
        self.db_path = os.path.join(self.project_root, "data", "routes.db")

    def fix_route_times(self) -> None:
        """Update route times in the SQLite database."""
        print("Starting database update...")
        print(f"Using database at: {self.db_path}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get all routes that need fixing
            cursor.execute("""
                SELECT home_team, away_team, driving_duration, transit_duration, driving_distance
                FROM routes 
                WHERE driving_duration <= 300  -- 5 minutes in seconds
                OR transit_duration <= 600     -- 10 minutes in seconds
                OR driving_duration IS NULL 
                OR transit_duration IS NULL
            """)
            routes_to_fix = cursor.fetchall()

            print(f"Found {len(routes_to_fix)} routes to fix")
            fixed_count = 0

            for home_team, away_team, driving_duration, transit_duration, driving_distance in routes_to_fix:
                # Get airport codes
                home_airport = get_team_airport(home_team)
                away_airport = get_team_airport(away_team)

                if home_airport and away_airport:
                    # Get coordinates
                    home_coords = get_airport_coordinates(home_airport)
                    away_coords = get_airport_coordinates(away_airport)

                    if home_coords and away_coords:
                        # Calculate distance in meters
                        distance_km = calculate_distance(
                            home_coords['lat'], home_coords['lon'],
                            away_coords['lat'], away_coords['lon']
                        )
                        distance_meters = int(distance_km * 1000)

                        # Calculate durations with minimums
                        new_driving_duration = max(1800, calculate_driving_time(distance_km))  # Minimum 30 minutes
                        new_transit_duration = transit_duration
                        if distance_km <= 500:  # Only set transit time if within range
                            new_transit_duration = max(2700, calculate_transit_time(distance_km))  # Minimum 45 minutes

                        # Update the database
                        cursor.execute("""
                            UPDATE routes 
                            SET driving_duration = ?,
                                transit_duration = ?,
                                driving_distance = ?,
                                transit_distance = ?,
                                last_updated = ?
                            WHERE home_team = ? AND away_team = ?
                        """, (
                            new_driving_duration,
                            new_transit_duration,
                            distance_meters,
                            distance_meters,
                            datetime.now().strftime('%m/%d/%Y %H:%M'),
                            home_team,
                            away_team
                        ))

                        fixed_count += 1
                        if fixed_count % 100 == 0:
                            print(f"Fixed {fixed_count} routes...")
                            conn.commit()

            # Final commit
            conn.commit()
            print(f"Successfully fixed {fixed_count} routes")

        except Exception as e:
            print(f"Error updating database: {str(e)}")
            conn.rollback()
            raise

        finally:
            conn.close()

    def print_route_summary(self) -> None:
        """Print a summary of routes in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT COUNT(*) FROM routes")
            total_routes = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM routes WHERE driving_duration = 0")
            zero_driving = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM routes WHERE transit_duration IS NULL")
            na_transit = cursor.fetchone()[0]

            print("\nRoute Summary:")
            print(f"Total routes: {total_routes}")
            print(f"Routes with zero driving time: {zero_driving}")
            print(f"Routes with N/A transit time: {na_transit}")

        finally:
            conn.close()


if __name__ == "__main__":
    fixer = RouteFixer()

    # Print summary before fixing
    print("\nBefore fixing:")
    fixer.print_route_summary()

    # Fix the routes
    fixer.fix_route_times()

    # Print summary after fixing
    print("\nAfter fixing:")
    fixer.print_route_summary()


