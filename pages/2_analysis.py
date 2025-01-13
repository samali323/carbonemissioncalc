# pages/2_Analysis.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import os

from src.models.emissions import EmissionsCalculator
from src.data.team_data import get_team_airport, get_airport_coordinates, TEAM_COUNTRIES
from src.utils.calculations import (
    calculate_transport_emissions,
    calculate_equivalencies,
    calculate_flight_time
)

def get_db_path():
    """Get the path to the routes database"""
    return os.path.join('data', 'routes.db')

def load_matches_data():
    """Load matches from both database and CSV"""
    try:
        # First, let's load and inspect the CSV
        matches_df = pd.read_csv('cleaned_matches.csv')

        # Debug print to check column names
        st.write("CSV Columns:", matches_df.columns.tolist())

        # Load route information from database
        conn = sqlite3.connect(get_db_path())
        routes_query = """
        SELECT 
            home_team as "Home Team",
            away_team as "Away Team",
            driving_duration/3600.0 as driving_hours,
            transit_duration/3600.0 as transit_hours,
            driving_distance/1000.0 as driving_km,
            transit_distance/1000.0 as transit_km,
            last_updated
        FROM routes
        """
        routes_df = pd.read_sql_query(routes_query, conn)
        conn.close()

        # Debug print to check route data
        st.write("Routes Columns:", routes_df.columns.tolist())

        # Merge the dataframes using the correct column names
        combined_df = pd.merge(
            matches_df,
            routes_df,
            left_on=['Home Team', 'Away Team'],  # Adjust these to match your actual column names
            right_on=['Home Team', 'Away Team'],
            how='left'
        )

        # Debug print of final dataframe
        st.write("Combined Data Shape:", combined_df.shape)
        return combined_df

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.write("Current working directory:", os.getcwd())
        return pd.DataFrame()
def load_league_summary(matches_df):
    """Calculate league summary statistics"""
    calculator = EmissionsCalculator()

    summary_data = []

    # Make sure the Competition column exists
    if 'Competition' not in matches_df.columns:
        st.error("Competition column not found in data")
        return pd.DataFrame()

    # Group matches by competition
    for comp in matches_df['Competition'].unique():
        comp_matches = matches_df[matches_df['Competition'] == comp]
        total_emissions = 0

        for _, row in comp_matches.iterrows():
            home_airport = get_team_airport(row['home_team'])
            away_airport = get_team_airport(row['away_team'])

            if home_airport and away_airport:
                home_coords = get_airport_coordinates(home_airport)
                away_coords = get_airport_coordinates(away_airport)

                if home_coords and away_coords:
                    result = calculator.calculate_flight_emissions(
                        origin_lat=home_coords['lat'],
                        origin_lon=home_coords['lon'],
                        dest_lat=away_coords['lat'],
                        dest_lon=away_coords['lon'],
                        passengers=30,
                        is_round_trip=False
                    )
                    total_emissions += result.total_emissions

        summary_data.append({
            'Competition': comp,
            'Matches': len(comp_matches),
            'Total Emissions': total_emissions,
            'Average': total_emissions / len(comp_matches) if len(comp_matches) > 0 else 0
        })

    return pd.DataFrame(summary_data)
