import os
import requests
from pathlib import Path
import streamlit as st
from PIL import Image
from io import BytesIO


# In logo_manager.py

@st.cache_data
def get_resized_logo(_logo_path: str, team_name: str, width: int = 100) -> Image.Image:
    """Get resized logo image with team-specific caching."""
    try:
        # Create a cache key from the combination of path and team name
        img = Image.open(_logo_path)
        aspect_ratio = img.height / img.width
        height = int(width * aspect_ratio)
        return img.resize((width, height))
    except Exception as e:
        print(f"Error processing logo for {team_name}: {str(e)}")
        return None


def generate_team_mapping():
    """Generate team mapping dictionary with correct folder structure."""
    mapping = {
        # Spain - LaLiga teams with correct PNG names

        'Athletic Bilbao': 'Spain - LaLiga/Athletic Bilbao.png',
        'Atletico Madrid': 'Spain - LaLiga/Atlético de Madrid.png',
        'Osasuna': 'Spain - LaLiga/CA Osasuna.png',
        'Leganes': 'Spain - LaLiga/CD Leganés.png',
        'Celta Vigo': 'Spain - LaLiga/Celta de Vigo.png',
        'Alaves': 'Spain - LaLiga/Deportivo Alavés.png',
        'Barcelona': 'Spain - LaLiga/FC Barcelona.png',
        'Getafe': 'Spain - LaLiga/Getafe CF.png',
        'Girona': 'Spain - LaLiga/Girona FC.png',
        'Rayo Vallecano': 'Spain - LaLiga/Rayo Vallecano.png',
        'Espanyol': 'Spain - LaLiga/RCD Espanyol Barcelona.png',
        'Mallorca': 'Spain - LaLiga/RCD Mallorca.png',
        'Real Betis': 'Spain - LaLiga/Real Betis Balompié.png',
        'Real Madrid': 'Spain - LaLiga/Real Madrid.png',
        'Real Sociedad': 'Spain - LaLiga/Real Sociedad.png',
        'Valladolid': 'Spain - LaLiga/Real Valladolid CF.png',
        'Sevilla': 'Spain - LaLiga/Sevilla FC.png',
        'Las Palmas': 'Spain - LaLiga/UD Las Palmas.png',
        'Valencia': 'Spain - LaLiga/Valencia CF.png',
        'Villarreal': 'Spain - LaLiga/Villarreal CF.png',

        # England - Premier League
        'Arsenal FC': 'England - Premier League/Arsenal FC.png',
        'Aston Villa': 'England - Premier League/Aston Villa.png',
        'Bournemouth': 'England - Premier League/AFC Bournemouth.png',
        'Brentford': 'England - Premier League/Brentford FC.png',
        'Brighton & Hove Albion': 'England - Premier League/Brighton & Hove Albion.png',
        'Chelsea': 'England - Premier League/Chelsea FC.png',
        'Crystal Palace': 'England - Premier League/Crystal Palace.png',
        'Everton': 'England - Premier League/Everton FC.png',
        'Fulham': 'England - Premier League/Fulham FC.png',
        'Ipswich Town': 'England - Premier League/Ipswich Town.png',
        'Leicester City': 'England - Premier League/Leicester City.png',
        'Liverpool': 'England - Premier League/Liverpool FC.png',
        'Manchester City': 'England - Premier League/Manchester City.png',
        'Manchester United': 'England - Premier League/Manchester United.png',
        'Newcastle United': 'England - Premier League/Newcastle United.png',
        'Nottingham Forest': 'England - Premier League/Nottingham Forest.png',
        'Southampton': 'England - Premier League/Southampton FC.png',
        'Tottenham Hotspur': 'England - Premier League/Tottenham Hotspur.png',
        'West Ham United': 'England - Premier League/West Ham United.png',
        'Wolverhampton Wanderers': 'England - Premier League/Wolverhampton Wanderers.png',

        # France - Ligue 1
        'Auxerre': 'France - Ligue 1/AJ Auxerre.png',
        'Angers': 'France - Ligue 1/Angers SCO.png',
        'AS Monaco': 'France - Ligue 1/AS Monaco.png',
        'Saint-Etienne': 'France - Ligue 1/AS Saint-Étienne.png',
        'Nantes': 'France - Ligue 1/FC Nantes.png',
        'Toulouse': 'France - Ligue 1/FC Toulouse.png',
        'Le Havre': 'France - Ligue 1/Le Havre AC.png',
        'Lille': 'France - Ligue 1/LOSC Lille.png',
        'Montpellier': 'France - Ligue 1/Montpellier HSC.png',
        'Nice': 'France - Ligue 1/OGC Nice.png',
        'Lyon': 'France - Ligue 1/Olympique Lyon.png',
        'Marseille': 'France - Ligue 1/Olympique Marseille.png',
        'Paris Saint-Germain': 'France - Ligue 1/Paris Saint-Germain.png',
        'Lens': 'France - Ligue 1/RC Lens.png',
        'Strasbourg': 'France - Ligue 1/RC Strasbourg Alsace.png',
        'Brest': 'France - Ligue 1/Stade Brestois 29.png',
        'Reims': 'France - Ligue 1/Stade Reims.png',
        'Rennes': 'France - Ligue 1/Stade Rennais FC.png',

        # Italy - Serie A
        'AC Milan': 'Italy - Serie A/AC Milan.png',
        'Monza': 'Italy - Serie A/AC Monza.png',
        'Fiorentina': 'Italy - Serie A/ACF Fiorentina.png',
        'Roma': 'Italy - Serie A/AS Roma.png',
        'Atalanta': 'Italy - Serie A/Atalanta BC.png',
        'Bologna': 'Italy - Serie A/Bologna FC 1909.png',
        'Cagliari': 'Italy - Serie A/Cagliari Calcio.png',
        'Como': 'Italy - Serie A/Como 1907.png',
        'Empoli': 'Italy - Serie A/FC Empoli.png',
        'Genoa': 'Italy - Serie A/Genoa CFC.png',
        'Hellas Verona': 'Italy - Serie A/Hellas Verona.png',
        'Inter Milan': 'Italy - Serie A/Inter Milan.png',
        'Juventus': 'Italy - Serie A/Juventus FC.png',
        'Parma': 'Italy - Serie A/Parma Calcio 1913.png',
        'Lazio': 'Italy - Serie A/SS Lazio.png',
        'Napoli': 'Italy - Serie A/SSC Napoli.png',
        'Torino': 'Italy - Serie A/Torino FC.png',
        'Udinese': 'Italy - Serie A/Udinese Calcio.png',
        'Lecce': 'Italy - Serie A/US Lecce.png',
        'Venezia': 'Italy - Serie A/Venezia FC.png',

        # Germany - Bundesliga
        '1. FC Heidenheim': 'Germany - Bundesliga/1.FC Heidenheim 1846.png',
        'Union Berlin': 'Germany - Bundesliga/1.FC Union Berlin.png',
        'Mainz 05': 'Germany - Bundesliga/1.FSV Mainz 05.png',
        'Bayer Leverkusen': 'Germany - Bundesliga/Bayer 04 Leverkusen.png',
        'Bayern Munich': 'Germany - Bundesliga/Bayern Munich.png',
        'Borussia Dortmund': 'Germany - Bundesliga/Borussia Dortmund.png',
        'Borussia Monchengladbach': 'Germany - Bundesliga/Borussia Mönchengladbach.png',
        'Eintracht Frankfurt': 'Germany - Bundesliga/Eintracht Frankfurt.png',
        'FC Augsburg': 'Germany - Bundesliga/FC Augsburg.png',
        'FC St. Pauli': 'Germany - Bundesliga/FC St. Pauli.png',
        'Holstein Kiel': 'Germany - Bundesliga/Holstein Kiel.png',
        'RB Leipzig': 'Germany - Bundesliga/RB Leipzig.png',
        'SC Freiburg': 'Germany - Bundesliga/SC Freiburg.png',
        'Werder Bremen': 'Germany - Bundesliga/SV Werder Bremen.png',
        'TSG Hoffenheim': 'Germany - Bundesliga/TSG 1899 Hoffenheim.png',
        'VfB Stuttgart': 'Germany - Bundesliga/VfB Stuttgart.png',
        'VfL Bochum': 'Germany - Bundesliga/VfL Bochum.png',
        'VfL Wolfsburg': 'Germany - Bundesliga/VfL Wolfsburg.png',

        # Portugal - Liga Portugal
        'Braga': 'Portugal - Liga Portugal/SC Braga.png',
        'Porto': 'Portugal - Liga Portugal/FC Porto.png',
        'Benfica': 'Portugal - Liga Portugal/SL Benfica.png',
        'Sporting CP': 'Portugal - Liga Portugal/Sporting CP.png',
        'Vitoria de Guimaraes': 'Portugal - Liga Portugal/Vitória Guimarães SC.png',

        # Belgium - Jupiler Pro League
        'Anderlecht': 'Belgium - Jupiler Pro League/RSC Anderlecht.png',
        'Club Brugge': 'Belgium - Jupiler Pro League/Club Brugge KV.png',
        'Gent': 'Belgium - Jupiler Pro League/KAA Gent.png',
        'Union Saint-Gilloise': 'Belgium - Jupiler Pro League/Union Saint-Gilloise.png',
        'Standard Liege': 'Belgium - Jupiler Pro League/Standard Liège.png',

        # Former Scottish Premiership teams
        'Celtic': 'Other European Teams/Celtic.png',
        'Hearts': 'Other European Teams/Heart of Midlothian.png',
        'Rangers': 'Other European Teams/Rangers.png',

        # Former Turkish Super Lig teams
        'Besiktas': 'Other European Teams/Besiktas JK.png',
        'Fenerbahce': 'Other European Teams/Fenerbahce.png',
        'Galatasaray': 'Other European Teams/Galatasaray.png',
        'Istanbul Basaksehir': 'Other European Teams/Istanbul Basaksehir.png',

        # Former Greek Super League teams
        'Olympiacos': 'Other European Teams/Olympiacos Piraeus.png',
        'PAOK': 'Other European Teams/PAOK Thessaloniki.png',
        'Panathinaikos': 'Other European Teams/Panathinaikos.png',

        # Former Austrian Bundesliga team
        'Red Bull Salzburg': 'Other European Teams/Red Bull Salzburg.png',

        # Former Ukrainian Premier League teams
        'Shakhtar Donetsk': 'Other European Teams/Shakhtar Donetsk.png',
        'Dynamo Kyiv': 'Other European Teams/Dynamo Kyiv.png',

        # Other teams
        'Ajax': 'Other European Teams/Ajax Amsterdam.png',
        'Copenhagen': 'Other European Teams/FC Copenhagen.png',
        'Malmo FF': 'Other European Teams/Malmo FF.png',
        'Slavia Prague': 'Other European Teams/SK Slavia Prague.png',
        'Young Boys': 'Other European Teams/BSC Young Boys.png'
    }
    return mapping


