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
        passengers: int = 30
) -> float:
    """
    Calculate emissions for different transport modes.

    Args:
        mode: Transport mode ('air', 'rail', or 'bus')
        distance_km: Distance in kilometers
        passengers: Number of passengers

    Returns:
        Emissions in metric tons of CO2
    """
    if mode == 'air':
        # Calculate flight time in hours (assume average speed of 800 km/h)
        avg_speed = 800  # km/h
        flight_time = distance_km / avg_speed

        # Calculate emissions using 250kg per passenger per hour
        emissions_per_passenger = 250 * flight_time  # kg CO2
        total_emissions = (emissions_per_passenger * passengers) / 1000  # Convert to metric tons

        return total_emissions

    elif mode in ['rail', 'bus']:
        # Get emissions factor for mode
        emissions_per_passenger_km = TRANSPORT_MODES[mode]['co2_per_km']
        return (distance_km * emissions_per_passenger_km * passengers) / 1000

    else:
        raise ValueError(f"Unknown transport mode: {mode}")


def calculate_journey_time(
        mode: str,
        distance_km: float,
        is_round_trip: bool = False
) -> str:
    """Calculate journey time based on distance in kilometers."""
    transport_config = TRANSPORT_MODES[mode]

    # Basic time calculation
    time_hours = distance_km / transport_config['speed']

    # Add mode-specific adjustments
    if mode == 'air':
        # Add time for takeoff, landing, boarding
        time_hours += 2  # 2 hours for airport procedures
    elif mode == 'rail':
        # Add time for station stops
        stops = max(1, int(distance_km / 200))  # One stop every 200km
        time_hours += stops * 0.25  # 15 minutes per stop
    elif mode == 'bus':
        # Add time for rest stops and urban traffic
        rest_stops = int(time_hours / 4)  # One 30-min rest stop every 4 hours
        time_hours += rest_stops * 0.5
        time_hours += 1  # Urban traffic buffer

    if is_round_trip:
        time_hours *= 2

    # Convert to hours and minutes
    hours = int(time_hours)
    minutes = int((time_hours - hours) * 60)

    return f"{hours}h {minutes}m"


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
