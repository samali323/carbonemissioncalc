import sqlite3
from datetime import datetime
from src.data.team_data import get_team_airport, get_airport_coordinates
from src.utils.calculations import calculate_distance, calculate_driving_time, calculate_transit_time #work on these functions


def fix_route_times_in_db(db_path: str = 'data/routes.db') -> None:
    """Update route times in the SQLite database."""
    print("Starting database update...")

    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get all routes that need fixing
        cursor.execute("""
            SELECT home_team, away_team, driving_time, transit_time, driving_km
            FROM routes 
            WHERE driving_time = '0 minutes' 
            OR transit_time = 'N/A' 
            OR driving_time IS NULL 
            OR transit_time IS NULL
        """)
        routes_to_fix = cursor.fetchall()

        print(f"Found {len(routes_to_fix)} routes to fix")
        fixed_count = 0

        for home_team, away_team, driving_time, transit_time, driving_km in routes_to_fix:
            # Get airport codes
            home_airport = get_team_airport(home_team)
            away_airport = get_team_airport(away_team)

            if home_airport and away_airport:
                # Get coordinates
                home_coords = get_airport_coordinates(home_airport)
                away_coords = get_airport_coordinates(away_airport)

                if home_coords and away_coords:
                    # Calculate distance
                    distance = calculate_distance(
                        home_coords['lat'], home_coords['lon'],
                        away_coords['lat'], away_coords['lon']
                    )

                    # Calculate times
                    new_driving_time = calculate_driving_time(distance)
                    new_transit_time = calculate_transit_time(distance)

                    # Update the database
                    cursor.execute("""
                        UPDATE routes 
                        SET driving_time = ?,
                            transit_time = ?,
                            driving_km = ?,
                            last_updated = ?
                        WHERE home_team = ? AND away_team = ?
                    """, (
                        new_driving_time,
                        new_transit_time,
                        round(distance, 3),
                        datetime.now().strftime('%m/%d/%Y %H:%M'),
                        home_team,
                        away_team
                    ))

                    fixed_count += 1
                    if fixed_count % 100 == 0:  # Progress update every 100 routes
                        print(f"Fixed {fixed_count} routes...")

        # Commit all changes
        conn.commit()
        print(f"Successfully fixed {fixed_count} routes")

    except Exception as e:
        print(f"Error updating database: {str(e)}")
        conn.rollback()
        raise

    finally:
        conn.close()


def print_route_summary(db_path: str = 'data/routes.db') -> None:
    """Print a summary of routes in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM routes")
        total_routes = cursor.fetchone()[0]

        # Get count of routes with zero driving time
        cursor.execute("SELECT COUNT(*) FROM routes WHERE driving_time = '0 minutes' OR driving_time IS NULL")
        zero_driving = cursor.fetchone()[0]

        # Get count of routes with N/A transit time
        cursor.execute("SELECT COUNT(*) FROM routes WHERE transit_time = 'N/A' OR transit_time IS NULL")
        na_transit = cursor.fetchone()[0]

        print("\nRoute Summary:")
        print(f"Total routes: {total_routes}")
        print(f"Routes with zero driving time: {zero_driving}")
        print(f"Routes with N/A transit time: {na_transit}")

    finally:
        conn.close()


if __name__ == "__main__":
    # Print summary before fixing
    print("\nBefore fixing:")
    print_route_summary()

    # Fix the routes
    fix_route_times_in_db()

    # Print summary after fixing
    print("\nAfter fixing:")
    print_route_summary()