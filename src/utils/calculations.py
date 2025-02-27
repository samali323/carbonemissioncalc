import math
import sqlite3
from typing import Dict, Optional

from src.config.constants import (
    TRANSPORT_MODES,
    DEFAULT_CARBON_PRICE, EU_ETS_PRICE, CARBON_PRICES_EUR, EUR_TO_GBP
)
from src.data.team_data import get_airport_coordinates, get_team_airport, TEAM_COUNTRIES
from src.models.icao_calculator import ICAOEmissionsCalculator


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using the Vincenty formula."""
    R = 6371  # Earth's radius in kilometers

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def determine_mileage_type(distance_km: float) -> str:
    """Determine flight type based on distance."""
    if distance_km < 800:  # Changed from 500 miles
        return "Short"
    elif distance_km < 4800:  # Changed from 3000 miles
        return "Medium"
    else:
        return "Long"


def calculate_transport_emissions(
        mode: str,
        distance_km: float,
        passengers: int = 30,
        is_round_trip: bool = False,
        home_team: str = None,
        away_team: str = None
) -> Optional[float]:
    """Calculate emissions for different transport modes."""
    if distance_km == 0:
        return None

    # Get route details from database
    conn = sqlite3.connect("data/routes.db")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT driving_duration, transit_duration
            FROM routes 
            WHERE home_team = ? AND away_team = ?
        """, (home_team, away_team))

        row = cursor.fetchone()

        # If we have no route data or durations are null, route is infeasible
        if not row:
            if mode in ['rail', 'bus']:
                return None
        else:
            driving_duration, transit_duration = row
            if mode == 'rail' and (transit_duration is None or transit_duration == 0):
                return None
            if mode == 'bus' and (driving_duration is None or driving_duration == 0):
                return None

        # Calculate as before for feasible routes
        base_distance = distance_km / (2 if is_round_trip else 1)

        if mode == 'air':
            calculator = ICAOEmissionsCalculator()
            result = calculator.calculate_emissions(
                distance_km=base_distance,
                aircraft_type="A320",
                cabin_class="business",
                passengers=passengers,
                cargo_tons=2.0,
                is_international=True
            )
            total_emissions = result["emissions_total_kg"] / 1000
            if is_round_trip:
                total_emissions *= 2
            return total_emissions

        elif mode in ['rail', 'bus']:
            mode_config = TRANSPORT_MODES[mode]
            adjusted_distance = base_distance * mode_config['distance_multiplier']
            emissions_per_passenger_km = mode_config['co2_per_km']
            total_emissions = (adjusted_distance * emissions_per_passenger_km * passengers) / 1000
            if is_round_trip:
                total_emissions *= 2
            return total_emissions

    finally:
        conn.close()


def get_carbon_price(away_team: str, home_team: str) -> float:
    """
    Get carbon price based on away team's country.
    Returns price in EUR or GBP for UK teams.
    """
    away_country = TEAM_COUNTRIES.get(away_team)
    home_country = TEAM_COUNTRIES.get(home_team)

    if not away_country:
        return DEFAULT_CARBON_PRICE

    # Get base price in EUR
    price_eur = CARBON_PRICES_EUR.get(away_country, EU_ETS_PRICE)

    # Convert to GBP if home team is from UK
    if home_country == 'GB':
        return price_eur * EUR_TO_GBP

    return price_eur


