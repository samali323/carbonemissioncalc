"""Constants and configurations for the emissions calculator."""

# Updated constants.py

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


# Default to EU ETS price if country not found

EU_ETS_PRICE = 88.46

DEFAULT_CARBON_PRICE = EU_ETS_PRICE


# Currency conversion rates

EUR_TO_GBP = 0.86

GBP_TO_EUR = 1.16

TEAM_COUNTRIES = {
    # England (GB)
    'Arsenal FC': 'GB',
    'Aston Villa': 'GB',
    'Bournemouth': 'GB',
    'Brighton & Hove Albion': 'GB',
    'Brentford': 'GB',
    'Chelsea': 'GB',
    'Crystal Palace': 'GB',
    'Everton': 'GB',
    'Fulham': 'GB',
    'Ipswich Town': 'GB',
    'Leicester City': 'GB',
    'Liverpool': 'GB',
    'Manchester City': 'GB',
    'Manchester United': 'GB',
    'Newcastle United': 'GB',
    'Nottingham Forest': 'GB',
    'Southampton': 'GB',
    'Tottenham Hotspur': 'GB',
    'West Ham United': 'GB',
    'Wolverhampton Wanderers': 'GB',

    # Germany (DE)
    '1. FC Heidenheim': 'DE',
    'Bayer Leverkusen': 'DE',
    'Bayern Munich': 'DE',
    'Borussia Dortmund': 'DE',
    'Borussia Monchengladbach': 'DE',
    'Eintracht Frankfurt': 'DE',
    'FC Augsburg': 'DE',
    'FC St. Pauli': 'DE',
    'Holstein Kiel': 'DE',
    'Mainz 05': 'DE',
    'RB Leipzig': 'DE',
    'SC Freiburg': 'DE',
    'TSG Hoffenheim': 'DE',
    'Union Berlin': 'DE',
    'VfB Stuttgart': 'DE',
    'VfL Bochum': 'DE',
    'VfL Wolfsburg': 'DE',
    'Werder Bremen': 'DE',

    # Spain (ES)
    'Alaves': 'ES',
    'Athletic Bilbao': 'ES',
    'Atletico Madrid': 'ES',
    'Barcelona': 'ES',
    'Celta Vigo': 'ES',
    'Espanyol': 'ES',
    'Getafe': 'ES',
    'Girona': 'ES',
    'Las Palmas': 'ES',
    'Leganes': 'ES',
    'Mallorca': 'ES',
    'Osasuna': 'ES',
    'Rayo Vallecano': 'ES',
    'Real Betis': 'ES',
    'Real Madrid': 'ES',
    'Real Sociedad': 'ES',
    'Sevilla': 'ES',
    'Valencia': 'ES',
    'Valladolid': 'ES',
    'Villarreal': 'ES',

    # Italy (IT)
    'AC Milan': 'IT',
    'Atalanta': 'IT',
    'Bologna': 'IT',
    'Cagliari': 'IT',
    'Como': 'IT',
    'Empoli': 'IT',
    'Fiorentina': 'IT',
    'Genoa': 'IT',
    'Hellas Verona': 'IT',
    'Inter Milan': 'IT',
    'Juventus': 'IT',
    'Lazio': 'IT',
    'Lecce': 'IT',
    'Monza': 'IT',
    'Napoli': 'IT',
    'Parma': 'IT',
    'Roma': 'IT',
    'Torino': 'IT',
    'Udinese': 'IT',
    'Venezia': 'IT',

    # France (FR)
    'Angers': 'FR',
    'AS Monaco': 'FR',
    'Auxerre': 'FR',
    'Brest': 'FR',
    'Le Havre': 'FR',
    'Lens': 'FR',
    'Lille': 'FR',
    'Lyon': 'FR',
    'Marseille': 'FR',
    'Montpellier': 'FR',
    'Nantes': 'FR',
    'Nice': 'FR',
    'Paris Saint-Germain': 'FR',
    'Reims': 'FR',
    'Rennes': 'FR',
    'Saint-Etienne': 'FR',
    'Strasbourg': 'FR',
    'Toulouse': 'FR',

    # Netherlands (NL)
    'Ajax': 'NL',
    'AZ Alkmaar': 'NL',
    'Feyenoord': 'NL',
    'PSV Eindhoven': 'NL',
    'Twente': 'NL',

    # Portugal (PT)
    'Benfica': 'PT',
    'Braga': 'PT',
    'Porto': 'PT',
    'Sporting CP': 'PT',
    'Vitoria de Guimaraes': 'PT',

    # Belgium (BE)
    'Anderlecht': 'BE',
    'Cercle Brugge': 'BE',
    'Club Brugge': 'BE',
    'Gent': 'BE',
    'Union Saint-Gilloise': 'BE',

    # Scotland (GB)
    'Celtic': 'GB',
    'Hearts': 'GB',
    'Rangers': 'GB',

    # Turkey (TR)
    'Besiktas': 'TR',
    'Fenerbahce': 'TR',
    'Galatasaray': 'TR',
    'Istanbul Basaksehir': 'TR',

    # Greece (GR)
    'Olympiacos': 'GR',
    'PAOK': 'GR',
    'Panathinaikos': 'GR',

    # Ukraine (UA)
    'Dynamo Kyiv': 'UA',
    'Shakhtar Donetsk': 'UA',

    # Czech Republic (CZ)
    'Celje': 'CZ',
    'Mlada Boleslav': 'CZ',
    'Slavia Prague': 'CZ',
    'Sparta Prague': 'CZ',
    'Viktoria Plzen': 'CZ',

    # Austria (AT)
    'LASK': 'AT',
    'Rapid Wien': 'AT',
    'Red Bull Salzburg': 'AT',
    'Sturm Graz': 'AT',

    # Switzerland (CH)
    'Lugano': 'CH',
    'St. Gallen': 'CH',
    'Young Boys': 'CH',

    # Sweden (SE)
    'Djurgardens IF': 'SE',
    'IF Elfsborg': 'SE',
    'Malmo FF': 'SE',

    # Finland (FI)
    'HJK Helsinki': 'FI',

    # Norway (NO)
    'Bodo/Glimt': 'NO',
    'Molde': 'NO',

    # Denmark (DK)
    'Copenhagen': 'DK',
    'Midtjylland': 'DK',

    # Hungary (HU)
    'Ferencvaros': 'HU',

    # Serbia (RS)
    'FK TSC Backa Topola': 'RS',
    'Red Star Belgrade': 'RS',

    # Croatia (HR)
    'Dinamo Zagreb': 'HR',

    # Slovakia (SK)
    'Slovan Bratislava': 'SK',

    # Slovenia (SI)
    'Olimpija Ljubljana': 'SI',

    # Romania (RO)
    'FCSB': 'RO',
    'Petrocub Hincesti': 'RO',

    # Belarus (BY)
    'Dinamo Minsk': 'BY',

    # Latvia (LV)
    'RFS': 'LV',

    # Kazakhstan (KZ)
    'Astana': 'KZ',

    # Israel (IL)
    'Maccabi Tel Aviv': 'IL',

    # Cyprus (CY)
    'APOEL': 'CY',
    'Omonia': 'CY',
    'Pafos': 'CY',

    # Azerbaijan (AZ)
    'Qarabag': 'AZ',

    # Armenia (AM)
    'Noah': 'AM',

    # Poland (PL)
    'Jagiellonia Biaystok': 'PL',
    'Legia Warsaw': 'PL',

    # Iceland (IS)
    'Vikingur Reykjavik': 'IS',

    # Ireland (IE)
    'Shamrock Rovers': 'IE',

    # Wales (GB)
    'The New Saints': 'GB',

    # Northern Ireland (GB)
    'Larne': 'GB',

    # Bosnia and Herzegovina (BA)
    'Borac Banja Luka': 'BA'
}

