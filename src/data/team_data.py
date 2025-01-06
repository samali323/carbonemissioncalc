# src/data/team_data.py
"""Team and airport data for the emissions calculator."""

TEAM_AIRPORTS = {
    # England

    'Arsenal FC': 'LHR',

    'Aston Villa': 'BHX',

    'Bournemouth': 'BOH',

    'Brentford': 'LHR',

    'Brighton & Hove Albion': 'LGW',

    'Chelsea': 'LHR',

    'Crystal Palace': 'LGW',

    'Everton': 'LPL',

    'Fulham': 'LHR',

    'Ipswich Town': 'STN',

    'Leicester City': 'EMA',

    'Liverpool': 'LPL',

    'Manchester City': 'MAN',

    'Manchester United': 'MAN',

    'Newcastle United': 'NCL',

    'Nottingham Forest': 'EMA',

    'Southampton': 'SOU',

    'Tottenham Hotspur': 'LHR',

    'West Ham United': 'LCY',

    'Wolverhampton Wanderers': 'BHX',

    # Germany

    '1. FC Heidenheim': 'STR',

    'Bayer Leverkusen': 'CGN',

    'Bayern Munich': 'MUC',

    'Borussia Dortmund': 'DTM',

    'Borussia Monchengladbach': 'DUS',

    'Eintracht Frankfurt': 'FRA',

    'FC Augsburg': 'AGB',

    'FC St. Pauli': 'HAM',

    'Holstein Kiel': 'HAM',

    'Mainz 05': 'FRA',

    'RB Leipzig': 'LEJ',

    'SC Freiburg': 'FKB',

    'TSG Hoffenheim': 'FRA',

    'Union Berlin': 'BER',

    'VfB Stuttgart': 'STR',

    'VfL Bochum': 'DTM',

    'VfL Wolfsburg': 'HAJ',

    'Werder Bremen': 'BRE',

    # Spain

    'Alaves': 'VIT',

    'Athletic Bilbao': 'BIO',

    'Atletico Madrid': 'MAD',

    'Barcelona': 'BCN',

    'Celta Vigo': 'VGO',

    'Espanyol': 'BCN',

    'Getafe': 'MAD',

    'Girona': 'GRO',

    'Las Palmas': 'LPA',

    'Leganes': 'MAD',

    'Mallorca': 'PMI',

    'Osasuna': 'PNA',

    'Rayo Vallecano': 'MAD',

    'Real Betis': 'SVQ',

    'Real Madrid': 'MAD',

    'Real Sociedad': 'EAS',

    'Sevilla': 'SVQ',

    'Valencia': 'VLC',

    'Valladolid': 'VLL',

    'Villarreal': 'VLC',

    # Italy

    'AC Milan': 'MXP',

    'Atalanta': 'BGY',

    'Bologna': 'BLQ',

    'Cagliari': 'CAG',

    'Como': 'MXP',

    'Empoli': 'FLR',

    'Fiorentina': 'FLR',

    'Genoa': 'GOA',

    'Hellas Verona': 'VRN',

    'Inter Milan': 'MXP',

    'Juventus': 'TRN',

    'Lazio': 'FCO',

    'Lecce': 'BDS',

    'Monza': 'MXP',

    'Napoli': 'NAP',

    'Parma': 'PMF',

    'Roma': 'FCO',

    'Torino': 'TRN',

    'Udinese': 'TRS',

    'Venezia': 'VCE',

    # France

    'Angers': 'ANE',

    'AS Monaco': 'NCE',

    'Auxerre': 'CDG',

    'Brest': 'BES',

    'Le Havre': 'LEH',

    'Lens': 'LIL',

    'Lille': 'LIL',

    'Lyon': 'LYS',

    'Marseille': 'MRS',

    'Montpellier': 'MPL',

    'Nantes': 'NTE',

    'Nice': 'NCE',

    'Paris Saint-Germain': 'CDG',

    'Reims': 'CDG',

    'Rennes': 'RNS',

    'Saint-Etienne': 'EBU',

    'Strasbourg': 'SXB',

    'Toulouse': 'TLS',

    # Netherlands

    'Ajax': 'AMS',

    'AZ Alkmaar': 'AMS',

    'Feyenoord': 'RTM',

    'PSV Eindhoven': 'EIN',

    'Twente': 'AMS',

    # Portugal

    'Benfica': 'LIS',

    'Braga': 'OPO',

    'Porto': 'OPO',

    'Sporting CP': 'LIS',

    'Vitoria de Guimaraes': 'OPO',

    # Belgium

    'Anderlecht': 'BRU',

    'Cercle Brugge': 'OST',

    'Club Brugge': 'OST',

    'Gent': 'BRU',

    'Union Saint-Gilloise': 'BRU',

    # Scotland

    'Celtic': 'GLA',

    'Hearts': 'EDI',

    'Rangers': 'GLA',

    # Turkey

    'Besiktas': 'IST',

    'Fenerbahce': 'IST',

    'Galatasaray': 'IST',

    'Istanbul Basaksehir': 'IST',

    # Greece

    'Olympiacos': 'ATH',

    'PAOK': 'SKG',

    'Panathinaikos': 'ATH',

    # Ukraine

    'Dynamo Kyiv': 'IEV',

    'Shakhtar Donetsk': 'WAW',  # Currently playing in Warsaw

    # Czech Republic

    'Celje': 'PRG',

    'Mlada Boleslav': 'PRG',

    'Slavia Prague': 'PRG',

    'Sparta Prague': 'PRG',

    'Viktoria Plzen': 'PRG',

    # Austria

    'LASK': 'LNZ',

    'Rapid Wien': 'VIE',

    'Red Bull Salzburg': 'SZG',

    'Sturm Graz': 'GRZ',

    # Switzerland

    'Lugano': 'LUG',

    'St. Gallen': 'ACH',

    'Young Boys': 'BRN',

    # Sweden

    'Djurgardens IF': 'ARN',

    'IF Elfsborg': 'GOT',

    'Malmo FF': 'MMX',

    'HJK Helsinki': 'HEL',

    # Norway

    'Bodo/Glimt': 'BOO',

    'Molde': 'MOL',

    # Denmark

    'Copenhagen': 'CPH',

    'Midtjylland': 'BLL',

    # Hungary

    'Ferencvaros': 'BUD',

    # Serbia

    'FK TSC Backa Topola': 'BEG',

    'Red Star Belgrade': 'BEG',

    # Croatia

    'Dinamo Zagreb': 'ZAG',

    # Slovakia

    'Slovan Bratislava': 'BTS',

    # Slovenia

    'Olimpija Ljubljana': 'LJU',

    # Romania

    'FCSB': 'OTP',

    'Petrocub Hincesti': 'RMO',

    # Belarus

    'Dinamo Minsk': 'MSQ',

    # Latvia

    'RFS': 'RIX',

    # Kazakhstan

    'Astana': 'ALA',

    # Israel

    'Maccabi Tel Aviv': 'TLV',

    # Cyprus

    'APOEL': 'LCA',

    'Omonia': 'LCA',

    'Pafos': 'PFO',

    # Azerbaijan

    'Qarabag': 'GYD',

    # Armenia

    'Noah': 'EVN',

    # Bulgaria

    'Ludogorets Razgrad': 'SOF',

    # Iceland

    'Vikingur Reykjavik': 'RKV',

    # Ireland

    'Shamrock Rovers': 'DUB',

    # Wales

    'The New Saints': 'LPL',  # Uses Liverpool airport

    # Northern Ireland

    'Larne': 'BFS',

    # Bosnia and Herzegovina

    'Borac Banja Luka': 'BNX',

    # Poland

    'Jagiellonia Biaystok': 'WAW',

    'Legia Warsaw': 'WAW'

}

