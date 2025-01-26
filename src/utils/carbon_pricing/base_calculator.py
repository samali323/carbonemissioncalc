# src/utils/carbon_pricing/base_calculator.py

class CarbonPricingCalculator:
    """Base calculator for aviation carbon pricing schemes"""

    def __init__(self):
        self.EU_ETS_PRICE = 88.0  # EUR/ton CO2 in 2024
        self.CORSIA_CREDIT_PRICE = 2.0  # EUR/ton CO2

        self.EEA_COUNTRIES = {
            'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR',
            'DE', 'GR', 'HU', 'IS', 'IE', 'IT', 'LV', 'LI', 'LT', 'LU',
            'MT', 'NL', 'NO', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE'
        }

        self.CORSIA_COUNTRIES = set()  # Add participating countries

    def is_eea_flight(self, origin: str, destination: str) -> bool:
        """Check if flight is within EEA"""
        return origin in self.EEA_COUNTRIES and destination in self.EEA_COUNTRIES

    def is_eea_connected(self, origin: str, destination: str) -> bool:
        """Check if flight connects to/from EEA"""
        return origin in self.EEA_COUNTRIES or destination in self.EEA_COUNTRIES

    def is_corsia_flight(self, origin: str, destination: str) -> bool:
        """Check if flight is covered by CORSIA"""
        return (origin in self.CORSIA_COUNTRIES and
                destination in self.CORSIA_COUNTRIES and
                origin != destination)  # Must be international

    def calculate_carbon_cost(self,
                              origin: str,
                              destination: str,
                              emissions: float,
                              distance_km: float) -> dict:
        """Basic carbon cost calculation"""
        costs = {
            'eu_ets': 0.0,
            'corsia': 0.0,
            'national': 0.0,
            'total': 0.0,
            'schemes': []
        }

        # Calculate EU ETS costs
        if self.is_eea_flight(origin, destination):
            costs['eu_ets'] = emissions * self.EU_ETS_PRICE
            costs['schemes'].append('EU ETS')

        # Calculate CORSIA costs
        if self.is_corsia_flight(origin, destination):
            costs['corsia'] = emissions * self.CORSIA_CREDIT_PRICE
            costs['schemes'].append('CORSIA')

        costs['total'] = costs['eu_ets'] + costs['corsia'] + costs['national']

        return costs
