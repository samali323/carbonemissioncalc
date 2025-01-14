import os
import requests
from pathlib import Path
import streamlit as st
from PIL import Image
from io import BytesIO

@st.cache_data
def get_resized_logo(_logo_path: str, width: int = 100) -> Image.Image:
    """Get resized logo image."""
    try:
        img = Image.open(_logo_path)
        # Calculate height maintaining aspect ratio
        aspect_ratio = img.height / img.width
        height = int(width * aspect_ratio)
        return img.resize((width, height))
    except Exception as e:
        print(f"Error processing logo: {str(e)}")
        return None

def generate_team_mapping():
    """Generate team mapping dictionary with correct folder structure."""
    mapping = {
        # England - Premier League
        'Arsenal FC': 'England - Premier League/arsenal.png',
        'Aston Villa': 'England - Premier League/aston-villa.png',
        'Bournemouth': 'England - Premier League/afc-bournemouth.png',
        'Brentford': 'England - Premier League/brentford.png',
        'Brighton & Hove Albion': 'England - Premier League/brighton-and-hove-albion.png',
        'Chelsea': 'England - Premier League/chelsea.png',
        'Crystal Palace': 'England - Premier League/crystal-palace.png',
        'Everton': 'England - Premier League/everton.png',
        'Fulham': 'England - Premier League/fulham.png',
        'Liverpool': 'England - Premier League/liverpool.png',
        'Manchester City': 'England - Premier League/manchester-city.png',
        'Manchester United': 'England - Premier League/manchester-united.png',
        'Newcastle United': 'England - Premier League/newcastle-united.png',
        'Nottingham Forest': 'England - Premier League/nottingham-forest.png',
        'Tottenham Hotspur': 'England - Premier League/tottenham-hotspur.png',
        'West Ham United': 'England - Premier League/west-ham-united.png',
        'Wolverhampton Wanderers': 'England - Premier League/wolverhampton-wanderers.png',

        # Germany - Bundesliga
        '1. FC Heidenheim': 'Germany - Bundesliga/1-fc-heidenheim.png',
        'Bayer Leverkusen': 'Germany - Bundesliga/bayer-leverkusen.png',
        'Bayern Munich': 'Germany - Bundesliga/bayern-munich.png',
        'Borussia Dortmund': 'Germany - Bundesliga/borussia-dortmund.png',
        'Borussia Monchengladbach': 'Germany - Bundesliga/borussia-monchengladbach.png',
        'Eintracht Frankfurt': 'Germany - Bundesliga/eintracht-frankfurt.png',
        'FC Augsburg': 'Germany - Bundesliga/fc-augsburg.png',
        'FC St. Pauli': 'Germany - Bundesliga/fc-st-pauli.png',
        'Holstein Kiel': 'Germany - Bundesliga/holstein-kiel.png',
        'Mainz 05': 'Germany - Bundesliga/mainz-05.png',
        'RB Leipzig': 'Germany - Bundesliga/rb-leipzig.png',
        'SC Freiburg': 'Germany - Bundesliga/sc-freiburg.png',
        'TSG Hoffenheim': 'Germany - Bundesliga/tsg-hoffenheim.png',
        'Union Berlin': 'Germany - Bundesliga/union-berlin.png',
        'VfB Stuttgart': 'Germany - Bundesliga/vfb-stuttgart.png',
        'VfL Bochum': 'Germany - Bundesliga/vfl-bochum.png',
        'VfL Wolfsburg': 'Germany - Bundesliga/vfl-wolfsburg.png',
        'Werder Bremen': 'Germany - Bundesliga/werder-bremen.png',

        # Spain - La Liga
        'Alaves': 'Spain - La Liga/deportivo-alaves.png',
        'Athletic Bilbao': 'Spain - La Liga/athletic-bilbao.png',
        'Atletico Madrid': 'Spain - La Liga/atletico-madrid.png',
        'Barcelona': 'Spain - La Liga/barcelona.png',
        'Celta Vigo': 'Spain - La Liga/celta-vigo.png',
        'Espanyol': 'Spain - La Liga/espanyol.png',
        'Getafe': 'Spain - La Liga/getafe.png',
        'Girona': 'Spain - La Liga/girona.png',
        'Las Palmas': 'Spain - La Liga/las-palmas.png',
        'Leganes': 'Spain - La Liga/leganes.png',
        'Mallorca': 'Spain - La Liga/mallorca.png',
        'Osasuna': 'Spain - La Liga/osasuna.png',
        'Rayo Vallecano': 'Spain - La Liga/rayo-vallecano.png',
        'Real Betis': 'Spain - La Liga/real-betis.png',
        'Real Madrid': 'Spain - La Liga/real-madrid.png',
        'Real Sociedad': 'Spain - La Liga/real-sociedad.png',
        'Sevilla': 'Spain - La Liga/sevilla.png',
        'Valencia': 'Spain - La Liga/valencia.png',
        'Valladolid': 'Spain - La Liga/real-valladolid.png',
        'Villarreal': 'Spain - La Liga/villarreal.png',

        # Italy - Serie A
        'AC Milan': 'Italy - Serie A/ac-milan.png',
        'Atalanta': 'Italy - Serie A/atalanta.png',
        'Bologna': 'Italy - Serie A/bologna.png',
        'Cagliari': 'Italy - Serie A/cagliari.png',
        'Como': 'Italy - Serie A/como-1907.png',
        'Empoli': 'Italy - Serie A/empoli.png',
        'Fiorentina': 'Italy - Serie A/fiorentina.png',
        'Genoa': 'Italy - Serie A/genoa.png',
        'Hellas Verona': 'Italy - Serie A/hellas-verona.png',
        'Inter Milan': 'Italy - Serie A/inter-milan.png',
        'Juventus': 'Italy - Serie A/juventus.png',
        'Lazio': 'Italy - Serie A/lazio.png',
        'Lecce': 'Italy - Serie A/lecce.png',
        'Monza': 'Italy - Serie A/ac-monza.png',
        'Napoli': 'Italy - Serie A/napoli.png',
        'Parma': 'Italy - Serie A/parma.png',
        'Roma': 'Italy - Serie A/roma.png',
        'Torino': 'Italy - Serie A/torino.png',
        'Udinese': 'Italy - Serie A/udinese.png',
        'Venezia': 'Italy - Serie A/venezia.png',

        # France - Ligue 1
        'Angers': 'France - Ligue 1/angers.png',
        'AS Monaco': 'France - Ligue 1/as-monaco.png',
        'Auxerre': 'France - Ligue 1/auxerre.png',
        'Brest': 'France - Ligue 1/stade-brestois.png',
        'Le Havre': 'France - Ligue 1/le-havre.png',
        'Lens': 'France - Ligue 1/rc-lens.png',
        'Lille': 'France - Ligue 1/lille.png',
        'Lyon': 'France - Ligue 1/olympique-lyonnais.png',
        'Marseille': 'France - Ligue 1/olympique-marseille.png',
        'Montpellier': 'France - Ligue 1/montpellier.png',
        'Nantes': 'France - Ligue 1/nantes.png',
        'Nice': 'France - Ligue 1/nice.png',
        'Paris Saint-Germain': 'France - Ligue 1/paris-saint-germain.png',
        'Reims': 'France - Ligue 1/stade-reims.png',
        'Rennes': 'France - Ligue 1/stade-rennais.png',
        'Saint-Etienne': 'France - Ligue 1/saint-etienne.png',
        'Strasbourg': 'France - Ligue 1/strasbourg.png',
        'Toulouse': 'France - Ligue 1/toulouse.png',

        # Netherlands - Eredivisie
        'Ajax': 'Netherlands - Eredivisie/ajax.png',
        'AZ Alkmaar': 'Netherlands - Eredivisie/az-alkmaar.png',
        'Feyenoord': 'Netherlands - Eredivisie/feyenoord.png',
        'PSV Eindhoven': 'Netherlands - Eredivisie/psv-eindhoven.png',
        'Twente': 'Netherlands - Eredivisie/fc-twente.png',

        # Portugal - Liga Portugal
        'Benfica': 'Portugal - Liga Portugal/benfica.png',
        'Braga': 'Portugal - Liga Portugal/sporting-braga.png',
        'Porto': 'Portugal - Liga Portugal/porto.png',
        'Sporting CP': 'Portugal - Liga Portugal/sporting-cp.png',
        'Vitoria de Guimaraes': 'Portugal - Liga Portugal/vitoria-guimaraes.png',

        # Belgium - Jupiler Pro League
        'Anderlecht': 'Belgium - Jupiler Pro League/anderlecht.png',
        'Cercle Brugge': 'Belgium - Jupiler Pro League/cercle-brugge.png',
        'Club Brugge': 'Belgium - Jupiler Pro League/club-brugge.png',
        'Gent': 'Belgium - Jupiler Pro League/kaa-gent.png',
        'Union Saint-Gilloise': 'Belgium - Jupiler Pro League/royale-union-saint-gilloise.png',

        # Other European Teams
        'Celtic': 'Scotland - Scottish Premiership/celtic.png',
        'Hearts': 'Scotland - Scottish Premiership/heart-of-midlothian.png',
        'Rangers': 'Scotland - Scottish Premiership/rangers.png',
        'Besiktas': 'Turkey - Super Lig/besiktas.png',
        'Fenerbahce': 'Turkey - Super Lig/fenerbahce.png',
        'Galatasaray': 'Turkey - Super Lig/galatasaray.png',
        'Istanbul Basaksehir': 'Turkey - Super Lig/istanbul-basaksehir.png',
        'Olympiacos': 'Greece - Super League 1/olympiacos.png',
        'PAOK': 'Greece - Super League 1/paok.png',
        'Panathinaikos': 'Greece - Super League 1/panathinaikos.png',
        'Red Bull Salzburg': 'Austria - Bundesliga/red-bull-salzburg.png',
        'Shakhtar Donetsk': 'Ukraine - Premier League/shakhtar-donetsk.png',
        'Ajax': 'Netherlands - Eredivisie/ajax.png',
        'Copenhagen': 'Denmark - Superliga/fc-copenhagen.png',
        'Dynamo Kyiv': 'Ukraine - Premier League/dynamo-kyiv.png',
        'Malmo FF': 'Sweden - Allsvenskan/malmo-ff.png',
        'Slavia Prague': 'Czech Republic - Chance Liga/slavia-prague.png',
        'Young Boys': 'Switzerland - Super League/bsc-young-boys.png'
    }
    return mapping

