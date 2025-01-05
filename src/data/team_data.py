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

    # Add more teams here...
}

AIRPORT_COORDINATES = {
    'BOH': {'lat': 50.7800, 'lon': -1.8425},  # Bournemouth
    'LGW': {'lat': 51.1537, 'lon': -0.1821},  # London Gatwick
    'LHR': {'lat': 51.4700, 'lon': -0.4543},  # London Heathrow
    'STN': {'lat': 51.8850, 'lon': 0.2389},  # London Stansted
    'LCY': {'lat': 51.5048, 'lon': 0.0495},  # London City
    'LPL': {'lat': 53.3336, 'lon': -2.8497},  # Liverpool
    'MAN': {'lat': 53.3537, 'lon': -2.2750},  # Manchester
    'BHX': {'lat': 52.4538, 'lon': -1.7480},  # Birmingham
    'EMA': {'lat': 52.8311, 'lon': -1.3281},  # East Midlands
    'NCL': {'lat': 55.0375, 'lon': -1.6916},  # Newcastle
    'SOU': {'lat': 50.9503, 'lon': -1.3568},  # Southampton
    'BFS': {'lat': 54.6575, 'lon': -6.2158},  # Belfast

    # Add more airports here...
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
