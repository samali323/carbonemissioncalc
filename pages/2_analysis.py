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

        # Load match emissions data with route information
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

        # Format time columns
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
            # Get airports and coordinates
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

                    # Calculate emissions
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

# Main app
def main():
    st.title('⚽ Football Travel Emissions Analysis')

    # Load data
    df = load_data()
    if df is None:
        return

    # Competition Summary
    st.markdown("### 🏆 Competition Summary")
    summary_df = calculate_competition_summary(df)

    # Format and display summary
    display_summary = summary_df.round(2).sort_values('Total Emissions (tons)', ascending=False)
    st.dataframe(
        display_summary,
        hide_index=True,
        use_container_width=True
    )

    # Match Selection
    st.markdown("### 🔍 Match Selection")
    col1, col2, col3 = st.columns(3)

    with col1:
        competition_filter = st.selectbox(
            "Competition",
            ["All"] + sorted(df['Competition'].unique().tolist())
        )

    with col2:
        filtered_df = df if competition_filter == "All" else df[df['Competition'] == competition_filter]
        home_filter = st.selectbox(
            "Home Team",
            ["All"] + sorted(filtered_df['Home Team'].unique().tolist())
        )

    with col3:
        if home_filter != "All":
            away_teams = df[df['Home Team'] == home_filter]['Away Team'].unique()
        else:
            away_teams = filtered_df['Away Team'].unique()
        away_filter = st.selectbox(
            "Away Team",
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

    # Match Details section
    st.markdown("### 📊 Match Details")

    # Select columns to display
    display_cols = [
        'Home Team', 'Away Team', 'Competition',
        'Driving Time', 'Transit Time',
        'driving_km', 'transit_km'
    ]

    # Display the dataframe
    st.dataframe(
        filtered_df[display_cols].rename(columns={
            'driving_km': 'Driving Distance (km)',
            'transit_km': 'Transit Distance (km)'
        }),
        hide_index=True,
        use_container_width=True
    )

    # Match selection
    st.markdown("### Select a match to load:")
    selected_index = st.radio(
        "",  # Empty label since we have the header above
        options=[(row['Home Team'], row['Away Team'], row['Competition'])
                 for _, row in filtered_df.iterrows()],
        format_func=lambda x: f"{x[0]} vs {x[1]} ({x[2]})",
        key="match_selector"
    )

    # Handle match selection
    if st.button("Load Selected Match in Calculator"):
        # Find the selected match in the dataframe
        selected_match = filtered_df[
            (filtered_df['Home Team'] == selected_index[0]) &
            (filtered_df['Away Team'] == selected_index[1])
            ].iloc[0]

        # Store in session state
        st.session_state.calculator_input = {
            'home_team': selected_match['Home Team'],
            'away_team': selected_match['Away Team'],
            'passengers': 30,
            'is_round_trip': False,
            'from_analysis': True
        }

        # Redirect to calculator page
        st.switch_page("app.py")  # Remove "pages/" prefix
if __name__ == "__main__":
    main()