class FootballLogoManager:
    def __init__(self):
        # Set up directories
        self.base_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent
        self.logos_dir = self.base_dir / "data" / "logos"
        self.logos_dir.mkdir(parents=True, exist_ok=True)

        # GitHub repository information
        self.repo_base_url = "https://raw.githubusercontent.com/luukhopman/football-logos/tree/master/logos"

        # Initialize team mapping
        self.team_mapping = generate_team_mapping()

    def get_logo_url(self, team_name: str) -> str:
        """Get the correct URL for a team's logo."""
        if team_name in self.team_mapping:
            return f"{self.repo_base_url}/{self.team_mapping[team_name]}"
        return None

    def get_logo(self, team_name: str, width: int = 100) -> Image.Image:
        """Get team logo as PIL Image."""
        try:
            if team_name not in self.team_mapping:
                print(f"Team {team_name} not found in mapping")
                return None

            # Get local path
            relative_path = self.team_mapping[team_name]
            local_path = self.logos_dir / relative_path

            # Create directories if they don't exist
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if logo exists locally
            if local_path.exists():
                return get_resized_logo(str(local_path), width)

            # Download from GitHub
            url = self.get_logo_url(team_name)
            if url:
                print(f"Downloading logo from: {url}")
                response = requests.get(url)
                if response.status_code == 200:
                    local_path.write_bytes(response.content)
                    return get_resized_logo(str(local_path), width)
                else:
                    print(f"Failed to download logo: {response.status_code}")

            return None

        except Exception as e:
            print(f"Error getting logo for {team_name}: {str(e)}")
            return None

    def display_match_logos(self, home_team: str, away_team: str, width: int = 100):
        """Display match logos in columns with team names."""
        col1, col2, col3 = st.columns([2, 1, 2])

        with col1:
            home_logo = self.get_logo(home_team, width)
            if home_logo:
                st.image(home_logo)
            st.markdown(f"<h4 style='text-align: center;'>{home_team}</h4>", unsafe_allow_html=True)

        with col2:
            st.markdown("<h3 style='text-align: center; margin-top: 25px;'>VS</h3>", unsafe_allow_html=True)

        with col3:
            away_logo = self.get_logo(away_team, width)
            if away_logo:
                st.image(away_logo)
            st.markdown(f"<h4 style='text-align: center;'>{away_team}</h4>", unsafe_allow_html=True)

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
