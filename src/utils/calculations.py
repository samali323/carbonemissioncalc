import math
from typing import Dict, Optional

import self

from src.config.constants import (
    KM_PER_MILE,
    TRANSPORT_MODES,
    EMISSION_FACTORS,
    AIRCRAFT_EMISSION_FACTORS
)
from src.data.team_data import get_airport_coordinates, get_team_airport

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

) -> float:
    """Calculate emissions for different transport modes."""

    if distance_km == 0:
        return 0.0

    # Calculate base distance (one-way)

    base_distance = distance_km / (2 if is_round_trip else 1)

    if mode == 'air':

        # Get airport codes for both teams

        home_airport = get_team_airport(home_team)

        away_airport = get_team_airport(away_team)

        # Get coordinates for both airports

        home_coords = get_airport_coordinates(home_airport)

        away_coords = get_airport_coordinates(away_airport)

        if home_coords and away_coords:

            # Create ICAO calculator instance

            calculator = ICAOEmissionsCalculator()

            # Calculate using ICAO method

            result = calculator.calculate_emissions(

                distance_km=base_distance,  # Use base distance

                aircraft_type="A320",

                cabin_class="business",

                passengers=passengers,

                cargo_tons=2.0,

                is_international=True

            )

            # Calculate total emissions

            total_emissions = result["emissions_total_kg"] / 1000  # Convert to metric tons

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
def calculate_equivalencies(emissions_mtco2: float) -> Dict[str, float]:
    """Calculate environmental equivalencies for given CO2 emissions."""
    return {
        'tree_years': emissions_mtco2 * 17.31,  # Trees grown for 10 years
        'car_miles': emissions_mtco2 * 2557.69,  # Miles driven by average car
        'phone_charges': emissions_mtco2 * 66019.23,  # Smartphones charged
        'led_hours': emissions_mtco2 * 289215.38,  # Hours of LED bulb use
        'garbage_bags': emissions_mtco2 * 42.31,  # Bags of waste recycled
        'gas_gallons': emissions_mtco2 * 113.46,  # Gallons of gasoline
        'coal_pounds': emissions_mtco2 * (1 / 9.07e-4)  # Pounds of coal
    }
