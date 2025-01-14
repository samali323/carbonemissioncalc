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

st.markdown("""

    <style>

    /* Main layout */

    .main {

        background-color: #0e1117;

        color: #ffffff;

        padding: 2rem;

    }

    

    /* Section headers */

    .section-header {

        background-color: #0e1117;

        border-radius: 10px;

        padding: 1rem;

        margin: 1.5rem 0;

        color: white;

        text-align: center !important;

    }

    

    /* Styled table for competition summary */

    .styled-table {

        margin: 25px auto;

        width: 100%;

        text-align: center;

        border-collapse: collapse;

        background-color: #0e1117;

        border-radius: 10px;

        overflow: hidden;

        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);

    }

    

    .styled-table th {

        background-color: #1f2937;

        color: #6B7280;

        padding: 12px;

        text-align: center;

        font-weight: normal;

        border-bottom: 1px solid #2d3139;

    }

    

    .styled-table td {

        padding: 12px;

        text-align: center;

        color: white;

        border-bottom: 1px solid #2d3139;

    }

    

    .styled-table tr:hover {

        background-color: #2d3139;

    }

    

    /* Center the entire table container */

    [data-testid="stDataFrame"] {

        width: 100%;

        margin: 0 auto;

        display: flex;

        justify-content: center;

    }

    

    /* Center text in all table cells */

    [data-testid="stDataFrame"] div[style*="overflow"] {

        display: flex;

        justify-content: center;

        text-align: center;

    }

    

    /* Remove default Streamlit table styling */

    .element-container div[data-testid="stDataFrame"] > div {

        background-color: transparent !important;

    }

    

    /* Match card styling */

    .match-card {

        background-color: #0d0c0c;

        border-radius: 10px;

        text-align: center !important;

        padding: 1.5rem;

        margin: 1rem 0;

        border: 1px solid #2d3139;

        transition: transform 0.2s ease;

    }

    

    .match-card:hover {

        background-color: #2d3139;

        transform: translateY(-2px);

    }

    

    /* Select box styling */

    div[data-baseweb="select"] {

        margin: 0 auto;

        text-align: center;

    }

    

    .stSelectbox {

        text-align: center;

    }

    

    .stSelectbox > div > div {

        text-align: center;

        background-color: #1f2937;

        border: 1px solid #2d3139;

    }

    

    .stSelectbox > label {

        text-align: center;

        width: 100%;

        color: #6B7280;

    }

    

    div[role="listbox"] {

        background-color: #1f2937;

        border: 1px solid #2d3139;

    }    

    [data-testid="stDataFrame"] td {

        text-align: center !important;

    }
   
    [data-testid="stDataFrame"] th {
        text-align: center !important;
    }

    

    /* Center the contents of each cell */

    [data-testid="stDataFrame"] div[style*="overflow"] {

        display: flex;

        justify-content: center;

        text-align: center;

    }

    </style>
""", unsafe_allow_html=True)


def format_number(value, decimal_places=2):
    """Format numbers with commas and specified decimal places"""
    return f"{value:,.{decimal_places}f}"


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

    # Calculate and display competition summary
    summary_df = calculate_competition_summary(df)
    display_summary = summary_df.round(2).sort_values('Total Emissions (tons)', ascending=False)

    # Format summary data
    for col in display_summary.columns:
        if col != 'Competition' and col != 'Matches':
            display_summary[col] = display_summary[col].apply(format_number)

    st.markdown("""
        <div class="section-header">
            <h3>🏆 Competition Summary</h3>
        </div>
    """, unsafe_allow_html=True)

    st.dataframe(display_summary, hide_index=True, use_container_width=True)

    # Match Selection filters
    st.markdown("""
        <div class="section-header">
            <h3>🔍 Match Selection</h3>
        </div>
    """, unsafe_allow_html=True)

    # Add this CSS before your columns code
    st.markdown("""
        <style>
        div[data-baseweb="select"] {
            margin: 0 auto;
            text-align: center;
        }
        .stSelectbox {
            text-align: center;
        }
        .stSelectbox > div > div {
            text-align: center;
        }
        /* Center the select box labels */
        .stSelectbox > label {
            text-align: center;
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)

    # Then your existing columns code
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
        away_teams = df['Away Team'].unique() if home_filter == "All" else df[df['Home Team'] == home_filter]['Away Team'].unique()
        away_filter = st.selectbox(
            "✈️ Select Away Team",
            ["All"] + sorted(away_teams)
        )
    # Apply filters
    filtered_df = df.copy()
    if competition_filter != "All":
        filtered_df = filtered_df[filtered_df['Competition'] == competition_filter]
    if home_filter != "All":
        filtered_df = filtered_df[filtered_df['Home Team'] == home_filter]
    if away_filter != "All":
        filtered_df = filtered_df[filtered_df['Away Team'] == away_filter]

    # Display matches
    for index, row in filtered_df.iterrows():
        st.markdown(f"""
            <div class="match-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div class="team-name" style="flex: 2; text-align: center;">{row['Home Team']}</div>
                    <div style="flex: 1; text-align: center;">
                        <span class="vs-text">VS</span>
                    </div>
                    <div class="team-name" style="flex: 2; text-align: center;">{row['Away Team']}</div>
                    <div style="flex: 1; text-align: right;">
                        <span class="competition-tag">{row['Competition']}</span>
                    </div>
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
