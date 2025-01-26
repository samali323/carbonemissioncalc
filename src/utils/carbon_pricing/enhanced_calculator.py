# src/utils/carbon_pricing/enhanced_calculator.py

class EnhancedCarbonPricingCalculator:
    """Enhanced calculator for aviation carbon pricing schemes"""

    def __init__(self):
        # Constants for EU ETS
        self.EU_ETS_PRICE = 88.46  # EUR/ton
        self.EU_ETS_FORECAST = {
            2024: 88.46,
            2025: 95.0,
            2026: 102.0,
            2027: 110.0  # Extension to all departing flights
        }

        # EEA Countries (EU + Iceland, Liechtenstein, Norway)
        self.EEA_COUNTRIES = {
            'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR',
            'DE', 'GR', 'HU', 'IS', 'IE', 'IT', 'LV', 'LI', 'LT', 'LU',
            'MT', 'NL', 'NO', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE'
        }

        # Flight Classification
        self.FLIGHT_CATEGORIES = {
            'domestic': {'description': 'Within same country'},
            'intra_eea': {'description': 'Between EEA countries'},
            'eea_outbound': {'description': 'From EEA to non-EEA'},
            'eea_inbound': {'description': 'From non-EEA to EEA'},
            'international': {'description': 'Between non-EEA countries'}
        }

        # Carbon Pricing
        self.CARBON_PRICES = {
            'AL': 12.19,  # Albania
            'AT': 45.00,  # Austria
            'DK': 26.13,  # Denmark
            'EE': 2.00,   # Estonia
            'FI': 93.02,  # Finland
            'FR': 44.60,  # France
            'DE': 45.00,  # Germany
            'HU': 36.00,  # Hungary
            'IS': 33.95,  # Iceland
            'IE': 56.00,  # Ireland
            'LV': 15.00,  # Latvia
            'LI': 122.87, # Liechtenstein
            'LU': 46.43,  # Luxembourg
            'NL': 66.50,  # Netherlands
            'NO': 99.01,  # Norway
            'PL': 0.09,   # Poland
            'PT': 56.25,  # Portugal
            'SI': 17.30,  # Slovenia
            'ES': 15.00,  # Spain
            'SE': 118.35, # Sweden
            'CH': 122.87, # Switzerland
            'UA': 0.72,   # Ukraine
            'GB': 21.04,  # United Kingdom
        }

        # Fuel Parameters
        self.FUEL_PARAMS = {
            'conventional': {
                'price': 1.20,  # EUR/L for Jet A-1
                'emissions': 3.16  # kg CO2/L
            },
            'saf': {
                'price': 2.50,  # EUR/L for SAF
                'emissions': 0.80,  # kg CO2/L
                'blend_requirement': 0.02  # 2% in 2024
            }
        }

    def classify_flight(self, origin: str, destination: str) -> str:
        """Determine flight category based on origin and destination"""
        if origin == destination:
            return 'domestic'
        elif origin in self.EEA_COUNTRIES and destination in self.EEA_COUNTRIES:
            return 'intra_eea'
        elif origin in self.EEA_COUNTRIES:
            return 'eea_outbound'
        elif destination in self.EEA_COUNTRIES:
            return 'eea_inbound'
        return 'international'

    def calculate_carbon_costs(self,
                               origin: str,
                               destination: str,
                               emissions: float,  # Now using ICAO emissions directly
                               fuel_usage: float,
                               include_forecast: bool = True) -> dict:
        """
        Calculate comprehensive carbon costs using ICAO emissions values

        Args:
            origin: Origin country code
            destination: Destination country code
            emissions: Total CO2 emissions in metric tons (from ICAO calculator)
            fuel_usage: Total fuel usage in liters
            include_forecast: Include future cost projections
        """
        flight_type = self.classify_flight(origin, destination)

        # Initialize results
        results = {
            'flight_type': flight_type,
            'current_costs': {
                'eu_ets': 0.0,
                'national': 0.0,
                'fuel': 0.0,
                'total': 0.0
            },
            'applicable_schemes': [],
            'fuel_breakdown': {},
            'forecast': {} if include_forecast else None
        }

        # Calculate SAF blend
        total_fuel = fuel_usage
        saf_volume = total_fuel * self.FUEL_PARAMS['saf']['blend_requirement']
        conv_volume = total_fuel * (1 - self.FUEL_PARAMS['saf']['blend_requirement'])

        # Calculate fuel costs
        conv_cost = conv_volume * self.FUEL_PARAMS['conventional']['price']
        saf_cost = saf_volume * self.FUEL_PARAMS['saf']['price']

        # Use proportional emissions based on ICAO total
        saf_proportion = saf_volume / total_fuel
        conv_proportion = conv_volume / total_fuel

        results['fuel_breakdown'] = {
            'conventional': {
                'volume': conv_volume,
                'cost': conv_cost,
                'emissions': emissions * conv_proportion  # Proportional emissions
            },
            'saf': {
                'volume': saf_volume,
                'cost': saf_cost,
                'emissions': emissions * saf_proportion  # Proportional emissions
            }
        }

        # Calculate EU ETS costs
        if flight_type in ['intra_eea', 'eea_outbound']:
            results['current_costs']['eu_ets'] = emissions * self.EU_ETS_PRICE
            results['applicable_schemes'].append('EU ETS')

        # Calculate national carbon costs
        origin_tax = self.CARBON_PRICES.get(origin, 0)
        if origin_tax > 0:
            results['current_costs']['national'] = emissions * origin_tax
            results['applicable_schemes'].append(f'{origin} National Carbon Tax')

        # Calculate total fuel cost
        results['current_costs']['fuel'] = conv_cost + saf_cost

        # Calculate total costs
        results['current_costs']['total'] = sum(results['current_costs'].values())

        # Generate forecast if requested
        if include_forecast:
            results['forecast'] = self._generate_forecast(
                emissions=emissions,
                fuel_usage=fuel_usage,
                flight_type=flight_type
            )

        return results
    def _generate_forecast(self, emissions: float, fuel_usage: float, flight_type: str) -> dict:
        """Generate cost forecasts for next three years"""
        forecast = {}
        base_year = 2024

        for year in range(base_year, base_year + 3):
            # Adjust EU ETS price
            ets_price = self.EU_ETS_FORECAST.get(year, self.EU_ETS_FORECAST[base_year])

            # Increase SAF blend requirement
            saf_requirement = self.FUEL_PARAMS['saf']['blend_requirement'] * (1.25 ** (year - base_year))

            # Calculate costs with future parameters
            conv_fuel = fuel_usage * (1 - saf_requirement)
            saf_fuel = fuel_usage * saf_requirement

            forecast[year] = {
                'eu_ets_price': ets_price,
                'saf_requirement': saf_requirement,
                'conventional_fuel_cost': conv_fuel * self.FUEL_PARAMS['conventional']['price'] * 1.05**(year - base_year),
                'saf_fuel_cost': saf_fuel * self.FUEL_PARAMS['saf']['price'] * 1.03**(year - base_year),
                'carbon_cost': emissions * ets_price if flight_type in ['intra_eea', 'eea_outbound'] else 0
            }

            forecast[year]['total_cost'] = (
                    forecast[year]['conventional_fuel_cost'] +
                    forecast[year]['saf_fuel_cost'] +
                    forecast[year]['carbon_cost']
            )

        return forecast

    def get_pricing_explanation(self, origin: str, destination: str) -> str:
        """Get detailed explanation of applicable carbon pricing"""
        flight_type = self.classify_flight(origin, destination)

        explanations = [
            f"Flight Classification: {self.FLIGHT_CATEGORIES[flight_type]['description']}"
        ]

        if flight_type in ['intra_eea', 'eea_outbound']:
            explanations.append(f"EU ETS Applies: €{self.EU_ETS_PRICE}/ton CO2")

        origin_tax = self.CARBON_PRICES.get(origin)
        if origin_tax:
            explanations.append(f"National Carbon Tax ({origin}): €{origin_tax}/ton CO2")

        explanations.append(
            f"SAF Blend Requirement: {self.FUEL_PARAMS['saf']['blend_requirement']*100}%"
        )

        return "\n".join(explanations)