class FootballLogoManager:
    def __init__(self):
        # Set up directory for local logos
        self.logos_dir = Path(r"C:\Users\samal\Documents\logos")
        self.league_mapping = {
            'England - Premier League': 'England - Premier League',
            'Germany - Bundesliga': 'Germany - Bundesliga',
            'Spain - LaLiga': 'Spain - LaLiga',
            'Italy - Serie A': 'Italy - Serie A',
            'France - Ligue 1': 'France - Ligue 1',
            'Netherlands - Eredivisie': 'Netherlands - Eredivisie',
            'Portugal - Liga Portugal': 'Portugal - Liga Portugal',
            'Belgium - Jupiler Pro League': 'Belgium - Jupiler Pro League',
            'Scotland - Scottish Premiership': 'Scotland - Scottish Premiership',
            'Turkey - Super Lig': 'Türkiye - Super Lig',  # Note the special character
            'Greece - Super League 1': 'Greece - Super League 1',
            'Ukraine - Premier League': 'Ukraine - Premier League',
            'Czech Republic - Chance Liga': 'Czech Republic - Chance Liga',
            'Austria - Bundesliga': 'Austria - Bundesliga',
            'Switzerland - Super League': 'Switzerland - Super League',
            'Sweden - Allsvenskan': 'Sweden - Allsvenskan',
            'Denmark - Superliga': 'Denmark - Superliga'
        }
        self.team_mapping = generate_team_mapping()

    def get_logo(self, team_name: str, width: int = 100) -> Image.Image:
        """Get team logo as PIL Image."""
        try:
            if team_name not in self.team_mapping:
                print(f"Team {team_name} not found in mapping")
                return None

            mapped_path = self.team_mapping[team_name]
            league_folder = mapped_path.split('/')[0]
            filename = mapped_path.split('/')[-1]

            # Get the correct league folder name
            actual_league_folder = self.league_mapping.get(league_folder, league_folder)

            # Construct the full path
            local_path = self.logos_dir / actual_league_folder / filename

            # Check if logo exists locally
            if local_path.exists():
                return get_resized_logo(str(local_path), team_name, width)  # Pass team_name to cache key
            else:
                print(f"Logo not found at: {local_path}")
                return None

        except Exception as e:
            print(f"Error getting logo for {team_name}: {str(e)}")
            return None

    def display_match_logos(self, home_team: str, away_team: str, width: int = 100):
        """Display match logos in columns with team names."""
        col1, col2, col3 = st.columns([2, 1, 2])

        with col1:
            # Create unique container for home team
            with st.container(key=f"home_team_container_{home_team}"):
                st.markdown(f"<h4 style='text-align: center;'>{home_team}</h4>", unsafe_allow_html=True)
                home_logo = self.get_logo(home_team, width)
                if home_logo:
                    st.image(home_logo)

        with col2:
            st.markdown("<h3 style='text-align: center;'>VS</h3>", unsafe_allow_html=True)

        with col3:
            # Create unique container for away team
            with st.container(key=f"away_team_container_{away_team}"):
                st.markdown(f"<h4 style='text-align: center;'>{away_team}</h4>", unsafe_allow_html=True)
                away_logo = self.get_logo(away_team, width)
                if away_logo:
                    st.image(away_logo)

    def display_team_selector(self, label: str, key: str, teams: list, width: int = 80):
        """Display team selector with logo."""
        team = st.selectbox(label, teams, key=key)
        logo = self.get_logo(team, width)
        if logo:
            st.image(logo)
        return team

    def display_match_card(self, home_team: str, away_team: str, competition: str, width: int = 60):
        """Display match card with logos."""
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 1, 2, 1, 3])

            with col1:
                home_logo = self.get_logo(home_team, width)
                if home_logo:
                    st.image(home_logo)
                st.markdown(f"<p style='text-align: center;'>{home_team}</p>", unsafe_allow_html=True)

            with col2:
                st.write("")

            with col3:
                st.markdown("<h4 style='text-align: center;'>VS</h4>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center; color: #666;'>{competition}</p>", unsafe_allow_html=True)

            with col4:
                st.write("")

            with col5:
                away_logo = self.get_logo(away_team, width)
                if away_logo:
                    st.image(away_logo)
                st.markdown(f"<p style='text-align: center;'>{away_team}</p>", unsafe_allow_html=True)