# Updated Social Cost of Carbon (convert $1367/short ton to metric ton)
# 1 metric ton = 1.10231 short tons
SOCIAL_CARBON_COST = 1367 / 1.10231  # Now approximately $1240.15 per metric ton
# Social carbon cost estimates (in USD per metric ton CO2)

SOCIAL_CARBON_COSTS = {

    'synthetic_median': 185.0,

    'synthetic_mean': 283.0,

    'synthetic_iqr_low': 97.0,

    'synthetic_iqr_high': 369.0,

    'epa_median': 157.0,

    'iwg_75th': 52.0

}


# Replace the existing SOCIAL_CARBON_COST constant with:

SOCIAL_CARBON_COST = SOCIAL_CARBON_COSTS['synthetic_median']  # Using median as default

# Different discount rates for sensitivity analysis
DISCOUNT_RATES = {
    'low': 0.02,      # 2% - conservative
    'medium': 0.05,   # 5% - moderate
    'high': 0.10      # 10% - aggressive
}

# Keep existing constants but update these
CARBON_PRICE = 80.0  # Default to EU avg price if country not specified
SOCIAL_COST_MULTIPLIER = SOCIAL_CARBON_COST / CARBON_PRICE  # Updated multiplier

# Conversion factors
KM_PER_MILE = 1.60934

# Financial and economic parameters
CARBON_PRICE = 80.0  # USD per metric ton CO2
FUEL_COST = 2.89  # USD per gallon A-1 Jet Fuel
PASSENGER_LOAD = 30  # Average team travel party
RISK_RATE = 0.047  # Risk premium rate
DISCOUNT_RATE = 0.10  # For NPV calculations
CARBON_PRICE_VOLATILITY = 0.25  # Annual volatility
SOCIAL_CARBON_COST = 1367.0  #https://www.nber.org/papers/w32450
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
