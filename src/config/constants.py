"""Constants and configurations for the emissions calculator."""

# Conversion factors
KM_PER_MILE = 1.60934

# Financial and economic parameters
CARBON_PRICE = 15.0  # USD per metric ton CO2
FUEL_COST = 2.89  # USD per gallon A-1 Jet Fuel
PASSENGER_LOAD = 30  # Average team travel party
RISK_RATE = 0.047  # Risk premium rate
DISCOUNT_RATE = 0.10  # For NPV calculations
CARBON_PRICE_VOLATILITY = 0.25  # Annual volatility
SOCIAL_CARBON_COST = 51.0  # current Biden admin estimate
SOCIAL_COST_MULTIPLIER = 3.0  # Social cost vs market price
COMPLIANCE_COST_RATE = 0.15  # Compliance cost as % of carbon cost
ALTERNATIVE_TRANSPORT_PREMIUM = 1.35  # Premium for alternative transport
EFFICIENCY_INVESTMENT_PER_TON = 1000  # Investment needed per ton reduction
EXPECTED_REDUCTION_RATE = 0.15  # Expected emission reduction rate
ANNUAL_CARBON_PRICE_GROWTH = 0.05  # Annual carbon price growth rate

# Transport mode characteristics
TRANSPORT_MODES = {

    'air': {

        'mode': 'air',

        'co2_per_km': 0.0,  # Handled separately using EMISSION_FACTORS

        'speed': 800,       # km/h

        'distance_multiplier': 1.0

    },

    'rail': {

        'mode': 'rail',

        'co2_per_km': 0.041,  # kg CO2 per passenger-km

        'speed': 200,

        'distance_multiplier': 1.2

    },

    'bus': {

        'mode': 'bus',

        'co2_per_km': 0.027,  # kg CO2 per passenger-km

        'speed': 80,

        'distance_multiplier': 1.3  # Updated from 1.4

    }

}
EMISSION_FACTORS = {
    'LongBusiness': 0.163 / 1.60934,    # Convert to kg CO2 per passenger-km
    'LongEconomy': 0.163 / 1.60934,
    'LongFirst': 0.163 / 1.60934,
    'LongPremiumEconomy': 0.163 / 1.60934,
    'MediumBusiness': 0.129 / 1.60934,
    'MediumEconomy': 0.129 / 1.60934,
    'MediumFirst': 0.129 / 1.60934,
    'MediumPremiumEconomy': 0.129 / 1.60934,
    'ShortBusiness': 0.207 / 1.60934,
    'ShortEconomy': 0.207 / 1.60934,
    'ShortFirst': 0.207 / 1.60934,
    'ShortPremiumEconomy': 0.207 / 1.60934
}

# Aircraft specific emission factors
AIRCRAFT_EMISSION_FACTORS = {
    'G-NEWG': 0.54 / 1.60934, 'G-SWRD': 0.54 / 1.60934,
    'G-CMLI': 0.15 / 1.60934, 'G-IACY': 0.10 / 1.60934,
    'G-CMEI': 0.18 / 1.60934, 'G-CLSN': 0.10 / 1.60934,
    'G-MAJY': 0.10 / 1.60934, 'G-MAJZ': 0.10 / 1.60934,
    'G-SAJC': 0.16 / 1.60934, 'G-SAJG': 0.16 / 1.60934,
    'G-SAJH': 0.16 / 1.60934, 'G-SAJK': 0.16 / 1.60934,
    'G-SAJN': 0.16 / 1.60934, 'G-SAJO': 0.16 / 1.60934,
    'G-POWK': 0.09 / 1.60934, 'G-POWT': 0.09 / 1.60934,
    'G-ISLO': 0.10 / 1.60934, 'G-ISLK': 0.10 / 1.60934,
    'G-ISLM': 0.10 / 1.60934,
    'G-GDFJ': 0.11 / 1.60934, 'G-GDFL': 0.11 / 1.60934
}

# Default values
DEFAULT_PASSENGERS = 30
DEFAULT_CARGO_TONS = 2.0