def create_analysis_page():
    st.title("⚽ Football Travel Emissions Analysis")

    # Load data
    matches_df = load_matches_data()

    if matches_df.empty:
        st.warning("No match data available")
        return

    # Create tabs
    tab1, tab2 = st.tabs(["Summary", "Match Details"])

    with tab1:
        st.header("League Summary")
        summary_df = load_league_summary(matches_df)

        # Display summary table
        st.dataframe(
            summary_df.style.format({
                'Total Emissions': '{:,.2f}',
                'Average': '{:,.2f}'
            }),
            use_container_width=True
        )

        # Create summary visualization
        fig = go.Figure(data=[
            go.Bar(name='Total Emissions', x=summary_df['Competition'], y=summary_df['Total Emissions']),
            go.Bar(name='Average per Match', x=summary_df['Competition'], y=summary_df['Average'])
        ])

        fig.update_layout(
            title='Emissions by League',
            xaxis_title='Competition',
            yaxis_title='Metric Tons CO₂'
        )

        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.header("Match Details")

        # Filters
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

        with col1:
            home_filter = st.text_input("Home Team Filter")
        with col2:
            away_filter = st.text_input("Away Team Filter")
        with col3:
            competition_filter = st.selectbox(
                "Competition",
                ["All"] + list(matches_df['Competition'].unique())
            )
        with col4:
            st.write("")
            st.write("")
            clear_filters = st.button("Clear Filters")

        # Apply filters
        filtered_df = matches_df.copy()
        if home_filter:
            filtered_df = filtered_df[filtered_df['home_team'].str.contains(home_filter, case=False)]
        if away_filter:
            filtered_df = filtered_df[filtered_df['away_team'].str.contains(away_filter, case=False)]
        if competition_filter != "All":
            filtered_df = filtered_df[filtered_df['Competition'] == competition_filter]

        # Display filtered matches
        st.dataframe(filtered_df, use_container_width=True)

        # Match analysis section
        st.subheader("Selected Match Analysis")
        col1, col2 = st.columns([1, 1])

        with col1:
            selected_home = st.selectbox("Select Home Team", filtered_df['home_team'].unique())
        with col2:
            selected_away = st.selectbox("Select Away Team", filtered_df['away_team'].unique())

        if st.button("Analyze Match"):
            calculator = EmissionsCalculator()

            # Calculate emissions
            home_airport = get_team_airport(selected_home)
            away_airport = get_team_airport(selected_away)

            if home_airport and away_airport:
                home_coords = get_airport_coordinates(home_airport)
                away_coords = get_airport_coordinates(away_airport)

                if home_coords and away_coords:
                    result = calculator.calculate_flight_emissions(
                        origin_lat=home_coords['lat'],
                        origin_lon=home_coords['lon'],
                        dest_lat=away_coords['lat'],
                        dest_lon=away_coords['lon'],
                        passengers=30,
                        is_round_trip=False
                    )

                    # Display analysis results
                    with st.expander("Flight Details", expanded=True):
                        st.write(f"🏠 Home Team: {selected_home} ({home_airport})")
                        st.write(f"🏃 Away Team: {selected_away} ({away_airport})")
                        st.write(f"📏 Distance: {result.distance_km:.1f} km")
                        st.write(f"✈️ Flight Type: {result.flight_type}")
                        st.write(f"📊 Total CO₂: {result.total_emissions:.2f} metric tons")

                    # Transport comparison
                    with st.expander("Transport Comparison", expanded=True):
                        match_row = filtered_df[
                            (filtered_df['home_team'] == selected_home) &
                            (filtered_df['away_team'] == selected_away)
                            ].iloc[0]

                        transport_data = pd.DataFrame({
                            'Mode': ['Air', 'Rail', 'Bus'],
                            'Time (hours)': [
                                calculate_flight_time(result.distance_km, False),
                                match_row['transit_hours'],
                                match_row['driving_hours']
                            ],
                            'Distance (km)': [
                                result.distance_km,
                                match_row['transit_km'],
                                match_row['driving_km']
                            ],
                            'CO₂ (tons)': [
                                result.total_emissions,
                                calculate_transport_emissions('rail', match_row['transit_km'], 30, False),
                                calculate_transport_emissions('bus', match_row['driving_km'], 30, False)
                            ]
                        })

                        st.dataframe(transport_data)

                    # Environmental impact
                    with st.expander("Environmental Impact", expanded=True):
                        impact = calculate_equivalencies(result.total_emissions)

                        cols = st.columns(2)
                        with cols[0]:
                            st.metric("Cars Off Road", f"{impact['gasoline_vehicles_year']:.1f}")
                            st.metric("Trees Required", f"{impact['tree_seedlings_10years']:.0f}")
                        with cols[1]:
                            st.metric("Home Energy", f"{impact['homes_energy_year']:.1f}")
                            st.metric("Waste Recycled", f"{impact['waste_tons_recycled']:.1f}")

if __name__ == "__main__":
    create_analysis_page()