AIRPORT_COORDINATES = {
        # UK Airports
        'LHR': {'lat': 51.4700, 'lon': -0.4543},  # London Heathrow
        'BHX': {'lat': 52.4538, 'lon': -1.7480},  # Birmingham
        'BOH': {'lat': 50.7800, 'lon': -1.8425},  # Bournemouth
        'LGW': {'lat': 51.1537, 'lon': -0.1821},  # London Gatwick
        'LPL': {'lat': 53.3336, 'lon': -2.8497},  # Liverpool
        'STN': {'lat': 51.8850, 'lon': 0.2389},   # London Stansted
        'EMA': {'lat': 52.8311, 'lon': -1.3281},  # East Midlands
        'MAN': {'lat': 53.3537, 'lon': -2.2750},  # Manchester
        'NCL': {'lat': 55.0375, 'lon': -1.6916},  # Newcastle
        'SOU': {'lat': 50.9503, 'lon': -1.3568},  # Southampton
        'LCY': {'lat': 51.5048, 'lon': 0.0495},   # London City
        'BFS': {'lat': 54.6575, 'lon': -6.2158},  # Belfast
        'GLA': {'lat': 55.8687, 'lon': -4.4351},  # Glasgow
        'EDI': {'lat': 55.9500, 'lon': -3.3725},  # Edinburgh

        # German Airports
        'STR': {'lat': 48.6890, 'lon': 9.2220},   # Stuttgart
        'CGN': {'lat': 50.8660, 'lon': 7.1427},   # Cologne
        'MUC': {'lat': 48.3538, 'lon': 11.7861},  # Munich
        'DTM': {'lat': 51.5180, 'lon': 7.6122},   # Dortmund
        'DUS': {'lat': 51.2895, 'lon': 6.7668},   # Düsseldorf
        'FRA': {'lat': 50.0379, 'lon': 8.5622},   # Frankfurt
        'AGB': {'lat': 48.4250, 'lon': 10.9317},  # Augsburg
        'HAM': {'lat': 53.6304, 'lon': 9.9882},   # Hamburg
        'LEJ': {'lat': 51.4237, 'lon': 12.2162},  # Leipzig
        'FKB': {'lat': 48.7793, 'lon': 8.0805},   # Karlsruhe/Baden-Baden
        'BER': {'lat': 52.3667, 'lon': 13.5033},  # Berlin Brandenburg
        'HAJ': {'lat': 52.4610, 'lon': 9.6850},   # Hannover
        'BRE': {'lat': 53.0475, 'lon': 8.7867},   # Bremen

        # Spanish Airports
        'VIT': {'lat': 42.8828, 'lon': -2.7244},  # Vitoria
        'BIO': {'lat': 43.3010, 'lon': -2.9106},  # Bilbao
        'MAD': {'lat': 40.4983, 'lon': -3.5676},  # Madrid
        'BCN': {'lat': 41.2971, 'lon': 2.0785},   # Barcelona
        'VGO': {'lat': 42.2318, 'lon': -8.6273},  # Vigo
        'GRO': {'lat': 41.9009, 'lon': 2.7606},   # Girona
        'LPA': {'lat': 27.9319, 'lon': -15.3867}, # Las Palmas
        'PMI': {'lat': 39.5517, 'lon': 2.7388},   # Palma de Mallorca
        'PNA': {'lat': 42.7700, 'lon': -1.6461},  # Pamplona
        'SVQ': {'lat': 37.4181, 'lon': -5.8931},  # Seville
        'EAS': {'lat': 43.3565, 'lon': -1.7908},  # San Sebastian
        'VLC': {'lat': 39.4893, 'lon': -0.4815},  # Valencia
        'VLL': {'lat': 41.7064, 'lon': -4.8519},  # Valladolid

        # Italian Airports
        'MXP': {'lat': 45.6306, 'lon': 8.7281},   # Milan Malpensa
        'BGY': {'lat': 45.6739, 'lon': 9.7042},   # Bergamo
        'BLQ': {'lat': 44.5354, 'lon': 11.2887},  # Bologna
        'CAG': {'lat': 39.2515, 'lon': 9.0543},   # Cagliari
        'FLR': {'lat': 43.8100, 'lon': 11.2051},  # Florence
        'GOA': {'lat': 44.4133, 'lon': 8.8375},   # Genoa
        'VRN': {'lat': 45.3959, 'lon': 10.8885},  # Verona
        'FCO': {'lat': 41.8045, 'lon': 12.2508},  # Rome Fiumicino
        'BDS': {'lat': 40.6576, 'lon': 17.9478},  # Brindisi
        'NAP': {'lat': 40.8847, 'lon': 14.2908},  # Naples
        'PMF': {'lat': 44.8245, 'lon': 10.2964},  # Parma
        'TRN': {'lat': 45.2008, 'lon': 7.6497},   # Turin
        'TRS': {'lat': 45.8275, 'lon': 13.4722},  # Trieste
        'VCE': {'lat': 45.5053, 'lon': 12.3519},  # Venice

        # French Airports
        'ANE': {'lat': 47.5600, 'lon': -0.3125},  # Angers
        'NCE': {'lat': 43.6584, 'lon': 7.2167},   # Nice
        'CDG': {'lat': 49.0097, 'lon': 2.5478},   # Paris Charles de Gaulle
        'BES': {'lat': 48.4478, 'lon': -4.4186},  # Brest
        'LEH': {'lat': 49.5341, 'lon': 0.0881},   # Le Havre
        'LIL': {'lat': 50.5634, 'lon': 3.0868},   # Lille
        'LYS': {'lat': 45.7256, 'lon': 5.0811},   # Lyon
        'MRS': {'lat': 43.4360, 'lon': 5.2147},   # Marseille
        'MPL': {'lat': 43.5762, 'lon': 3.9630},   # Montpellier
        'NTE': {'lat': 47.1532, 'lon': -1.6111},  # Nantes
        'RNS': {'lat': 48.0694, 'lon': -1.7347},  # Rennes
        'EBU': {'lat': 45.5400, 'lon': 4.2964},   # Saint-Etienne
        'SXB': {'lat': 48.5383, 'lon': 7.6282},   # Strasbourg
        'TLS': {'lat': 43.6293, 'lon': 1.3638},   # Toulouse

        # Benelux Airports
        'AMS': {'lat': 52.3086, 'lon': 4.7639},   # Amsterdam
        'RTM': {'lat': 51.9569, 'lon': 4.4370},   # Rotterdam
        'EIN': {'lat': 51.4500, 'lon': 5.3747},   # Eindhoven
        'BRU': {'lat': 50.9010, 'lon': 4.4856},   # Brussels
        'OST': {'lat': 51.1989, 'lon': 2.8622},   # Ostend

        # Portuguese Airports
        'LIS': {'lat': 38.7813, 'lon': -9.1359},  # Lisbon
        'OPO': {'lat': 41.2481, 'lon': -8.6814},  # Porto

        # Eastern European Airports
        'IST': {'lat': 41.2750, 'lon': 28.7519},  # Istanbul
        'ATH': {'lat': 37.9364, 'lon': 23.9445},  # Athens
        'SKG': {'lat': 40.5197, 'lon': 22.9709},  # Thessaloniki
        'IEV': {'lat': 50.4018, 'lon': 30.4492},  # Kiev Zhuliany
        'WAW': {'lat': 52.1657, 'lon': 20.9671},  # Warsaw
        'PRG': {'lat': 50.1008, 'lon': 14.2600},  # Prague
        'LNZ': {'lat': 48.2332, 'lon': 14.1875},  # Linz
        'VIE': {'lat': 48.1102, 'lon': 16.5697},  # Vienna
        'SZG': {'lat': 47.7933, 'lon': 13.0043},  # Salzburg
        'GRZ': {'lat': 46.9911, 'lon': 15.4393},  # Graz

        # Other European Airports
        'LUG': {'lat': 46.0043, 'lon': 8.9106},   # Lugano
        'ACH': {'lat': 47.4850, 'lon': 9.5615},   # St. Gallen-Altenrhein
        'BRN': {'lat': 46.9141, 'lon': 7.4971},   # Bern
        'ARN': {'lat': 59.6519, 'lon': 17.9186},  # Stockholm Arlanda
        'GOT': {'lat': 57.6629, 'lon': 12.2797},  # Gothenburg
        'MMX': {'lat': 55.5363, 'lon': 13.3762},  # Malmö
        'HEL': {'lat': 60.3172, 'lon': 24.9633},  # Helsinki
        'BOO': {'lat': 67.2692, 'lon': 14.3653},  # Bodø
        'MOL': {'lat': 62.7447, 'lon': 7.2622},   # Molde
        'CPH': {'lat': 55.6180, 'lon': 12.6508},  # Copenhagen
        'BLL': {'lat': 55.7403, 'lon': 9.1519},   # Billund
        'BUD': {'lat': 47.4298, 'lon': 19.2611},  # Budapest
        'BEG': {'lat': 44.8184, 'lon': 20.3090},  # Belgrade
        'ZAG': {'lat': 45.7429, 'lon': 16.0688},  # Zagreb
        'BTS': {'lat': 48.1702, 'lon': 17.2127},  # Bratislava
        'LJU': {'lat': 46.2237, 'lon': 14.4576},  # Ljubljana
        'OTP': {'lat': 44.5711, 'lon': 26.0858},  # Bucharest
        'RMO': {'lat': 46.9625, 'lon': 28.9305},  # Orhei
        'MSQ': {'lat': 53.8824, 'lon': 28.0325},  # Minsk
        'RIX': {'lat': 56.9236, 'lon': 23.9711},  # Riga
        'ALA': {'lat': 43.3521, 'lon': 77.0337},  # Almaty
        'TLV': {'lat': 32.0114, 'lon': 34.8867},  # Tel Aviv
        'LCA': {'lat': 34.8752, 'lon': 33.6241},  # Larnaca
        'PFO': {'lat': 34.7180, 'lon': 32.4856},  # Paphos
        'GYD': {'lat': 40.4675, 'lon': 50.0467},  # Baku
        'EVN': {'lat': 40.1473, 'lon': 44.3959},  # Yerevan
        'SOF': {'lat': 42.6967, 'lon': 23.4141},  # Sofia
        'RKV': {'lat': 64.1300, 'lon': -21.9406}, # Reykjavik
        'DUB': {'lat': 53.4213, 'lon': -6.2700},  # Dublin
        'BNX': {'lat': 44.9413, 'lon': 17.2975}   # Banja Luka
    }



def get_airport_coordinates(airport_code: str) -> dict:
    """Get coordinates for an airport code."""
    if airport_code in AIRPORT_COORDINATES:
        return AIRPORT_COORDINATES[airport_code]
    return None


def get_team_airport(team_name: str) -> str:
    """Get airport code for a team."""
    return TEAM_AIRPORTS.get(team_name)


def get_all_teams() -> list[str]:
    """Get list of all teams."""
    return sorted(TEAM_AIRPORTS.keys())