def calculate_equivalencies(emissions_mtco2: float) -> Dict[str, float]:
    """
    Calculate environmental equivalencies for given CO2 emissions in metric tons.
    Based on EPA conversion factors.
    """
    return {
        # Vehicle emissions
        'gasoline_vehicles_year': emissions_mtco2 / 0.233,  # Gasoline vehicles driven for one year
        'electric_vehicles_year': emissions_mtco2 / 0.883,  # Electric vehicles driven for one year
        'gasoline_vehicle_miles': emissions_mtco2 * 2547,  # Miles driven by gasoline vehicle

        # Fuel consumption
        'gasoline_gallons': emissions_mtco2 * 113,  # Gallons of gasoline
        'diesel_gallons': emissions_mtco2 * 98.2,  # Gallons of diesel
        'propane_cylinders': emissions_mtco2 * 45.9,  # Propane cylinders for BBQ
        'oil_barrels': emissions_mtco2 * 2.3,  # Barrels of oil

        # Home energy use
        'homes_energy_year': emissions_mtco2 / 0.134,  # Homes' energy use for one year
        'homes_electricity_year': emissions_mtco2 / 0.208,  # Homes' electricity use for one year

        # Industrial measures
        'coal_pounds': emissions_mtco2 * 1111,  # Pounds of coal burned
        'coal_railcars': emissions_mtco2 * 0.006,  # Railcars of coal
        'tanker_trucks': emissions_mtco2 * 0.013,  # Tanker trucks of gasoline

        # Waste and recycling
        'waste_tons_recycled': emissions_mtco2 * 0.353,  # Tons of waste recycled vs landfilled
        'garbage_trucks_recycled': emissions_mtco2 * 0.05,  # Garbage trucks of waste recycled
        'trash_bags_recycled': emissions_mtco2 * 85,  # Trash bags of waste recycled

        # Renewable energy
        'wind_turbines_year': emissions_mtco2 * 0.0003,  # Wind turbines running for a year

        # Carbon sequestration
        'tree_seedlings_10years': emissions_mtco2 * 16.5,  # Tree seedlings grown for 10 years
        'forest_acres_year': emissions_mtco2 * 1.0,  # Acres of U.S. forests in one year
        'forest_preserved_acres': emissions_mtco2 * 0.006,  # Acres of U.S. forests preserved

        # Electronic devices
        'smartphones_charged': emissions_mtco2 * 80847  # Number of smartphones charged
    }


def calculate_driving_time(distance_km: float) -> int:
    """Calculate driving time in seconds based on distance with 30 minute minimum."""
    MINIMUM_DRIVING_TIME = 30 * 60  # 30 minutes in seconds

    # Calculate base time using speeds
    if distance_km < 50:
        speed = 40  # km/h for city driving
    elif distance_km < 100:
        speed = 60  # km/h for mixed driving
    elif distance_km < 500:
        speed = 80  # km/h for highway driving
    else:
        speed = 90  # km/h for long distance driving

    calculated_time = int((distance_km / speed) * 3600)  # Convert to seconds

    # Return the larger of calculated time or minimum time
    return max(calculated_time, MINIMUM_DRIVING_TIME)


def calculate_transit_time(distance_km: float) -> int:
    """Calculate transit time in seconds based on distance with 45 minute minimum."""
    if distance_km > 500:
        return None  # Will be stored as NULL in database for N/A

    MINIMUM_TRANSIT_TIME = 45 * 60  # 45 minutes in seconds

    # Calculate base time using speeds
    if distance_km < 50:
        speed = 30  # km/h for local transit
    elif distance_km < 100:
        speed = 45  # km/h for regional transit
    else:
        speed = 60  # km/h for intercity rail

    calculated_time = int((distance_km / speed) * 3600)  # Convert to seconds

    # Return the larger of calculated time or minimum time
    return max(calculated_time, MINIMUM_TRANSIT_TIME)


def format_time_duration(seconds: int) -> str:
    """
    Format seconds into hours and minutes string.
    Always shows minutes, only shows hours if > 0

    Args:
        seconds: Time duration in seconds, can be None

    Returns:
        Formatted time string or "N/A" if seconds is None
    """
    if seconds is None:
        return "N/A"

    try:
        hours = int(seconds) // 3600
        minutes = (int(seconds) % 3600) // 60

        if hours == 0:
            return f"{minutes} minutes"
        else:
            return f"{hours} hours {minutes} minutes"
    except (TypeError, ValueError):
        return "N/A"

def calculate_flight_time(distance_km: float, is_round_trip: bool = False) -> int:
    """
    Calculate flight time in seconds based on distance.
    Includes taxi time, takeoff, landing, and cruise portions.

    Args:
        distance_km: Distance in kilometers for one leg
        is_round_trip: Whether this is a round trip flight

    Returns:
        Total time in seconds
    """
    # Constants for one leg of the journey
    CRUISE_SPEED = 800      # km/h
    GROUND_OPS = 1800      # 30 minutes total for taxi, takeoff, landing per leg
    MIN_TIME = 1800        # Minimum 30 minutes for very short flights

    # Calculate cruise time
    cruise_time = (distance_km / CRUISE_SPEED) * 3600  # Convert to seconds

    # Total time for one leg
    one_leg_time = cruise_time + GROUND_OPS

    # Ensure minimum time
    one_leg_time = max(one_leg_time, MIN_TIME)

    # Double for round trip
    if is_round_trip:
        return int(one_leg_time * 2)
    else:
        return int(one_leg_time)
