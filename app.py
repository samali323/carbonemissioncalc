import streamlit as st
from src.models.emissions import EmissionsCalculator
from src.data.team_data import get_all_teams, get_team_airport, get_airport_coordinates
from src.utils.calculations import (
    calculate_transport_emissions,
    calculate_equivalencies,
    calculate_flight_time
)

# Initialize calculator
calculator = EmissionsCalculator()

# Set page config
st.set_page_config(
    page_title="Football Team Flight Emissions Calculator",
    page_icon="✈️",
    layout="wide"
)

# Title and description
st.title("⚽ Football Team Flight Emissions Calculator")
st.write("Calculate carbon emissions for football team travel")

# Check if coming from analysis page
if 'from_analysis' in st.session_state and st.session_state.from_analysis:
    initial_home = st.session_state.get('home_team_selection')
    initial_away = st.session_state.get('away_team_selection')
    initial_passengers = st.session_state.get('passengers', 30)
    initial_round_trip = st.session_state.get('is_round_trip', False)
    # Clear the flag
    st.session_state.from_analysis = False
else:
    initial_home = get_all_teams()[0]
    initial_away = get_all_teams()[0]
    initial_passengers = 30
    initial_round_trip = False

# Input section
st.markdown("### Input Details")

# Team selection
home_team = st.selectbox(
    "Home Team",
    get_all_teams(),
    index=get_all_teams().index(initial_home)
)

away_team = st.selectbox(
    "Away Team",
    get_all_teams(),
    index=get_all_teams().index(initial_away)
)

# Journey settings
col1, col2 = st.columns(2)
with col1:
    passengers = st.number_input(
        "Number of Passengers",
        min_value=1,
        value=initial_passengers
    )
with col2:
    is_round_trip = st.checkbox(
        "Round Trip",
        value=initial_round_trip
    )

# Calculate button
if st.button("Calculate Emissions"):
    try:
        # Get airports and coordinates
        home_airport = get_team_airport(home_team)
        away_airport = get_team_airport(away_team)

        if not home_airport or not away_airport:
            st.error("Airport not found for one or both teams")
        else:
            home_coords = get_airport_coordinates(home_airport)
            away_coords = get_airport_coordinates(away_airport)

            if not home_coords or not away_coords:
                st.error("Coordinates not found for one or both airports")
            else:
                # Calculate emissions
                result = calculator.calculate_flight_emissions(
                    origin_lat=home_coords['lat'],
                    origin_lon=home_coords['lon'],
                    dest_lat=away_coords['lat'],
                    dest_lon=away_coords['lon'],
                    passengers=passengers,
                    is_round_trip=is_round_trip
                )

                # Display results section
                st.markdown("---")  # Add separator
                st.subheader("Results")

                # Flight Details
                st.markdown("#### 🛫 Flight Details")
                details_cols = st.columns(2)
                with details_cols[0]:
                    st.write(f"🏠 **Home Team:** {home_team} ({home_airport})")
                    st.write(f"🏃 **Away Team:** {away_team} ({away_airport})")
                    st.write(f"📏 **Distance:** {result.distance_km:,.1f} km")
                with details_cols[1]:
                    st.write(f"✈️ **Flight Type:** {result.flight_type}")
                    st.write(f"🔄 **Round Trip:** {'Yes' if is_round_trip else 'No'}")
                    st.write(f"👥 **Passengers:** {passengers}")

                # Emissions Results
                st.markdown("#### 🌡️ Emissions Results")
                emission_cols = st.columns(2)
                with emission_cols[0]:
                    st.metric(
                        "Total CO₂ Emissions",
                        f"{result.total_emissions:,.2f} metric tons"
                    )
                with emission_cols[1]:
                    st.metric(
                        "Per Passenger",
                        f"{result.per_passenger:,.2f} metric tons"
                    )

                # Calculate alternative transport emissions
                base_distance = result.distance_km
                air_emissions = result.total_emissions
                rail_emissions = calculate_transport_emissions(
                    'rail', base_distance, passengers, is_round_trip
                )
                bus_emissions = calculate_transport_emissions(
                    'bus', base_distance, passengers, is_round_trip
                )

                # Transport comparison
                st.markdown("#### 🚊 Transport Mode Comparison")
                transport_df = {
                    'Mode': ['Air', 'Rail', 'Bus'],
                    'CO₂ (tons)': [
                        f"{air_emissions:.2f}",
                        f"{rail_emissions:.2f}",
                        f"{bus_emissions:.2f}"
                    ],
                    'CO₂ Saved (tons)': [
                        "0.00",
                        f"{air_emissions - rail_emissions:.2f}",
                        f"{air_emissions - bus_emissions:.2f}"
                    ]
                }
                st.table(transport_df)

                # Environmental Impact
                st.markdown("#### 🌍 Environmental Impact Equivalencies")
                impact = calculate_equivalencies(result.total_emissions)

                # Display selected equivalencies
                impact_cols = st.columns(4)
                with impact_cols[0]:
                    st.metric("🚗 Gasoline Vehicles (1 year)",
                              f"{impact['gasoline_vehicles_year']:.1f}")
                with impact_cols[1]:
                    st.metric("🏠 Homes Powered (1 year)",
                              f"{impact['homes_energy_year']:.1f}")
                with impact_cols[2]:
                    st.metric("🌳 Tree Seedlings (10 years)",
                              f"{impact['tree_seedlings_10years']:.1f}")
                with impact_cols[3]:
                    st.metric("♻️ Waste Recycled (tons)",
                              f"{impact['waste_tons_recycled']:.1f}")

    except Exception as e:
        st.error(f"Error calculating emissions: {str(e)}")

# Add helpful information in sidebar
with st.sidebar:
    st.header("About")
    st.write("""
    This calculator helps estimate the carbon emissions from football team travel.
    
    **Features:**
    - Calculate flight emissions
    - Compare different transport modes
    - View environmental impact
    - Round trip calculations
    """)

    st.header("Instructions")
    st.write("""
    1. Select home and away teams
    2. Enter number of passengers
    3. Choose round trip if applicable
    4. Click Calculate Emissions
    """)
