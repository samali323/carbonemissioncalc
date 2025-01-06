"""Constants and configurations for the emissions calculator."""

# Conversion factors
KM_PER_MILE = 1.60934

# Transport mode characteristics
TRANSPORT_MODES = {

    'air': {

        'mode': 'air',

        'co2_per_km': 0.0,  # Calculated differently for air

        'speed': 800,       # km/h

        'cost_per_km': 0.50, # USD per passenger-km

        'distance_multiplier': 1.0  # Direct route

    },

    'rail': {

        'mode': 'rail',

        'co2_per_km': 0.041,  # Modern electric train

        'speed': 200,         # Average high-speed rail

        'cost_per_km': 0.18,

        'distance_multiplier': 1.2  # 20% longer than air route

    },

    'bus': {

        'mode': 'bus',

        'co2_per_km': 0.027,  # Modern coach bus

        'speed': 80,          # Average coach speed

        'cost_per_km': 0.12,

        'distance_multiplier': 1.4  # 40% longer than air route

    }

}
# Emission factors for different flight types
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
