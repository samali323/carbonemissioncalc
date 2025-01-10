# src/utils/route_viewer.py
import pandas as pd
import sqlite3
import os
from datetime import datetime


class RouteViewer:
    def __init__(self):
        # Get project root directory
        self.project_root = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            "..",
            ".."
        ))
        self.db_path = os.path.join(self.project_root, "data", "routes.db")

    def format_time(self, seconds):
        """Convert seconds to hours and minutes format"""
        if pd.isna(seconds):
            return "N/A"

        hours = int(seconds) // 3600
        minutes = (int(seconds) % 3600) // 60

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

    def get_all_routes(self):
        """Get all routes with formatted times"""
        try:
            conn = sqlite3.connect(self.db_path)

            query = """
            SELECT 
                home_team,
                away_team,
                driving_duration,
                transit_duration,
                driving_distance / 1000.0 as driving_km,
                transit_distance / 1000.0 as transit_km,
                last_updated
            FROM routes
            ORDER BY home_team, away_team
            """

            df = pd.read_sql_query(query, conn)
            conn.close()

            # Add formatted columns
            df['driving_time'] = df['driving_duration'].apply(self.format_time)
            df['transit_time'] = df['transit_duration'].apply(self.format_time)

            return df
        except Exception as e:
            print(f"Error reading database: {str(e)}")
            return pd.DataFrame()

    def export_routes(self, format='readable', output_path=None):
        """
        Export routes data to CSV.

        Args:
            format: 'readable' for formatted times or 'raw' for seconds
            output_path: Custom path for output file
        """
        df = self.get_all_routes()

        if df.empty:
            print("No data to export")
            return

        # Generate default filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"routes_export_{timestamp}.csv"

        if not output_path:
            output_path = os.path.join(self.project_root, default_filename)

        # Prepare data for export
        if format == 'readable':
            export_df = df[[
                'home_team',
                'away_team',
                'driving_time',
                'transit_time',
                'driving_km',
                'transit_km',
                'last_updated'
            ]]
        else:  # raw format
            export_df = df[[
                'home_team',
                'away_team',
                'driving_duration',
                'transit_duration',
                'driving_km',
                'transit_km',
                'last_updated'
            ]]

        # Export to CSV
        export_df.to_csv(output_path, index=False)
        print(f"Data exported to: {output_path}")
        print(f"Total routes exported: {len(export_df)}")

    def show_team_routes(self, team_name):
        """Show all routes for a specific team"""
        df = self.get_all_routes()

        team_matches = df[
            (df['home_team'] == team_name) |
            (df['away_team'] == team_name)
            ]

        if team_matches.empty:
            print(f"No matches found for {team_name}")
        else:
            print(f"\nAll matches for {team_name}:")
            print(team_matches[['home_team', 'away_team', 'driving_time', 'transit_time']])

        return team_matches


# Example usage
if __name__ == "__main__":
    viewer = RouteViewer()

    print("Routes Database Viewer and Exporter")
    print("-----------------------------------")

    while True:
        print("\nOptions:")
        print("1. View sample of routes")
        print("2. Search for team")
        print("3. Export all routes (readable format)")
        print("4. Export all routes (raw format)")
        print("5. Exit")

        choice = input("\nEnter your choice (1-5): ")

        if choice == '1':
            routes = viewer.get_all_routes()
            print("\nSample of routes (first 5):")
            print(routes[['home_team', 'away_team', 'driving_time', 'transit_time']].head())

        elif choice == '2':
            team = input("Enter team name: ")
            viewer.show_team_routes(team)

        elif choice == '3':
            viewer.export_routes(format='readable')

        elif choice == '4':
            viewer.export_routes(format='raw')

        elif choice == '5':
            break

        else:
            print("Invalid choice. Please try again.")

    print("\nGoodbye!")