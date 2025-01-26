
# Financial Constants

# ============= CURRENCY AND CONVERSION CONSTANTS =============
KM_PER_MILE = 1.60934
EUR_TO_GBP = 0.86
GBP_TO_EUR = 1.16

# ============= CARBON PRICING CONSTANTS =============

EU_ETS_PRICE = 88.46
DEFAULT_CARBON_PRICE = EU_ETS_PRICE
CARBON_PRICE = 80.0  # USD per metric ton CO2
CARBON_PRICE_VOLATILITY = 0.25  # Annual volatility
ANNUAL_CARBON_PRICE_GROWTH = 0.05  # Annual carbon price growth rate

# Country-specific carbon prices (EUR)
CARBON_PRICES_EUR = {

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

# ============= SOCIAL COST CONSTANTS =============
SOCIAL_CARBON_COSTS = {
    'synthetic_median': 185.0,
    'synthetic_mean': 283.0,
    'synthetic_iqr_low': 97.0,
    'synthetic_iqr_high': 369.0,
    'epa_median': 157.0,
    'iwg_75th': 52.0,
    'nber_research': 1367
}
SOCIAL_CARBON_COST = SOCIAL_CARBON_COSTS['synthetic_median']
SOCIAL_COST_MULTIPLIER = SOCIAL_CARBON_COST / CARBON_PRICE
SOCIAL_CARBON_COST = 1367 / 1.10231  # Now approximately $1240.15 per metric ton

# ============= FINANCIAL PARAMETERS =============

# Different discount rates for sensitivity analysis
DISCOUNT_RATES = {
    'low': 0.02,      # 2% - conservative
    'medium': 0.05,   # 5% - moderate
    'high': 0.10      # 10% - aggressive
}
DISCOUNT_RATE = 0.10  # Default for NPV calculations
RISK_RATE = 0.047    # Risk premium rate
FUEL_COST = 2.89     # USD per gallon A-1 Jet Fuel
COMPLIANCE_COST_RATE = 0.15  # Compliance cost as % of carbon cost
EFFICIENCY_INVESTMENT_PER_TON = 1000  # Investment needed per ton reduction
EXPECTED_REDUCTION_RATE = 0.15  # Expected emission reduction rate

# ============= TRANSPORT CONSTANTS =============
DEFAULT_PASSENGERS = 30
DEFAULT_CARGO_TONS = 2.0
PASSENGER_LOAD = 30  # Average team travel party
ALTERNATIVE_TRANSPORT_PREMIUM = 1.35  # Premium for alternative transport

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

# ============= EMISSION FACTORS =============
# Flight class emission factors (kg CO2 per passenger-km)
EMISSION_FACTORS = {
    'LongBusiness': 0.163 / 1.60934,
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

# Aircraft-specific emission factors (kg CO2 per passenger-km)
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
