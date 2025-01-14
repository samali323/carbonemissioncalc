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
    """Generate team mapping dictionary with URL-encoded paths."""

    mapping = {

        # Spain - LaLiga

        'Athletic Bilbao': 'Spain%20-%20LaLiga/Athletic%20Bilbao.png',

        'Atletico Madrid': 'Spain%20-%20LaLiga/Atl%C3%A9tico%20de%20Madrid.png',

        'Osasuna': 'Spain%20-%20LaLiga/CA%20Osasuna.png',

        'Leganes': 'Spain%20-%20LaLiga/CD%20Legan%C3%A9s.png',

        'Celta Vigo': 'Spain%20-%20LaLiga/Celta%20de%20Vigo.png',

        'Alaves': 'Spain%20-%20LaLiga/Deportivo%20Alav%C3%A9s.png',

        'Barcelona': 'Spain%20-%20LaLiga/FC%20Barcelona.png',

        'Getafe': 'Spain%20-%20LaLiga/Getafe%20CF.png',

        'Girona': 'Spain%20-%20LaLiga/Girona%20FC.png',

        'Rayo Vallecano': 'Spain%20-%20LaLiga/Rayo%20Vallecano.png',

        'Espanyol': 'Spain%20-%20LaLiga/RCD%20Espanyol%20Barcelona.png',

        'Mallorca': 'Spain%20-%20LaLiga/RCD%20Mallorca.png',

        'Real Betis': 'Spain%20-%20LaLiga/Real%20Betis%20Balompi%C3%A9.png',

        'Real Madrid': 'Spain%20-%20LaLiga/Real%20Madrid.png',

        'Real Sociedad': 'Spain%20-%20LaLiga/Real%20Sociedad.png',

        'Valladolid': 'Spain%20-%20LaLiga/Real%20Valladolid%20CF.png',

        'Sevilla': 'Spain%20-%20LaLiga/Sevilla%20FC.png',

        'Las Palmas': 'Spain%20-%20LaLiga/UD%20Las%20Palmas.png',

        'Valencia': 'Spain%20-%20LaLiga/Valencia%20CF.png',

        'Villarreal': 'Spain%20-%20LaLiga/Villarreal%20CF.png',

        # England - Premier League

        'Arsenal FC': 'England%20-%20Premier%20League/Arsenal%20FC.png',

        'Aston Villa': 'England%20-%20Premier%20League/Aston%20Villa.png',

        'Bournemouth': 'England%20-%20Premier%20League/AFC%20Bournemouth.png',

        'Brentford': 'England%20-%20Premier%20League/Brentford%20FC.png',

        'Brighton & Hove Albion': 'England%20-%20Premier%20League/Brighton%20%26%20Hove%20Albion.png',

        'Chelsea': 'England%20-%20Premier%20League/Chelsea%20FC.png',

        'Crystal Palace': 'England%20-%20Premier%20League/Crystal%20Palace.png',

        'Everton': 'England%20-%20Premier%20League/Everton%20FC.png',

        'Fulham': 'England%20-%20Premier%20League/Fulham%20FC.png',

        'Ipswich Town': 'England%20-%20Premier%20League/Ipswich%20Town.png',

        'Leicester City': 'England%20-%20Premier%20League/Leicester%20City.png',

        'Liverpool': 'England%20-%20Premier%20League/Liverpool%20FC.png',

        'Manchester City': 'England%20-%20Premier%20League/Manchester%20City.png',

        'Manchester United': 'England%20-%20Premier%20League/Manchester%20United.png',

        'Newcastle United': 'England%20-%20Premier%20League/Newcastle%20United.png',

        'Nottingham Forest': 'England%20-%20Premier%20League/Nottingham%20Forest.png',

        'Southampton': 'England%20-%20Premier%20League/Southampton%20FC.png',

        'Tottenham Hotspur': 'England%20-%20Premier%20League/Tottenham%20Hotspur.png',

        'West Ham United': 'England%20-%20Premier%20League/West%20Ham%20United.png',

        'Wolverhampton Wanderers': 'England%20-%20Premier%20League/Wolverhampton%20Wanderers.png',

        # France - Ligue 1

        'Auxerre': 'France%20-%20Ligue%201/AJ%20Auxerre.png',

        'Angers': 'France%20-%20Ligue%201/Angers%20SCO.png',

        'AS Monaco': 'France%20-%20Ligue%201/AS%20Monaco.png',

        'Saint-Etienne': 'France%20-%20Ligue%201/AS%20Saint-%C3%89tienne.png',

        'Nantes': 'France%20-%20Ligue%201/FC%20Nantes.png',

        'Toulouse': 'France%20-%20Ligue%201/FC%20Toulouse.png',

        'Le Havre': 'France%20-%20Ligue%201/Le%20Havre%20AC.png',

        'Lille': 'France%20-%20Ligue%201/LOSC%20Lille.png',

        'Montpellier': 'France%20-%20Ligue%201/Montpellier%20HSC.png',

        'Nice': 'France%20-%20Ligue%201/OGC%20Nice.png',

        'Lyon': 'France%20-%20Ligue%201/Olympique%20Lyon.png',

        'Marseille': 'France%20-%20Ligue%201/Olympique%20Marseille.png',

        'Paris Saint-Germain': 'France%20-%20Ligue%201/Paris%20Saint-Germain.png',

        'Lens': 'France%20-%20Ligue%201/RC%20Lens.png',

        'Strasbourg': 'France%20-%20Ligue%201/RC%20Strasbourg%20Alsace.png',

        'Brest': 'France%20-%20Ligue%201/Stade%20Brestois%2029.png',

        'Reims': 'France%20-%20Ligue%201/Stade%20Reims.png',

        'Rennes': 'France%20-%20Ligue%201/Stade%20Rennais%20FC.png',

        # Italy - Serie A

        'AC Milan': 'Italy%20-%20Serie%20A/AC%20Milan.png',

        'Monza': 'Italy%20-%20Serie%20A/AC%20Monza.png',

        'Fiorentina': 'Italy%20-%20Serie%20A/ACF%20Fiorentina.png',

        'Roma': 'Italy%20-%20Serie%20A/AS%20Roma.png',

        'Atalanta': 'Italy%20-%20Serie%20A/Atalanta%20BC.png',

        'Bologna': 'Italy%20-%20Serie%20A/Bologna%20FC%201909.png',

        'Cagliari': 'Italy%20-%20Serie%20A/Cagliari%20Calcio.png',

        'Como': 'Italy%20-%20Serie%20A/Como%201907.png',

        'Empoli': 'Italy%20-%20Serie%20A/FC%20Empoli.png',

        'Genoa': 'Italy%20-%20Serie%20A/Genoa%20CFC.png',

        'Hellas Verona': 'Italy%20-%20Serie%20A/Hellas%20Verona.png',

        'Inter Milan': 'Italy%20-%20Serie%20A/Inter%20Milan.png',

        'Juventus': 'Italy%20-%20Serie%20A/Juventus%20FC.png',

        'Parma': 'Italy%20-%20Serie%20A/Parma%20Calcio%201913.png',

        'Lazio': 'Italy%20-%20Serie%20A/SS%20Lazio.png',

        'Napoli': 'Italy%20-%20Serie%20A/SSC%20Napoli.png',

        'Torino': 'Italy%20-%20Serie%20A/Torino%20FC.png',

        'Udinese': 'Italy%20-%20Serie%20A/Udinese%20Calcio.png',

        'Lecce': 'Italy%20-%20Serie%20A/US%20Lecce.png',

        'Venezia': 'Italy%20-%20Serie%20A/Venezia%20FC.png',

        # Germany - Bundesliga

        '1. FC Heidenheim': 'Germany%20-%20Bundesliga/1.FC%20Heidenheim%201846.png',

        'Union Berlin': 'Germany%20-%20Bundesliga/1.FC%20Union%20Berlin.png',

        'Mainz 05': 'Germany%20-%20Bundesliga/1.FSV%20Mainz%2005.png',

        'Bayer Leverkusen': 'Germany%20-%20Bundesliga/Bayer%2004%20Leverkusen.png',

        'Bayern Munich': 'Germany%20-%20Bundesliga/Bayern%20Munich.png',

        'Borussia Dortmund': 'Germany%20-%20Bundesliga/Borussia%20Dortmund.png',

        'Borussia Monchengladbach': 'Germany%20-%20Bundesliga/Borussia%20M%C3%B6nchengladbach.png',

        'Eintracht Frankfurt': 'Germany%20-%20Bundesliga/Eintracht%20Frankfurt.png',

        'FC Augsburg': 'Germany%20-%20Bundesliga/FC%20Augsburg.png',

        'FC St. Pauli': 'Germany%20-%20Bundesliga/FC%20St.%20Pauli.png',

        'Holstein Kiel': 'Germany%20-%20Bundesliga/Holstein%20Kiel.png',

        'RB Leipzig': 'Germany%20-%20Bundesliga/RB%20Leipzig.png',

        'SC Freiburg': 'Germany%20-%20Bundesliga/SC%20Freiburg.png',

        'Werder Bremen': 'Germany%20-%20Bundesliga/SV%20Werder%20Bremen.png',

        'TSG Hoffenheim': 'Germany%20-%20Bundesliga/TSG%201899%20Hoffenheim.png',

        'VfB Stuttgart': 'Germany%20-%20Bundesliga/VfB%20Stuttgart.png',

        'VfL Bochum': 'Germany%20-%20Bundesliga/VfL%20Bochum.png',

        'VfL Wolfsburg': 'Germany%20-%20Bundesliga/VfL%20Wolfsburg.png',

        # Portugal - Liga Portugal

        'Braga': 'Portugal%20-%20Liga%20Portugal/SC%20Braga.png',

        'Porto': 'Portugal%20-%20Liga%20Portugal/FC%20Porto.png',

        'Benfica': 'Portugal%20-%20Liga%20Portugal/SL%20Benfica.png',

        'Sporting CP': 'Portugal%20-%20Liga%20Portugal/Sporting%20CP.png',

        'Vitoria de Guimaraes': 'Portugal%20-%20Liga%20Portugal/Vit%C3%B3ria%20Guimar%C3%A3es%20SC.png',

        # Belgium - Jupiler Pro League

        'Anderlecht': 'Belgium%20-%20Jupiler%20Pro%20League/RSC%20Anderlecht.png',

        'Club Brugge': 'Belgium%20-%20Jupiler%20Pro%20League/Club%20Brugge%20KV.png',

        'Gent': 'Belgium%20-%20Jupiler%20Pro%20League/KAA%20Gent.png',

        'Union Saint-Gilloise': 'Belgium%20-%20Jupiler%20Pro%20League/Union%20Saint-Gilloise.png',

        'Standard Liege': 'Belgium%20-%20Jupiler%20Pro%20League/Standard%20Li%C3%A8ge.png',

        # Other European Teams

        'Celtic': 'Other%20European%20Teams/Celtic.png',

        'Hearts': 'Other%20European%20Teams/Heart%20of%20Midlothian.png',

        'Rangers': 'Other%20European%20Teams/Rangers.png',

        'Besiktas': 'Other%20European%20Teams/Besiktas%20JK.png',

        'Fenerbahce': 'Other%20European%20Teams/Fenerbahce.png',

        'Galatasaray': 'Other%20European%20Teams/Galatasaray.png',

        'Istanbul Basaksehir': 'Other%20European%20Teams/Istanbul%20Basaksehir.png',

        'Olympiacos': 'Other%20European%20Teams/Olympiacos%20Piraeus.png',

        'PAOK': 'Other%20European%20Teams/PAOK%20Thessaloniki.png',

        'Panathinaikos': 'Other%20European%20Teams/Panathinaikos.png',

        'Red Bull Salzburg': 'Other%20European%20Teams/Red%20Bull%20Salzburg.png',

        'Shakhtar Donetsk': 'Other%20European%20Teams/Shakhtar%20Donetsk.png',

        'Dynamo Kyiv': 'Other%20European%20Teams/Dynamo%20Kyiv.png',

        'Ajax': 'Other%20European%20Teams/Ajax%20Amsterdam.png',

        'Copenhagen': 'Other%20European%20Teams/FC%20Copenhagen.png',

        'Malmo FF': 'Other%20European%20Teams/Malmo%20FF.png',

        'Slavia Prague': 'Other%20European%20Teams/SK%20Slavia%20Prague.png',

        'Young Boys': 'Other%20European%20Teams/BSC%20Young%20Boys.png'

    }

    return mapping


class FootballLogoManager:
    def __init__(self):
        # Set up directory for local logos
        self.base_url = "https://raw.githubusercontent.com/samali323/carbonemissioncalc/main/logos/"
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

    @st.cache_data
    def get_logo(self, team_name: str, width: int = 100) -> Image.Image:

        """Get team logo as PIL Image from URL."""

        try:

            if team_name not in self.team_mapping:
                print(f"Team {team_name} not found in mapping")

                return None

            mapped_path = self.team_mapping[team_name]

            # Construct the full URL

            logo_url = f"{self.base_url}{mapped_path}"

            # Fetch image from URL

            response = requests.get(logo_url)

            if response.status_code == 200:

                img = Image.open(BytesIO(response.content))

                aspect_ratio = img.height / img.width

                height = int(width * aspect_ratio)

                return img.resize((width, height))

            else:

                print(f"Failed to fetch logo from {logo_url}")

                return None


        except Exception as e:

            print(f"Error getting logo for {team_name}: {str(e)}")

            return None

    def display_match_logos(self, home_team: str, away_team: str, width: int = 80):
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
