"""Core emissions calculation model."""
from dataclasses import dataclass
from typing import Dict, Optional

from src.config.constants import COMPLIANCE_COST_RATE, CARBON_PRICE_VOLATILITY, DISCOUNT_RATES, \
    CARBON_PRICES_EUR, SOCIAL_CARBON_COST, DISCOUNT_RATE
from src.utils.calculations import calculate_distance, determine_mileage_type, get_carbon_price
from src.models.icao_calculator import ICAOEmissionsCalculator
@dataclass
class EmissionsFinancialMetrics:
    """Data class to store financial metrics for emissions calculations."""
    carbon_cost: float
    operational_cost: float
    risk_exposure: float
    total_impact: float
    total_risk_adjusted: float
    carbon_intensity: float
    marginal_abatement_cost: float
    social_cost_carbon: float
    regulatory_compliance_cost: float
    carbon_price_sensitivity: float
    opportunity_cost: float
    net_present_value: float
    emission_reduction_roi: float
    cost_per_passenger_mile: float
    carbon_market_exposure: float
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
        self.icao_calculator = ICAOEmissionsCalculator()  # Make sure this is initialized

    def calculate_match_costs(
            self,
            distance_km: float,
            emissions_mt: float,
            home_team: str,
            away_team: str,
            is_international: bool = False,
            time_horizon_years: int = 5,
            aircraft_type: str = "A320",
            route_type: str = "INTRA_EUROPE"
    ) -> EmissionsFinancialMetrics:
        """Calculate comprehensive match costs with country-specific carbon prices."""
        try:
            # Get appropriate carbon price based on away team's country
            carbon_price = get_carbon_price(away_team, home_team)

            # Calculate costs with new carbon price
            carbon_cost = emissions_mt * carbon_price

            # Use updated social cost of carbon (1367 USD converted to EUR)
            social_cost = emissions_mt * (1367 / 1.09)  # Using current USD to EUR rate

            # Calculate other metrics...
            operational_cost = distance_km * 15.0
            risk_exposure = carbon_cost * 0.2
            carbon_intensity = emissions_mt / distance_km

            # Return financial metrics
            return EmissionsFinancialMetrics(
                carbon_cost=carbon_cost,
                operational_cost=operational_cost,
                risk_exposure=risk_exposure,
                total_impact=carbon_cost + operational_cost,
                total_risk_adjusted=(carbon_cost + operational_cost + risk_exposure),
                carbon_intensity=carbon_intensity,
                marginal_abatement_cost=carbon_cost / emissions_mt,
                social_cost_carbon=social_cost,
                regulatory_compliance_cost=carbon_cost * COMPLIANCE_COST_RATE,
                carbon_price_sensitivity=carbon_cost * CARBON_PRICE_VOLATILITY,
                opportunity_cost=carbon_cost * DISCOUNT_RATE,
                net_present_value=(carbon_cost + operational_cost) / (1 + DISCOUNT_RATE) ** time_horizon_years,
                emission_reduction_roi=(social_cost - carbon_cost) / carbon_cost,
                cost_per_passenger_mile=operational_cost / (distance_km * 0.621371),
                carbon_market_exposure=carbon_cost * (1 + CARBON_PRICE_VOLATILITY)
            )

        except Exception as e:
            print(f"Error in calculate_match_costs: {str(e)}")
            return None

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
        """Calculate emissions for a flight using ICAO methodology."""
        # Calculate base distance (one-way)
        base_distance = calculate_distance(origin_lat, origin_lon, dest_lat, dest_lon)

        # Calculate base emissions using ICAO calculator
        icao_results = self.icao_calculator.calculate_emissions(
            distance_km=base_distance,
            aircraft_type=aircraft_type,
            cabin_class=cabin_class,
            passengers=passengers,
            cargo_tons=cargo_tons,
            is_international=is_international
        )

        # Calculate total emissions based on round trip setting
        total_emissions = icao_results["emissions_total_kg"]
        if is_round_trip:
            total_emissions *= 2
            base_distance *= 2

        # Create result object
        result = EmissionsResult(
            total_emissions=total_emissions / 1000,  # Convert to metric tons
            per_passenger=(total_emissions / passengers) / 1000,
            distance_km=base_distance,  # This will be doubled for round trip
            corrected_distance_km=icao_results["corrected_distance_km"] * (2 if is_round_trip else 1),
            fuel_consumption=icao_results["fuel_consumption_kg"] * (2 if is_round_trip else 1),
            flight_type=determine_mileage_type(base_distance / (2 if is_round_trip else 1)),
            # Use one-way distance for type
            is_round_trip=is_round_trip,
            additional_data=icao_results["factors_applied"]
        )

        return result

    def get_environmental_impact(self) -> Dict[str, float]:
        """Calculate environmental impact metrics."""
        if not self.latest_result:
            return {}

        from src.utils.calculations import calculate_equivalencies
        return calculate_equivalencies(self.latest_result.total_emissions)
