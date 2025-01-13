import streamlit as st
import pandas as pd
import sqlite3
from src.models.emissions import EmissionsCalculator
from src.data.team_data import get_team_airport, get_airport_coordinates
from src.utils.calculations import calculate_distance

# Page config
st.set_page_config(
    page_title="Football Travel Emissions Analysis",
    page_icon="⚽",
    layout="wide"
)

# Enhanced CSS styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .match-card {
        background: linear-gradient(135deg, #f0f2f6 0%, #e6e9ef 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .match-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
    }
    .match-header {
        background: linear-gradient(135deg, #262730 0%, #1a1c23 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .vs-text {
        color: #ff4b4b;
        font-weight: bold;
        font-size: 24px;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
    }
    .competition-tag {
        background: linear-gradient(135deg, #ff4b4b 0%, #ff6b6b 100%);
        color: white;
        padding: 8px 15px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(255, 75, 75, 0.2);
    }
    .stButton button {
        border-radius: 20px;
        padding: 10px 20px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    </style>
""", unsafe_allow_html=True)

def format_time(hours):
    """Convert hours to HH:MM format"""
    if pd.isna(hours):
        return "N/A"
    total_minutes = int(hours * 60)
    h = total_minutes // 60
    m = total_minutes % 60
    if h == 0:
        return f"{m}m"
    return f"{h}h {m}m"

def load_data():
    """Load data from database"""
    try:
        conn = sqlite3.connect('data/routes.db')
        query = """
        SELECT 
            r.home_team as "Home Team",
            r.away_team as "Away Team",
            r.competition as "Competition",
            r.driving_duration/3600.0 as driving_hours,
            r.transit_duration/3600.0 as transit_hours,
            r.driving_distance/1000.0 as driving_km,
            r.transit_distance/1000.0 as transit_km
        FROM routes r
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        df['Driving Time'] = df['driving_hours'].apply(format_time)
        df['Transit Time'] = df['transit_hours'].apply(format_time)
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def calculate_competition_summary(df):
    """Calculate summary statistics by competition"""
    calculator = EmissionsCalculator()
    summary_data = []

    for competition in df['Competition'].unique():
        comp_df = df[df['Competition'] == competition]
        total_matches = len(comp_df)
        total_distance = 0
        total_emissions = 0

        for _, row in comp_df.iterrows():
            home_airport = get_team_airport(row['Home Team'])
            away_airport = get_team_airport(row['Away Team'])

            if home_airport and away_airport:
                home_coords = get_airport_coordinates(home_airport)
                away_coords = get_airport_coordinates(away_airport)

                if home_coords and away_coords:
                    distance = calculate_distance(
                        home_coords['lat'], home_coords['lon'],
                        away_coords['lat'], away_coords['lon']
                    )
                    total_distance += distance

                    result = calculator.calculate_flight_emissions(
                        origin_lat=home_coords['lat'],
                        origin_lon=home_coords['lon'],
                        dest_lat=away_coords['lat'],
                        dest_lon=away_coords['lon'],
                        passengers=30,
                        is_round_trip=False
                    )
                    total_emissions += result.total_emissions

        if total_matches > 0:
            summary_data.append({
                'Competition': competition,
                'Matches': total_matches,
                'Total Distance (km)': total_distance,
                'Total Emissions (tons)': total_emissions,
                'Avg Distance (km)': total_distance / total_matches,
                'Avg Emissions (tons)': total_emissions / total_matches
            })

    return pd.DataFrame(summary_data)

def main():
    st.title('⚽ Football Travel Emissions Analysis')

    # Load data
    df = load_data()
    if df is None:
        return

    # Competition Summary with enhanced styling
    st.markdown("""
        <div class='match-header'>
            <h3>🏆 Competition Summary</h3>
        </div>
    """, unsafe_allow_html=True)

    summary_df = calculate_competition_summary(df)
    display_summary = summary_df.round(2).sort_values('Total Emissions (tons)', ascending=False)

    # Display summary in a styled container
    st.markdown("<div class='summary-card'>", unsafe_allow_html=True)
    st.dataframe(
        display_summary,
        hide_index=True,
        use_container_width=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Match Selection with styled filters
    st.markdown("""
        <div class='match-header'>
            <h3>🔍 Match Selection</h3>
        </div>
    """, unsafe_allow_html=True)

    # Filters in styled container
    with st.container():
        st.markdown("<div class='filter-container'>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)

        with col1:
            competition_filter = st.selectbox(
                "🏆 Select Competition",
                ["All"] + sorted(df['Competition'].unique().tolist())
            )

        with col2:
            filtered_df = df if competition_filter == "All" else df[df['Competition'] == competition_filter]
            home_filter = st.selectbox(
                "🏠 Select Home Team",
                ["All"] + sorted(filtered_df['Home Team'].unique().tolist())
            )

        with col3:
            if home_filter != "All":
                away_teams = df[df['Home Team'] == home_filter]['Away Team'].unique()
            else:
                away_teams = filtered_df['Away Team'].unique()
            away_filter = st.selectbox(
                "✈️ Select Away Team",
                ["All"] + sorted(away_teams)
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # Apply filters
    filtered_df = df.copy()
    if competition_filter != "All":
        filtered_df = filtered_df[filtered_df['Competition'] == competition_filter]
    if home_filter != "All":
        filtered_df = filtered_df[filtered_df['Home Team'] == home_filter]
    if away_filter != "All":
        filtered_df = filtered_df[filtered_df['Away Team'] == away_filter]

    # Display matches in cards
    for index, row in filtered_df.iterrows():
        st.markdown(f"""
            <div class='match-card'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div style='flex: 2;color: black;text-align: center;'>{row['Home Team']}</div>
                    <div style='flex: 1; text-align: center;'>
                        <span class='vs-text'>VS</span>
                    </div>
                    <div style='flex: 2; color: black; text-align: center;'>{row['Away Team']}</div>
                    <div style='flex: 1; text-align: right;'>
                        <span class='competition-tag'>{row['Competition']}</span>
                    </div>
                </div>
                <div style='margin-top: 15px; display: flex; justify-content: space-between; color: #666;'>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if st.button("Calculate Emissions", key=f"calc_{index}"):
            st.session_state.calculator_input = {
                'home_team': row['Home Team'],
                'away_team': row['Away Team'],
                'passengers': 30,
                'is_round_trip': False,
                'from_analysis': True
            }
            st.switch_page("app.py")

if __name__ == "__main__":
    main()
