"""Core emissions calculation model."""
from dataclasses import dataclass
from typing import Dict, Optional
from src.utils.calculations import calculate_distance, determine_mileage_type
from src.models.icao_calculator import ICAOEmissionsCalculator

@dataclass
class EmissionsResult:
    """Data class to store emissions calculation results."""
    total_emissions: float
    per_passenger: float
    distance_km: float
    corrected_distance_km: float
    fuel_consumption: float
    flight_type: str
    is_round_trip: bool
    additional_data: Dict

class EmissionsCalculator:
    """Main emissions calculator class."""

    def __init__(self):
        """Initialize the emissions calculator."""
        self.latest_result: Optional[EmissionsResult] = None
        self.icao_calculator = ICAOEmissionsCalculator()

    def calculate_flight_emissions(
            self,
            origin_lat: float,
            origin_lon: float,
            dest_lat: float,
            dest_lon: float,
            passengers: int,
            is_round_trip: bool = False,
            cabin_class: str = "business",
            aircraft_type: str = "A320",
            cargo_tons: float = 2.0,
            is_international: bool = True
    ) -> EmissionsResult:
        """
        Calculate emissions for a flight using ICAO methodology.

        Args:
            origin_lat: Origin latitude
            origin_lon: Origin longitude
            dest_lat: Destination latitude
            dest_lon: Destination longitude
            passengers: Number of passengers
            is_round_trip: Whether this is a round trip
            cabin_class: Cabin class (economy, premium_economy, business, first)
            aircraft_type: Type of aircraft
            cargo_tons: Cargo weight in metric tons
            is_international: Whether this is an international flight

        Returns:
            EmissionsResult object with calculation results
        """
        # Calculate distance
        distance = calculate_distance(origin_lat, origin_lon, dest_lat, dest_lon)

        # Determine flight type
        flight_type = determine_mileage_type(distance)

        # Calculate base emissions using ICAO calculator
        icao_results = self.icao_calculator.calculate_emissions(
            distance_km=distance,
            aircraft_type=aircraft_type,
            cabin_class=cabin_class,
            passengers=passengers,
            cargo_tons=cargo_tons,
            is_international=is_international
        )

        # Adjust for round trip if needed
        if is_round_trip:
            distance *= 2
            icao_results["emissions_total_kg"] *= 2
            icao_results["fuel_consumption_kg"] *= 2

        # Create result object
        result = EmissionsResult(
            total_emissions=icao_results["emissions_total_kg"] / 1000,  # Convert to metric tons
            per_passenger=icao_results["emissions_per_pax_kg"] / 1000,
            distance_km=distance,
            corrected_distance_km=icao_results["corrected_distance_km"],
            fuel_consumption=icao_results["fuel_consumption_kg"],
            flight_type=flight_type,
            is_round_trip=is_round_trip,
            additional_data=icao_results["factors_applied"]
        )

        self.latest_result = result
        return result

    def get_environmental_impact(self) -> Dict[str, float]:
        """Calculate environmental impact metrics."""
        if not self.latest_result:
            return {}

        from src.utils.calculations import calculate_equivalencies
        return calculate_equivalencies(self.latest_result.total_emissions)
