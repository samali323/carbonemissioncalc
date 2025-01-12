from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import pandas as pd

# Import your existing functions
from src.utils.calculations import (
    calculate_transport_emissions,
    calculate_equivalencies,
    calculate_flight_time
)
from src.models.emissions import EmissionsCalculator
from src.data.team_data import get_team_airport, get_airport_coordinates, get_all_teams

app = Flask(__name__)
# Update CORS to allow all Appsmith domains
CORS(app, origins=["https://app.appsmith.com", "https://app.appsmith.com/*", "http://localhost:5000"])
calculator = EmissionsCalculator()

def get_db_path():
    """Get database path"""
    import os
    project_root = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        ".."
    ))
    return os.path.join(project_root, "data", "routes.db")

@app.route('/api/teams', methods=['GET'])
def get_teams():
    """Get list of all teams"""
    try:
        teams = get_all_teams()
        return jsonify(teams)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/matches', methods=['GET'])
def get_matches():
    """Get all matches from the database"""
    try:
        conn = sqlite3.connect(get_db_path())
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

        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/matches/filter', methods=['POST'])
def filter_matches():
    """Filter matches based on teams"""
    try:
        data = request.json
        home_team = data.get('home_team', '').lower()
        away_team = data.get('away_team', '').lower()

        conn = sqlite3.connect(get_db_path())
        query = """
        SELECT * FROM routes 
        WHERE LOWER(home_team) LIKE ? 
        AND LOWER(away_team) LIKE ?
        """
        df = pd.read_sql_query(
            query,
            conn,
            params=(f'%{home_team}%', f'%{away_team}%')
        )
        conn.close()

        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/match/<home_team>/<away_team>', methods=['GET'])
def get_match_details(home_team, away_team):
    """Get detailed calculations for a specific match"""
    try:
        # Get airports and coordinates
        home_airport = get_team_airport(home_team)
        away_airport = get_team_airport(away_team)

        if not home_airport or not away_airport:
            return jsonify({'error': 'Airport not found'}), 400

        home_coords = get_airport_coordinates(home_airport)
        away_coords = get_airport_coordinates(away_airport)

        if not home_coords or not away_coords:
            return jsonify({'error': 'Coordinates not found'}), 400

        # Get route information from database
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("""
            SELECT driving_duration, transit_duration, driving_distance, transit_distance
            FROM routes 
            WHERE home_team = ? AND away_team = ?
        """, (home_team, away_team))
        route_data = cursor.fetchone()
        conn.close()

        # Calculate emissions
        result = calculator.calculate_flight_emissions(
            origin_lat=home_coords['lat'],
            origin_lon=home_coords['lon'],
            dest_lat=away_coords['lat'],
            dest_lon=away_coords['lon'],
            passengers=30,  # Default value, can be made configurable
            is_round_trip=False
        )

        # Add route times if available
        transport_times = {
            'driving_time': route_data[0] if route_data else None,
            'transit_time': route_data[1] if route_data else None,
            'flight_time': calculate_flight_time(result.distance_km, False)
        }

        return jsonify({
            'match_details': {
                'home_team': home_team,
                'away_team': away_team,
                'home_airport': home_airport,
                'away_airport': away_airport
            },
            'emissions': {
                'total': float(result.total_emissions),
                'per_passenger': float(result.per_passenger),
                'distance_km': float(result.distance_km),
                'flight_type': result.flight_type
            },
            'transport_times': transport_times,
            'environmental_impact': calculate_equivalencies(result.total_emissions)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calculate', methods=['POST'])
def calculate_emissions():
    """Calculate emissions for given teams and parameters"""
    try:
        data = request.json

        # Get input parameters
        home_team = data.get('home_team')
        away_team = data.get('away_team')
        passengers = int(data.get('passengers', 30))
        is_round_trip = data.get('is_round_trip', False)

        # Get airports and coordinates
        home_airport = get_team_airport(home_team)
        away_airport = get_team_airport(away_team)

        if not home_airport or not away_airport:
            return jsonify({'error': 'Airport not found for one or both teams'}), 400

        home_coords = get_airport_coordinates(home_airport)
        away_coords = get_airport_coordinates(away_airport)

        if not home_coords or not away_coords:
            return jsonify({'error': 'Coordinates not found for one or both airports'}), 400

        # Calculate emissions
        result = calculator.calculate_flight_emissions(
            origin_lat=home_coords['lat'],
            origin_lon=home_coords['lon'],
            dest_lat=away_coords['lat'],
            dest_lon=away_coords['lon'],
            passengers=passengers,
            is_round_trip=is_round_trip
        )

        # Get route information from database
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("""
            SELECT driving_duration, transit_duration, driving_distance, transit_distance
            FROM routes 
            WHERE home_team = ? AND away_team = ?
        """, (home_team, away_team))
        route_data = cursor.fetchone()
        conn.close()

        # Calculate transport times and distances
        distance_km = float(result.distance_km)
        driving_km = route_data[2]/1000 if route_data and route_data[2] else distance_km
        transit_km = route_data[3]/1000 if route_data and route_data[3] else distance_km

        if is_round_trip:
            driving_km *= 2
            transit_km *= 2

        # Calculate all transport emissions
        transport_comparison = {
            'air': {
                'emissions': float(result.total_emissions),
                'time': calculate_flight_time(distance_km, is_round_trip),
                'distance': distance_km
            },
            'rail': {
                'emissions': float(calculate_transport_emissions('rail', transit_km, passengers, is_round_trip)),
                'time': route_data[1] * 2 if route_data and route_data[1] and is_round_trip else route_data[1] if route_data else None,
                'distance': transit_km
            },
            'bus': {
                'emissions': float(calculate_transport_emissions('bus', driving_km, passengers, is_round_trip)),
                'time': route_data[0] * 2 if route_data and route_data[0] and is_round_trip else route_data[0] if route_data else None,
                'distance': driving_km
            }
        }
#test
        return jsonify({
            'total_emissions': float(result.total_emissions),
            'per_passenger': float(result.per_passenger),
            'distance_km': float(result.distance_km),
            'flight_type': result.flight_type,
            'is_round_trip': is_round_trip,
            'home_team': home_team,
            'away_team': away_team,
            'transport_comparison': transport_comparison,
            'environmental_impact': calculate_equivalencies(result.total_emissions)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
