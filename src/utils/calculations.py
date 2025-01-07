import math
from typing import Dict, Optional
from src.config.constants import (
    KM_PER_MILE,
    TRANSPORT_MODES,
    EMISSION_FACTORS,
    AIRCRAFT_EMISSION_FACTORS
)


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
        is_round_trip: bool = False
) -> float:
    """Calculate emissions for different transport modes."""
    if distance_km == 0:
        return 0.0

    # Calculate one-way distance if round trip
    one_way_distance = distance_km / 2 if is_round_trip else distance_km

    if mode == 'air':
        flight_type = determine_mileage_type(one_way_distance)
        if flight_type == "Short":
            emissions_factor = EMISSION_FACTORS['ShortBusiness']
        elif flight_type == "Medium":
            emissions_factor = EMISSION_FACTORS['MediumBusiness']
        else:
            emissions_factor = EMISSION_FACTORS['LongBusiness']

        total_emissions = (one_way_distance * emissions_factor * passengers) / 1000
    elif mode in ['rail', 'bus']:
        mode_config = TRANSPORT_MODES[mode]
        adjusted_distance = one_way_distance * mode_config['distance_multiplier']
        emissions_per_passenger_km = mode_config['co2_per_km']
        total_emissions = (adjusted_distance * emissions_per_passenger_km * passengers) / 1000

    # Double emissions for round trip
    if is_round_trip:
        total_emissions *= 2

    return total_emissions

def calculate_journey_time(mode: str, distance_km: float, is_round_trip: bool = False) -> str:
    """Calculate journey time based on mode and distance."""
    # Get speed from transport modes config
    speed = TRANSPORT_MODES[mode]['speed']

    # Minimum distance check
    if distance_km < 1:
        return "N/A"  # or "0h 00m" depending on preference

    # Calculate basic time in hours
    time_hours = distance_km / speed

    # Add mode-specific adjustments
    if mode == 'air':
        # Add 2 hours for airport procedures (1 hour each end)
        time_hours += 2
    elif mode == 'rail':
        # Add 30 minutes for station procedures
        time_hours += 0.5
    elif mode == 'bus':
        # Add rest stops (15 minutes per 2 hours)
        rest_stops = (time_hours // 2) * 0.25
        time_hours += rest_stops

    # Double time for round trip
    if is_round_trip:
        time_hours *= 2

    # Convert to hours and minutes
    hours = int(time_hours)
    minutes = int((time_hours - hours) * 60)

    return f"{hours}h {minutes:02d}m"

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
