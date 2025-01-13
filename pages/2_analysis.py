import streamlit as st
import pandas as pd
import sqlite3
import os
from pathlib import Path
from src.data.team_data import get_team_airport, get_airport_coordinates
from src.models.emissions import EmissionsCalculator
from src.utils.calculations import calculate_distance

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

def get_db_path():
    """Get the correct database path"""
    possible_paths = [
        Path(__file__).parent.parent / "data" / "routes.db",
        Path(__file__).parent.parent.parent / "data" / "routes.db",
        Path.cwd() / "data" / "routes.db"
    ]

    for path in possible_paths:
        if path.exists():
            return str(path)
    return str(possible_paths[0])

def load_data_from_db():
    """Load routes data from SQLite database"""
    db_path = get_db_path()

    try:
        conn = sqlite3.connect(db_path)

        # Load routes data including Competition
        routes_query = """
        SELECT 
            home_team as "Home Team",
            away_team as "Away Team",
            driving_duration/3600.0 as driving_hours,
            transit_duration/3600.0 as transit_hours,
            driving_distance/1000.0 as driving_km,
            transit_distance/1000.0 as transit_km,
            last_updated,
            Competition
        FROM routes
        WHERE Competition IS NOT NULL
        """
        routes_df = pd.read_sql_query(routes_query, conn)
        conn.close()

        return routes_df

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def calculate_competition_summary(df):
    """Calculate summary statistics by competition"""
    calculator = EmissionsCalculator()
    summary_data = []

    # Group by competition
    for competition in sorted(df['Competition'].unique()):
        competition_df = df[df['Competition'] == competition]
        total_matches = len(competition_df)
        total_emissions = 0
        total_distance = 0

        for _, row in competition_df.iterrows():
            # Get airports
            home_airport = get_team_airport(row['Home Team'])
            away_airport = get_team_airport(row['Away Team'])

            if home_airport and away_airport:
                # Get coordinates
                home_coords = get_airport_coordinates(home_airport)
                away_coords = get_airport_coordinates(away_airport)

                if home_coords and away_coords:
                    # Calculate distance and emissions
                    distance = calculate_distance(
                        home_coords['lat'], home_coords['lon'],
                        away_coords['lat'], away_coords['lon']
                    )
                    total_distance += distance

                    # Calculate emissions using ICAO calculator
                    result = calculator.icao_calculator.calculate_emissions(
                        distance_km=distance,
                        aircraft_type="A320",
                        cabin_class="business",
                        passengers=30,
                        cargo_tons=2.0,
                        is_international=True
                    )

                    emissions = result["emissions_total_kg"] / 1000  # Convert to metric tons
                    total_emissions += emissions

        # Add competition summary
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

def create_analysis_page():
    """Create the analysis page"""
    st.title("⚽ Football Travel Emissions Analysis")

    # Load data
    df = load_data_from_db()

    if df is None:
        return

    # Format time columns
    df['Driving Time'] = df['driving_hours'].apply(format_time)
    df['Transit Time'] = df['transit_hours'].apply(format_time)

    # Calculate and display summary
    st.markdown("### 🏆 Competition Summary")
    summary_df = calculate_competition_summary(df)

    # Display summary as a table
    st.dataframe(
        summary_df.round(2).sort_values('Total Emissions (tons)', ascending=False),
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
        # Filter home teams based on competition
        filtered_df = df if competition_filter == "All" else df[df['Competition'] == competition_filter]
        home_filter = st.selectbox(
            "Home Team",
            ["All"] + sorted(filtered_df['Home Team'].unique().tolist())
        )

    with col3:
        # Filter away teams based on home team
        if home_filter != "All":
            away_teams = df[df['Home Team'] == home_filter]['Away Team'].unique()
        else:
            away_teams = filtered_df['Away Team'].unique()
        away_filter = st.selectbox("Away Team", ["All"] + sorted(away_teams))

    # Apply filters
    filtered_df = df.copy()
    if competition_filter != "All":
        filtered_df = filtered_df[filtered_df['Competition'] == competition_filter]
    if home_filter != "All":
        filtered_df = filtered_df[filtered_df['Home Team'] == home_filter]
    if away_filter != "All":
        filtered_df = filtered_df[filtered_df['Away Team'] == away_filter]

    # Display match details
    st.markdown("### 📊 Match Details")

    # Select columns to display
    display_cols = [
        'Home Team', 'Away Team', 'Competition',
        'Driving Time', 'Transit Time',
        'Driving Distance (km)', 'Transit Distance (km)'
    ]

    # Prepare data for display
    display_df = filtered_df.copy()
    display_df['Driving Distance (km)'] = display_df['driving_km'].round(3)
    display_df['Transit Distance (km)'] = display_df['transit_km'].round(3)

    # Create single selectable dataframe
    selected_match = st.data_editor(
        display_df[display_cols],
        hide_index=True,
        use_container_width=True,
        column_config={
            "Home Team": st.column_config.TextColumn("Home Team", width="medium"),
            "Away Team": st.column_config.TextColumn("Away Team", width="medium"),
            "Competition": st.column_config.TextColumn("Competition", width="medium"),
            "Driving Time": st.column_config.TextColumn("Driving Time", width="small"),
            "Transit Time": st.column_config.TextColumn("Transit Time", width="small"),
            "Driving Distance (km)": st.column_config.NumberColumn("Driving Distance (km)", format="%.3f"),
            "Transit Distance (km)": st.column_config.NumberColumn("Transit Distance (km)", format="%.3f")
        },
        num_rows="dynamic"
    )

    # Handle match selection for calculator
    if st.button("Load Selected Match in Calculator"):
        if not filtered_df.empty:
            # Get the first selected match
            selected_row = filtered_df.iloc[0]

            # Store in session state using lowercase keys to match main app
            st.session_state.update({
                'home_team_selection': selected_row['Home Team'],
                'away_team_selection': selected_row['Away Team'],
                'passengers': 30,
                'is_round_trip': False,
                'from_analysis': True  # Flag to indicate selection came from analysis
            })

            # Provide feedback
            st.success(f"Loading match: {selected_row['Home Team']} vs {selected_row['Away Team']}")

            # Redirect to calculator page
            st.switch_page("app.py")  # or "app.py" depending on your main page name
    # Add extra statistics
    st.markdown("### 📈 Additional Statistics")
    stats_cols = st.columns(3)

    with stats_cols[0]:
        st.metric("Total Competitions", len(df['Competition'].unique()))
    with stats_cols[1]:
        st.metric("Total Teams", len(set(df['Home Team'].unique()) | set(df['Away Team'].unique())))
    with stats_cols[2]:
        st.metric("Total Matches", len(df))

if __name__ == "__main__":
    create_analysis_page()
