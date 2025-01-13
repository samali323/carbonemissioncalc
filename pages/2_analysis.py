import streamlit as st
import pandas as pd
import sqlite3
import os
from pathlib import Path
from src.data.team_data import get_team_airport, get_airport_coordinates
from src.models.emissions import EmissionsCalculator
from src.utils.calculations import calculate_distance

def get_db_path():
    """Get the correct database path"""
    # Try different possible locations for the database
    possible_paths = [
        Path(__file__).parent.parent / "data" / "routes.db",
        Path(__file__).parent.parent.parent / "data" / "routes.db",
        Path.cwd() / "data" / "routes.db",
        Path(os.path.abspath(os.path.dirname(__file__))) / ".." / "data" / "routes.db"
    ]

    for path in possible_paths:
        if path.exists():
            return str(path)

    # If no path found, return default path for error handling
    return str(possible_paths[0])

def load_data_from_db():
    """Load match and route data from SQLite database"""
    db_path = get_db_path()

    try:
        # Print path for debugging
        st.write(f"Attempting to connect to database at: {db_path}")

        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        conn = sqlite3.connect(db_path)

        # Load routes data
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

        return routes_df

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Please verify that the database file exists and the path is correct.")
        return None

def calculate_league_summary(df):
    """Calculate summary statistics by competition"""
    calculator = EmissionsCalculator()
    summary_data = []

    for _, row in df.iterrows():
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

                summary_data.append({
                    'Teams': f"{row['Home Team']} vs {row['Away Team']}",
                    'Distance (km)': distance,
                    'Emissions (tons)': emissions,
                    'Driving Time (hrs)': row['driving_hours'],
                    'Transit Time (hrs)': row['transit_hours']
                })

    return pd.DataFrame(summary_data)

def create_analysis_page():
    """Create the analysis page"""
    st.title("⚽ Football Travel Emissions Analysis")

    # Add database connection status
    db_path = get_db_path()
    st.sidebar.markdown("### Database Status")
    if os.path.exists(db_path):
        st.sidebar.success("Database file found")
    else:
        st.sidebar.error("Database file not found")
        st.sidebar.info(f"Looking for database at:\n{db_path}")
        return

    # Load data
    df = load_data_from_db()

    if df is None:
        return

    # Display basic statistics
    st.markdown("### 📊 Dataset Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Matches", len(df))
    with col2:
        st.metric("Unique Teams", len(set(df['Home Team'].unique()) | set(df['Away Team'].unique())))
    with col3:
        st.metric("Date Range", f"{df['last_updated'].min()[:10]} to {df['last_updated'].max()[:10]}")

    # Calculate and display summary
    st.markdown("### 🏆 League Summary")

    # Calculate summary statistics
    summary_df = calculate_league_summary(df)

    # Display summary metrics
    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
    with metrics_col1:
        st.metric("Average Distance", f"{summary_df['Distance (km)'].mean():,.0f} km")
    with metrics_col2:
        st.metric("Average Emissions", f"{summary_df['Emissions (tons)'].mean():,.1f} tons")
    with metrics_col3:
        st.metric("Total Emissions", f"{summary_df['Emissions (tons)'].sum():,.1f} tons")

    # Add filters
    st.markdown("### 🔍 Match Details")
    col1, col2 = st.columns(2)
    with col1:
        home_filter = st.selectbox("Filter by Home Team", ["All"] + sorted(df['Home Team'].unique().tolist()))
    with col2:
        away_filter = st.selectbox("Filter by Away Team", ["All"] + sorted(df['Away Team'].unique().tolist()))

    # Apply filters
    filtered_df = df.copy()
    if home_filter != "All":
        filtered_df = filtered_df[filtered_df['Home Team'] == home_filter]
    if away_filter != "All":
        filtered_df = filtered_df[filtered_df['Away Team'] == away_filter]

    # Display filtered data
    st.dataframe(
        filtered_df.sort_values('driving_km', ascending=False),
        hide_index=True,
        use_container_width=True
    )

    # Add visualization
    st.markdown("### 📈 Journey Analysis")
    chart_type = st.selectbox(
        "Select Chart Type",
        ["Distance Distribution", "Travel Time Comparison", "Emissions by Distance"]
    )

    if chart_type == "Distance Distribution":
        st.bar_chart(summary_df['Distance (km)'].value_counts(bins=20))
    elif chart_type == "Travel Time Comparison":
        st.line_chart(summary_df[['Driving Time (hrs)', 'Transit Time (hrs)']])
    else:
        st.scatter_chart(data=summary_df, x='Distance (km)', y='Emissions (tons)')

if __name__ == "__main__":
    create_analysis_page()
