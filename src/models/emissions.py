"""Core emissions calculation model."""
from dataclasses import dataclass
from typing import Dict, Optional
from src.utils.calculations import calculate_distance, determine_mileage_type
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
        self.icao_calculator = ICAOEmissionsCalculator()

    def calculate_match_costs(
            self,
            distance_km: float,
            emissions_mt: float,
            is_international: bool = False,
            time_horizon_years: int = 5,
            aircraft_type: str = "A320",
            route_type: str = "INTRA_EUROPE"
    ) -> EmissionsFinancialMetrics:
        """
        Calculate comprehensive match costs including emissions, operations, and risk factors.

        Args:
            distance_km: Distance in kilometers
            emissions_mt: Emissions in metric tons
            is_international: Whether the flight is international
            time_horizon_years: Years for future cost projections
            aircraft_type: Type of aircraft used
            route_type: Type of route

        Returns:
            EmissionsFinancialMetrics object containing all financial metrics
        """
        try:
            # Base carbon price (example values)
            carbon_price_per_ton = 50.0  # Current carbon price
            operational_cost_per_km = 15.0  # Basic operational cost per km

            # Calculate basic costs
            carbon_cost = emissions_mt * carbon_price_per_ton
            operational_cost = distance_km * operational_cost_per_km

            # Calculate risk factors
            risk_exposure = carbon_cost * 0.2  # 20% risk factor
            carbon_market_exposure = carbon_cost * 1.5  # Future market exposure

            # Calculate efficiency metrics
            carbon_intensity = emissions_mt / distance_km
            marginal_abatement_cost = carbon_cost / emissions_mt
            cost_per_passenger_mile = operational_cost / (distance_km * 0.621371)  # Convert to miles

            # Calculate long-term impacts
            social_cost_carbon = emissions_mt * 100  # Social cost per ton
            regulatory_compliance_cost = carbon_cost * 0.1  # 10% of carbon cost

            # Calculate total impacts
            total_impact = carbon_cost + operational_cost
            total_risk_adjusted = total_impact + risk_exposure

            # ROI and NPV calculations
            emission_reduction_roi = 0.15  # 15% expected return
            net_present_value = total_impact * (1 - (1 / (1 + 0.05) ** time_horizon_years))

            # Carbon price sensitivity
            carbon_price_sensitivity = carbon_cost * 0.1  # 10% sensitivity factor

            return EmissionsFinancialMetrics(
                carbon_cost=carbon_cost,
                operational_cost=operational_cost,
                risk_exposure=risk_exposure,
                total_impact=total_impact,
                total_risk_adjusted=total_risk_adjusted,
                carbon_intensity=carbon_intensity,
                marginal_abatement_cost=marginal_abatement_cost,
                social_cost_carbon=social_cost_carbon,
                regulatory_compliance_cost=regulatory_compliance_cost,
                carbon_price_sensitivity=carbon_price_sensitivity,
                opportunity_cost=carbon_cost * 0.05,  # 5% opportunity cost
                net_present_value=net_present_value,
                emission_reduction_roi=emission_reduction_roi,
                cost_per_passenger_mile=cost_per_passenger_mile,
                carbon_market_exposure=carbon_market_exposure
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
